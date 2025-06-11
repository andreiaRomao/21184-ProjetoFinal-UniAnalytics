import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from db.moodleConnection import get_moodle_connection
from utils.logger import logger  # ← Importa o logger personalizado

# Função para verificar se o email existe na base de dados do Moodle
def email_exists_in_moodle(email):
    try:
        conn = get_moodle_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM mdl_user WHERE email = %s", (email,))
            result = cursor.fetchone()
        conn.close()
        logger.debug(f"Verificação de email no Moodle: {email} {'existe' if result else 'não existe'}.")
        return result is not None
    except Exception as e:
        logger.error(f"Erro ao verificar email no Moodle: {email} — {e}")
        return False

# Função para obter o papel do utilizador no Moodle e traduzi-lo para papel local
def get_user_role_from_moodle(email):
    try:
        conn = get_moodle_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT r.shortname
                FROM mdl_user u
                JOIN mdl_role_assignments ra ON u.id = ra.userid
                JOIN mdl_role r ON ra.roleid = r.id
                WHERE u.email = %s
                LIMIT 1;
            """, (email,))
            result = cursor.fetchone()
        conn.close()

        if result:
            role_map = {
                'student': 'aluno',
                'editingteacher': 'professor',
                'teacher': 'professor',
                'manager': 'admin'
            }
            role = role_map.get(result['shortname'], 'desconhecido')
            logger.debug(f"Role obtido do Moodle para {email}: {result['shortname']} → {role}")
            return role
        else:
            logger.warning(f"Não foi encontrado role para o email {email} no Moodle.")
            return None
    except Exception as e:
        logger.error(f"Erro ao obter o role do utilizador no Moodle ({email}): {e}")
        return None

# Função para registar o utilizador localmente, caso exista no Moodle
def register_user(email, password):
    try:
        conn = sqlite3.connect('db/uniAnalytics.db')
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            logger.info(f"Tentativa de registo com email já existente: {email}")
            conn.close()
            return False, "Email já registado localmente."

        if not email_exists_in_moodle(email):
            logger.info(f"Tentativa de registo com email não existente no Moodle: {email}")
            conn.close()
            return False, "Email não encontrado no Moodle."

        role = get_user_role_from_moodle(email)
        if role == 'desconhecido' or not role:
            logger.warning(f"Registo falhado para {email}: role inválido ({role})")
            conn.close()
            return False, "Role do utilizador não autorizado ou não identificado."

        password_hash = generate_password_hash(password)
        cursor.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                       (email, password_hash, role))
        conn.commit()
        conn.close()

        logger.info(f"Utilizador registado com sucesso: {email} ({role})")
        return True, f"Conta criada com sucesso com o role: {role}"
    except Exception as e:
        logger.error(f"Erro no registo do utilizador {email}: {e}")
        return False, "Erro interno ao registar o utilizador."

# Função para autenticar um utilizador local (login)
def authenticate_user(email, password):
    try:
        conn = sqlite3.connect('db/uniAnalytics.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()

        if result and check_password_hash(result[0], password):
            logger.info(f"Login bem-sucedido: {email}")
            return True
        else:
            logger.warning(f"Tentativa de login falhada para {email}")
            return False
    except Exception as e:
        logger.error(f"Erro na autenticação do utilizador {email}: {e}")
        return False

# Função auxiliar para obter o papel de um utilizador local autenticado
def get_user_role(email):
    try:
        conn = sqlite3.connect('db/uniAnalytics.db')
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        if result:
            logger.debug(f"Role local de {email}: {result[0]}")
        else:
            logger.warning(f"Role não encontrado para {email}")
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Erro ao obter o role local de {email}: {e}")
        return None