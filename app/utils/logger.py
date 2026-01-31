import json
import logging
from typing import Any


def get_logger(name: str) -> logging.Logger:
    """構造化ログを出力するロガーを取得"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def log_info(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """構造化ログを出力（INFO）"""
    log_data = {"level": "INFO", "message": message, **kwargs}
    logger.info(json.dumps(log_data, ensure_ascii=False))


def log_error(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """構造化ログを出力（ERROR）"""
    log_data = {"level": "ERROR", "message": message, **kwargs}
    logger.error(json.dumps(log_data, ensure_ascii=False))
