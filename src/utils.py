from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

import yaml


@dataclass(frozen=True)
class SeriesConfig:
    nome: str
    codigo: int
    unidade: str
    fonte: str = "Banco Central do Brasil (SGS)"


@dataclass(frozen=True)
class AppConfig:
    series: list[SeriesConfig]


def ensure_directories(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def load_config(path: Path) -> AppConfig:
    with path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}

    series_entries = raw.get("series", [])
    series_list = [
        SeriesConfig(
            nome=entry["nome"],
            codigo=int(entry["codigo"]),
            unidade=entry.get("unidade", ""),
        )
        for entry in series_entries
    ]
    return AppConfig(series=series_list)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def compute_date_range(
    date_from: date | None, date_to: date | None, days_back: int | None
) -> tuple[date, date]:
    today = date.today()
    if date_to is None:
        date_to = today
    if date_from is None:
        back_days = days_back if days_back is not None else 730
        date_from = date_to - timedelta(days=back_days)
    return date_from, date_to


def validate_dataframe(
    df: Any, expected_columns: list[str], logger: Any, label: str
) -> None:
    logger.info("Validando %s", label)
    missing = [col for col in expected_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes em {label}: {missing}")

    null_counts = df[expected_columns].isna().sum()
    logger.info("Nulos %s: %s", label, null_counts.to_dict())

    duplicate_count = df.duplicated(subset=["data", "serie_codigo"]).sum()
    logger.info("Duplicados %s: %s", label, int(duplicate_count))

    if "valor" in df.columns:
        stats = df["valor"].describe().to_dict()
        logger.info("Resumo %s: %s", label, stats)
