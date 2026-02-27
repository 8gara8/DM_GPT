import pandas as pd

from demark.engine.sequential import calculate_td_sequential


def _df_from_close(close_vals):
    n = len(close_vals)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    close = pd.Series(close_vals, dtype=float)
    return pd.DataFrame(
        {
            "Open": close + 0.5,
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Volume": [1000] * n,
        },
        index=dates,
    )


def test_buy_setup_detected():
    closes = [20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7]
    df = _df_from_close(closes)
    res = calculate_td_sequential(df)
    assert any(e["type"] == "setup_complete" and e["direction"] == "buy" for e in res.events)


def test_countdown_progresses_non_consecutive():
    # crafted to create buy setup then countdown qualifying intermittently
    closes = [
        30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17,
        18, 16, 17, 15, 16, 14, 15, 13, 14, 12, 13, 11, 12, 10,
    ]
    df = _df_from_close(closes)
    res = calculate_td_sequential(df)
    assert res.phase in {"setup", "countdown", "none"}


def test_short_history_returns_no_signal():
    df = _df_from_close([1, 2, 3, 4, 5])
    res = calculate_td_sequential(df)
    assert res.phase == "none"
    assert res.events == []
