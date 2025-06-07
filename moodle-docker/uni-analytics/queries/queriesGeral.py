import pandas as pd
from db.moodleConnection import connect_to_moodle_db

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

def fetch_all_forum_posts():
    from db.moodleConnection import connect_to_moodle_db
    conn = connect_to_moodle_db()
    query = """
        SELECT
            u.id AS userid,
            u.firstname,
            u.lastname,
            COALESCE(r.shortname, 'none') AS role,
            f.course AS course_id,
            p.id AS post_id,
            p.created AS timecreated,
            CASE
                WHEN p.parent = 0 THEN 'topic'
                ELSE 'reply'
            END AS post_type
        FROM mdl_forum_posts p
        JOIN mdl_forum_discussions d ON p.discussion = d.id
        JOIN mdl_forum f ON d.forum = f.id
        JOIN mdl_user u ON p.userid = u.id
        LEFT JOIN mdl_context ctx ON ctx.contextlevel = 50 AND ctx.instanceid = f.course
        LEFT JOIN mdl_role_assignments ra ON ra.contextid = ctx.id AND ra.userid = u.id
        LEFT JOIN mdl_role r ON r.id = ra.roleid
        WHERE u.deleted = 0;
    """
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print("Erro ao obter dados dos fóruns:", e)
        conn.close()
        return []