import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "uniAnalytics.db")

def connect_to_forms_db():
    return sqlite3.connect(DB_PATH)

def init_forms_table():
    conn = connect_to_forms_db()
    cursor = conn.cursor()

    # Tabela de perguntas disponíveis nos formulários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forms_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_type TEXT NOT NULL,                       -- Tipo de formulário (ex: diagnóstico, final, etc.)
            question TEXT NOT NULL,                        -- Texto da pergunta
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabela com as respostas possíveis associadas a cada pergunta
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forms_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,                  -- ID da pergunta associada
            answer TEXT NOT NULL,                          -- Texto da resposta possível
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES forms_questions(id)
        );
    """)

    # Tabela que regista a resposta selecionada por cada aluno
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forms_student_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,                   -- ID do aluno
            question_id INTEGER NOT NULL,                  -- ID da pergunta
            answer_id INTEGER NOT NULL,                    -- ID da resposta escolhida
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES forms_questions(id),
            FOREIGN KEY (answer_id) REFERENCES forms_answers(id)
        );
    """)


    conn.commit()
    conn.close()