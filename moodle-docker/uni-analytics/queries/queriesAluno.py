import pandas as pd
from db.moodleConnection import connect_to_moodle_db


def fetch_all_interacoes():
    from db.moodleConnection import connect_to_moodle_db
    conn = connect_to_moodle_db()
    query = """
        SELECT
          l.userid,
          l.courseid,
          l.timecreated,
          CASE
            WHEN l.eventname LIKE '%mod_resource%' THEN 'Ficheiros'
            WHEN l.eventname LIKE '%mod_page%'     THEN 'Páginas'
            WHEN l.eventname LIKE '%mod_url%'      THEN 'Links'
            WHEN l.eventname LIKE '%mod_book%'     THEN 'Livros'
            WHEN l.eventname LIKE '%mod_folder%'   THEN 'Pastas'
            WHEN l.eventname LIKE '%mod_quiz%'     THEN 'Quizzes'
            WHEN l.eventname LIKE '%mod_lesson%'   THEN 'Lições' 
            WHEN l.eventname LIKE '%mod_assign%'   THEN 'Tarefas'
            WHEN l.eventname LIKE '%mod_forum%'    THEN 'Fóruns'
            ELSE 'Outro'
          END AS tipo_interacao
        FROM mdl_logstore_standard_log l
        WHERE l.edulevel = 2
          AND l.action IN ('viewed', 'launched')
          AND (
            l.eventname LIKE '%mod_resource%' OR
            l.eventname LIKE '%mod_page%'     OR
            l.eventname LIKE '%mod_url%'      OR
            l.eventname LIKE '%mod_book%'     OR
            l.eventname LIKE '%mod_folder%'   OR
            l.eventname LIKE '%mod_quiz%'     OR
            l.eventname LIKE '%mod_lesson%'   OR 
            l.eventname LIKE '%mod_assign%'   OR
            l.eventname LIKE '%mod_forum%'
          );
    """

    conn = connect_to_moodle_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print("Erro ao obter dados das interações:", e)
        conn.close()
        return []
