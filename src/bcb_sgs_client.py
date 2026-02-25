"""
bcb_sgs_client.py — Cliente da API SGS do Banco Central
========================================================

OBJETIVO:
    Fazer requisições HTTP à API SGS (Sistema Gerenciador de Séries
    Temporais) do Banco Central do Brasil e retornar os dados brutos.

API UTILIZADA:
    https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados

    Parâmetros:
    - formato: json
    - dataInicial: dd/MM/yyyy
    - dataFinal: dd/MM/yyyy

    Retorno (JSON):
    [
        {"data": "02/01/2025", "valor": "6.1832"},
        {"data": "03/01/2025", "valor": "6.1456"},
        ...
    ]

TRATAMENTO DE ERROS:
    A API do BCB pode ficar fora do ar temporariamente.
    O cliente faz até N tentativas (retry) antes de desistir.
    Se falhar, levanta RuntimeError — o main.py captura e registra
    no log sem interromper as demais séries.

EXPLICAÇÃO PARA LEIGOS:
    Este módulo é o "mensageiro": vai até o Banco Central, pede
    os dados e traz de volta. Se o Banco não responder, tenta
    de novo. Se continuar sem responder, avisa que falhou.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import requests

# URL base da API SGS — {codigo} é substituído pelo código da série
# Exemplo: código 1 = Dólar comercial (compra)
BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"


def _format_date(value: date) -> str:
    """
    Converte data Python para o formato esperado pela API do BCB.

    A API espera dd/MM/yyyy (formato brasileiro), não yyyy-MM-dd.
    Exemplo: date(2025, 1, 15) → "15/01/2025"
    """
    return value.strftime("%d/%m/%Y")


def fetch_series(
    codigo: int,
    date_from: date,
    date_to: date,
    retries: int = 3,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """
    Consulta a API SGS e retorna os dados brutos de uma série.

    Parâmetros:
        codigo: código SGS da série (ex: 1 = Dólar, 432 = Selic)
        date_from: data inicial da consulta
        date_to: data final da consulta
        retries: número de tentativas em caso de falha (padrão: 3)
        timeout: segundos máximos de espera por resposta (padrão: 30)

    Retorna:
        Lista de dicionários com chaves "data" e "valor".
        Exemplo: [{"data": "02/01/2025", "valor": "6.1832"}, ...]

    Levanta:
        RuntimeError se todas as tentativas falharem.

    EXPLICAÇÃO PARA LEIGOS:
        Imagine que você liga para o Banco Central e pede:
        "Me dá a cotação do Dólar de 01/01/2025 a 31/01/2025."
        Se a linha cair, você tenta de novo (até 3 vezes).
        Se depois de 3 tentativas ainda não conseguiu, desiste
        e avisa que não foi possível.
    """
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

            data = response.json()

            # A API pode retornar um dict de erro em vez de lista
            # Ex: {"erro": "Série não encontrada"}
            if isinstance(data, dict) and "erro" in data:
                raise RuntimeError(
                    f"API retornou erro para série {codigo}: {data['erro']}"
                )

            return data

        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries:
                continue  # Tenta novamente
            break         # Esgotou as tentativas

    raise RuntimeError(
        f"Falha ao baixar série {codigo} após {retries} tentativas: {last_error}"
    )
