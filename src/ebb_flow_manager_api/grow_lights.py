from bisect import bisect_left
from itertools import pairwise
from math import isfinite, sqrt
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator
from pymongo import ReturnDocument
from pymongo.collection import Collection

from ebb_flow_manager_api.catalog import (
    DATA_FOLDER,
    Document,
    GrowId,
    GrowName,
    load_catalog,
    upsert_catalog,
)

PositiveFinite = Annotated[FiniteFloat, Field(gt=0)]
CanopyDistance = Annotated[PositiveFinite, Field(strict=True)]
OutputPercent = Annotated[FiniteFloat, Field(ge=0, le=100)]
SECONDS_PER_MINUTE = 60
PHOTON_MICROMOLES_PER_MOLE = 1_000_000
DEFAULT_GROW_LIGHT_FOLDER = DATA_FOLDER / "grow_lights"


class ReferenceArea(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width: PositiveFinite
    length: PositiveFinite


class PpfdEstimate(BaseModel):
    ppfd_umol_m2_s: FiniteFloat | None
    status: Literal["off", "reference", "interpolated", "extrapolated", "unavailable"]


def _sample_interval(axis: list[float], point: float) -> tuple[int, int]:
    index = bisect_left(axis, point)
    if index < len(axis) and axis[index] == point:
        return index, index
    lower = max(0, min(index - 1, len(axis) - 2))
    return lower, lower + 1


def _interpolate(
    point: float, x_lower: float, x_upper: float, y_lower: float, y_upper: float
) -> float:
    if x_lower == x_upper:
        return y_lower
    fraction = (point - x_lower) / (x_upper - x_lower)
    return y_lower + fraction * (y_upper - y_lower)


class PpfdTable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_area_cm: ReferenceArea
    statistic: Literal["area_average"]
    source_url: str
    source_revision: str
    output_percent: list[OutputPercent] = Field(min_length=1)
    canopy_distance_cm: list[PositiveFinite] = Field(min_length=2)
    values_umol_m2_s: list[list[PositiveFinite]]

    @model_validator(mode="after")
    def validate_grid(self) -> Self:
        if self.output_percent[0] <= 0 or self.output_percent[-1] != 100:
            raise ValueError("PPFD dimming samples must start above 0 and end at 100%.")
        for axis in (self.output_percent, self.canopy_distance_cm):
            if any(lower >= upper for lower, upper in pairwise(axis)):
                raise ValueError("PPFD table axes must be strictly increasing.")
        if len(self.values_umol_m2_s) != len(self.canopy_distance_cm) or any(
            len(row) != len(self.output_percent) for row in self.values_umol_m2_s
        ):
            raise ValueError("PPFD table dimensions must match the axes.")
        return self

    def estimate(self, output_percent: float, distance_cm: float) -> PpfdEstimate:
        if output_percent == 0:
            return PpfdEstimate(ppfd_umol_m2_s=0, status="off")

        outputs = self.output_percent
        distances = self.canopy_distance_cm
        sample_output = max(output_percent, outputs[0])
        min_dim, max_dim = _sample_interval(outputs, sample_output)
        min_dist, max_dist = _sample_interval(distances, distance_cm)

        def at_distance(index: int) -> float:
            row = self.values_umol_m2_s[index]
            return _interpolate(
                sample_output,
                outputs[min_dim],
                outputs[max_dim],
                row[min_dim],
                row[max_dim],
            )

        ppfd_lower = at_distance(min_dist)
        ppfd_upper = at_distance(max_dist)
        outside_distance_range = not distances[0] <= distance_cm <= distances[-1]
        if outside_distance_range:
            # A line in inverse square root space fits a shifted inverse-square curve.
            reciprocal_root = _interpolate(
                distance_cm,
                distances[min_dist],
                distances[max_dist],
                1 / sqrt(ppfd_lower),
                1 / sqrt(ppfd_upper),
            )
            if ppfd_lower <= ppfd_upper or reciprocal_root <= 0:
                return PpfdEstimate(ppfd_umol_m2_s=None, status="unavailable")
            root = 1 / reciprocal_root
            ppfd = root * root
        else:
            ppfd = _interpolate(
                distance_cm,
                distances[min_dist],
                distances[max_dist],
                ppfd_lower,
                ppfd_upper,
            )

        if not isfinite(ppfd):
            return PpfdEstimate(ppfd_umol_m2_s=None, status="unavailable")
        if outside_distance_range or output_percent < sample_output:
            return PpfdEstimate(
                ppfd_umol_m2_s=ppfd * (output_percent / sample_output),
                status="extrapolated",
            )
        return PpfdEstimate(
            ppfd_umol_m2_s=ppfd,
            status=(
                "reference"
                if min_dim == max_dim and min_dist == max_dist
                else "interpolated"
            ),
        )


def add_schedule_estimates(
    schedule: Document, table: PpfdTable, distance_cm: float
) -> None:
    points = schedule["points"]
    ramp_levels = table.output_percent
    if not table.canopy_distance_cm[0] <= distance_cm <= table.canopy_distance_cm[-1]:
        # Sample the nonlinear response at finer intervals for extrapolated distances.
        ramp_levels = sorted(set(ramp_levels).union(range(1, 100)))

    calibrated_points = [points[0]]
    for start, end in pairwise(points):
        start_output, end_output = start["output_percent"], end["output_percent"]
        if end["minute"] > start["minute"] and start_output != end_output:
            low, high = sorted((start_output, end_output))
            levels = [level for level in ramp_levels if low < level < high]
            if end_output < start_output:
                levels.reverse()
            for level in levels:
                minute = _interpolate(
                    level, start_output, end_output, start["minute"], end["minute"]
                )
                calibrated_points.append({"minute": minute, "output_percent": level})
        calibrated_points.append(end)

    for entry in (*schedule["changes"], *calibrated_points):
        entry["ppfd"] = table.estimate(
            entry["output_percent"], distance_cm
        ).model_dump()
    schedule["points"] = calibrated_points

    ppfd_minutes = 0.0
    status = "estimated"
    for start, end in pairwise(calibrated_points):
        minutes = end["minute"] - start["minute"]
        if minutes == 0:
            continue
        start_ppfd, end_ppfd = start["ppfd"], end["ppfd"]
        before, after = start_ppfd["ppfd_umol_m2_s"], end_ppfd["ppfd_umol_m2_s"]
        if before is None or after is None:
            schedule.update(dli_mol_m2_day=None, dli_status="unavailable")
            return
        low, high = sorted((start["output_percent"], end["output_percent"]))
        if (
            "extrapolated" in (start_ppfd["status"], end_ppfd["status"])
            or low < table.output_percent[0]
            and high > 0
        ):
            status = "extrapolated"
        ppfd_minutes += (before + after) / 2 * minutes
    schedule.update(
        dli_mol_m2_day=ppfd_minutes * SECONDS_PER_MINUTE / PHOTON_MICROMOLES_PER_MOLE,
        dli_status=status,
    )


class GrowLightProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: GrowName
    ppfd: PpfdTable


class GrowLight(GrowLightProfile):
    id: GrowId


def load_grow_lights(folder: Path = DEFAULT_GROW_LIGHT_FOLDER) -> dict[str, Document]:
    return load_catalog(folder, GrowLightProfile)


class GrowLightSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    grow_light_id: GrowId | None = None
    canopy_distance_cm: CanopyDistance | None = None


class GrowLightInstallation(GrowLightSettings):
    grow_light_id: GrowId
    canopy_distance_cm: CanopyDistance


class MongoGrowLights:
    def __init__(
        self, lights: Collection[Document], installations: Collection[Document]
    ) -> None:
        self.lights = lights
        self.installations = installations

    def import_lights(
        self, profiles: dict[str, Document], *, update: bool = False
    ) -> dict[str, int]:
        return upsert_catalog(self.lights, profiles, update=update)

    def catalog(self) -> list[GrowLight]:
        return [
            GrowLight(id=light.pop("_id"), **light)
            for light in self.lights.find().sort("name")
        ]

    def light(self, light_id: str) -> GrowLight | None:
        light = self.lights.find_one({"_id": light_id}, {"_id": 0})
        return GrowLight(id=light_id, **light) if light else None

    def installation(self, controller_id: int) -> GrowLightSettings | None:
        installation = self.installations.find_one({"_id": controller_id}, {"_id": 0})
        return GrowLightSettings.model_validate(installation) if installation else None

    def save_installation(
        self, controller_id: int, update: GrowLightSettings
    ) -> GrowLightSettings:
        settings = self.installations.find_one_and_update(
            {"_id": controller_id},
            {"$set": update.model_dump(exclude_unset=True)},
            upsert=True,
            projection={"_id": 0},
            return_document=ReturnDocument.AFTER,
        )
        return GrowLightSettings.model_validate(settings)
