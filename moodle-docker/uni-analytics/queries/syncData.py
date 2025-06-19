from datetime import datetime
from db.uniAnalytics import connect_to_uni_analytics_db
from utils.logger import logger
from queries.queriesAluno import *
from queries.queriesComuns import *
from queries.formsComuns import *
from queries.queriesProfessor import *

# Função para sincronizar os dados dos fóruns
def sync_forum_data():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        logger.debug("[SYNC] A obter dados dos fóruns a partir do Moodle...")
        dados = fetch_all_forum_posts()
        
        conn_local = connect_to_uni_analytics_db()
        cursor_local = conn_local.cursor()
        cursor_local.execute("DELETE FROM forum")

        inseridos = 0
        ignorados = 0

        for row in dados:
            try:
                logger.debug(f"[SYNC][FORUM] Inserir: user_id={row['user_id']}, role={row['role']}, course_id={row['course_id']}, post_type={row['post_type']}, time_created={row['time_created']}")
                cursor_local.execute("""
                    INSERT INTO forum (
                        post_id, user_id, role, course_id, post_type, parent, time_created, time_updated
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["post_id"],
                    row["user_id"],
                    row["role"],
                    row["course_id"],
                    row["post_type"],
                    row["parent"],                   
                    row["time_created"],
                    now # last_updated
                ))
                inseridos += 1
            except Exception as item_error:
                ignorados += 1
                logger.warning(f"[SYNC][FORUM] Registo ignorado por erro: {str(item_error)} | Dados: {row}")

        conn_local.commit()
        conn_local.close()
        logger.info(f"[SYNC] Forum sincronizado com {inseridos} registos. Ignorados: {ignorados}.")
    except Exception as e:
        logger.exception(f"[SYNC] Erro ao sincronizar dados de forum: {str(e)}")

# Função para sincronizar os dados de interações
def sync_interacao_data():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        logger.debug("[SYNC] A obter dados de interações a partir do Moodle...")
        dados = fetch_all_interacoes()
        
        conn_local = connect_to_uni_analytics_db()
        cursor_local = conn_local.cursor()
        cursor_local.execute("DELETE FROM interacao")

        inseridos = 0
        ignorados = 0

        for row in dados:
            try:
                logger.debug(f"[SYNC][INTERACAO] Inserir: user_id={row['user_id']}, course_id={row['course_id']}, tipo_interacao={row['tipo_interacao']}, time_created={row['time_created']}")
                cursor_local.execute("""
                    INSERT INTO interacao (
                        user_id, course_id, tipo_interacao, time_created, time_updated
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    row["user_id"],
                    row["course_id"],
                    row["tipo_interacao"],
                    row["time_created"],
                    now
                ))
                inseridos += 1
            except Exception as item_error:
                ignorados += 1
                logger.warning(f"[SYNC][INTERACAO] Registo ignorado por erro: {str(item_error)} | Dados: {row}")

        conn_local.commit()
        conn_local.close()
        logger.info(f"[SYNC] Interações sincronizadas com {inseridos} registos. Ignorados: {ignorados}.")
    except Exception as e:
        logger.exception(f"[SYNC] Erro ao sincronizar dados de interações: {str(e)}")

# Função para sincronizar os dados de progresso e notas
def sync_grade_progress_data():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        logger.debug("[SYNC] A obter dados de progresso a partir do Moodle...")
        dados = fetch_all_grade_progress()
        
        conn_local = connect_to_uni_analytics_db()
        cursor_local = conn_local.cursor()
        cursor_local.execute("DELETE FROM grade_progress")

        inseridos = 0
        ignorados = 0

        for row in dados:
            try:
                logger.debug(
                    f"[SYNC][GRADE_PROGRESS] Inserir: user_id={row['user_id']}, course_id={row['course_id']}, "
                    f"module_type={row['module_type']}, item_name={row['item_name']}, final_grade={row['final_grade']}, "
                    f"group={row['group_name']}, time_created={row['time_created']}"
                )

                cursor_local.execute("""
                    INSERT INTO grade_progress (
                        course_module_id, course_id, module_type, user_id,
                        completion_state, item_name, group_id, group_name,
                        final_grade, time_created, time_updated
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["course_module_id"],
                    row["course_id"],
                    row["module_type"],
                    row["user_id"],
                    row["completion_state"],
                    row["item_name"],
                    row["group_id"],
                    row["group_name"],
                    float(row["final_grade"]) if row["final_grade"] is not None else None,
                    row["time_created"],
                    now
                ))
                inseridos += 1
            except Exception as item_error:
                ignorados += 1
                logger.warning(f"[SYNC][GRADE_PROGRESS] Registo ignorado por erro: {str(item_error)} | Dados: {row}")

        conn_local.commit()
        conn_local.close()
        logger.info(f"[SYNC] Grade progress sincronizado com {inseridos} registos. Ignorados: {ignorados}.")
    except Exception as e:
        logger.exception(f"[SYNC] Erro ao sincronizar dados de grade_progress: {str(e)}")

# Função para sincronizar os dados dos e-fólios
def sync_efolios_data():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        logger.debug("[SYNC] A obter e-fólios a partir do Moodle...")
        dados = fetch_all_efolios()

        conn_local = connect_to_uni_analytics_db()
        cursor_local = conn_local.cursor()
        cursor_local.execute("DELETE FROM efolios")

        inseridos = 0
        ignorados = 0

        for row in dados:
            try:
                logger.debug(
                    f"[SYNC][EFOLIOS] Inserir: item_id={row['item_id']}, "
                    f"name={row['name']}, course_id={row['course_id']}, "
                    f"course_name={row['course_name']}, start={row['start_date']}, end={row['end_date']}, created={row['time_created']}"
                )
                cursor_local.execute("""
                    INSERT INTO efolios (
                        item_id, name, course_id, course_name, start_date, end_date,
                        available_pre, available_pos, time_created, time_updated
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["item_id"],
                    row["name"],
                    row["course_id"],
                    row["course_name"],
                    row["start_date"],
                    row["end_date"],
                    0,  # available_pre
                    0,  # available_pos
                    row["time_created"],  # time_created da origem
                    now  # time_updated no momento da sincronização
                ))
                inseridos += 1
            except Exception as item_error:
                ignorados += 1
                logger.warning(f"[SYNC][EFOLIOS] Registo ignorado por erro: {str(item_error)} | Dados: {row}")

        conn_local.commit()
        conn_local.close()
        logger.info(f"[SYNC] E-fólios sincronizados com {inseridos} registos. Ignorados: {ignorados}.")
    except Exception as e:
        logger.exception(f"[SYNC] Erro ao sincronizar dados de e-fólios: {str(e)}")

