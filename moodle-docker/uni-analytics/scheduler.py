import os
import time
import schedule
from datetime import datetime, timedelta
from queries.syncData import executar_todos_os_syncs
from utils.logger import logger
from db.uniAnalytics import connect_to_uni_analytics_db

# Job que executa a sincronização dos dados de Moodle para a base de dados uniAnalytics
def job_sync_all():
    logger.info("[JOB] Início da sincronização geral.")
    executar_todos_os_syncs()
    logger.info("[JOB] Sincronização completa.")

# Job que actualiza disponibilização dos formulários de acordo com janela temporária
def job_validar_formularios():
    logger.info("[JOB] Início da verificação de disponibilidade de formulários.")
    try:
        conn = connect_to_uni_analytics_db()
        cursor = conn.cursor()
        hoje = datetime.now()

        cursor.execute("SELECT item_id, start_date, end_date FROM efolios")
        efolios = cursor.fetchall()

        logger.debug(f"[JOB] {len(efolios)} e-fólios encontrados para validação.")

        for item_id, start_str, end_str in efolios:
            start_date = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            end_date = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")

            janela_pre_inicio = start_date - timedelta(days=7)
            janela_pre_fim = start_date
            available_pre = int(janela_pre_inicio <= hoje <= janela_pre_fim)

            janela_pos_inicio = end_date
            janela_pos_fim = end_date + timedelta(days=7)
            available_pos = int(janela_pos_inicio <= hoje <= janela_pos_fim)

            logger.debug(
                f"[JOB] E-fólio {item_id} — PRE: {available_pre} ({janela_pre_inicio} a {janela_pre_fim}), "
                f"POS: {available_pos} ({janela_pos_inicio} a {janela_pos_fim})"
            )

            cursor.execute("""
                UPDATE efolios
                SET available_pre = ?, available_pos = ?
                WHERE item_id = ?
            """, (available_pre, available_pos, item_id))
            logger.debug(f"[JOB] Atualização feita para item_id={item_id}")

        conn.commit()
        conn.close()
        logger.info("[JOB] Verificação de formulários concluída com sucesso.")

    except Exception as e:
        logger.exception("[JOB] Erro na verificação de disponibilidade de formulários.")

# Job de backup da base de dados
def job_backup_bd():
    try:
        origem = "/app/db/uniAnalytics.db"
        destino_dir = "/app/backups/local_db"
        os.makedirs(destino_dir, exist_ok=True)

        # Criar nome com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = os.path.join(destino_dir, f"backup_{timestamp}.db")

        # Copiar o ficheiro
        with open(origem, "rb") as src, open(destino, "wb") as dst:
            dst.write(src.read())
        logger.info(f"[JOB] Backup criado: {destino}")

        # Apagar backups antigos
        dias_reter = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
        limite_data = datetime.now() - timedelta(days=dias_reter)
        apagados = 0

        for ficheiro in os.listdir(destino_dir):
            if ficheiro.startswith("backup_") and ficheiro.endswith(".db"):
                caminho = os.path.join(destino_dir, ficheiro)
                mtime = datetime.fromtimestamp(os.path.getmtime(caminho))
                if mtime < limite_data:
                    os.remove(caminho)
                    apagados += 1
                    logger.info(f"[JOB] Backup antigo removido: {ficheiro}")

        logger.info(f"[JOB] Limpeza concluída. {apagados} ficheiros removidos.")

    except Exception as e:
        logger.exception("[JOB] Erro ao criar ou limpar backups")

# Agendamento do job de sincronização (hora configurável)
sync_hour = os.getenv("SYNC_HOUR", "00")
sync_minute = os.getenv("SYNC_MINUTE", "00")
schedule.every().day.at(f"{sync_hour}:{sync_minute}").do(job_sync_all)
logger.info(f"[JOB] Sincronização agendada para {sync_hour}:{sync_minute} todos os dias.")

# Agendamento do job de verificação de formulários (hora configurável)
validation_hour = os.getenv("VALIDATION_HOUR", "01")
validation_minute = os.getenv("VALIDATION_MINUTE", "00")
schedule.every().day.at(f"{validation_hour}:{validation_minute}").do(job_validar_formularios)
logger.info(f"[JOB] Validação de formulários agendada para {validation_hour}:{validation_minute} todos os dias.")

# Agendamento do job de backup da base de dados (hora configurável)
backup_hour = os.getenv("BACKUP_HOUR", "02")
backup_minute = os.getenv("BACKUP_MINUTE", "00")
schedule.every().day.at(f"{backup_hour}:{backup_minute}").do(job_backup_bd)
logger.info(f"[JOB] Backup agendado para {backup_hour}:{backup_minute} todos os dias.")

# Executar ambos imediatamente ao iniciar 
# A ordem é importante para garantir que a sincronização e validação estejam completas antes do backup
logger.info("[JOB] Execução imediata de sincronização ao iniciar o scheduler.")
job_sync_all()

logger.info("[JOB] Execução de validação de formulários após sincronização inicial.")
job_validar_formularios()

logger.info("[JOB] Execução de backup após validação inicial.")
job_backup_bd()

# Loop de execução contínua
while True:
    schedule.run_pending()
    time.sleep(60)