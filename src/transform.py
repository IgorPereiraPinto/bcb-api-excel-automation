"""
transform.py — Padronização e Tratamento dos Dados do BCB
==========================================================

OBJETIVO:
    Transformar os dados brutos da API SGS em um DataFrame limpo
    e padronizado, pronto para persistência no Excel.

TRANSFORMAÇÕES APLICADAS:
    1. Conversão de datas: "dd/MM/yyyy" (texto) → datetime
    2. Conversão de valores: "6.1832" (texto) → 6.1832 (float)
    3. Adição de metadados: nome da série, código, unidade
    4. Ordenação por data
    5. Deduplicação: se a mesma data/série aparecer mais de uma vez,
       mantém a versão mais recente (keep="last")

EXPLICAÇÃO PARA LEIGOS:
    A API do BCB retorna dados "crus" — datas como texto, valores
    como texto, sem identificação de qual série é. Este módulo
    limpa, padroniza e enriquece os dados para que o Excel
    receba tudo pronto e organizado.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.utils import SeriesConfig

# Colunas do DataFrame padronizado (contrato com o excel_writer.py)
STANDARD_COLUMNS = ["data", "valor", "serie_nome", "serie_codigo", "unidade"]


def transform_series(
    series_data: list[dict[str, Any]],
    series_config: SeriesConfig,
) -> pd.DataFrame:
    """
    Transforma os dados brutos de UMA série em DataFrame padronizado.

    Parâmetros:
        series_data: lista de dicts da API (chaves: "data", "valor")
        series_config: configuração da série (nome, código, unidade)

    Retorna:
        DataFrame com colunas: data, valor, serie_nome, serie_codigo, unidade

    EXPLICAÇÃO PARA LEIGOS:
        A API retorna algo como:
            [{"data": "02/01/2025", "valor": "6.1832"}, ...]

        Este método transforma em:
            data        | valor  | serie_nome             | serie_codigo | unidade
            2025-01-02  | 6.1832 | Dólar comercial (compra) | 1          | R$/US$
    """
    df = pd.DataFrame(series_data)

    # Se a API retornou vazio (feriado, sem dados no período)
    if df.empty:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    # ── Conversão de tipos ──
    # Data: "02/01/2025" (texto brasileiro) → datetime
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")

    # Valor: "6.1832" (texto) → 6.1832 (float)
    # errors="coerce" transforma valores inválidos em NaN (não trava)
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

    # ── Enriquecer com metadados da série ──
    df["serie_nome"] = series_config.nome
    df["serie_codigo"] = series_config.codigo
    df["unidade"] = series_config.unidade

    # ── Padronizar colunas e ordenar ──
    df = df[STANDARD_COLUMNS]
    df = df.sort_values("data")

    # ── Deduplicar ──
    # Se a API retornar a mesma data duas vezes (raro, mas possível
    # em séries revisadas), mantém a versão mais recente.
    df = df.drop_duplicates(subset=["data", "serie_codigo"], keep="last")

    return df


def combine_series(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Combina DataFrames de múltiplas séries em um único DataFrame.

    Parâmetros:
        frames: lista de DataFrames (um por série coletada)

    Retorna:
        DataFrame único com todas as séries, ordenado e deduplicado.

    EXPLICAÇÃO PARA LEIGOS:
        Se coletamos Dólar (20 registros), Euro (20 registros) e
        Selic (20 registros), este método junta tudo numa tabela
        de 60 registros, ordenada por série e data.
    """
    if not frames:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(["serie_codigo", "data"])
    combined = combined.drop_duplicates(
        subset=["data", "serie_codigo"], keep="last"
    )

    return combined
