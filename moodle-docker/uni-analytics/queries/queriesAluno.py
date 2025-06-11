import pandas as pd
from db.moodleConnection import connect_to_moodle_db

def fetch_all_completions():
    from db.moodleConnection import connect_to_moodle_db
    conn = connect_to_moodle_db()
    query = """      
WITH grupo_unico AS (
    SELECT gm.userid, g.id AS groupid, g.name AS groupname, g.courseid
    FROM mdl_groups_members gm
    JOIN mdl_groups g ON g.id = gm.groupid
)

SELECT
    cm.id AS coursemodule_id,
    cm.course AS course_id,
    cm.added AS timecreated,
    m.name AS module_type,
    cmc.userid,
    cmc.completionstate,
    COALESCE(gi.itemname, CONCAT('[ID ', cm.id, ']')) AS itemname,
    gu.groupid,
    gu.groupname,
    gg.finalgrade
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
            WHEN l.eventname LIKE '%mod_lesson%'   THEN 'Lições' 
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
            l.eventname LIKE '%mod_lesson%'   OR 
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
