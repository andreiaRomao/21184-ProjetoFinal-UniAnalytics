import sqlite3
import os

def connect_to_forms_db():
    # Caminho absoluto relativo ao diretório atual
    db_path = os.path.join(os.path.dirname(__file__), "../db/forms.db")
    return sqlite3.connect(db_path)

    # Garante que a tabela existe
    init_forms_table(conn)

    return conn

def init_forms_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pergunta TEXT NOT NULL,
            resposta TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()