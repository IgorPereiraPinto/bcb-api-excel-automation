from __future__ import annotations

from datetime import date
from typing import Any

import requests

BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"


def _format_date(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def fetch_series(
    codigo: int,
    date_from: date,
    date_to: date,
    retries: int = 3,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    params = {
        "formato": "json",
        "dataInicial": _format_date(date_from),
        "dataFinal": _format_date(date_to),
    }
    url = BASE_URL.format(codigo=codigo)

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            if attempt == retries:
                break
    raise RuntimeError(f"Falha ao baixar série {codigo}: {last_error}")
