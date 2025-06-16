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
