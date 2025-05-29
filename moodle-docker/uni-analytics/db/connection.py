import os
import time
import mysql.connector
from mysql.connector import Error

def connect_to_moodle_db(retries=10, delay=3):
    for attempt in range(retries):
        try:
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                # host=os.getenv("DB_HOST", "db"), # Default to 'db' for Docker setup
                user=os.getenv("DB_USER", "moodle"),
                password=os.getenv("DB_PASS", "moodle"),
                database=os.getenv("DB_NAME", "moodle")
            )
            if conn.is_connected():
                print("Uni Analytics ligado à base de dados Moodle.")
                return conn
        except Error as e:
            print(f"Tentativa {attempt+1} falhou: {e}")
            time.sleep(delay)
    raise Exception("Não foi possível ligar à base de dados após várias tentativas.")
