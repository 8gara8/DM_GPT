from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

Direction = Literal["buy", "sell"]
Phase = Literal["none", "setup", "countdown"]


@dataclass
class SequentialState:
    ticker: str
    timeframe: str
    direction: Optional[Direction]
    phase: Phase
    current_count: int
    setup_completed_date: Optional[str]
    count_started_date: Optional[str]
    tdst_level: Optional[float]
    is_perfected: bool
    countdown_bar_8_close: Optional[float]
    composite_pattern: Optional[str]
    last_updated: datetime


@dataclass
class AlertRecord:
    ticker: str
    timeframe: str
    alert_type: str
    priority: str
    message: str
    dedupe_key: str
