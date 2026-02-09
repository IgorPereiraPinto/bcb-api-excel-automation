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
    parser = argparse.ArgumentParser(description="Coletor SGS Banco Central")
    parser.add_argument("--from", dest="date_from", help="Data inicial YYYY-MM-DD")
    parser.add_argument("--to", dest="date_to", help="Data final YYYY-MM-DD")
    parser.add_argument(
        "--days-back",
        dest="days_back",
        type=int,
        default=None,
        help="Dias retroativos (default: 730)",
    )
    parser.add_argument(
        "--config",
        dest="config_path",
        default="config/series_config.yaml",
        help="Caminho do YAML de séries",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        default="data/output/indicadores_bcb.xlsx",
        help="Caminho do Excel de saída",
    )
    return parser


def main() -> int:
    load_dotenv()

    parser = build_parser()
    args = parser.parse_args()

    date_from = parse_date(args.date_from)
    date_to = parse_date(args.date_to)

    date_from, date_to = compute_date_range(date_from, date_to, args.days_back)

    output_path = Path(args.output_path)
    log_path = output_path.parent / "run.log"

    ensure_directories([output_path.parent, Path("data/raw")])
    logger = setup_logging(log_path)

    logger.info("Iniciando coleta SGS %s -> %s", date_from, date_to)

    config = load_config(Path(args.config_path))
    frames = []
    status = {"erro": None}

    for series in config.series:
        logger.info("Baixando série %s (%s)", series.nome, series.codigo)
        try:
            raw = fetch_series(series.codigo, date_from, date_to)
            frame = transform_series(raw, series)
            frames.append(frame)
            logger.info("Série %s: %s linhas", series.codigo, len(frame))
        except Exception as exc:  # noqa: BLE001 - log para usuários leigos
            logger.error("Erro ao baixar série %s: %s", series.codigo, exc)
            status["erro"] = str(exc)

    combined = combine_series(frames)
    validate_dataframe(
        combined,
        ["data", "valor", "serie_nome", "serie_codigo", "unidade"],
        logger,
        "dados consolidados",
    )

    added = update_excel(output_path, combined, config.series, status)
    logger.info("Linhas novas adicionadas: %s", added)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
