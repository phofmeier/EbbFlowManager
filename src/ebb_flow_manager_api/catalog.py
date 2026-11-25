from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, Field, TypeAdapter
from pymongo.collection import Collection

Document = dict[str, Any]
GrowId = Annotated[str, Field(max_length=64, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
GrowName = Annotated[str, Field(min_length=1, max_length=100, pattern=r"\S")]
DATA_FOLDER = Path(__file__).with_name("data")


def load_catalog(folder: Path, model: type[BaseModel]) -> dict[str, Document]:
    paths = sorted(folder.glob("*.json"))
    if not paths:
        raise ValueError(f"No catalog JSON files found in {folder}.")
    ids: TypeAdapter[str] = TypeAdapter(GrowId)
    documents = {}
    for path in paths:
        try:
            record_id = ids.validate_python(path.stem)
            record = model.model_validate_json(path.read_text(encoding="utf-8"))
        except ValueError as error:
            raise ValueError(f"{path.name}: {error}") from error
        documents[record_id] = record.model_dump(exclude_none=True)
    return documents


def upsert_catalog(
    collection: Collection[Document],
    documents: dict[str, Document],
    *,
    update: bool = False,
) -> dict[str, int]:
    counts = {"inserted": 0, "updated": 0, "unchanged": 0}
    operation = "$set" if update else "$setOnInsert"
    for record_id, document in documents.items():
        result = collection.update_one(
            {"_id": record_id}, {operation: document}, upsert=True
        )
        if result.upserted_id is not None:
            counts["inserted"] += 1
        elif result.modified_count:
            counts["updated"] += 1
        else:
            counts["unchanged"] += 1
    return counts
