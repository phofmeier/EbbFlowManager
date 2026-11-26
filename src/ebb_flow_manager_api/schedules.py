from itertools import pairwise
from typing import Annotated, Any, Self

from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

MINUTES_PER_DAY = 1440
DIMMER_MAX = 32767
MAX_PUMP_STARTS = 24
MAX_LIGHT_CHANGES = 10

ClockTime = Annotated[
    str, StringConstraints(pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
]
TransitionMinutes = Annotated[int, Field(ge=0, le=255, strict=True)]


def _daily_gaps(times: list[str]) -> list[int]:
    if not times:
        return []
    minutes = [minute_of_day(time) for time in times]
    next_day = minutes[0] + MINUTES_PER_DAY
    return [end - start for start, end in pairwise([*minutes, next_day])]


class PumpSchedule(BaseModel):
    duration_seconds: int = Field(ge=0, le=65535, strict=True)
    start_times: list[ClockTime] = Field(max_length=MAX_PUMP_STARTS)

    @field_validator("start_times")
    @classmethod
    def order_unique_starts(cls, starts: list[str]) -> list[str]:
        if len(set(starts)) != len(starts):
            raise ValueError("Pump start times must be unique")
        return sorted(starts)

    @model_validator(mode="after")
    def validate_runs(self) -> Self:
        if self.start_times and self.duration_seconds == 0:
            raise ValueError("Pump run duration must be positive when starts are set.")
        for time, gap_minutes in zip(self.start_times, _daily_gaps(self.start_times)):
            if self.duration_seconds > gap_minutes * 60:
                raise ValueError(f"The pump run at {time} overlaps the next start.")
        return self

    def firmware_config(self) -> dict:
        return {
            "pump_time_s": self.duration_seconds,
            "nr_pump_cycles": len(self.start_times),
            "times_minutes_per_day": [minute_of_day(time) for time in self.start_times],
        }


class LightChange(BaseModel):
    time: ClockTime
    output_percent: float = Field(ge=0, le=100, allow_inf_nan=False)
    transition_minutes: TransitionMinutes


class LightSchedule(BaseModel):
    changes: list[LightChange] = Field(max_length=MAX_LIGHT_CHANGES)

    @field_validator("changes")
    @classmethod
    def order_unique_changes(cls, changes: list[LightChange]) -> list[LightChange]:
        if len({change.time for change in changes}) != len(changes):
            raise ValueError("Light change times must be unique")
        ordered = sorted(changes, key=lambda change: change.time)
        times = [change.time for change in ordered]
        for change, gap in zip(ordered, _daily_gaps(times)):
            if len(ordered) > 1 and _ends_at_or_after_midnight(
                minute_of_day(change.time), change.transition_minutes
            ):
                raise ValueError(
                    f"The transition at {change.time} must finish before midnight."
                )
            if change.transition_minutes > gap:
                raise ValueError(
                    f"The light transition at {change.time} overlaps the next change."
                )
        return ordered

    def firmware_config(self) -> dict:
        return {
            "nr_light_changes": len(self.changes),
            "times_min_per_day": [
                minute_of_day(change.time) for change in self.changes
            ],
            "intensity": [
                round(change.output_percent * DIMMER_MAX / 100)
                for change in self.changes
            ],
            "rise_time_min": [change.transition_minutes for change in self.changes],
        }


def minute_of_day(time: str) -> int:
    hour, minute = map(int, time.split(":"))
    return hour * 60 + minute


def clock_time(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


def _ends_at_or_after_midnight(minute: int, transition: int) -> bool:
    return minute + transition >= MINUTES_PER_DAY


def present_pump(config: dict[str, Any] | None) -> dict | None:
    if config is None:
        return None
    starts = config.get("times_minutes_per_day", [])
    return {
        "duration_seconds": config.get("pump_time_s", 0),
        "start_times": [clock_time(minute) for minute in sorted(starts)],
    }


def present_light(config: dict[str, Any] | None) -> dict | None:
    if config is None:
        return None
    changes = sorted(
        zip(
            config.get("times_min_per_day", []),
            config.get("intensity", []),
            config.get("rise_time_min", []),
        )
    )
    transition_reaches_midnight = len(changes) > 1 and any(
        _ends_at_or_after_midnight(minute, transition)
        for minute, _, transition in changes
    )
    return {
        "changes": [
            {
                "time": clock_time(minute),
                "output_percent": output_percent(raw),
                "output_percent_exact": exact_output_percent(raw),
                "transition_minutes": transition,
            }
            for minute, raw, transition in changes
        ],
        "points": [] if transition_reaches_midnight else light_curve(changes),
        "transition_reaches_midnight": transition_reaches_midnight,
    }


def exact_output_percent(raw: int) -> float:
    return max(0, min(raw, DIMMER_MAX)) * 100 / DIMMER_MAX


def output_percent(raw: int) -> float:
    return round(exact_output_percent(raw), 2)


def light_curve(changes: list[tuple[int, int, int]]) -> list[dict]:
    # The firmware treats a single entry as constant output.
    level = output_percent(changes[-1][1]) if changes else 0
    points: list[dict] = [{"minute": 0, "output_percent": level}]
    if len(changes) > 1:
        for index, (minute, raw, transition) in enumerate(changes):
            next_minute = (
                changes[index + 1][0] if index + 1 < len(changes) else MINUTES_PER_DAY
            )
            points.append({"minute": minute, "output_percent": level})
            target = output_percent(raw)
            if transition:
                ramp_minutes = min(transition, next_minute - minute)
                level = round(level + (target - level) * ramp_minutes / transition, 2)
                minute += ramp_minutes
            else:
                level = target
            points.append({"minute": minute, "output_percent": level})
    points.append({"minute": MINUTES_PER_DAY, "output_percent": level})
    return points
