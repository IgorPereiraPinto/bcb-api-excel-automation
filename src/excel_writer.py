"""
excel_writer.py — Persistência Incremental no Excel
=====================================================

OBJETIVO:
    Atualizar o arquivo Excel com os dados novos coletados,
    sem perder o histórico existente e sem duplicar registros.

ABAS DO EXCEL:
    - "dados":  histórico completo (data, valor, série, unidade)
    - "series": catálogo das séries configuradas
    - "status": log da última execução (data/hora, linhas novas, erros)

COMPORTAMENTO:
    - Se o Excel NÃO existe → cria do zero com as 3 abas
    - Se o Excel JÁ existe → lê os dados existentes, faz merge
      com os novos, deduplica e salva tudo junto

EXPLICAÇÃO PARA LEIGOS:
    Imagine uma planilha que acumula dados dia após dia.
    Toda manhã o script abre a planilha, adiciona os dados novos
    no final, remove duplicatas (se rodar duas vezes no mesmo dia),
    e salva. O histórico nunca é perdido.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils import SeriesConfig

# Colunas esperadas na aba "dados"
DATA_COLUMNS = ["data", "valor", "serie_nome", "serie_codigo", "unidade"]


def _read_existing_data(path: Path) -> pd.DataFrame:
    """
    Lê os dados existentes do Excel (se houver).

    Se o arquivo não existir ou a aba "dados" não existir,
    retorna um DataFrame vazio com as colunas corretas.
    Isso garante que o merge funcione mesmo na primeira execução.
    """
    if not path.exists():
        return pd.DataFrame(columns=DATA_COLUMNS)

    try:
        return pd.read_excel(path, sheet_name="dados")
    except (ValueError, KeyError):
        # Arquivo existe mas não tem aba "dados" → tratar como vazio
        return pd.DataFrame(columns=DATA_COLUMNS)


def _build_series_df(series_list: list[SeriesConfig]) -> pd.DataFrame:
    """
    Monta o DataFrame da aba "series" (catálogo das séries configuradas).

    Esta aba serve como documentação dentro do próprio Excel:
    quem abrir a planilha sabe exatamente quais séries estão
    sendo coletadas, com código, unidade e fonte.
    """
    return pd.DataFrame([
        {
            "nome": series.nome,
            "codigo": series.codigo,
            "unidade": series.unidade,
            "categoria": series.categoria,
            "uso": series.uso,
            "fonte": series.fonte,
        }
        for series in series_list
    ])


def update_excel(
    path: Path,
    new_data: pd.DataFrame,
    series_list: list[SeriesConfig],
    status: dict[str, Any],
) -> int:
    """
    Atualiza o Excel com os dados novos de forma incremental.

    Parâmetros:
        path: caminho do arquivo Excel
        new_data: DataFrame com os dados novos coletados
        series_list: lista de SeriesConfig (para a aba "series")
        status: dicionário com informações de status {"erro": None ou "msg"}

    Retorna:
        Número de linhas novas adicionadas.

    Fluxo:
        1. Lê dados existentes do Excel (ou cria vazio)
        2. Concatena com dados novos
        3. Remove duplicatas (mesma data + série → mantém a mais recente)
        4. Ordena por série e data
        5. Salva o Excel com 3 abas
    """
    # ── Passo 1: Ler histórico existente ──
    existing = _read_existing_data(path)
    existing["data"] = pd.to_datetime(existing["data"], errors="coerce")

    # ── Passo 2: Merge com dados novos ──
    combined = pd.concat([existing, new_data], ignore_index=True)

    # ── Passo 3: Deduplicar ──
    # Se o script rodar duas vezes no mesmo dia, não duplica.
    # keep="last" mantém o dado mais recente (caso de revisão pelo BCB).
    combined = combined.drop_duplicates(
        subset=["data", "serie_codigo"], keep="last"
    )
    combined = combined.sort_values(["serie_codigo", "data"])

    # ── Passo 4: Calcular linhas adicionadas ──
    rows_before = len(existing)
    rows_after = len(combined)
    added_rows = max(rows_after - rows_before, 0)

    # ── Passo 5: Montar aba de status ──
    status_df = pd.DataFrame([{
        "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "linhas_existentes": rows_before,
        "linhas_novas": added_rows,
        "linhas_total": rows_after,
        "series_coletadas": len(series_list),
        "erro": status.get("erro"),
    }])

    # ── Passo 6: Salvar Excel com 3 abas ──
    path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        combined.to_excel(writer, sheet_name="dados", index=False)
        _build_series_df(series_list).to_excel(
            writer, sheet_name="series", index=False
        )
        status_df.to_excel(writer, sheet_name="status", index=False)

        # Congelar cabeçalho (facilita navegação em planilhas grandes)
        try:
            for sheet_name in ["dados", "series", "status"]:
                ws = writer.book[sheet_name]
                ws.freeze_panes = ws.cell(row=2, column=1)
        except Exception:
            pass  # Se falhar, segue sem congelar

    return added_rows
