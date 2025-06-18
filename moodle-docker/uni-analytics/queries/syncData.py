from datetime import datetime
from db.uniAnalytics import connect_to_uni_analytics_db
from utils.logger import logger
from queries.queriesAluno import *
from queries.queriesComuns import *
from queries.formsComuns import *

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
        dados = fetch_all_completions()
        
        conn_local = connect_to_uni_analytics_db()
        cursor_local = conn_local.cursor()
        cursor_local.execute("DELETE FROM grade_progress")

        inseridos = 0
        ignorados = 0

        for row in dados:
            try:
                logger.debug(
                    f"[SYNC][GRADE_PROGRESS] Inserir: userid={row['userid']}, course_id={row['course_id']}, "
                    f"module_type={row['module_type']}, itemname={row['itemname']}, finalgrade={row['finalgrade']}, "
                    f"group={row['groupname']}, timecreated={row['timecreated']}"
                )

                cursor_local.execute("""
                    INSERT INTO grade_progress (
                        coursemodule_id, course_id, module_type, userid,
                        completionstate, itemname, groupid, groupname,
                        finalgrade, timecreated, lastrefreshdatetime
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["coursemodule_id"],
                    row["course_id"],
                    row["module_type"],
                    row["userid"],
                    row["completionstate"],
                    row["itemname"],
                    row["groupid"],
                    row["groupname"],
                    float(row["finalgrade"]) if row["finalgrade"] is not None else None,
                    row["timecreated"],
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

# Ponto de entrada principal para o scheduler
def executar_todos_os_syncs():
    sync_forum_data()
    sync_interacao_data()
    sync_grade_progress_data()
    sync_efolios_data()