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


class CodeSectionAnnotation(ORMModel):
    # Relationships
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_annotation")

    # Attributes
    path: str
    verb: str
    args: list[str] = Field(default_factory=list)

    # Foreign Keys
    code_section_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSection.code_section_annotation"
    )

    async def delete(self) -> None:
        """Delete this annotation payload through its owned handler rail."""

        payload = {}
        await invoke_instance(orm_model=self, function_name="delete", payload=payload)
        return None

    @classmethod
    async def build_via_code_section(
        cls, code_section_id: UUID, path: str, verb: str, args: list[str] = []
    ) -> CodeSectionAnnotation:
        """Build the unique annotation payload under a CodeSection."""

        payload = {"code_section_id": code_section_id, "path": path, "verb": verb, "args": args}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionAnnotation):
            return value
        return CodeSectionAnnotation.validate_invocation_value(value)


class CodeSectionAnnotationDeleteInput(BaseModel):
    pass


class CodeSectionAnnotationDeleteOutput(BaseModel):
    pass


class CodeSectionAnnotationBuildViaCodeSectionInput(BaseModel):
    code_section_id: UUID = Field(description="Foreign key for CodeSection.code_section_annotation")
    path: str
    verb: str
    args: list[str] = Field(default_factory=list)


class CodeSectionAnnotationBuildViaCodeSectionOutput(BaseModel):
    value: CodeSectionAnnotation


FUNCTIONS = {
    "CodeSectionAnnotation": {
        "delete": {
            "canonical": {
                "name": "delete",
                "description": "Delete this annotation payload through its owned handler rail.",
                "is_constructor": False,
            },
            "input": CodeSectionAnnotationDeleteInput,
            "output": CodeSectionAnnotationDeleteOutput,
        },
        "build_via_code_section": {
            "canonical": {
                "name": "build_via_code_section",
                "description": "Build the unique annotation payload under a CodeSection.",
                "is_constructor": True,
            },
            "input": CodeSectionAnnotationBuildViaCodeSectionInput,
            "output": CodeSectionAnnotationBuildViaCodeSectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionAnnotation",
    "CodeSectionAnnotationDeleteInput",
    "CodeSectionAnnotationDeleteOutput",
    "CodeSectionAnnotationBuildViaCodeSectionInput",
    "CodeSectionAnnotationBuildViaCodeSectionOutput",
    "FUNCTIONS",
]
