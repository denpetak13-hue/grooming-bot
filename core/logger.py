import structlog
import logging
from pathlib import Path
from datetime import datetime

# Kreiramo logs folder
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"grooming_bot_{datetime.now().strftime('%Y-%m-%d')}.log"

# Konfiguracija za file + console
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.WriteLoggerFactory(
        file=open(log_file, "a", encoding="utf-8")
    ),
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Početna poruka
logger.info("📝 File logging AKTIVIRAN")
logger.info(f"Logovi se čuvaju u: {log_file.resolve()}")