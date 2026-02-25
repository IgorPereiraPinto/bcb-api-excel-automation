"""
test_transform.py — Testes do Módulo de Transformação
======================================================

OBJETIVO:
    Validar que o pipeline de transformação (transform.py) funciona
    corretamente: conversão de tipos, deduplicação, combinação de
    séries e tratamento de edge cases.

COMO EXECUTAR:
    pytest                          # todos os testes
    pytest tests/test_transform.py  # só este arquivo
    pytest -v                       # modo verboso (mostra cada teste)

COBERTURA:
    - Transformação básica (tipos, colunas, ordenação)
    - Deduplicação (mesma data/série → mantém a mais recente)
    - Combinação de múltiplas séries
    - Edge cases (dados vazios, valores inválidos)
"""

import pandas as pd
import pytest

from src.transform import combine_series, transform_series
from src.utils import SeriesConfig


# ════════════════════════════════════════════════════════════════
# FIXTURES (dados reutilizáveis nos testes)
# ════════════════════════════════════════════════════════════════

@pytest.fixture
def series_dolar():
    """Configuração de série simulando o Dólar."""
    return SeriesConfig(
        nome="Dólar comercial (compra)",
        codigo=1,
        unidade="R$/US$",
        categoria="cambio",
        uso="Contratos de importação",
    )


@pytest.fixture
def series_selic():
    """Configuração de série simulando a Selic."""
    return SeriesConfig(
        nome="Selic (a.a.)",
        codigo=432,
        unidade="% a.a.",
        categoria="juros",
        uso="Custo de oportunidade",
    )


@pytest.fixture
def raw_data_basic():
    """Dados brutos simulando resposta da API SGS."""
    return [
        {"data": "01/01/2024", "valor": "1.5"},
        {"data": "02/01/2024", "valor": "2.5"},
    ]


# ════════════════════════════════════════════════════════════════
# TESTES: transform_series()
# ════════════════════════════════════════════════════════════════

class TestTransformSeries:
    """Testes da função transform_series()."""

    def test_columns_match_standard(self, series_dolar, raw_data_basic):
        """Verifica se o DataFrame retornado tem as 5 colunas padrão."""
        df = transform_series(raw_data_basic, series_dolar)

        expected_columns = [
            "data", "valor", "serie_nome", "serie_codigo", "unidade",
        ]
        assert list(df.columns) == expected_columns

    def test_serie_metadata_applied(self, series_dolar, raw_data_basic):
        """Verifica se os metadados da série são aplicados corretamente."""
        df = transform_series(raw_data_basic, series_dolar)

        assert df["serie_codigo"].unique().tolist() == [1]
        assert df["serie_nome"].unique().tolist() == ["Dólar comercial (compra)"]
        assert df["unidade"].unique().tolist() == ["R$/US$"]

    def test_values_converted_to_float(self, series_dolar, raw_data_basic):
        """
        Verifica se valores string são convertidos para float.

        A API retorna "1.5" (texto). O transform deve converter
        para 1.5 (numérico) para permitir cálculos.
        """
        df = transform_series(raw_data_basic, series_dolar)

        assert df["valor"].tolist() == [1.5, 2.5]
        assert df["valor"].dtype == float

    def test_dates_converted_to_datetime(self, series_dolar, raw_data_basic):
        """
        Verifica se datas são convertidas de texto para datetime.

        A API retorna "01/01/2024" (texto brasileiro).
        O transform deve converter para Timestamp(2024-01-01).
        """
        df = transform_series(raw_data_basic, series_dolar)

        assert pd.api.types.is_datetime64_any_dtype(df["data"])
        assert df["data"].iloc[0] == pd.Timestamp("2024-01-01")

    def test_sorted_by_date(self, series_dolar):
        """Verifica se o resultado está ordenado por data (crescente)."""
        raw = [
            {"data": "15/01/2024", "valor": "3.0"},
            {"data": "02/01/2024", "valor": "1.0"},
            {"data": "10/01/2024", "valor": "2.0"},
        ]
        df = transform_series(raw, series_dolar)

        dates = df["data"].tolist()
        assert dates == sorted(dates)

    def test_empty_input_returns_empty_df(self, series_dolar):
        """
        Verifica comportamento com dados vazios.

        Isso acontece quando a API não tem dados para o período
        (ex: consultar sábado/domingo para séries diárias).
        """
        df = transform_series([], series_dolar)

        assert len(df) == 0
        assert list(df.columns) == [
            "data", "valor", "serie_nome", "serie_codigo", "unidade",
        ]

    def test_invalid_values_become_nan(self, series_dolar):
        """
        Verifica se valores não-numéricos viram NaN (não travam).

        Pode acontecer se a API retornar "..." ou "-" em vez de número.
        """
        raw = [
            {"data": "01/01/2024", "valor": "1.5"},
            {"data": "02/01/2024", "valor": "N/D"},  # Valor inválido
        ]
        df = transform_series(raw, series_dolar)

        assert df["valor"].iloc[0] == 1.5
        assert pd.isna(df["valor"].iloc[1])

    def test_deduplicates_within_single_series(self, series_dolar):
        """
        Verifica se duplicatas na mesma série são removidas.

        keep="last" garante que valores revisados pelo BCB
        substituem os originais.
        """
        raw = [
            {"data": "01/01/2024", "valor": "5.00"},
            {"data": "01/01/2024", "valor": "5.25"},  # Revisão
        ]
        df = transform_series(raw, series_dolar)

        assert len(df) == 1
        assert df["valor"].iloc[0] == 5.25  # Mantém o mais recente


