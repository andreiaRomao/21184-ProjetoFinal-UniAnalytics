import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "forms.db")

def connect_to_forms_db():
    return sqlite3.connect(DB_PATH)

def init_forms_table():
    conn = connect_to_forms_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pergunta TEXT NOT NULL,
            resposta TEXT NOT NULL,
            tipo_formulario TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()