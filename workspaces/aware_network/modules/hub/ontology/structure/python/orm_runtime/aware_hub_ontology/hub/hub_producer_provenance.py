from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject


class HubProducerProvenance(ORMModel):
    # Attributes
    build_ref: str | None = Field(default=None)
    materialization_ref: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)
    producer_key: str
    producer_kind: str
    producer_revision_id: str | None = Field(default=None)
    provenance_key: str = Field(default="default")
    source_revision_id: str | None = Field(default=None)
    source_revision_kind: str | None = Field(default=None)

    @classmethod
    async def build(
        cls,
        producer_kind: str,
        producer_key: str = "default",
        provenance_key: str = "default",
        producer_revision_id: str | None = None,
        source_revision_id: str | None = None,
        source_revision_kind: str | None = None,
        materialization_ref: str | None = None,
        build_ref: str | None = None,
        metadata: JsonObject = {},
    ) -> HubProducerProvenance:
        """
        Create one generic producer provenance record.

        Contract:
        - Producer-specific revision fields remain opaque to Hub.
        - WorkspaceRevision can appear here without making Workspace API part of Hub.
        """

        payload = {
            "producer_kind": producer_kind,
            "producer_key": producer_key,
            "provenance_key": provenance_key,
            "producer_revision_id": producer_revision_id,
            "source_revision_id": source_revision_id,
            "source_revision_kind": source_revision_kind,
            "materialization_ref": materialization_ref,
            "build_ref": build_ref,
            "metadata": metadata,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, HubProducerProvenance):
            return value
        return HubProducerProvenance.validate_invocation_value(value)


class HubProducerProvenanceBuildInput(BaseModel):
    producer_kind: str
    producer_key: str = Field(default="default")
    provenance_key: str = Field(default="default")
    producer_revision_id: str | None = Field(default=None)
    source_revision_id: str | None = Field(default=None)
    source_revision_kind: str | None = Field(default=None)
    materialization_ref: str | None = Field(default=None)
    build_ref: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class HubProducerProvenanceBuildOutput(BaseModel):
    value: HubProducerProvenance


FUNCTIONS = {
    "HubProducerProvenance": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one generic producer provenance record.\n\nContract:\n- Producer-specific revision fields remain opaque to Hub.\n- WorkspaceRevision can appear here without making Workspace API part of Hub.",
                "is_constructor": True,
            },
            "input": HubProducerProvenanceBuildInput,
            "output": HubProducerProvenanceBuildOutput,
        },
    },
}

__all__ = [
    "HubProducerProvenance",
    "HubProducerProvenanceBuildInput",
    "HubProducerProvenanceBuildOutput",
    "FUNCTIONS",
]
