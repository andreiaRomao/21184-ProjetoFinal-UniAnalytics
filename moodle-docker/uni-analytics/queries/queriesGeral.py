import pandas as pd
from db.connection import connect_to_moodle_db

def fetch_user_course_data():
    conn = connect_to_moodle_db()
    query = """
        SELECT c.fullname AS curso, COUNT(u.id) AS total_alunos
        FROM mdl_user u
        JOIN mdl_user_enrolments ue ON ue.userid = u.id
        JOIN mdl_enrol e ON e.id = ue.enrolid
        JOIN mdl_course c ON c.id = e.courseid
        GROUP BY c.fullname
        ORDER BY total_alunos DESC
        LIMIT 10;
    """
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns)
    conn.close()
    return df
