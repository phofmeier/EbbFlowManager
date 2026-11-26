from argparse import ArgumentParser
from os import getenv
from pathlib import Path
from typing import Literal

import yaml
from pymongo.errors import PyMongoError

from ebb_flow_manager_api.grow import DEFAULT_CROP_PROFILE_FOLDER, load_crop_profiles
from ebb_flow_manager_api.grow_lights import DEFAULT_GROW_LIGHT_FOLDER, load_grow_lights
from ebb_flow_manager_api.live import LiveControllers


def run_import(catalog: Literal["crops", "grow_lights"]) -> None:
    if catalog == "crops":
        label = "crop profile"
        folder = DEFAULT_CROP_PROFILE_FOLDER
        read = load_crop_profiles
        update_help = "Update crop names and replace phases listed in the JSON files."
    else:
        label = "grow-light fixture"
        folder = DEFAULT_GROW_LIGHT_FOLDER
        read = load_grow_lights
        update_help = "Update fixture names and replace their PPFD calibration tables."

    parser = ArgumentParser(description=f"Import {label} JSON files into MongoDB.")
    parser.add_argument(
        "--config",
        default=getenv("EBBFLOW_CONFIG"),
        help="Manager YAML configuration (defaults to EBBFLOW_CONFIG).",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=folder,
        help=f"One JSON file per {label} (defaults to the bundled folder).",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help=update_help,
    )
    args = parser.parse_args()
    if not args.config:
        parser.error("Set --config or EBBFLOW_CONFIG to the manager YAML file.")

    try:
        documents = read(args.source)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    try:
        controllers = LiveControllers(args.config)
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        yaml.YAMLError,
        PyMongoError,
    ) as error:
        parser.error(
            f"Could not load the manager configuration ({type(error).__name__})."
        )

    if catalog == "crops":
        destination = controllers.grow.crops.full_name
        write = controllers.grow.import_profiles
    else:
        destination = controllers.grow_lights.lights.full_name
        write = controllers.grow_lights.import_lights
    try:
        with controllers.mongo:
            counts = write(documents, update=args.update)
            if catalog == "crops" and args.source.resolve() == folder.resolve():
                controllers.grow.migrate_lettuce_temperature(documents)
    except PyMongoError as error:
        parser.exit(
            1,
            f"Could not complete the import into {destination} "
            f"({type(error).__name__}). Check MongoDB and retry.\n",
        )
    print(
        f"{destination}: {counts['inserted']} inserted, "
        f"{counts['updated']} updated, {counts['unchanged']} unchanged."
    )
