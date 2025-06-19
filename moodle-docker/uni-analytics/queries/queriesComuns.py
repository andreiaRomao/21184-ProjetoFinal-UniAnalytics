import pandas as pd
from db.moodleConnection import connect_to_moodle_db
from db.uniAnalytics import connect_to_uni_analytics_db

################### Moodle Queries ###################
# Função para obter dados do Moodle dos cursos e alunos
def fetch_all_user_course_data():
    conn = connect_to_moodle_db()
    query = """
        SELECT
          u.id AS user_id,
          u.email AS email,
          CONCAT(u.firstname, ' ', u.lastname) AS name,
          r.shortname AS role,
          c.id AS course_id,
          c.fullname AS course_name,
          MAX(g.name) AS group_name,
          u.timecreated AS time_created
        FROM mdl_user u
        JOIN mdl_role_assignments ra ON ra.userid = u.id
        JOIN mdl_context ctx ON ctx.id = ra.contextid AND ctx.contextlevel = 50
        JOIN mdl_course c ON c.id = ctx.instanceid
        JOIN mdl_role r ON r.id = ra.roleid
        LEFT JOIN mdl_groups_members gm ON gm.userid = u.id
        LEFT JOIN mdl_groups g ON g.id = gm.groupid AND g.courseid = c.id
        GROUP BY u.id, u.email, name, r.shortname, c.id, c.fullname, u.timecreated
        ORDER BY course_id, role, name;           
    """
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns)
    conn.close()
    return df

# Função para obter dados do Moodle dos fóruns
def fetch_all_forum_posts():
    from db.moodleConnection import connect_to_moodle_db
    conn = connect_to_moodle_db()
    query = """
        SELECT
            u.id AS user_id,
            u.firstname,
            u.lastname,
            COALESCE(r.shortname, 'none') AS role,
            f.course AS course_id,
            p.id AS post_id,
            p.parent AS parent,
            p.created AS time_created,
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

# Função para obter dados do Moodle das notas e progresso dos alunos
def fetch_all_grade_progress():
    conn = connect_to_moodle_db()
    query = """      
    WITH grupo_unico AS (
        SELECT gm.userid, g.id AS groupid, g.name AS groupname, g.courseid
        FROM mdl_groups_members gm
        JOIN mdl_groups g ON g.id = gm.groupid
    )
    
    SELECT
        cm.id AS course_module_id,
        cm.course AS course_id,
        cm.added AS time_created,
        m.name AS module_type,
        cmc.userid AS user_id,
        cmc.completionstate AS completion_state,
        COALESCE(gi.itemname, CONCAT('[ID ', cm.id, ']')) AS item_name,
        gu.groupid AS group_id,
        gu.groupname AS group_name,
        gg.finalgrade AS final_grade
    FROM mdl_course_modules cm
    JOIN mdl_modules m 
        ON m.id = cm.module
    INNER JOIN mdl_course_modules_completion cmc 
        ON cm.id = cmc.coursemoduleid
    LEFT JOIN mdl_grade_items gi 
        ON gi.iteminstance = cm.instance 
       AND gi.itemtype = 'mod' 
       AND gi.itemmodule = m.name          -- garante correspondência com o tipo correto (assign, quiz, lesson...)
       AND gi.courseid = cm.course
    LEFT JOIN mdl_grade_grades gg 
        ON gg.itemid = gi.id 
       AND gg.userid = cmc.userid
    LEFT JOIN grupo_unico gu 
        ON gu.userid = cmc.userid 
       AND gu.courseid = cm.course
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
    
################### Local Queries ###################
# Função para obter dados locais de fóruns de Moodle
def fetch_all_forum_posts_local():
    conn = connect_to_uni_analytics_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT post_id, user_id, role, course_id, post_type, parent, time_created
        FROM forum
    """)
    rows = cursor.fetchall()
    conn.close()

    # Converter para lista de dicionários
    colunas = ["post_id", "user_id", "role", "course_id", "post_type", "parent", "time_created"]
    return [dict(zip(colunas, row)) for row in rows]

# Função para obter dados locais de progresso e notas dos alunos
def fetch_all_grade_progress_local():
    conn = connect_to_uni_analytics_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT course_module_id, course_id, module_type, user_id,
               completion_state, item_name, group_id, group_name,
               final_grade, time_created, time_updated
        FROM grade_progress
    """)
    rows = cursor.fetchall()
    conn.close()

    # Converter para lista de dicionários
    colunas = [
        "course_module_id", "course_id", "module_type", "user_id",
        "completion_state", "item_name", "group_id", "group_name",
        "final_grade", "time_created", "time_updated"
    ]
    return [dict(zip(colunas, row)) for row in rows]

# Função para obter dados locais de cursos e alunos
def fetch_all_user_course_data_local():
    conn = connect_to_uni_analytics_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            user_id,
            email,
            name,
            role,
            course_id,
            course_name,
            group_name, 
            time_created, 
            time_updated
        FROM course_data
    """)
    rows = cursor.fetchall()
    conn.close()

    # Converter para lista de dicionários
    colunas = ["user_id", "email", "name", "role", "course_id", "course_name", "group_name", "time_created", "time_updated"]
    return [dict(zip(colunas, row)) for row in rows]