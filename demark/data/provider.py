from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf


class YFinanceProvider:
    def fetch_daily_ohlcv(self, ticker: str, years: int = 10) -> pd.DataFrame:
        end = datetime.utcnow().date() + timedelta(days=1)
        start = end - timedelta(days=365 * years)
        data = yf.download(
            ticker,
            start=start.isoformat(),
            end=end.isoformat(),
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        if data.empty:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [c[0] for c in data.columns]

        data = data[["Open", "High", "Low", "Close", "Volume"]].copy()
        data.index = pd.to_datetime(data.index)
        return data.sort_index()
