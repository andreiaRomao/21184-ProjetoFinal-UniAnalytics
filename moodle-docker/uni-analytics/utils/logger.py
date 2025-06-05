import logging
import os
from logging.handlers import TimedRotatingFileHandler

# Lê configurações das variáveis de ambiente
LOG_DIR = os.getenv("LOG_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")) # Diretório onde os logs serão armazenados
LOG_FILENAME = os.getenv("LOG_FILENAME", "uniAnalytics.log") # Nome do ficheiro de log
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper() # Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", 7)) # Número de dias para manter os logs
LOG_ROTATE_WHEN = os.getenv("LOG_ROTATE_WHEN", "midnight")  # Quando existe a rotação dos logs (pode ser 'midnight', 'hour', 'day', etc.)
LOG_ROTATE_INTERVAL = int(os.getenv("LOG_ROTATE_INTERVAL", 1)) # Intervalo de rotação em dias ou horas (depende do de cima)

# Cria a pasta se não existir
os.makedirs(LOG_DIR, exist_ok=True)

# Caminho final do ficheiro
log_path = os.path.join(LOG_DIR, LOG_FILENAME)

# Configuração do logger
logger = logging.getLogger("uniAnalyticsLogger")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.DEBUG))

if not logger.handlers:
    handler = TimedRotatingFileHandler(
        log_path,
        when=LOG_ROTATE_WHEN,
        interval=LOG_ROTATE_INTERVAL,
        backupCount=LOG_RETENTION_DAYS,
        encoding="utf-8"
    )
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)