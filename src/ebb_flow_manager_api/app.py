from contextlib import asynccontextmanager
from datetime import UTC, datetime
from hashlib import sha256
from json import dumps
from os import getenv
from threading import Lock
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import FiniteFloat
from pymongo.errors import PyMongoError

from ebb_flow_manager_api.catalog import GrowId
from ebb_flow_manager_api.grow import GrowPhaseUpdate, GrowSelection
from ebb_flow_manager_api.grow_lights import (
    GrowLight,
    GrowLightInstallation,
    GrowLightSettings,
    PpfdEstimate,
    add_schedule_estimates,
)
from ebb_flow_manager_api.light_schedule_planning import (
    LightScheduleSuggestion,
    LightScheduleTargets,
    suggest_light_schedule,
)
from ebb_flow_manager_api.live import LiveControllers
from ebb_flow_manager_api.schedules import LightSchedule, PumpSchedule


@asynccontextmanager
async def lifespan(app: FastAPI):
    config_path = getenv("EBBFLOW_CONFIG")
    if not config_path:
        raise RuntimeError("Set EBBFLOW_CONFIG to the manager YAML file.")
    controllers = LiveControllers(config_path)
    with controllers.mongo:
        app.state.controllers = controllers
        yield


def controller_store(request: Request) -> LiveControllers:
    return request.app.state.controllers


ControllerStore = Annotated[LiveControllers, Depends(controller_store)]

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)
save_locks: dict[int, Lock] = {}
latest_changes: dict[int, dict[str, str]] = {}
ScheduleRevisionHeader = Annotated[str | None, Header(alias="X-Schedule-Revision")]


def schedule_revision(config: dict | None) -> str:
    return sha256(dumps(config, sort_keys=True).encode()).hexdigest()


@app.exception_handler(PyMongoError)
async def handle_database_error(_: Request, __: PyMongoError):
    return JSONResponse(
        status_code=503, content={"detail": "Controller data is unavailable."}
    )


@app.get("/")
async def root():
    return {"message": "Ebb Flow Manager API (FastAPI)", "version": "1.0"}


@app.get("/controllers/")
def get_controllers(controllers: ControllerStore):
    return [controller["id"] for controller in controllers.summaries()]


@app.get("/api/controllers")
def get_controller_summaries(controllers: ControllerStore):
    return controllers.summaries()


@app.get("/api/controllers/{controller_id}/dashboard")
def get_controller_dashboard(controller_id: int, controllers: ControllerStore):
    now = datetime.now(UTC)
    snapshot = controllers.snapshot(controller_id, now)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Controller not found.")
    dashboard = snapshot.dashboard(controller_id, now)
    installation = controllers.grow_lights.installation(controller_id)
    schedule = dashboard["light"]
    if (
        installation is not None
        and installation.grow_light_id is not None
        and installation.canopy_distance_cm is not None
        and schedule is not None
        and schedule["points"]
    ):
        fixture = controllers.grow_lights.light(installation.grow_light_id)
        if fixture is not None:
            add_schedule_estimates(
                schedule, fixture.ppfd, installation.canopy_distance_cm
            )
    return {
        **dashboard,
        "schedule_revisions": {
            "pump": schedule_revision(snapshot.config.get("pump_cycles")),
            "light": schedule_revision(snapshot.config.get("light")),
        },
        "latest_change": latest_changes.get(controller_id),
        "grow_selection": controllers.grow.selection(controller_id),
        "grow_light_installation": installation,
    }


@app.get("/api/crops")
def get_crop_profiles(controllers: ControllerStore):
    return controllers.grow.catalog()


@app.get("/api/grow-lights")
def get_grow_lights(controllers: ControllerStore) -> list[GrowLight]:
    return controllers.grow_lights.catalog()


@app.get("/api/grow-lights/{light_id}/ppfd")
def estimate_grow_light_ppfd(
    light_id: GrowId,
    output_percent: Annotated[FiniteFloat, Query(ge=0, le=100)],
    canopy_distance_cm: Annotated[FiniteFloat, Query(gt=0)],
    controllers: ControllerStore,
) -> PpfdEstimate:
    light = controllers.grow_lights.light(light_id)
    if light is None:
        raise HTTPException(status_code=404, detail="Grow light not found.")
    return light.ppfd.estimate(output_percent, canopy_distance_cm)


