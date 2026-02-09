from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils import SeriesConfig


def _read_existing_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(
            columns=["data", "valor", "serie_nome", "serie_codigo", "unidade"]
        )
    try:
        return pd.read_excel(path, sheet_name="dados")
    except ValueError:
        return pd.DataFrame(
            columns=["data", "valor", "serie_nome", "serie_codigo", "unidade"]
        )


def _build_series_df(series_list: list[SeriesConfig]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "nome": series.nome,
                "codigo": series.codigo,
                "unidade": series.unidade,
                "fonte": series.fonte,
            }
            for series in series_list
        ]
    )


def update_excel(
    path: Path,
    new_data: pd.DataFrame,
    series_list: list[SeriesConfig],
    status: dict[str, Any],
) -> int:
    existing = _read_existing_data(path)
    existing["data"] = pd.to_datetime(existing["data"], errors="coerce")

    combined = pd.concat([existing, new_data], ignore_index=True)
    combined = combined.drop_duplicates(subset=["data", "serie_codigo"], keep="last")
    combined = combined.sort_values(["serie_codigo", "data"])

    rows_before = len(existing)
    rows_after = len(combined)
    added_rows = max(rows_after - rows_before, 0)

    status_df = pd.DataFrame(
        [
            {
                "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "linhas_novas": added_rows,
                "erro": status.get("erro"),
            }
        ]
    )

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        combined.to_excel(writer, sheet_name="dados", index=False)
        _build_series_df(series_list).to_excel(writer, sheet_name="series", index=False)
        status_df.to_excel(writer, sheet_name="status", index=False)

    return added_rows