# Função para sincronizar os dados dos cursos e utilizadores
def sync_user_course_data():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        logger.debug("[SYNC] A obter dados de cursos e utilizadores a partir do Moodle...")
        dados = fetch_all_user_course_data()

        conn_local = connect_to_uni_analytics_db()
        cursor_local = conn_local.cursor()
        cursor_local.execute("DELETE FROM course_data")

        inseridos = 0
        ignorados = 0

        for _, row in dados.iterrows():
            try:
                logger.debug(
                    f"[SYNC][COURSE_DATA] Inserir: user_id={row['user_id']}, email={row['email']}, "
                    f"name={row['name']}, role={row['role']}, course_id={row['course_id']}, "
                    f"course_name={row['course_name']}, group_name={row['group_name']}, "
                    f"time_created={row['time_created']}"
                )
                cursor_local.execute("""
                    INSERT INTO course_data (
                        user_id, email, name, role, course_id, course_name,
                        group_name, time_created, time_updated
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["user_id"],
                    row["email"],
                    row["name"],
                    row["role"],
                    row["course_id"],
                    row["course_name"],
                    row["group_name"],
                    row["time_created"],
                    now
                ))
                inseridos += 1
            except Exception as item_error:
                ignorados += 1
                logger.warning(f"[SYNC][COURSE_DATA] Registo ignorado por erro: {str(item_error)} | Dados: {row.to_dict()}")

        conn_local.commit()
        conn_local.close()
        logger.info(f"[SYNC] Dados de cursos/utilizadores sincronizados com {inseridos} registos. Ignorados: {ignorados}.")
    except Exception as e:
        logger.exception(f"[SYNC] Erro ao sincronizar dados de cursos/utilizadores: {str(e)}")

# Função para sincronizar os conteúdos disponibilizados
def sync_conteudos_disponibilizados():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        logger.debug("[SYNC] A obter conteúdos disponibilizados do Moodle...")
        dados = fetch_all_conteudos_disponibilizados()

        conn_local = connect_to_uni_analytics_db()
        cursor_local = conn_local.cursor()
        cursor_local.execute("DELETE FROM conteudos_disponibilizados")

        inseridos = 0
        for row in dados:
            logger.debug(
                f"[SYNC][CONTEUDOS] Inserir: course_module_id={row['course_module_id']}, "
                f"course_id={row['course_id']}, module_type={row['module_type']}, "
                f"time_created={row['time_created']}, time_updated={now}"
            )
            cursor_local.execute("""
                INSERT INTO conteudos_disponibilizados (
                    course_module_id, course_id, module_type, time_created, time_updated
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                row["course_module_id"],
                row["course_id"],
                row["module_type"],
                row["time_created"],
                now
            ))
            inseridos += 1

        conn_local.commit()
        conn_local.close()
        logger.info(f"[SYNC] Conteúdos disponibilizados sincronizados: {inseridos} registos.")
    except Exception as e:
        logger.exception(f"[SYNC] Erro ao sincronizar conteúdos disponibilizados: {str(e)}")

# Função para sincronizar os logs de acesso ao curso
def sync_course_access_logs():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        logger.debug("[SYNC] A obter logs de acesso ao curso do Moodle...")
        dados = fetch_all_course_access_logs()

        conn_local = connect_to_uni_analytics_db()
        cursor_local = conn_local.cursor()
        cursor_local.execute("DELETE FROM course_access_logs")

        inseridos = 0
        for row in dados:
            logger.debug(
                f"[SYNC][ACESSOS] Inserir: user_id={row['user_id']}, name={row['name']}, "
                f"role={row['role']}, course_id={row['course_id']}, course_name={row['course_name']}, "
                f"access_time={row['access_time']}, time_updated={now}"
            )
            cursor_local.execute("""
                INSERT INTO course_access_logs (
                    user_id, name, role, course_id, course_name, access_time, time_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                row["user_id"],
                row["name"],
                row["role"],
                row["course_id"],
                row["course_name"],
                row["access_time"],
                now
            ))
            inseridos += 1

        conn_local.commit()
        conn_local.close()
        logger.info(f"[SYNC] Logs de acesso ao curso sincronizados: {inseridos} registos.")
    except Exception as e:
        logger.exception(f"[SYNC] Erro ao sincronizar logs de acesso ao curso: {str(e)}")

# Ponto de entrada principal para o scheduler
def executar_todos_os_syncs():
    sync_forum_data()
    sync_interacao_data()
    sync_grade_progress_data()
    sync_efolios_data()
    sync_user_course_data()
    sync_conteudos_disponibilizados()
    sync_course_access_logs()