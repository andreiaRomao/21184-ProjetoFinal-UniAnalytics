from db.uniAnalytics import connect_to_uni_analytics_db
from utils.logger import logger

def pre_pos_obter_course_id_e_total_respostas(item_id):
    conn = connect_to_uni_analytics_db()
    cursor = conn.cursor()

    query = """
        SELECT 
          (SELECT course_id FROM efolios WHERE item_id = ?) AS course_id,
          (SELECT COUNT(DISTINCT student_id) 
           FROM forms_student_answers 
           WHERE form_type = 'pre' AND item_id = ?) AS total_respostas;
    """
    cursor.execute(query, (item_id, item_id))
    row = cursor.fetchone()
    conn.close()

    if row:
        course_id, total_respostas = row
        return course_id, total_respostas
    else:
        return None, 0

def fetch_all_efolios():
    from db.moodleConnection import connect_to_moodle_db
    conn = connect_to_moodle_db()
    query = """
        SELECT
            gi.id AS item_id,
            a.name,
            a.course AS course_id,
            c.fullname AS course_name,
            FROM_UNIXTIME(a.allowsubmissionsfromdate) AS start_date,
            FROM_UNIXTIME(a.duedate) AS end_date
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