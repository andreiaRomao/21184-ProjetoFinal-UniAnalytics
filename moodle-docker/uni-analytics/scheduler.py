import os
import time
import schedule
from queries.syncData import executar_todos_os_syncs
from utils.logger import logger

def job_sync_all():
    logger.info("[JOB] Início da sincronização geral.")
    executar_todos_os_syncs()
    logger.info("[JOB] Sincronização completa.")

# Obter hora e minuto de ambiente
sync_hour = os.getenv("SYNC_HOUR", "00")
sync_minute = os.getenv("SYNC_MINUTE", "00")

# Executar logo ao arrancar
logger.info("[JOB] Execução imediata ao iniciar o scheduler.")
job_sync_all()

# Caso queriamos agendar a sincronização a cada minuto para DEBUD
#schedule.every(1).minutes.do(executar_todos_os_syncs)

# Agendar execução diária
schedule.every().day.at(f"{sync_hour}:{sync_minute}").do(job_sync_all)
logger.info(f"[JOB] Sincronização agendada para {sync_hour}:{sync_minute} todos os dias.")

# Loop de execução
while True:
    schedule.run_pending()
    time.sleep(60)