import pandas as pd

from src.transform import combine_series, transform_series
from src.utils import SeriesConfig


def test_transform_series_basic():
    series = SeriesConfig(nome="Teste", codigo=123, unidade="%")
    raw = [
        {"data": "01/01/2024", "valor": "1.5"},
        {"data": "02/01/2024", "valor": "2.5"},
    ]

    df = transform_series(raw, series)

    assert list(df.columns) == [
        "data",
        "valor",
        "serie_nome",
        "serie_codigo",
        "unidade",
    ]
    assert df["serie_codigo"].unique().tolist() == [123]
    assert df["valor"].tolist() == [1.5, 2.5]


def test_combine_series_deduplicates():
    series = SeriesConfig(nome="Teste", codigo=123, unidade="%")
    raw_first = [{"data": "01/01/2024", "valor": "1.5"}]
    raw_second = [{"data": "01/01/2024", "valor": "1.8"}]

    df_first = transform_series(raw_first, series)
    df_second = transform_series(raw_second, series)

    combined = combine_series([df_first, df_second])

    assert isinstance(combined, pd.DataFrame)
    assert len(combined) == 1
    assert combined.iloc[0]["valor"] == 1.8
