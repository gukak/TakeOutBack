"""
Système de journalisation pour TakeOutBack.
Supporte les logs texte et JSON.
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from src.utils.path import get_logs_path


class JsonFormatter(logging.Formatter):
    """Formateur JSON pour les logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Formateur texte pour les logs."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp}] [{record.levelname}] {record.getMessage()}"


def setup_logger(
    name: str = "takeoutback",
    log_level: int = logging.INFO,
    json_format: bool = False,
) -> logging.Logger:
    """Configure et retourne un logger."""
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if not logger.handlers:
        logs_path = get_logs_path()
        logs_path.mkdir(parents=True, exist_ok=True)

        if json_format:
            formatter = JsonFormatter()
            log_file = logs_path / "operations.json"
        else:
            formatter = TextFormatter()
            log_file = logs_path / "operations.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "takeoutback") -> logging.Logger:
    """Retourne un logger existant ou en crée un nouveau."""
    return logging.getLogger(name)


def log_operation(
    operation_type: str,
    details: Optional[dict] = None,
    status: str = "completed",
) -> None:
    """Enregistre une opération dans le journal."""
    logger = get_logger()
    log_data = {
        "operation_type": operation_type,
        "timestamp": datetime.now().isoformat(),
        "status": status,
    }
    if details:
        log_data.update(details)
    logger.info(f"Opération: {operation_type} - {status}")