@app.put("/api/controllers/{controller_id}/grow-light-installation")
def save_grow_light_installation(
    controller_id: int,
    installation: GrowLightInstallation,
    controllers: ControllerStore,
) -> GrowLightInstallation:
    update_grow_light_installation(controller_id, installation, controllers)
    return installation


@app.patch("/api/controllers/{controller_id}/grow-light-installation")
def update_grow_light_installation(
    controller_id: int, update: GrowLightSettings, controllers: ControllerStore
) -> GrowLightSettings:
    if controllers.status(controller_id) is None:
        raise HTTPException(status_code=404, detail="Controller not found.")
    if not update.model_fields_set:
        raise HTTPException(
            status_code=422, detail="Provide a grow light or canopy distance."
        )
    if (
        update.grow_light_id is not None
        and controllers.grow_lights.light(update.grow_light_id) is None
    ):
        raise HTTPException(status_code=404, detail="Grow light not found.")
    return controllers.grow_lights.save_installation(controller_id, update)


@app.put("/api/crops/{crop_id}/phases/{phase_id}")
def save_grow_phase(
    crop_id: GrowId,
    phase_id: GrowId,
    update: GrowPhaseUpdate,
    controllers: ControllerStore,
):
    controllers.grow.save_phase(crop_id, phase_id, update)
    return update.phase()


@app.put("/api/controllers/{controller_id}/grow-selection")
def save_grow_selection(
    controller_id: int, selection: GrowSelection, controllers: ControllerStore
):
    if controllers.status(controller_id) is None:
        raise HTTPException(status_code=404, detail="Controller not found.")
    if not controllers.grow.has_phase(selection):
        raise HTTPException(status_code=404, detail="Crop phase not found.")
    controllers.grow.save_selection(controller_id, selection)
    return selection


def save_schedule(
    controllers: LiveControllers,
    controller_id: int,
    section: str,
    config: dict,
    expected_revision: str | None,
) -> dict:
    status = controllers.status(controller_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Controller not found.")
    if status.get("connection") != "connected":
        raise HTTPException(status_code=409, detail="Controller is disconnected.")

    with_lock = save_locks.setdefault(controller_id, Lock())
    if not with_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="A settings change is in progress.")
    try:
        if expected_revision is not None:
            current = controllers.configuration(controller_id).get(section)
            if current != config and schedule_revision(current) != expected_revision:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "This schedule changed since you opened it. "
                        "Close and reopen settings to review the latest schedule."
                    ),
                )

        latest_changes[controller_id] = {"section": section, "state": "pending"}
        try:
            state = controllers.apply(controller_id, section, config)
        except Exception:
            latest_changes[controller_id] = {"section": section, "state": "unconfirmed"}
            raise
        latest_changes[controller_id] = {"section": section, "state": state}
        return {"state": state}
    finally:
        with_lock.release()


@app.put("/api/controllers/{controller_id}/pump")
def save_pump_schedule(
    controller_id: int,
    schedule: PumpSchedule,
    controllers: ControllerStore,
    expected_revision: ScheduleRevisionHeader = None,
):
    return save_schedule(
        controllers,
        controller_id,
        "pump_cycles",
        schedule.firmware_config(),
        expected_revision,
    )


@app.put("/api/controllers/{controller_id}/light")
def save_light_schedule(
    controller_id: int,
    schedule: LightSchedule,
    controllers: ControllerStore,
    expected_revision: ScheduleRevisionHeader = None,
):
    return save_schedule(
        controllers,
        controller_id,
        "light",
        schedule.firmware_config(),
        expected_revision,
    )


@app.post("/api/controllers/{controller_id}/light/suggestion")
def suggest_controller_light_schedule(
    controller_id: int, targets: LightScheduleTargets, controllers: ControllerStore
) -> LightScheduleSuggestion:
    if controllers.status(controller_id) is None:
        raise HTTPException(status_code=404, detail="Controller not found.")
    settings = controllers.grow_lights.installation(controller_id)
    if settings is None or settings.grow_light_id is None:
        raise HTTPException(status_code=409, detail="Save a light fixture first.")
    distance_cm = targets.canopy_distance_cm or settings.canopy_distance_cm
    if distance_cm is None:
        raise HTTPException(status_code=409, detail="Enter the canopy distance first.")
    fixture = controllers.grow_lights.light(settings.grow_light_id)
    if fixture is None:
        raise HTTPException(status_code=404, detail="Grow light not found.")
    try:
        return suggest_light_schedule(targets, fixture.ppfd, distance_cm)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("ebb_flow_manager_api.app:app", host="0.0.0.0", port=8001, reload=True)
