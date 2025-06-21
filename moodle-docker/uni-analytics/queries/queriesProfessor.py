import pandas as pd
from db.moodleConnection import connect_to_moodle_db
from db.uniAnalytics import connect_to_uni_analytics_db

################### Moodle Queries ###################
# Função para obter os conteudos disponibilizados por professores
def fetch_all_conteudos_disponibilizados():
    conn = connect_to_moodle_db()
    query = """
        SELECT
            cm.id AS course_module_id,
            cm.course AS course_id,
            cm.added AS time_created,
            m.name AS module_type
        FROM mdl_course_modules cm
        JOIN mdl_modules m ON m.id = cm.module
        WHERE m.name IN ('resource', 'page', 'url', 'book', 'folder', 'quiz', 'lesson', 'forum', 'scorm');
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

# Função para obter informação sobre acessos
def fetch_all_course_access_logs():
    conn = connect_to_moodle_db()
    query = """
        SELECT
            u.id AS user_id,
            CONCAT(u.firstname, ' ', u.lastname) AS name,
            r.shortname AS role,
            c.id AS course_id,
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

################### Local Queries ###################
# Conteúdos disponibilizados localmente
def fetch_conteudos_disponibilizados_local():
    conn = connect_to_uni_analytics_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            course_module_id,
            course_id,
            module_type,
            time_created,
            time_updated
        FROM conteudos_disponibilizados
    """)
    rows = cursor.fetchall()
    conn.close()

    colunas = ["course_module_id", "course_id", "module_type", "time_created", "time_updated"]

    return [dict(zip(colunas, row)) for row in rows]

# Logs de acesso ao curso localmente
def fetch_course_access_logs_local():
    conn = connect_to_uni_analytics_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            user_id,
            name,
            role,
            course_id,
            course_name,
            access_time,
            time_updated
        FROM course_access_logs
    """)
    rows = cursor.fetchall()
    conn.close()

    colunas = ["user_id", "name", "role", "course_id", "course_name", "access_time", "time_updated"]
    return [dict(zip(colunas, row)) for row in rows]