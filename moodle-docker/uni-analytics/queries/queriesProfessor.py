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
        WHERE m.name IN ('resource', 'page', 'url', 'book', 'folder', 'quiz', 'lesson');
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

def fetch_course_access_logs():
    conn = connect_to_moodle_db()
    query = """
        SELECT
            u.id AS userid,
            CONCAT(u.firstname, ' ', u.lastname) AS name,
            r.shortname AS role,
            c.id AS courseid,
            c.fullname AS course_name,
            FROM_UNIXTIME(l.timecreated) AS access_time
        FROM mdl_user u
        JOIN mdl_role_assignments ra ON ra.userid = u.id
        JOIN mdl_context ctx ON ctx.id = ra.contextid AND ctx.contextlevel = 50
        JOIN mdl_course c ON c.id = ctx.instanceid
        JOIN mdl_role r ON r.id = ra.roleid
        JOIN mdl_logstore_standard_log l 
          ON l.userid = u.id AND l.courseid = c.id
          AND l.action = 'viewed' AND l.target = 'course'
        WHERE u.deleted = 0;
    """
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print("Erro ao obter logs de acesso ao curso:", e)
        conn.close()
        return []
