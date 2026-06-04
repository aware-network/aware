from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_storage_ontology.bucket.storage_bucket import StorageBucket


class StorageBlob(ORMModel):
    # Relationships
    bucket: StorageBucket | None = Field(default=None, exclude=True)

    # Attributes
    mime_type: str
    object_key: str | None = Field(default=None)
    path_local: str | None = Field(default=None)
    sha: str
    size_bytes: int

    # Foreign Keys
    bucket_id: UUID | None = Field(default=None, description="Foreign key for StorageBlob.bucket")

    @classmethod
    async def create(cls, sha: str, mime_type: str, size_bytes: int) -> StorageBlob:
        """
        Registers a StorageBlob metadata record for already-uploaded bytes.

        Contract:
        - Commits must never include raw bytes.
        - Bytes are uploaded out-of-band (HTTP data-plane).
        - This constructor records the immutable metadata required to resolve and validate bytes.

        Parameters:
            sha: SHA-256 hex of the raw bytes.
            mime_type: MIME type of the blob.
            size_bytes: Size of the blob in bytes.

        Returns: The created (or idempotently re-used) StorageBlob.
        """

        payload = {"sha": sha, "mime_type": mime_type, "size_bytes": size_bytes}
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, StorageBlob):
            return value
        return StorageBlob.validate_invocation_value(value)


class StorageBlobCreateInput(BaseModel):
    sha: str
    mime_type: str
    size_bytes: int


class StorageBlobCreateOutput(BaseModel):
    value: StorageBlob


FUNCTIONS = {
    "StorageBlob": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Registers a StorageBlob metadata record for already-uploaded bytes.\n\nContract:\n- Commits must never include raw bytes.\n- Bytes are uploaded out-of-band (HTTP data-plane).\n- This constructor records the immutable metadata required to resolve and validate bytes.\n\nParameters:\n    sha: SHA-256 hex of the raw bytes.\n    mime_type: MIME type of the blob.\n    size_bytes: Size of the blob in bytes.\n\nReturns: The created (or idempotently re-used) StorageBlob.",
                "is_constructor": True,
            },
            "input": StorageBlobCreateInput,
            "output": StorageBlobCreateOutput,
        },
    },
}

__all__ = [
    "StorageBlob",
    "StorageBlobCreateInput",
    "StorageBlobCreateOutput",
    "FUNCTIONS",
]
