from __future__ import annotations

import pandas as pd


TIMEFRAME_MAP = {
    "daily": None,
    "weekly": "W-FRI",
    "monthly": "ME",
    "yearly": "YE",
}


def aggregate_ohlcv(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if timeframe == "daily":
        out = df.copy()
        out = out.dropna(subset=["Open", "High", "Low", "Close"]).sort_index()
        return out

    rule = TIMEFRAME_MAP[timeframe]
    if rule is None:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    agg = (
        df.resample(rule)
        .agg(
            {
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }
        )
        .dropna(subset=["Open", "High", "Low", "Close"])
    )
    return agg
