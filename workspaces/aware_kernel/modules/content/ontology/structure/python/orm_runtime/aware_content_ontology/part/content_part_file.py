from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Content Ontology
from aware_content_ontology.content.content_enums import ModalityType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_storage_ontology.blob.storage_blob import StorageBlob


class ContentPartFile(ORMModel):
    # Relationships
    storage_blob: StorageBlob | None = Field(
        default=None, exclude=True, description="Association target reference to StorageBlob"
    )

    # Attributes
    inline_data: bytes | None = Field(default=None)
    mime_type: str
    modality_type: ModalityType
    provider_id: str | None = Field(default=None)
    raw_path: str | None = Field(default=None)

    # Foreign Keys
    storage_blob_id: UUID = Field(description="Join FK to StorageBlob")
    content_part_id: UUID = Field(description="Join FK to ContentPart")

    @classmethod
    async def create_content_part_file_via_content_part(
        cls,
        content_part_id: UUID,
        modality_type: ModalityType,
        mime_type: str,
        inline_data: bytes | None = None,
        provider_id: str | None = None,
        raw_path: str | None = None,
    ) -> ContentPartFile:
        """Creates file/media metadata for a ContentPart to StorageBlob edge."""

        payload = {
            "content_part_id": content_part_id,
            "modality_type": modality_type,
            "mime_type": mime_type,
            "inline_data": inline_data,
            "provider_id": provider_id,
            "raw_path": raw_path,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_content_part_file_via_content_part", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPartFile):
            return value
        return ContentPartFile.validate_invocation_value(value)


class ContentPartFileCreateContentPartFileViaContentPartInput(BaseModel):
    content_part_id: UUID = Field(description="Join FK to ContentPart")
    modality_type: ModalityType
    mime_type: str
    inline_data: bytes | None = Field(default=None)
    provider_id: str | None = Field(default=None)
    raw_path: str | None = Field(default=None)


class ContentPartFileCreateContentPartFileViaContentPartOutput(BaseModel):
    value: ContentPartFile


FUNCTIONS = {
    "ContentPartFile": {
        "create_content_part_file_via_content_part": {
            "canonical": {
                "name": "create_content_part_file_via_content_part",
                "description": "Creates file/media metadata for a ContentPart to StorageBlob edge.",
                "is_constructor": True,
            },
            "input": ContentPartFileCreateContentPartFileViaContentPartInput,
            "output": ContentPartFileCreateContentPartFileViaContentPartOutput,
        },
    },
}

__all__ = [
    "ContentPartFile",
    "ContentPartFileCreateContentPartFileViaContentPartInput",
    "ContentPartFileCreateContentPartFileViaContentPartOutput",
    "FUNCTIONS",
]
