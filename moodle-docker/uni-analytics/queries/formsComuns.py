from db.uniAnalytics import connect_to_uni_analytics_db
from db.moodleConnection import connect_to_moodle_db
from utils.logger import logger
from datetime import datetime

################### Moodle Queries ###################
# Função para obter dados do Moodle dos e-fólios
def fetch_all_efolios():
    conn = connect_to_moodle_db()
    query = """
        SELECT
            gi.id AS item_id,
            a.name,
            a.course AS course_id,
            c.fullname AS course_name,
            FROM_UNIXTIME(a.allowsubmissionsfromdate) AS start_date,
            FROM_UNIXTIME(a.duedate) AS end_date,
            FROM_UNIXTIME(gi.timemodified) AS time_created
        FROM mdl_assign a
        JOIN mdl_grade_items gi ON gi.iteminstance = a.id
        JOIN mdl_course c ON c.id = a.course
        WHERE gi.itemmodule = 'assign' AND a.name LIKE '%folio%';
    """
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print("Erro ao obter dados dos e-fólios:", e)
        conn.close()
        return []

################### Local Queries ###################
def pre_pos_obter_course_id_e_total_respostas(item_id):
    conn = connect_to_uni_analytics_db()
    cursor = conn.cursor()

    query = """
        SELECT 
            (SELECT course_id FROM efolios WHERE item_id = ?) AS course_id,
            form_type,
            COUNT(DISTINCT student_id) AS total_respostas
        FROM forms_student_answers
        WHERE item_id = ?
        GROUP BY form_type;;
    """
    cursor.execute(query, (item_id, item_id))
    rows = cursor.fetchall()
    conn.close()

    if rows:
        # Retorna uma lista de tuplos (course_id, form_type, total_respostas)
        return rows
    else:
        return []
    
# Função para obter dados locais de Efolios
def fetch_all_efolios_local():
    conn = connect_to_uni_analytics_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT item_id, name, course_id, course_name, start_date, end_date, 
               available_pre, available_pos, time_created, time_updated
        FROM efolios
    """)
    rows = cursor.fetchall()
    conn.close()

    # Converter para lista de dicionários
    colunas = [
        "item_id", "name", "course_id", "course_name", "start_date", "end_date",
        "available_pre", "available_pos", "time_created", "time_updated"
    ]
    return [dict(zip(colunas, row)) for row in rows]
