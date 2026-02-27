# DeMark Indicators Daily Monitor

Phase 1 MVP of a DeMark monitoring system focused on TD Sequential with watchlist management, SQLite persistence, CLI scanning, and a simple web dashboard.

## Features (Phase 1)

- TD Sequential setup (9) + countdown (13) engine
- Setup perfection check
- TDST level calculation
- Watchlist management in SQLite
- Multi-timeframe scan (daily/weekly/monthly/yearly)
- Console alerts for setup/countdown completion and approaching thresholds
- Web dashboard for daily signal summary

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick start

```bash
demark init
demark list
demark scan
demark dashboard
```

Then open `http://localhost:8050`.

## CLI examples

```bash
demark add AAPL MSFT GOOGL --tag tech
demark add SPY QQQ DIA --tag index
demark remove TSLA
demark list
demark list --tag tech
demark export watchlist.json
demark import watchlist.json
```

## Project layout

- `demark/engine/sequential.py` — TD Sequential logic
- `demark/data/` — market data provider + timeframe aggregation
- `demark/storage/db.py` — SQLite schema + operations
- `demark/alerts/alerts.py` — alert generation
- `demark/dashboard/` — Flask dashboard
- `demark/cli.py` — CLI entrypoint
- `tests/` — unit tests

## Notes

- Data source uses `yfinance` and can be swapped later.
- MVP prioritizes robust daily monitoring and persistence over charting.
