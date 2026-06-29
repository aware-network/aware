from __future__ import annotations

from pathlib import Path
from uuid import UUID

from pydantic import BaseModel

from aware_types import JsonArray, JsonObject, Vector


class _Payload(BaseModel):
    payload: JsonObject
    changes: JsonArray
    embedding: Vector


def test_json_helpers_validate_and_serialize_common_runtime_values() -> None:
    payload = _Payload.model_validate(
        {
            "payload": {
                "path": Path("docs/release.md"),
                "owner_id": UUID("00000000-0000-0000-0000-000000000001"),
            },
            "changes": [{"kind": "update"}, ("tuple", "value")],
            "embedding": [1, "2.5"],
        }
    )

    assert payload.payload == JsonObject(
        {
            "path": "docs/release.md",
            "owner_id": "00000000-0000-0000-0000-000000000001",
        }
    )
    assert payload.changes == JsonArray([{"kind": "update"}, ["tuple", "value"]])
    assert payload.embedding == Vector([1.0, 2.5])
    assert payload.model_dump(mode="json") == {
        "payload": {
            "path": "docs/release.md",
            "owner_id": "00000000-0000-0000-0000-000000000001",
        },
        "changes": [{"kind": "update"}, ["tuple", "value"]],
        "embedding": [1.0, 2.5],
    }
