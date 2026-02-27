from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import click

from demark.alerts.alerts import build_alerts
from demark.config import load_config
from demark.dashboard.app import create_app
from demark.data.aggregator import aggregate_ohlcv
from demark.data.provider import YFinanceProvider
from demark.engine.sequential import calculate_td_sequential
from demark.storage.db import Database


@click.group()
@click.option("--config", "config_path", default=None, help="Path to config file")
@click.pass_context
def cli(ctx: click.Context, config_path: str | None):
    cfg = load_config(config_path)
    db = Database(cfg["database"]["path"])
    ctx.obj = {"config": cfg, "db": db}


@cli.command()
@click.argument("tickers", nargs=-1)
@click.option("--tag", default=None)
@click.pass_obj
def add(obj, tickers: tuple[str], tag: str | None):
    if not tickers:
        raise click.UsageError("Provide at least one ticker")
    obj["db"].add_tickers(tickers, tag=tag)
    click.echo(f"Added {len(tickers)} ticker(s)")


@cli.command()
@click.argument("ticker")
@click.pass_obj
def remove(obj, ticker: str):
    obj["db"].remove_ticker(ticker)
    click.echo(f"Removed {ticker.upper()}")


@cli.command("list")
@click.option("--tag", default=None)
@click.pass_obj
def list_cmd(obj, tag: str | None):
    rows = obj["db"].list_tickers(tag=tag)
    for r in rows:
        click.echo(f"{r['ticker']}\t{r['tag'] or '-'}\t{r['created_at']}")
    if not rows:
        click.echo("Watchlist is empty")


@cli.command()
@click.argument("path")
@click.pass_obj
def export(obj, path: str):
    data = obj["db"].export_watchlist()
    p = Path(path)
    if p.suffix.lower() == ".json":
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    else:
        raise click.UsageError("Only JSON export currently supported")
    click.echo(f"Exported {len(data)} tickers to {path}")


@cli.command(name="import")
@click.argument("path")
@click.pass_obj
def import_cmd(obj, path: str):
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    tickers = [row["ticker"] for row in data]
    obj["db"].add_tickers(tickers)
    click.echo(f"Imported {len(tickers)} ticker(s)")


@cli.command()
@click.pass_obj
def init(obj):
    defaults = obj["config"]["watchlist"]["default_tickers"]
    obj["db"].add_tickers(defaults, tag="default")
    click.echo(f"Initialized default watchlist: {', '.join(defaults)}")


@cli.command()
@click.pass_obj
def scan(obj):
    cfg = obj["config"]
    db = obj["db"]
    provider = YFinanceProvider()
    rows = db.list_tickers()
    if not rows:
        click.echo("No tickers in watchlist. Run: demark init or demark add ...")
        return

    timeframes = cfg["timeframes"]
    for row in rows:
        ticker = row["ticker"]
        try:
            raw = provider.fetch_daily_ohlcv(ticker)
            if raw.empty:
                click.echo(f"[WARN] No data for {ticker}")
                continue
            for tf in timeframes:
                bars = aggregate_ohlcv(raw, tf)
                result = calculate_td_sequential(bars)
                count = result.countdown_count if result.phase == "countdown" else result.setup_count
                db.upsert_signal_state(
                    {
                        "ticker": ticker,
                        "timeframe": tf,
                        "indicator_type": "sequential",
                        "direction": result.direction,
                        "phase": result.phase,
                        "current_count": count,
                        "count_started_date": None,
                        "setup_completed_date": None,
                        "tdst_level": result.tdst_level,
                        "is_perfected": result.setup_perfected,
                        "countdown_bar_8_close": result.countdown_bar_8_close,
                        "composite_pattern": "9" if result.setup_completed_idx is not None else None,
                        "status": result.status,
                        "last_updated": datetime.utcnow().isoformat(),
                    }
                )
                alerts = build_alerts(
                    ticker,
                    tf,
                    result,
                    cfg["alerts"]["approaching_setup_threshold"],
                    cfg["alerts"]["approaching_countdown_threshold"],
                )
                for a in alerts:
                    if db.insert_alert(a):
                        click.echo(f"[{a['priority'].upper()}] {a['message']}")
        except Exception as exc:
            click.echo(f"[ERROR] {ticker}: {exc}")

    click.echo("Scan complete")


@cli.command()
@click.pass_obj
def dashboard(obj):
    cfg = obj["config"]
    host = cfg["alerts"]["dashboard"]["host"]
    port = int(cfg["alerts"]["dashboard"]["port"])
    app = create_app(cfg["database"]["path"])
    app.run(host=host, port=port)


if __name__ == "__main__":
    cli()
