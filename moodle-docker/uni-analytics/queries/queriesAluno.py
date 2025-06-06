import pandas as pd
from db.moodleConnection import connect_to_moodle_db

def fetch_all_completions():
    from db.moodleConnection import connect_to_moodle_db
    conn = connect_to_moodle_db()
    query = """      
        SELECT
            cm.id AS coursemodule_id,
            cm.course AS course_id,
            cm.added AS timecreated,
            m.name AS module_type,
            cmc.userid,
            cmc.completionstate,
            gi.itemname,
            g.id AS groupid,
            g.name AS groupname,
            gg.finalgrade
        FROM mdl_course_modules cm
        JOIN mdl_modules m ON m.id = cm.module
        LEFT JOIN mdl_course_modules_completion cmc
            ON cm.id = cmc.coursemoduleid
        LEFT JOIN mdl_grade_items gi
            ON gi.iteminstance = cm.instance AND gi.itemtype = 'mod' AND gi.courseid = cm.course
        LEFT JOIN mdl_grade_grades gg
            ON gg.itemid = gi.id AND gg.userid = cmc.userid
        LEFT JOIN mdl_user_enrolments ue
            ON ue.userid = cmc.userid
        LEFT JOIN mdl_enrol e
            ON e.id = ue.enrolid AND e.courseid = cm.course
        LEFT JOIN mdl_groups_members gm
            ON gm.userid = cmc.userid
        LEFT JOIN mdl_groups g
            ON g.id = gm.groupid
        WHERE cm.completion > 0;        
    """
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print("Erro ao obter completions globais:", e)
        conn.close()
        return []

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
