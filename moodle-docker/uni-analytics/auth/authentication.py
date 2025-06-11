import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from db.moodleConnection import connect_to_moodle_db
from utils.logger import logger 

# Função para obter toda a informação relevante do utilizador a partir do Moodle
def get_user_info_from_moodle(email):
    try:
        conn = connect_to_moodle_db()
        with conn.cursor(dictionary=True) as cursor:
            query = """
                SELECT
                    u.id AS moodle_user_id,
                    u.email,
                    u.firstname,
                    u.lastname,
                    r.shortname AS moodle_role
                FROM mdl_user u
                JOIN mdl_role_assignments ra ON u.id = ra.userid
                JOIN mdl_role r ON r.id = ra.roleid
                WHERE u.email = %s
                LIMIT 1;
            """
            logger.debug(f"Query ao Moodle: {query.strip()} | Parâmetro: {email}")
            cursor.execute(query, (email,))
            result = cursor.fetchone()
            logger.debug(f"Resultado da query para {email}: {result}")
        conn.close()

        if result:
            # Se o utilizador não tiver role atribuída no Moodle
            if not result.get('moodle_role'):
                logger.warning(f"Utilizador {email} existe no Moodle mas não tem role atribuída.")
                return {'error': 'sem_role'}

            # Mapeamento de roles Moodle → sistema local
            role_map = {
                'student': 'aluno',
                'editingteacher': 'professor',
                'teacher': 'professor',
                'manager': 'admin'
            }
            result['mapped_role'] = role_map.get(result['moodle_role'], 'desconhecido')
            return result
        else:
            return None
    except Exception as e:
        logger.error(f"Erro ao obter informações do utilizador {email} no Moodle: {e}")
        return None

# Função para registar o utilizador localmente, caso exista no Moodle
def register_user(email, password):
    try:
        # Verifica se já existe localmente
        conn = sqlite3.connect('db/uniAnalytics.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            logger.info(f"Tentativa de registo com email já existente: {email}")
            conn.close()
            return False, "Email já registado localmente.", None

        # Vai buscar as informações do Moodle
        user_info = get_user_info_from_moodle(email)
        if not user_info:
            logger.info(f"Tentativa de registo com email não existente no Moodle: {email}")
            conn.close()
            return False, "Email não encontrado no Moodle.", None

        # Se não tem role atribuída
        if user_info.get('error') == 'sem_role':
            logger.warning(f"Falha no registo do utilizador: {email} — Email encontrado mas sem role associada.")
            conn.close()
            return False, "Utilizador encontrado no Moodle mas sem role associada.", None

        role = user_info['mapped_role']
        if role == 'desconhecido':
            logger.warning(f"Registo falhado para {email}: role inválido ({user_info['moodle_role']})")
            conn.close()
            return False, "Role do utilizador não autorizado ou não identificado.", None

        # Gera o hash da password e insere na base de dados local
        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (moodle_user_id, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (user_info['moodle_user_id'], email, password_hash, role))
        conn.commit()
        conn.close()

        logger.info(f"Utilizador registado com sucesso: {email} ({role})")
        return True, f"Conta criada com sucesso com o role: {role}", user_info
    except Exception as e:
        logger.error(f"Erro no registo do utilizador {email}: {e}")
        return False, "Erro interno ao registar o utilizador.", None

# Função para autenticar um utilizador local (login)
def authenticate_user(email, password):
    try:
        conn = sqlite3.connect('db/uniAnalytics.db')
        cursor = conn.cursor()

        # Vai buscar o hash da password, id do utilizador e role
        cursor.execute("SELECT moodle_user_id, password_hash, role FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()

        # Verifica se encontrou e se a password está correta
        if result and check_password_hash(result[1], password):
            moodle_user_id, _, role = result
            logger.info(f"Login bem-sucedido: {email}")
            return {
                "moodle_user_id": moodle_user_id,
                "mapped_role": role
            }
        else:
            logger.warning(f"Tentativa de login falhada para {email}")
            return None
    except Exception as e:
        logger.error(f"Erro na autenticação do utilizador {email}: {e}")
        return None