from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator
from pymongo.collection import Collection

from ebb_flow_manager_api.catalog import (
    DATA_FOLDER,
    Document,
    GrowId,
    GrowName,
    load_catalog,
    upsert_catalog,
)

DEFAULT_CROP_PROFILE_FOLDER = DATA_FOLDER / "crops"
LETTUCE_TEMPERATURE_MIGRATION = "_lettuce_temperature_migrated"


class TargetRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: FiniteFloat
    max: FiniteFloat

    @model_validator(mode="after")
    def ordered_bounds(self) -> Self:
        if self.min > self.max:
            raise ValueError("The minimum target must not exceed the maximum.")
        return self


class GrowTargets(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ph: TargetRange | None = None
    ec_ms_cm: TargetRange | None = None
    reservoir_temperature_c: TargetRange | None = None
    air_temperature_c: TargetRange | None = None
    relative_humidity_pct: TargetRange | None = None
    ppfd_umol_m2_s: TargetRange | None = None
    dli_mol_m2_day: TargetRange | None = None

    @model_validator(mode="after")
    def valid_units(self) -> Self:
        if self.ph and (self.ph.min < 0 or self.ph.max > 14):
            raise ValueError("pH targets must be between 0 and 14.")
        humidity = self.relative_humidity_pct
        if humidity and (humidity.min < 0 or humidity.max > 100):
            raise ValueError("Relative humidity targets must be between 0 and 100%.")
        for target in (self.ec_ms_cm, self.ppfd_umol_m2_s, self.dli_mol_m2_day):
            if target and target.min < 0:
                raise ValueError("EC, PPFD, and DLI targets must be nonnegative.")
        return self


class GrowPhase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: GrowName
    targets: GrowTargets


class CropProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: GrowName
    phases: dict[GrowId, GrowPhase] = Field(min_length=1)


def load_crop_profiles(
    folder: Path = DEFAULT_CROP_PROFILE_FOLDER,
) -> dict[str, Document]:
    return load_catalog(folder, CropProfile)


class GrowPhaseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crop_name: GrowName
    phase_name: GrowName
    targets: GrowTargets

    def phase(self) -> Document:
        return GrowPhase(name=self.phase_name, targets=self.targets).model_dump(
            exclude_none=True
        )


class GrowSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crop_id: GrowId
    phase_id: GrowId


class MongoGrowProfiles:
    def __init__(
        self, crops: Collection[Document], selections: Collection[Document]
    ) -> None:
        self.crops = crops
        self.selections = selections

    def import_profiles(
        self, profiles: dict[str, Document], *, update: bool = False
    ) -> dict[str, int]:
        if update:
            profiles = {
                crop_id: {
                    "name": crop["name"],
                    **{f"phases.{key}": phase for key, phase in crop["phases"].items()},
                }
                for crop_id, crop in profiles.items()
            }
        return upsert_catalog(self.crops, profiles, update=update)

    def migrate_lettuce_temperature(self, profiles: dict[str, Document]) -> None:
        lettuce = profiles.get("lettuce", {})
        production = lettuce.get("phases", {}).get("production", {})
        previous_targets = production.get("targets", {}).copy()
        temperature = previous_targets.pop("reservoir_temperature_c", None)
        if temperature is None:
            return

        targets_path = "phases.production.targets"
        pending_migration = {
            "_id": "lettuce",
            LETTUCE_TEMPERATURE_MIGRATION: {"$exists": False},
        }
        self.crops.update_one(
            {**pending_migration, targets_path: previous_targets},
            {
                "$set": {
                    f"{targets_path}.reservoir_temperature_c": temperature,
                    LETTUCE_TEMPERATURE_MIGRATION: True,
                }
            },
        )
        self.crops.update_one(
            pending_migration, {"$set": {LETTUCE_TEMPERATURE_MIGRATION: True}}
        )

    def catalog(self) -> list[Document]:
        crops = self.crops.find({}, {LETTUCE_TEMPERATURE_MIGRATION: 0}).sort("name")
        return [{"id": crop.pop("_id"), **crop} for crop in crops]

    def save_phase(self, crop_id: str, phase_id: str, update: GrowPhaseUpdate) -> None:
        self.crops.update_one(
            {"_id": crop_id},
            {"$set": {"name": update.crop_name, f"phases.{phase_id}": update.phase()}},
            upsert=True,
        )

    def has_phase(self, selection: GrowSelection) -> bool:
        return (
            self.crops.find_one(
                {
                    "_id": selection.crop_id,
                    f"phases.{selection.phase_id}": {"$exists": True},
                },
                {"_id": 1},
            )
            is not None
        )

    def selection(self, controller_id: int) -> Document | None:
        return self.selections.find_one({"_id": controller_id}, {"_id": 0})

    def save_selection(self, controller_id: int, selection: GrowSelection) -> None:
        self.selections.update_one(
            {"_id": controller_id}, {"$set": selection.model_dump()}, upsert=True
        )
