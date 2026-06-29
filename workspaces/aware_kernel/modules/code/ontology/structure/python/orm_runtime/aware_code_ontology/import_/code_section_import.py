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
    from aware_code_ontology.code.code_section import CodeSection
    from aware_code_ontology.import_.code_section_import_name import CodeSectionImportName
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionImport(ORMModel):
    # Relationships
    code_section_import_names: list[CodeSectionImportName] = Field(default_factory=list)
    module_segment: ContentPartTextSegment
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_import")

    # Attributes
    module_text: str
    is_from_import: bool
    is_star_import: bool
    relative_level: int = Field(default=0)

    # Foreign Keys
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_import")
    module_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionImport.module_segment")

    async def delete(self) -> None:
        """Delete this import payload and its owned import-name entries through the owned handler rail."""

        payload = {}
        await invoke_instance(orm_model=self, function_name="delete", payload=payload)
        return None

    async def create_name(
        self,
        name_text: str,
        name_slot_key: str,
        name_byte_start: int,
        name_byte_end: int,
        alias_text: str | None = None,
        alias_slot_key: str | None = None,
        alias_byte_start: int | None = None,
        alias_byte_end: int | None = None,
    ) -> CodeSectionImportName:
        """Create a deterministic import-name entry under this import."""

        payload = {
            "name_text": name_text,
            "name_slot_key": name_slot_key,
            "name_byte_start": name_byte_start,
            "name_byte_end": name_byte_end,
            "alias_text": alias_text,
            "alias_slot_key": alias_slot_key,
            "alias_byte_start": alias_byte_start,
            "alias_byte_end": alias_byte_end,
        }
        result = await invoke_instance(orm_model=self, function_name="create_name", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.import_.code_section_import_name import CodeSectionImportName

        if isinstance(value, CodeSectionImportName):
            return value
        return CodeSectionImportName.validate_invocation_value(value)

    @classmethod
    async def build_via_code_section(
        cls,
        code_section_id: UUID,
        module_text: str,
        is_from_import: bool,
        module_slot_key: str,
        module_byte_start: int,
        module_byte_end: int,
        is_star_import: bool = False,
        relative_level: int = 0,
    ) -> CodeSectionImport:
        """Build the import payload under a CodeSection."""

        payload = {
            "code_section_id": code_section_id,
            "module_text": module_text,
            "is_from_import": is_from_import,
            "module_slot_key": module_slot_key,
            "module_byte_start": module_byte_start,
            "module_byte_end": module_byte_end,
            "is_star_import": is_star_import,
            "relative_level": relative_level,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionImport):
            return value
        return CodeSectionImport.validate_invocation_value(value)


class CodeSectionImportDeleteInput(BaseModel):
    pass


class CodeSectionImportDeleteOutput(BaseModel):
    pass


class CodeSectionImportCreateNameInput(BaseModel):
    name_text: str
    name_slot_key: str
    name_byte_start: int
    name_byte_end: int
    alias_text: str | None = Field(default=None)
    alias_slot_key: str | None = Field(default=None)
    alias_byte_start: int | None = Field(default=None)
    alias_byte_end: int | None = Field(default=None)


class CodeSectionImportCreateNameOutput(BaseModel):
    value: CodeSectionImportName


class CodeSectionImportBuildViaCodeSectionInput(BaseModel):
    code_section_id: UUID = Field(description="Foreign key for CodeSection.code_section_import")
    module_text: str
    is_from_import: bool
    module_slot_key: str
    module_byte_start: int
    module_byte_end: int
    is_star_import: bool = Field(default=False)
    relative_level: int = Field(default=0)


class CodeSectionImportBuildViaCodeSectionOutput(BaseModel):
    value: CodeSectionImport


FUNCTIONS = {
    "CodeSectionImport": {
        "delete": {
            "canonical": {
                "name": "delete",
                "description": "Delete this import payload and its owned import-name entries through the owned handler rail.",
                "is_constructor": False,
            },
            "input": CodeSectionImportDeleteInput,
            "output": CodeSectionImportDeleteOutput,
        },
        "create_name": {
            "canonical": {
                "name": "create_name",
                "description": "Create a deterministic import-name entry under this import.",
                "is_constructor": False,
            },
            "input": CodeSectionImportCreateNameInput,
            "output": CodeSectionImportCreateNameOutput,
        },
        "build_via_code_section": {
            "canonical": {
                "name": "build_via_code_section",
                "description": "Build the import payload under a CodeSection.",
                "is_constructor": True,
            },
            "input": CodeSectionImportBuildViaCodeSectionInput,
            "output": CodeSectionImportBuildViaCodeSectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionImport",
    "CodeSectionImportDeleteInput",
    "CodeSectionImportDeleteOutput",
    "CodeSectionImportCreateNameInput",
    "CodeSectionImportCreateNameOutput",
    "CodeSectionImportBuildViaCodeSectionInput",
    "CodeSectionImportBuildViaCodeSectionOutput",
    "FUNCTIONS",
]
