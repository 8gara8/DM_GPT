import pandas as pd

from demark.data.aggregator import aggregate_ohlcv


def test_weekly_aggregation():
    idx = pd.date_range("2024-01-01", periods=10, freq="D")
    df = pd.DataFrame(
        {
            "Open": range(10),
            "High": [x + 1 for x in range(10)],
            "Low": [x - 1 for x in range(10)],
            "Close": range(10),
            "Volume": [100] * 10,
        },
        index=idx,
    )
    out = aggregate_ohlcv(df, "weekly")
    assert len(out) >= 2
    assert set(["Open", "High", "Low", "Close", "Volume"]).issubset(out.columns)
