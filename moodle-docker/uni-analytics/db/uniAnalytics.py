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
            question_id INTEGER NOT NULL,
            answer_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES forms_questions(id),
            FOREIGN KEY (answer_id) REFERENCES forms_answers(id)
        );
    """)

    # Tabela de dados de participação em fóruns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forum (
            userid INTEGER NOT NULL,
            role TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            post_type TEXT NOT NULL,
            parent INTEGER NOT NULL,
            timecreated DATETIME NOT NULL,
            lastrefreshdatetime DATETIME
        );
    """)

    # Tabela de interações gerais dos utilizadores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interacao (
            userid INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            tipo_interacao TEXT NOT NULL,
            timecreated DATETIME NOT NULL,
            lastrefreshdatetime DATETIME
        );
    """)

    # Tabela de progresso e notas dos alunos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grade_progress (
            coursemodule_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            module_type TEXT NOT NULL,
            userid INTEGER NOT NULL,
            completionstate INTEGER,
            itemname TEXT,
            groupid INTEGER,
            groupname TEXT,
            finalgrade REAL,
            timecreated DATETIME NOT NULL,
            lastrefreshdatetime DATETIME
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

    conn.commit()
    conn.close()