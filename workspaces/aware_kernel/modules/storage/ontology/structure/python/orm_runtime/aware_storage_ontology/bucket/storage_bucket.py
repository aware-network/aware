from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Storage Ontology
from aware_storage_ontology.bucket.storage_bucket_enums import StorageBackend

# Types
from aware_types import JsonObject


class StorageBucket(ORMModel):
    # Attributes
    allowed_mime_types: list[str] = Field(default_factory=list)
    backend: StorageBackend = Field(default=StorageBackend.local)
    config: JsonObject | None = Field(default=None)
    name: str

    @classmethod
    async def build(
        cls,
        name: str,
        backend: StorageBackend = StorageBackend.local,
        allowed_mime_types: list[str] = [],
        config: JsonObject | None = None,
    ) -> StorageBucket:
        """
        Create a deterministic storage bucket metadata root.

        Contract:
        - Identity is deterministic from `(name)`.
        - Backend/config values are mutable policy metadata.
        """

        payload = {"name": name, "backend": backend, "allowed_mime_types": allowed_mime_types, "config": config}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, StorageBucket):
            return value
        return StorageBucket.validate_invocation_value(value)


class StorageBucketBuildInput(BaseModel):
    name: str
    backend: StorageBackend = Field(default=StorageBackend.local)
    allowed_mime_types: list[str] = Field(default_factory=list)
    config: JsonObject | None = Field(default=None)


class StorageBucketBuildOutput(BaseModel):
    value: StorageBucket


FUNCTIONS = {
    "StorageBucket": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create a deterministic storage bucket metadata root.\n\nContract:\n- Identity is deterministic from `(name)`.\n- Backend/config values are mutable policy metadata.",
                "is_constructor": True,
            },
            "input": StorageBucketBuildInput,
            "output": StorageBucketBuildOutput,
        },
    },
}

__all__ = [
    "StorageBucket",
    "StorageBucketBuildInput",
    "StorageBucketBuildOutput",
    "FUNCTIONS",
]
