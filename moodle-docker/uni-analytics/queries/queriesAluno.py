import pandas as pd
from db.connection import connect_to_moodle_db

def fetch_user_course_avaliation(aluno_id, course_id):
    conn = connect_to_moodle_db()
    query = """
        SELECT
            ROUND(
                SUM(CASE WHEN cmc.completionstate = 1 THEN 1 ELSE 0 END)
                / COUNT(*) * 100
            ,0) AS pct_concluido
        FROM mdl_course_modules cm
        JOIN mdl_modules m
            ON m.id = cm.module
        LEFT JOIN mdl_course_modules_completion cmc
            ON cm.id = cmc.coursemoduleid
            AND cmc.userid = %s
            AND cmc.completionstate = 1
        WHERE cm.course = %s
            AND cm.completion > 0
            AND m.name = 'assign';
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (aluno_id, course_id))
        row = cursor.fetchone()
        conn.close()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as e:
        print("Erro ao executar a query de progresso de avaliação:", e)
        conn.close()
        return 0

def fetch_user_course_formative(aluno_id, course_id):
    conn = connect_to_moodle_db()
    query = """
        SELECT
            ROUND(
                SUM(CASE WHEN cmc.completionstate = 1 THEN 1 ELSE 0 END)
                / COUNT(*) * 100
            ,0) AS pct_formativas
        FROM mdl_course_modules cm
        JOIN mdl_modules m
            ON m.id = cm.module
        LEFT JOIN mdl_course_modules_completion cmc
            ON cm.id = cmc.coursemoduleid
            AND cmc.userid = %s
            AND cmc.completionstate = 1
        WHERE cm.course = %s
            AND cm.completion > 0
            AND m.name IN ('page', 'resource');
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (aluno_id, course_id))
        row = cursor.fetchone()
        conn.close()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as e:
        print("Erro ao executar a query de progresso de formativas:", e)
        conn.close()
        return 0

def fetch_user_course_quizz(aluno_id, course_id):
    conn = connect_to_moodle_db()
    query = """
        SELECT
            ROUND(
                SUM(CASE WHEN cmc.completionstate = 1 THEN 1 ELSE 0 END)
                / COUNT(*) * 100
            ,0) AS pct_quiz
        FROM mdl_course_modules cm
        JOIN mdl_modules m
            ON m.id = cm.module
        LEFT JOIN mdl_course_modules_completion cmc
            ON cm.id = cmc.coursemoduleid
            AND cmc.userid = %s
            AND cmc.completionstate = 1
        WHERE cm.course = %s
            AND cm.completion > 0
            AND m.name = 'quiz';
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (aluno_id, course_id))
        row = cursor.fetchone()
        conn.close()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as e:
        print("Erro ao executar a query de progresso de quizz:", e)
        conn.close()
        return 0

def fetch_user_forum_created_posts(aluno_id, course_id):
    conn = connect_to_moodle_db()
    query = """
        SELECT COUNT(*) AS total_topicos_do_aluno
        FROM mdl_forum_posts p
        JOIN mdl_forum_discussions d
          ON p.discussion = d.id
        JOIN mdl_forum f
          ON d.forum = f.id
        JOIN mdl_user u
          ON p.userid = u.id
        JOIN mdl_context ctx
          ON ctx.contextlevel = 50
             AND ctx.instanceid = f.course
        JOIN mdl_role_assignments ra
          ON ra.contextid = ctx.id
             AND ra.userid    = u.id
        JOIN mdl_role r
          ON r.id        = ra.roleid
             AND r.shortname = 'student'
        WHERE
          f.course   = %s
          AND u.id    = %s
          AND p.parent = 0
          AND u.deleted = 0;
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (course_id, aluno_id))
        row = cursor.fetchone()
        conn.close()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as e:
        print("Erro ao buscar mensagens criadas no fórum:", e)
        conn.close()
        return 0

def fetch_user_forum_replies(aluno_id, course_id):
    conn = connect_to_moodle_db()
    query = """
        SELECT
          COUNT(*) AS total_respostas
        FROM mdl_forum_posts p
        JOIN mdl_forum_discussions d
          ON p.discussion = d.id
        JOIN mdl_forum f
          ON d.forum = f.id
        JOIN mdl_user u
          ON p.userid = u.id
        JOIN mdl_context ctx
          ON ctx.contextlevel = 50
             AND ctx.instanceid = f.course
        JOIN mdl_role_assignments ra
          ON ra.contextid = ctx.id
             AND ra.userid = u.id
        JOIN mdl_role r
          ON r.id = ra.roleid
             AND r.shortname = 'student'
        WHERE
          f.course   = %s
          AND p.parent <> 0
          AND u.deleted = 0
          AND p.userid  = %s;
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (course_id, aluno_id))
        row = cursor.fetchone()
        conn.close()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as e:
        print("Erro ao executar a query de respostas do fórum:", e)
        conn.close()
        return 0

def fetch_user_course_progress(aluno_id, course_id):
    conn = connect_to_moodle_db()
    query = """
        WITH stats AS (
            SELECT
                CASE
                    WHEN m.name = 'assign'             THEN 'Avaliação'
                    WHEN m.name IN ('page','resource') THEN 'Formativas'
                    WHEN m.name = 'quiz'               THEN 'Quiz'
                END AS categoria,
                COUNT(*) AS total_atividades,
                SUM(CASE WHEN cmc.completionstate = 1 THEN 1 ELSE 0 END) AS concluidas
            FROM mdl_course_modules cm
            JOIN mdl_modules m
              ON m.id = cm.module
            LEFT JOIN mdl_course_modules_completion cmc
              ON cm.id = cmc.coursemoduleid
                 AND cmc.userid = %s
                 AND cmc.completionstate = 1
            WHERE cm.course = %s
              AND cm.completion > 0
              AND m.name IN ('assign','page','resource','quiz')
            GROUP BY categoria
        )
        SELECT ROUND(
            SUM(concluidas) / NULLIF(SUM(total_atividades), 0) * 100, 0
        ) AS progresso_pct
        FROM stats;
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (aluno_id, course_id))
        row = cursor.fetchone()
        conn.close()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as e:
        print("Erro ao calcular progresso global:", e)
        conn.close()
        return 0

def fetch_user_course_performance(aluno_id, course_id):
    conn = connect_to_moodle_db()
    query = """
        SELECT
          desempenho.soma_efolios,
          CASE
            WHEN desempenho.soma_efolios <  3.0 THEN 'Crítico'
            WHEN desempenho.soma_efolios <  4.0 THEN 'Em Risco'
            ELSE                              'Expectável'
          END AS performance_level
        FROM (
          SELECT
            COALESCE(SUM(gg.finalgrade), 0) AS soma_efolios
          FROM mdl_grade_grades gg
          JOIN mdl_grade_items gi
            ON gg.itemid = gi.id
          WHERE gi.courseid = %s
            AND gg.userid   = %s
            AND gi.itemtype = 'mod'
            AND REPLACE(
                  REPLACE(
                    REPLACE(
                      REPLACE(
                        LOWER(gi.itemname),
                        ' ', ''
                      ),
                      '-', ''
                    ),
                    'ó', 'o'
                  ),
                  'é', 'e'
                ) LIKE '%efolio%'
        ) AS desempenho;
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (course_id, aluno_id))
        row = cursor.fetchone()
        conn.close()
        return row[1] if row and row[1] is not None else "Desconhecido"
    except Exception as e:
        print("Erro ao calcular desempenho do aluno:", e)
        conn.close()
        return "Erro"
