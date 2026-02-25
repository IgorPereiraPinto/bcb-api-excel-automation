"""
utils.py — Utilitários e Dataclasses
======================================

OBJETIVO:
    Centralizar funções auxiliares e estruturas de dados usadas
    por múltiplos módulos do projeto.

CONTEÚDO:
    - SeriesConfig: configuração de uma série do BCB
    - AppConfig: configuração completa do aplicativo
    - load_config(): lê o YAML e retorna AppConfig
    - parse_date(): converte string YYYY-MM-DD em date
    - compute_date_range(): calcula período de consulta
    - validate_dataframe(): validações de qualidade
    - ensure_directories(): cria pastas se não existirem
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

import yaml


# ════════════════════════════════════════════════════════════════
# DATACLASSES DE CONFIGURAÇÃO
# ════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SeriesConfig:
    """
    Configuração de uma série do Banco Central.

    Mapeada diretamente do YAML. Os campos obrigatórios são
    nome, codigo e unidade. Os demais são opcionais e servem
    para documentação e organização.

    Atributos:
        nome: nome descritivo (ex: "Dólar comercial (compra)")
        codigo: código SGS no Banco Central (ex: 1)
        unidade: unidade de medida (ex: "R$/US$")
        categoria: agrupamento (câmbio, juros, inflação, atividade)
        uso: contexto de negócio (para documentação)
        fonte: fonte oficial dos dados
    """
    nome: str
    codigo: int
    unidade: str
    categoria: str = ""
    uso: str = ""
    fonte: str = "Banco Central do Brasil (SGS)"


@dataclass(frozen=True)
class AppConfig:
    """
    Configuração completa do aplicativo.

    Contém a lista de séries a coletar e as configurações
    operacionais (days_back, timeout, etc.).
    """
    series: list[SeriesConfig]
    days_back_default: int = 730
    timeout_seconds: int = 30
    retry_attempts: int = 2


# ════════════════════════════════════════════════════════════════
# FUNÇÕES DE CONFIGURAÇÃO
# ════════════════════════════════════════════════════════════════

def ensure_directories(paths: Iterable[Path]) -> None:
    """Cria diretórios se não existirem (idempotente)."""
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def load_config(path: Path) -> AppConfig:
    """
    Lê o YAML de configuração e retorna AppConfig.

    Parâmetros:
        path: caminho do arquivo YAML (ex: config/series_config.yaml)

    Retorna:
        AppConfig com lista de SeriesConfig e configurações operacionais

    EXPLICAÇÃO PARA LEIGOS:
        O YAML é como uma "lista de compras" — define quais
        séries coletar. Esta função lê a lista e transforma
        em objetos Python que o resto do código consegue usar.
    """
    with path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}

    # ── Ler configurações operacionais (bloco "settings") ──
    settings = raw.get("settings", {})
    days_back = settings.get("days_back_default", 730)
    timeout = settings.get("timeout_seconds", 30)
    retry = settings.get("retry_attempts", 2)

    # ── Ler séries ──
    series_entries = raw.get("series", [])
    series_list = [
        SeriesConfig(
            nome=entry["nome"],
            codigo=int(entry["codigo"]),
            unidade=entry.get("unidade", ""),
            categoria=entry.get("categoria", ""),
            uso=entry.get("uso", ""),
        )
        for entry in series_entries
    ]

    return AppConfig(
        series=series_list,
        days_back_default=days_back,
        timeout_seconds=timeout,
        retry_attempts=retry,
    )


# ════════════════════════════════════════════════════════════════
# FUNÇÕES DE DATA
# ════════════════════════════════════════════════════════════════

def parse_date(value: str | None) -> date | None:
    """
    Converte string YYYY-MM-DD em date. Retorna None se vazio.

    Usado para parsear os argumentos --from e --to da CLI.
    Exemplo: "2024-01-01" → date(2024, 1, 1)
    """
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def compute_date_range(
    date_from: date | None,
    date_to: date | None,
    days_back: int | None,
) -> tuple[date, date]:
    """
    Calcula o período de consulta baseado nos argumentos da CLI.

    Regras:
        - Se --from e --to foram informados → usa diretamente
        - Se --to não foi informado → usa hoje
        - Se --from não foi informado → calcula a partir de --days-back
        - Se nenhum argumento → últimos 730 dias (2 anos)

    EXPLICAÇÃO PARA LEIGOS:
        Se você digitar: python -m src.main --days-back 3
        E hoje é 15/01/2025, o período será: 12/01/2025 a 15/01/2025.
    """
    today = date.today()

    if date_to is None:
        date_to = today

    if date_from is None:
        back_days = days_back if days_back is not None else 730
        date_from = date_to - timedelta(days=back_days)

    return date_from, date_to


# ════════════════════════════════════════════════════════════════
# FUNÇÕES DE VALIDAÇÃO
# ════════════════════════════════════════════════════════════════

def validate_dataframe(
    df: Any,
    expected_columns: list[str],
    logger: Any,
    label: str,
) -> None:
    """
    Validações de qualidade no DataFrame consolidado.

    Verifica:
        - Todas as colunas esperadas existem
        - Contagem de nulos por coluna
        - Contagem de duplicatas (data + série)
        - Estatísticas descritivas da coluna "valor"

    Não levanta exceção para nulos/duplicatas — apenas registra
    no log para diagnóstico. A exceção é colunas ausentes,
    que indicam erro no pipeline e devem ser corrigidas.
    """
    logger.info("Validando %s", label)

    # 1. Colunas obrigatórias
    missing = [col for col in expected_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes em {label}: {missing}")

    # 2. Nulos (informativo, não bloqueia)
    null_counts = df[expected_columns].isna().sum()
    if null_counts.sum() > 0:
        logger.warning("Nulos em %s: %s", label, null_counts.to_dict())
    else:
        logger.info("Nulos em %s: nenhum", label)

    # 3. Duplicatas (informativo)
    duplicate_count = df.duplicated(subset=["data", "serie_codigo"]).sum()
    if duplicate_count > 0:
        logger.warning("Duplicatas em %s: %s", label, int(duplicate_count))
    else:
        logger.info("Duplicatas em %s: nenhuma", label)

    # 4. Estatísticas descritivas
    if "valor" in df.columns and len(df) > 0:
        stats = df["valor"].describe()
        logger.info(
            "Resumo %s: min=%.4f, max=%.4f, mean=%.4f, count=%d",
            label, stats["min"], stats["max"], stats["mean"], int(stats["count"]),
        )
