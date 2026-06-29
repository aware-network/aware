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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionImportName(ORMModel):
    # Relationships
    name_segment: ContentPartTextSegment
    alias_segment: ContentPartTextSegment | None = Field(default=None)

    # Attributes
    name_text: str
    alias_text: str | None = Field(default=None)

    # Foreign Keys
    code_section_import_id: UUID = Field(description="Foreign key for CodeSectionImport.code_section_import_names")
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionImportName.name_segment")
    alias_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionImportName.alias_segment"
    )

    async def delete(self) -> None:
        """Delete this import-name payload through its owned handler rail."""

        payload = {}
        await invoke_instance(orm_model=self, function_name="delete", payload=payload)
        return None

    @classmethod
    async def build_via_code_section_import(
        cls,
        code_section_import_id: UUID,
        name_text: str,
        name_slot_key: str,
        name_byte_start: int,
        name_byte_end: int,
        alias_text: str | None = None,
        alias_slot_key: str | None = None,
        alias_byte_start: int | None = None,
        alias_byte_end: int | None = None,
    ) -> CodeSectionImportName:
        """Build a deterministic import-name entry under an import section."""

        payload = {
            "code_section_import_id": code_section_import_id,
            "name_text": name_text,
            "name_slot_key": name_slot_key,
            "name_byte_start": name_byte_start,
            "name_byte_end": name_byte_end,
            "alias_text": alias_text,
            "alias_slot_key": alias_slot_key,
            "alias_byte_start": alias_byte_start,
            "alias_byte_end": alias_byte_end,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section_import", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionImportName):
            return value
        return CodeSectionImportName.validate_invocation_value(value)


class CodeSectionImportNameDeleteInput(BaseModel):
    pass


class CodeSectionImportNameDeleteOutput(BaseModel):
    pass


class CodeSectionImportNameBuildViaCodeSectionImportInput(BaseModel):
    code_section_import_id: UUID = Field(description="Foreign key for CodeSectionImport.code_section_import_names")
    name_text: str
    name_slot_key: str
    name_byte_start: int
    name_byte_end: int
    alias_text: str | None = Field(default=None)
    alias_slot_key: str | None = Field(default=None)
    alias_byte_start: int | None = Field(default=None)
    alias_byte_end: int | None = Field(default=None)


class CodeSectionImportNameBuildViaCodeSectionImportOutput(BaseModel):
    value: CodeSectionImportName


FUNCTIONS = {
    "CodeSectionImportName": {
        "delete": {
            "canonical": {
                "name": "delete",
                "description": "Delete this import-name payload through its owned handler rail.",
                "is_constructor": False,
            },
            "input": CodeSectionImportNameDeleteInput,
            "output": CodeSectionImportNameDeleteOutput,
        },
        "build_via_code_section_import": {
            "canonical": {
                "name": "build_via_code_section_import",
                "description": "Build a deterministic import-name entry under an import section.",
                "is_constructor": True,
            },
            "input": CodeSectionImportNameBuildViaCodeSectionImportInput,
            "output": CodeSectionImportNameBuildViaCodeSectionImportOutput,
        },
    },
}

__all__ = [
    "CodeSectionImportName",
    "CodeSectionImportNameDeleteInput",
    "CodeSectionImportNameDeleteOutput",
    "CodeSectionImportNameBuildViaCodeSectionImportInput",
    "CodeSectionImportNameBuildViaCodeSectionImportOutput",
    "FUNCTIONS",
]
