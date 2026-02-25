"""
logging_config.py — Configuração de Logs
==========================================

OBJETIVO:
    Configurar o sistema de logging para registrar tudo que
    acontece durante a execução: séries coletadas, erros,
    linhas adicionadas, timestamps.

DESTINOS:
    - Arquivo (run.log): histórico permanente para auditoria
    - Console (stdout): feedback imediato durante execução manual

FORMATO:
    2025-01-15 07:00:12 | INFO | Série 1 (Dólar): 22 linhas coletadas
    2025-01-15 07:00:13 | ERROR | Série 432 (Selic): timeout após 30s

POR QUE LOGGING E NÃO PRINT?
    - print() some quando roda automatizado (Task Scheduler / cron)
    - logging grava em arquivo permanente + aparece no console
    - Permite filtrar por nível (INFO, WARNING, ERROR)
    - Inclui timestamp automático
"""

from __future__ import annotations

import logging
from pathlib import Path


def setup_logging(log_path: Path) -> logging.Logger:
    """
    Configura e retorna o logger do projeto.

    Parâmetros:
        log_path: caminho do arquivo de log (ex: data/output/run.log)

    Retorna:
        Logger configurado com handlers de arquivo e console.

    O logger é criado uma única vez (singleton por nome).
    Chamadas subsequentes retornam o mesmo logger.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("bcb")
    logger.setLevel(logging.INFO)

    # Formato: timestamp | nível | mensagem
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Evitar handlers duplicados se chamado mais de uma vez
    if not logger.handlers:
        # Handler 1: arquivo (histórico permanente)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Handler 2: console (feedback imediato)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger
