import pandas as pd
from db.moodleConnection import connect_to_moodle_db
import queries.queriesGeral as qg

def fetch_conteudos_disponibilizados():
    conn = connect_to_moodle_db()
    query = """
        SELECT
            cm.id AS coursemodule_id,
            cm.course AS course_id,
            cm.added AS timecreated,
            m.name AS module_type
        FROM mdl_course_modules cm
        JOIN mdl_modules m ON m.id = cm.module
        WHERE m.name IN ('resource', 'page', 'url', 'book', 'folder', 'quiz');
    """
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print("Erro ao obter conteúdos disponibilizados:", e)
        conn.close()
        return []