# ════════════════════════════════════════════════════════════════
# TESTES: combine_series()
# ════════════════════════════════════════════════════════════════

class TestCombineSeries:
    """Testes da função combine_series()."""

    def test_combines_multiple_series(self, series_dolar, series_selic):
        """Verifica se múltiplas séries são combinadas corretamente."""
        raw_dolar = [{"data": "01/01/2024", "valor": "4.95"}]
        raw_selic = [{"data": "01/01/2024", "valor": "11.75"}]

        df_dolar = transform_series(raw_dolar, series_dolar)
        df_selic = transform_series(raw_selic, series_selic)
        combined = combine_series([df_dolar, df_selic])

        assert len(combined) == 2
        assert set(combined["serie_codigo"].tolist()) == {1, 432}

    def test_deduplicates_across_runs(self, series_dolar):
        """
        Verifica se duplicatas entre execuções são removidas.

        Cenário: o script roda duas vezes no mesmo dia.
        A segunda execução pode trazer o mesmo dado com valor
        revisado. O combine deve manter apenas a versão mais recente.
        """
        raw_first = [{"data": "01/01/2024", "valor": "1.5"}]
        raw_second = [{"data": "01/01/2024", "valor": "1.8"}]

        df_first = transform_series(raw_first, series_dolar)
        df_second = transform_series(raw_second, series_dolar)
        combined = combine_series([df_first, df_second])

        assert len(combined) == 1
        assert combined.iloc[0]["valor"] == 1.8  # Mantém a mais recente

    def test_empty_frames_list(self):
        """Verifica comportamento com lista vazia (nenhuma série coletada)."""
        combined = combine_series([])

        assert len(combined) == 0
        assert list(combined.columns) == [
            "data", "valor", "serie_nome", "serie_codigo", "unidade",
        ]

    def test_preserves_all_dates(self, series_dolar):
        """Verifica se datas diferentes da mesma série são preservadas."""
        raw = [
            {"data": "01/01/2024", "valor": "4.90"},
            {"data": "02/01/2024", "valor": "4.95"},
            {"data": "03/01/2024", "valor": "5.00"},
        ]
        df = transform_series(raw, series_dolar)
        combined = combine_series([df])

        assert len(combined) == 3

    def test_sorted_by_serie_and_date(self, series_dolar, series_selic):
        """Verifica se o resultado final está ordenado por série e data."""
        raw_dolar = [
            {"data": "02/01/2024", "valor": "5.00"},
            {"data": "01/01/2024", "valor": "4.95"},
        ]
        raw_selic = [{"data": "01/01/2024", "valor": "11.75"}]

        df_dolar = transform_series(raw_dolar, series_dolar)
        df_selic = transform_series(raw_selic, series_selic)
        combined = combine_series([df_dolar, df_selic])

        # Deve estar ordenado: primeiro Dólar (código 1), depois Selic (432)
        codigos = combined["serie_codigo"].tolist()
        assert codigos == sorted(codigos)
