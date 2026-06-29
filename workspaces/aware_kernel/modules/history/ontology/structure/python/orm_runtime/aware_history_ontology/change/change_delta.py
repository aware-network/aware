from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# History Ontology
from aware_history_ontology.change.change_enums import ChangeDeltaKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import Json


class ChangeDelta(ORMModel):
    # Attributes
    position: int
    property: str | None = Field(default=None)
    kind: ChangeDeltaKind
    payload: Json

    # Foreign Keys
    change_id: UUID = Field(description="Foreign key for Change.change_deltas")

    @classmethod
    async def create_via_change(
        cls, change_id: UUID, position: int, kind: ChangeDeltaKind, payload: Json, property: str | None = None
    ) -> ChangeDelta:
        """Create one delta under this Change."""

        payload = {"change_id": change_id, "position": position, "kind": kind, "payload": payload, "property": property}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_change", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ChangeDelta):
            return value
        return ChangeDelta.validate_invocation_value(value)


class ChangeDeltaCreateViaChangeInput(BaseModel):
    change_id: UUID = Field(description="Foreign key for Change.change_deltas")
    position: int
    kind: ChangeDeltaKind
    payload: Json
    property: str | None = Field(default=None)


class ChangeDeltaCreateViaChangeOutput(BaseModel):
    value: ChangeDelta


FUNCTIONS = {
    "ChangeDelta": {
        "create_via_change": {
            "canonical": {
                "name": "create_via_change",
                "description": "Create one delta under this Change.",
                "is_constructor": True,
            },
            "input": ChangeDeltaCreateViaChangeInput,
            "output": ChangeDeltaCreateViaChangeOutput,
        },
    },
}

__all__ = [
    "ChangeDelta",
    "ChangeDeltaCreateViaChangeInput",
    "ChangeDeltaCreateViaChangeOutput",
    "FUNCTIONS",
]
