"""
Logging structuré en JSON pour le pipeline ETL.
"""

import logging
import sys
from pythonjsonlogger import jsonlogger
from src.utils.config import Config


def get_logger(name: str) -> logging.Logger:
    """
    Crée et retourne un logger structuré (JSON).

    Args:
        name: Nom du module (ex: 'web_scraper', 'bronze_cleaner')

    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)

    # Éviter les handlers en double si appelé plusieurs fois
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)

    if Config.LOG_FORMAT == "json":
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger
