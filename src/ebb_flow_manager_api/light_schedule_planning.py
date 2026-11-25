from typing import Literal

from pydantic import BaseModel, ConfigDict

from ebb_flow_manager_api.grow_lights import (
    PHOTON_MICROMOLES_PER_MOLE,
    SECONDS_PER_MINUTE,
    CanopyDistance,
    PositiveFinite,
    PpfdTable,
    add_schedule_estimates,
)
from ebb_flow_manager_api.schedules import (
    MINUTES_PER_DAY,
    LightChange,
    LightSchedule,
    TransitionMinutes,
    clock_time,
    present_light,
)

OUTPUT_STEPS_PER_PERCENT = 100


class LightScheduleTargets(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_ppfd_umol_m2_s: PositiveFinite
    dli_mol_m2_day: PositiveFinite
    rise_time_minutes: TransitionMinutes
    canopy_distance_cm: CanopyDistance | None = None


class LightScheduleSuggestion(BaseModel):
    schedule: LightSchedule
    canopy_distance_cm: CanopyDistance
    peak_ppfd_umol_m2_s: PositiveFinite
    dli_mol_m2_day: PositiveFinite
    dli_status: Literal["estimated", "extrapolated"]


def suggest_light_schedule(
    targets: LightScheduleTargets, table: PpfdTable, distance_cm: float
) -> LightScheduleSuggestion:
    output, peak = _output_for_ppfd(targets.max_ppfd_umol_m2_s, table, distance_cm)
    rise = targets.rise_time_minutes
    min_on_minutes = max(1, rise)
    max_on_minutes = MINUTES_PER_DAY - max(1, rise)
    shortest = _on_off_schedule(output, rise, min_on_minutes)
    minimum = present_light(shortest.firmware_config())
    assert minimum is not None
    add_schedule_estimates(minimum, table, distance_cm)
    min_dli = minimum["dli_mol_m2_day"]
    if min_dli is None:
        raise ValueError(
            "PPFD could not be estimated across the requested transitions."
        )
    peak_during_schedule = max(
        point["ppfd"]["ppfd_umol_m2_s"] or 0 for point in minimum["points"]
    )
    if peak_during_schedule > targets.max_ppfd_umol_m2_s:
        raise ValueError(
            "The fixture calibration exceeds max PPFD during a transition."
        )

    # Extending the on period adds full-output minutes without changing either ramp.
    dli_per_minute = peak * (SECONDS_PER_MINUTE / PHOTON_MICROMOLES_PER_MOLE)
    max_dli = min_dli + (max_on_minutes - min_on_minutes) * dli_per_minute
    desired_dli = targets.dli_mol_m2_day
    if desired_dli < min_dli:
        raise ValueError(
            f"Minimum DLI is {min_dli:.3g} mol/m²/day at this PPFD and rise time."
        )
    if desired_dli > max_dli:
        raise ValueError(
            f"Maximum DLI is {max_dli:.3g} mol/m²/day at this PPFD and rise time."
        )

    extra_minutes = round((desired_dli - min_dli) / dli_per_minute)
    return LightScheduleSuggestion(
        schedule=_on_off_schedule(output, rise, min_on_minutes + extra_minutes),
        canopy_distance_cm=distance_cm,
        peak_ppfd_umol_m2_s=peak_during_schedule,
        dli_mol_m2_day=min_dli + extra_minutes * dli_per_minute,
        dli_status=minimum["dli_status"],
    )


def _output_for_ppfd(
    target: float, table: PpfdTable, distance_cm: float
) -> tuple[float, float]:
    def estimate(output: float) -> float:
        ppfd = table.estimate(output, distance_cm).ppfd_umol_m2_s
        if ppfd is None:
            raise ValueError("PPFD could not be estimated at this canopy distance.")
        return ppfd

    maximum = estimate(100)
    if target > maximum:
        raise ValueError(
            f"This fixture can reach {maximum:.3g} µmol/m²/s at this canopy distance."
        )
    lower, upper = 0, 100 * OUTPUT_STEPS_PER_PERCENT
    while lower < upper:
        step = (lower + upper + 1) // 2
        if estimate(step / OUTPUT_STEPS_PER_PERCENT) <= target:
            lower = step
        else:
            upper = step - 1
    output = lower / OUTPUT_STEPS_PER_PERCENT
    peak = estimate(output)
    if peak == 0:
        raise ValueError(
            "Max PPFD is too low for a nonzero output at this canopy distance."
        )
    return output, peak


def _on_off_schedule(output: float, rise: int, on_minutes: int) -> LightSchedule:
    # Center the full light window, including ramp-down, on controller noon.
    start = (MINUTES_PER_DAY - on_minutes - rise) // 2
    return LightSchedule(
        changes=[
            LightChange(
                time=clock_time(start), output_percent=output, transition_minutes=rise
            ),
            LightChange(
                time=clock_time(start + on_minutes),
                output_percent=0,
                transition_minutes=rise,
            ),
        ]
    )
