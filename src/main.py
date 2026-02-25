"""
main.py — Ponto de Entrada (CLI)
==================================

OBJETIVO:
    Orquestrar o fluxo completo de coleta de indicadores:
    1. Ler configuração (YAML)
    2. Para cada série: coletar → transformar → acumular
    3. Persistir no Excel (incremental)
    4. Registrar logs e status

COMO EXECUTAR:
    # Últimos 10 dias
    python -m src.main --days-back 10

    # Período específico
    python -m src.main --from 2024-01-01 --to 2024-12-31

    # Execução diária (padrão para agendamento)
    python -m src.main --days-back 3

PARÂMETROS:
    --from       Data inicial (YYYY-MM-DD)
    --to         Data final (YYYY-MM-DD)
    --days-back  Dias retroativos (padrão: 730 se nenhum período informado)
    --config     Caminho do YAML (padrão: config/series_config.yaml)
    --output     Caminho do Excel (padrão: data/output/indicadores_bcb.xlsx)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from src.bcb_sgs_client import fetch_series
from src.excel_writer import update_excel
from src.logging_config import setup_logging
from src.transform import combine_series, transform_series
from src.utils import (
    compute_date_range,
    ensure_directories,
    load_config,
    parse_date,
    validate_dataframe,
)


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos da CLI."""
    parser = argparse.ArgumentParser(
        description="Coletor de séries temporais do Banco Central (API SGS)"
    )
    parser.add_argument(
        "--from", dest="date_from",
        help="Data inicial (YYYY-MM-DD). Ex: --from 2024-01-01",
    )
    parser.add_argument(
        "--to", dest="date_to",
        help="Data final (YYYY-MM-DD). Ex: --to 2024-12-31",
    )
    parser.add_argument(
        "--days-back", dest="days_back", type=int, default=None,
        help="Dias retroativos a partir de hoje (padrão: 730 se nenhum período informado)",
    )
    parser.add_argument(
        "--config", dest="config_path",
        default="config/series_config.yaml",
        help="Caminho do YAML de configuração (padrão: config/series_config.yaml)",
    )
    parser.add_argument(
        "--output", dest="output_path",
        default="data/output/indicadores_bcb.xlsx",
        help="Caminho do Excel de saída (padrão: data/output/indicadores_bcb.xlsx)",
    )
    return parser


def main() -> int:
    """
    Pipeline completo de coleta e persistência.

    Fluxo:
        1. Parsear argumentos da CLI
        2. Configurar logging
        3. Ler configuração do YAML
        4. Para cada série:
           a. Chamar API SGS
           b. Transformar dados
           c. Acumular no buffer
        5. Combinar todas as séries
        6. Atualizar Excel (incremental)
        7. Registrar resultado no log

    Retorna:
        0 = sucesso, 1 = erro crítico
    """
    load_dotenv()

    parser = build_parser()
    args = parser.parse_args()

    # ── Configurar datas ──
    date_from = parse_date(args.date_from)
    date_to = parse_date(args.date_to)
    date_from, date_to = compute_date_range(date_from, date_to, args.days_back)

    # ── Configurar caminhos ──
    output_path = Path(args.output_path)
    log_path = output_path.parent / "run.log"
    ensure_directories([output_path.parent, Path("data/raw")])

    # ── Configurar logging ──
    logger = setup_logging(log_path)
    logger.info("=" * 50)
    logger.info("Iniciando coleta SGS: %s → %s", date_from, date_to)

    # ── Ler configuração ──
    config = load_config(Path(args.config_path))
    logger.info("Séries configuradas: %s", len(config.series))

    # ── Coletar cada série ──
    frames = []
    status = {"erro": None}
    series_ok = 0
    series_erro = 0

    for series in config.series:
        logger.info("Baixando série %s (%s)...", series.nome, series.codigo)
        try:
            raw = fetch_series(series.codigo, date_from, date_to)
            frame = transform_series(raw, series)
            frames.append(frame)
            series_ok += 1
            logger.info(
                "  ✅ Série %s: %s registros coletados", series.codigo, len(frame)
            )
        except Exception as exc:
            series_erro += 1
            logger.error("  ❌ Série %s: %s", series.codigo, exc)
            status["erro"] = str(exc)

    # ── Combinar e validar ──
    combined = combine_series(frames)
    validate_dataframe(
        combined,
        ["data", "valor", "serie_nome", "serie_codigo", "unidade"],
        logger,
        "dados consolidados",
    )

    # ── Persistir no Excel ──
    added = update_excel(output_path, combined, config.series, status)

    # ── Resultado final ──
    logger.info("-" * 50)
    logger.info("Séries coletadas com sucesso: %s/%s", series_ok, len(config.series))
    if series_erro:
        logger.warning("Séries com erro: %s", series_erro)
    logger.info("Linhas novas adicionadas ao Excel: %s", added)
    logger.info("Excel atualizado: %s", output_path)
    logger.info("=" * 50)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
