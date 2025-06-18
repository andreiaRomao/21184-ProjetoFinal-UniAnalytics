import pandas as pd
from db.moodleConnection import connect_to_moodle_db
from db.uniAnalytics import connect_to_uni_analytics_db

################### Moodle Queries ###################
# Função para obter dados de Moodle das interações
def fetch_all_interacoes():
    conn = connect_to_moodle_db()
    query = """
        SELECT
          l.userid as user_id,
          l.courseid as course_id,
          l.timecreated as time_created,
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

################### Local Queries ###################
# Função para obter dados locais de interações de Moodle
def fetch_all_interacoes_local():
    conn = connect_to_uni_analytics_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, course_id, time_created, tipo_interacao, time_updated
        FROM interacao
    """)
    rows = cursor.fetchall()
    conn.close()

    # Converter para lista de dicionários
    colunas = ["user_id", "course_id", "time_created", "tipo_interacao", "time_updated"]
    return [dict(zip(colunas, row)) for row in rows]