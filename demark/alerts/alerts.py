from __future__ import annotations

from datetime import datetime


def build_alerts(
    ticker: str,
    timeframe: str,
    result,
    setup_threshold: int,
    countdown_threshold: int,
) -> list[dict]:
    out: list[dict] = []
    for event in result.events:
        if event["type"] == "setup_complete":
            msg = (
                f"{ticker} {timeframe}: {event['direction'].title()} Setup 9 completed "
                f"(perfected: {'yes' if event['perfected'] else 'no'}). "
                f"TDST level: {event['tdst']}"
            )
            out.append(
                _mk(ticker, timeframe, "setup_complete", "warning", msg, f"setup-{event['date']}")
            )
        elif event["type"] == "countdown_complete":
            msg = (
                f"{ticker} {timeframe}: {event['direction'].title()} Countdown 13 completed "
                f"(qualified: {event['qualified']})."
            )
            out.append(
                _mk(
                    ticker,
                    timeframe,
                    "countdown_complete",
                    "critical",
                    msg,
                    f"countdown-{event['date']}",
                )
            )

    if result.phase == "setup" and result.setup_count >= setup_threshold:
        msg = (
            f"{ticker} {timeframe}: {result.direction.title()} Setup at bar {result.setup_count} of 9"
        )
        out.append(_mk(ticker, timeframe, "setup_approaching", "info", msg, f"setup-appr-{result.setup_count}"))

    if result.phase == "countdown" and result.countdown_count >= countdown_threshold:
        priority = "warning" if result.countdown_count >= 12 else "info"
        msg = (
            f"{ticker} {timeframe}: {result.direction.title()} Countdown at bar {result.countdown_count} of 13"
        )
        out.append(
            _mk(
                ticker,
                timeframe,
                "countdown_approaching",
                priority,
                msg,
                f"countdown-appr-{result.countdown_count}",
            )
        )
    return out


def _mk(ticker: str, timeframe: str, alert_type: str, priority: str, message: str, key_suffix: str):
    return {
        "ticker": ticker,
        "timeframe": timeframe,
        "alert_type": alert_type,
        "priority": priority,
        "message": message,
        "dedupe_key": f"{ticker}:{timeframe}:{key_suffix}",
        "triggered_at": datetime.utcnow().isoformat(),
        "sent": False,
    }
