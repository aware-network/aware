from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# History Ontology
from aware_history_ontology.change.change_enums import (
    ChangeDeltaKind,
    ChangeType,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import Json

if TYPE_CHECKING:
    from aware_history_ontology.change.change_delta import ChangeDelta


class Change(ORMModel):
    # Relationships
    change_deltas: list[ChangeDelta] = Field(default_factory=list)

    # Attributes
    key: str
    created_at: datetime
    type: ChangeType

    @classmethod
    async def create(cls, key: str, created_at: datetime, type: ChangeType) -> Change:
        """Create a standalone canonical change envelope."""

        payload = {"key": key, "created_at": created_at, "type": type}
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Change):
            return value
        return Change.validate_invocation_value(value)

    async def create_delta(
        self, position: int, kind: ChangeDeltaKind, payload: Json, property: str | None = None
    ) -> ChangeDelta:
        """
        Create one delta under this Change.

        Contract:
        - Parent `change_id` is propagated by traversal lowering.
        - Stable identity is keyed by `(change_id, position)`.
        """

        payload = {"position": position, "kind": kind, "payload": payload, "property": property}
        result = await invoke_instance(orm_model=self, function_name="create_delta", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_history_ontology.change.change_delta import ChangeDelta

        if isinstance(value, ChangeDelta):
            return value
        return ChangeDelta.validate_invocation_value(value)


class ChangeCreateInput(BaseModel):
    key: str
    created_at: datetime
    type: ChangeType


class ChangeCreateOutput(BaseModel):
    value: Change


class ChangeCreateDeltaInput(BaseModel):
    position: int
    kind: ChangeDeltaKind
    payload: Json
    property: str | None = Field(default=None)


class ChangeCreateDeltaOutput(BaseModel):
    value: ChangeDelta


FUNCTIONS = {
    "Change": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create a standalone canonical change envelope.",
                "is_constructor": True,
            },
            "input": ChangeCreateInput,
            "output": ChangeCreateOutput,
        },
        "create_delta": {
            "canonical": {
                "name": "create_delta",
                "description": "Create one delta under this Change.\n\nContract:\n- Parent `change_id` is propagated by traversal lowering.\n- Stable identity is keyed by `(change_id, position)`.",
                "is_constructor": False,
            },
            "input": ChangeCreateDeltaInput,
            "output": ChangeCreateDeltaOutput,
        },
    },
}

__all__ = [
    "Change",
    "ChangeCreateInput",
    "ChangeCreateOutput",
    "ChangeCreateDeltaInput",
    "ChangeCreateDeltaOutput",
    "FUNCTIONS",
]
