import pandas as pd
from db.moodleConnection import connect_to_moodle_db

def fetch_user_course_data():
    conn = connect_to_moodle_db()
    query = """
        SELECT
          u.id AS userid,
          u.email AS email,
          CONCAT(u.firstname, ' ', u.lastname) AS name,
          r.shortname AS role,
          c.id AS courseid,
          c.fullname AS course_name,
          MAX(g.name) AS groupname
        FROM mdl_user u
        JOIN mdl_role_assignments ra ON ra.userid = u.id
        JOIN mdl_context ctx ON ctx.id = ra.contextid AND ctx.contextlevel = 50  -- 50 = nível de curso
        JOIN mdl_course c ON c.id = ctx.instanceid
        JOIN mdl_role r ON r.id = ra.roleid
        LEFT JOIN mdl_groups_members gm ON gm.userid = u.id
        LEFT JOIN mdl_groups g ON g.id = gm.groupid AND g.courseid = c.id
        GROUP BY u.id, u.email, name, r.shortname, c.id, c.fullname
        ORDER BY courseid, role, name;              
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
            p.parent AS parent,
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

def fetch_all_efolios():
    from db.moodleConnection import connect_to_moodle_db
    conn = connect_to_moodle_db()
    query = """
        SELECT
            gi.id AS item_id,
            a.name,
            FROM_UNIXTIME(a.allowsubmissionsfromdate) AS start_date,
            FROM_UNIXTIME(a.duedate) AS end_date
        FROM mdl_assign a
        JOIN mdl_grade_items gi ON gi.iteminstance = a.id
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
