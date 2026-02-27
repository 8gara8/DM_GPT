from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


@dataclass
class SequentialResult:
    direction: Optional[str] = None
    phase: str = "none"
    setup_count: int = 0
    countdown_count: int = 0
    setup_start_idx: Optional[int] = None
    setup_completed_idx: Optional[int] = None
    setup_perfected: bool = False
    countdown_bar_8_close: Optional[float] = None
    countdown_qualified: Optional[bool] = None
    tdst_level: Optional[float] = None
    status: str = "No active signal"
    events: list[dict] = field(default_factory=list)


def _qualifies_setup(close_now: float, close_4_back: float, direction: str) -> bool:
    if direction == "buy":
        return close_now < close_4_back
    return close_now > close_4_back


def calculate_td_sequential(df: pd.DataFrame) -> SequentialResult:
    result = SequentialResult()
    if len(df) < 13:
        return result

    df = df.reset_index(drop=False).rename(columns={df.index.name or "index": "Date"})

    setup_count = {"buy": 0, "sell": 0}
    setup_start = {"buy": None, "sell": None}
    countdown_count = {"buy": 0, "sell": 0}
    countdown_active = {"buy": False, "sell": False}
    countdown_bar8_close = {"buy": None, "sell": None}

    for i in range(len(df)):
        if i < 4:
            continue

        for direction in ("buy", "sell"):
            opp = "sell" if direction == "buy" else "buy"
            is_setup_bar = _qualifies_setup(df.loc[i, "Close"], df.loc[i - 4, "Close"], direction)
            if is_setup_bar:
                if setup_count[direction] == 0:
                    setup_start[direction] = i
                setup_count[direction] += 1
            else:
                setup_count[direction] = 0
                setup_start[direction] = None

            if 0 < setup_count[direction] < 9:
                result.direction = direction
                result.phase = "setup"
                result.setup_count = setup_count[direction]
                result.setup_start_idx = setup_start[direction]
                result.setup_completed_idx = None
                result.setup_perfected = False
                result.status = f"{direction.title()} Setup {setup_count[direction]} of 9"

            if setup_count[direction] == 9:
                start_idx = setup_start[direction]
                perfected = False
                if start_idx is not None and i >= start_idx + 8:
                    bar6 = start_idx + 5
                    bar7 = start_idx + 6
                    bar8 = start_idx + 7
                    bar9 = start_idx + 8
                    if direction == "buy":
                        perfected = (
                            df.loc[bar8, "Low"] < df.loc[bar6, "Low"]
                            and df.loc[bar8, "Low"] < df.loc[bar7, "Low"]
                        ) or (
                            df.loc[bar9, "Low"] < df.loc[bar6, "Low"]
                            and df.loc[bar9, "Low"] < df.loc[bar7, "Low"]
                        )
                    else:
                        perfected = (
                            df.loc[bar8, "High"] > df.loc[bar6, "High"]
                            and df.loc[bar8, "High"] > df.loc[bar7, "High"]
                        ) or (
                            df.loc[bar9, "High"] > df.loc[bar6, "High"]
                            and df.loc[bar9, "High"] > df.loc[bar7, "High"]
                        )

                tdst = None
                if start_idx and start_idx > 0:
                    prev_close = df.loc[start_idx - 1, "Close"]
                    if direction == "buy":
                        tdst = max(df.loc[start_idx - 1, "High"], prev_close)
                    else:
                        tdst = min(df.loc[start_idx - 1, "Low"], prev_close)

                result.events.append(
                    {
                        "type": "setup_complete",
                        "direction": direction,
                        "index": i,
                        "date": str(df.loc[i, "Date"]),
                        "perfected": perfected,
                        "tdst": tdst,
                    }
                )
                countdown_active[direction] = True
                countdown_count[direction] = 0
                countdown_bar8_close[direction] = None
                countdown_active[opp] = False
                countdown_count[opp] = 0

                result.direction = direction
                result.phase = "setup"
                result.setup_count = 9
                result.setup_start_idx = start_idx
                result.setup_completed_idx = i
                result.setup_perfected = perfected
                result.tdst_level = tdst
                result.status = f"{direction.title()} Setup 9 completed"

                setup_count[direction] = 0
                setup_start[direction] = None

            if i >= 2 and countdown_active[direction]:
                if direction == "buy":
                    qualifies = df.loc[i, "Close"] <= df.loc[i - 2, "Low"]
                else:
                    qualifies = df.loc[i, "Close"] >= df.loc[i - 2, "High"]

                if qualifies:
                    countdown_count[direction] += 1
                    if countdown_count[direction] == 8:
                        countdown_bar8_close[direction] = df.loc[i, "Close"]
                    if countdown_count[direction] == 13:
                        bar8 = countdown_bar8_close[direction]
                        qualified = None
                        if bar8 is not None:
                            if direction == "buy":
                                qualified = df.loc[i, "Close"] <= bar8
                            else:
                                qualified = df.loc[i, "Close"] >= bar8
                        result.events.append(
                            {
                                "type": "countdown_complete",
                                "direction": direction,
                                "index": i,
                                "date": str(df.loc[i, "Date"]),
                                "qualified": qualified,
                            }
                        )
                        result.direction = direction
                        result.phase = "countdown"
                        result.countdown_count = 13
                        result.countdown_qualified = qualified
                        result.countdown_bar_8_close = bar8
                        result.status = f"{direction.title()} Countdown 13 completed"
                        countdown_active[direction] = False
                if countdown_active[direction]:
                    result.direction = direction
                    result.phase = "countdown"
                    result.countdown_count = countdown_count[direction]
                    result.countdown_bar_8_close = countdown_bar8_close[direction]
                    result.status = (
                        f"{direction.title()} Countdown {countdown_count[direction]} of 13"
                    )

    return result
