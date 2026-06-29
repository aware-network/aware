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
from aware_content_ontology.part.content_part_enums import ContentPartType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_content_ontology.part.content_part_file import ContentPartFile
    from aware_content_ontology.part.content_part_multimodal_index import ContentPartMultimodalIndex
    from aware_content_ontology.part.content_part_text import ContentPartText
    from aware_storage_ontology.blob.storage_blob import StorageBlob


class ContentPart(ORMModel):
    # Relationships
    content_part_multimodal_index: ContentPartMultimodalIndex | None = Field(default=None)
    content_part_text: ContentPartText | None = Field(default=None)

    # Attributes
    type: ContentPartType

    # Foreign Keys
    content_part_content_id: UUID = Field(description="Foreign key for ContentPartContent.content_part")

    # Edges
    content_part_file: ContentPartFile | None = Field(
        default=None, exclude=True, description="Edge association helper for storage_blobs"
    )

    @property
    def storage_blobs(self) -> StorageBlob | None:
        return (
            self.content_part_file.storage_blob
            if self.content_part_file is not None and self.content_part_file.storage_blob is not None
            else None
        )

    async def attach_file(
        self,
        modality_type: ModalityType,
        mime_type: str,
        inline_data: bytes | None = None,
        provider_id: str | None = None,
        raw_path: str | None = None,
    ) -> ContentPartFile:
        """Attaches file/media metadata to this content part."""

        payload = {
            "modality_type": modality_type,
            "mime_type": mime_type,
            "inline_data": inline_data,
            "provider_id": provider_id,
            "raw_path": raw_path,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_file", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_content_ontology.part.content_part_file import ContentPartFile

        if isinstance(value, ContentPartFile):
            return value
        return ContentPartFile.validate_invocation_value(value)

    @classmethod
    async def create_content_part_via_content_part_content(
        cls, content_part_content_id: UUID, type: ContentPartType, content_part_text_id: UUID | None = None
    ) -> ContentPart:
        """Creates a new content part."""

        payload = {
            "content_part_content_id": content_part_content_id,
            "type": type,
            "content_part_text_id": content_part_text_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_content_part_via_content_part_content", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPart):
            return value
        return ContentPart.validate_invocation_value(value)

    @classmethod
    async def create_text_part_via_content_part_content(
        cls,
        content_part_content_id: UUID,
        seed_inline_text: str | None = None,
        type: ContentPartType = ContentPartType.text,
    ) -> ContentPart:
        """Creates a text content part and its text child."""

        payload = {
            "content_part_content_id": content_part_content_id,
            "seed_inline_text": seed_inline_text,
            "type": type,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_text_part_via_content_part_content", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPart):
            return value
        return ContentPart.validate_invocation_value(value)


class ContentPartAttachFileInput(BaseModel):
    modality_type: ModalityType
    mime_type: str
    inline_data: bytes | None = Field(default=None)
    provider_id: str | None = Field(default=None)
    raw_path: str | None = Field(default=None)


class ContentPartAttachFileOutput(BaseModel):
    value: ContentPartFile


class ContentPartCreateContentPartViaContentPartContentInput(BaseModel):
    content_part_content_id: UUID = Field(description="Foreign key for ContentPartContent.content_part")
    type: ContentPartType
    content_part_text_id: UUID | None = Field(default=None)


class ContentPartCreateContentPartViaContentPartContentOutput(BaseModel):
    value: ContentPart


class ContentPartCreateTextPartViaContentPartContentInput(BaseModel):
    content_part_content_id: UUID = Field(description="Foreign key for ContentPartContent.content_part")
    seed_inline_text: str | None = Field(default=None)
    type: ContentPartType = Field(default=ContentPartType.text)


class ContentPartCreateTextPartViaContentPartContentOutput(BaseModel):
    value: ContentPart


FUNCTIONS = {
    "ContentPart": {
        "attach_file": {
            "canonical": {
                "name": "attach_file",
                "description": "Attaches file/media metadata to this content part.",
                "is_constructor": False,
            },
            "input": ContentPartAttachFileInput,
            "output": ContentPartAttachFileOutput,
        },
        "create_content_part_via_content_part_content": {
            "canonical": {
                "name": "create_content_part_via_content_part_content",
                "description": "Creates a new content part.",
                "is_constructor": True,
            },
            "input": ContentPartCreateContentPartViaContentPartContentInput,
            "output": ContentPartCreateContentPartViaContentPartContentOutput,
        },
        "create_text_part_via_content_part_content": {
            "canonical": {
                "name": "create_text_part_via_content_part_content",
                "description": "Creates a text content part and its text child.",
                "is_constructor": True,
            },
            "input": ContentPartCreateTextPartViaContentPartContentInput,
            "output": ContentPartCreateTextPartViaContentPartContentOutput,
        },
    },
}

__all__ = [
    "ContentPart",
    "ContentPartAttachFileInput",
    "ContentPartAttachFileOutput",
    "ContentPartCreateContentPartViaContentPartContentInput",
    "ContentPartCreateContentPartViaContentPartContentOutput",
    "ContentPartCreateTextPartViaContentPartContentInput",
    "ContentPartCreateTextPartViaContentPartContentOutput",
    "FUNCTIONS",
]
