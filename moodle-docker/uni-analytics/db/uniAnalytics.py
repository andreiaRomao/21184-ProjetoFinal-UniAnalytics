import sqlite3
import os

# Caminho da base de dados local
DB_PATH = os.path.join(os.path.dirname(__file__), "uniAnalytics.db")

# Função que estabelece ligação à base de dados
def connect_to_uni_analytics_db():
    return sqlite3.connect(DB_PATH)

# Função para inicializar todas as tabelas necessárias no sistema
def init_uni_analytics_db():
    conn = connect_to_uni_analytics_db()
    cursor = conn.cursor()

    # Tabela de perguntas dos formulários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forms_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_type TEXT NOT NULL,
            question TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabela de respostas possíveis às perguntas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forms_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            answer TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES forms_questions(id)
        );
    """)

    # Tabela de respostas dadas pelos alunos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forms_student_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            answer_id INTEGER NOT NULL,
            form_type TEXT NOT NULL, 
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES forms_questions(id),
            FOREIGN KEY (answer_id) REFERENCES forms_answers(id)
        );
    """)

    # Tabela de dados de participação em fóruns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forum (
            post_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            post_type TEXT NOT NULL,
            parent INTEGER NOT NULL,
            time_created DATETIME NOT NULL,
            time_updated DATETIME
        );
    """)

    # Tabela de interações gerais dos utilizadores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interacao (
            userid INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            tipo_interacao TEXT NOT NULL,
            time_created DATETIME NOT NULL,
            time_updated DATETIME
        );
    """)

    # Tabela de progresso e notas dos alunos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grade_progress (
            course_module_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            module_type TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            completion_state INTEGER,
            item_name TEXT,
            group_id INTEGER,
            group_name TEXT,
            final_grade REAL,
            time_created DATETIME,
            time_updated DATETIME
        );
    """)

    # Cria a tabela de utilizadores locais com email, password e role.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            moodle_user_id INTEGER NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('aluno', 'professor', 'admin')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabela com os e-fólios importados do Moodle
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS efolios (
            item_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            course_name TEXT NOT NULL,
            start_date DATETIME NOT NULL,
            end_date DATETIME NOT NULL,
            available_pre INTEGER DEFAULT 0,
            available_pos INTEGER DEFAULT 0,
            time_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            time_updated DATETIME DEFAULT CURRENT_TIMESTAMP           
        );
    """)

    # Tabela com os dados dos cursos e alunos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_data (
            user_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            course_name TEXT NOT NULL,
            group_name TEXT,
            time_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            time_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabela para os conteúdos disponibilizados pelos professores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conteudos_disponibilizados (
            course_module_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            module_type TEXT NOT NULL,
            time_created DATETIME NOT NULL,
            time_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabela para os logs de acesso ao curso
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_access_logs (
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            course_name TEXT NOT NULL,
            access_time DATETIME NOT NULL,
            time_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()