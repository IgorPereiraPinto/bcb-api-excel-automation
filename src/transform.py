from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from src.utils import SeriesConfig


def transform_series(
    series_data: list[dict[str, Any]], series_config: SeriesConfig
) -> pd.DataFrame:
    df = pd.DataFrame(series_data)
    if df.empty:
        return pd.DataFrame(
            columns=["data", "valor", "serie_nome", "serie_codigo", "unidade"]
        )

    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["serie_nome"] = series_config.nome
    df["serie_codigo"] = series_config.codigo
    df["unidade"] = series_config.unidade

    df = df[["data", "valor", "serie_nome", "serie_codigo", "unidade"]]
    df = df.sort_values("data")
    df = df.drop_duplicates(subset=["data", "serie_codigo"], keep="last")

    return df


def combine_series(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame(
            columns=["data", "valor", "serie_nome", "serie_codigo", "unidade"]
        )

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(["serie_codigo", "data"])
    combined = combined.drop_duplicates(subset=["data", "serie_codigo"], keep="last")
    return combined
