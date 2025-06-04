import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "forms.db")

def connect_to_forms_db():
    return sqlite3.connect(DB_PATH)

def init_forms_table():
    conn = connect_to_forms_db()
    cursor = conn.cursor()

    # Tabela de perguntas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS formularios_perguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_formulario TEXT NOT NULL,
            pergunta TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabela de respostas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS formularios_respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pergunta_id INTEGER NOT NULL,
            resposta TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pergunta_id) REFERENCES formularios_perguntas(id)
        );
    """)

    # Tabela de respostas dadas pelos alunos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos_respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER NOT NULL,
            pergunta_id INTEGER NOT NULL,
            resposta TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pergunta_id) REFERENCES formularios_perguntas(id)
        );
    """)

    conn.commit()
    conn.close()