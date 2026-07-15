from __future__ import annotations

# Standard
from typing import (
    Any,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology.code.code_plan import CodeContentPlan
    from aware_code_ontology.code.code_section import CodeSection
    from aware_code_ontology.code.code_test import CodeTest
    from aware_code_ontology.code.code_test_unit import CodeTestUnit
    from aware_content_ontology.part.content_part_text import ContentPartText


class Code(ORMModel):
    # Relationships
    code_sections: list[CodeSection] = Field(default_factory=list, exclude=True)
    content_part_text: ContentPartText
    tests: list[CodeTest] = Field(default_factory=list)

    # Attributes
    relative_path: str
    language: CodeLanguage | None = Field(default=None)

    # Foreign Keys
    content_part_text_id: UUID | None = Field(default=None, description="Foreign key for Code.content_part_text")
    code_package_code_id: UUID = Field(description="Propagation FK to CodePackageCode")

    async def create_section(
        self,
        section_key: str,
        qualname: str,
        type: CodeSectionType,
        identity_hash: str,
        byte_start: int,
        byte_end: int,
        metadata: JsonObject | None = None,
    ) -> CodeSection:
        """Create a deterministic CodeSection under this Code snapshot."""

        payload = {
            "section_key": section_key,
            "qualname": qualname,
            "type": type,
            "identity_hash": identity_hash,
            "byte_start": byte_start,
            "byte_end": byte_end,
            "metadata": metadata,
        }
        result = await invoke_instance(orm_model=self, function_name="create_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.code.code_section import CodeSection

        if isinstance(value, CodeSection):
            return value
        return CodeSection.validate_invocation_value(value)

    async def create_test(
        self, framework_id: UUID, discovery_kind: str = "language_plugin", selector_prefix: str | None = None
    ) -> CodeTest:
        """Create one canonical test surface for this Code object and framework."""

        payload = {"framework_id": framework_id, "discovery_kind": discovery_kind, "selector_prefix": selector_prefix}
        result = await invoke_instance(orm_model=self, function_name="create_test", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.code.code_test import CodeTest

        if isinstance(value, CodeTest):
            return value
        return CodeTest.validate_invocation_value(value)

    async def sync_test_unit(
        self,
        framework_id: UUID,
        code_section_id: UUID,
        unit_key: str,
        selector: str,
        kind: str = "function",
        name: str | None = None,
        discovery_kind: str = "language_plugin",
        selector_prefix: str | None = None,
    ) -> CodeTestUnit:
        """
        Upsert one framework-specific test unit under this Code object.

        This is the Code-owned inventory mutation rail used by CodePackage sync.
        """

        payload = {
            "framework_id": framework_id,
            "code_section_id": code_section_id,
            "unit_key": unit_key,
            "selector": selector,
            "kind": kind,
            "name": name,
            "discovery_kind": discovery_kind,
            "selector_prefix": selector_prefix,
        }
        result = await invoke_instance(orm_model=self, function_name="sync_test_unit", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.code.code_test_unit import CodeTestUnit

        if isinstance(value, CodeTestUnit):
            return value
        return CodeTestUnit.validate_invocation_value(value)

    async def apply_content_plan(self, plan: CodeContentPlan) -> Any:
        """Apply a canonical code content materialization plan through the owned Code handler rail."""

        payload = {"plan": plan}
        result = await invoke_instance(orm_model=self, function_name="apply_content_plan", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value

    async def delete(self) -> Any:
        """Delete this Code subtree and owned content payloads."""

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="delete", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value

    async def replace_content(self, content_text: str, language: CodeLanguage | None = None) -> Any:
        """Compatibility wrapper that parses inline text and delegates to `apply_content_plan(...)`."""

        payload = {"content_text": content_text, "language": language}
        result = await invoke_instance(orm_model=self, function_name="replace_content", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value

    @classmethod
    async def create_via_code_package_code(
        cls, code_package_code_id: UUID, relative_path: str, plan: CodeContentPlan
    ) -> Code:
        """Create a Code instance under one CodePackage from a canonical content plan."""

        payload = {"code_package_code_id": code_package_code_id, "relative_path": relative_path, "plan": plan}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_code_package_code", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Code):
            return value
        return Code.validate_invocation_value(value)


class CodeCreateSectionInput(BaseModel):
    section_key: str
    qualname: str
    type: CodeSectionType
    identity_hash: str
    byte_start: int
    byte_end: int
    metadata: JsonObject | None = Field(default=None)


class CodeCreateSectionOutput(BaseModel):
    value: CodeSection


class CodeCreateTestInput(BaseModel):
    framework_id: UUID
    discovery_kind: str = Field(default="language_plugin")
    selector_prefix: str | None = Field(default=None)


class CodeCreateTestOutput(BaseModel):
    value: CodeTest


class CodeSyncTestUnitInput(BaseModel):
    framework_id: UUID
    code_section_id: UUID
    unit_key: str
    selector: str
    kind: str = Field(default="function")
    name: str | None = Field(default=None)
    discovery_kind: str = Field(default="language_plugin")
    selector_prefix: str | None = Field(default=None)


class CodeSyncTestUnitOutput(BaseModel):
    value: CodeTestUnit


class CodeApplyContentPlanInput(BaseModel):
    plan: CodeContentPlan


class CodeApplyContentPlanOutput(BaseModel):
    value: Any


class CodeDeleteInput(BaseModel):
    pass


class CodeDeleteOutput(BaseModel):
    value: Any


class CodeReplaceContentInput(BaseModel):
    content_text: str
    language: CodeLanguage | None = Field(default=None)


class CodeReplaceContentOutput(BaseModel):
    value: Any


class CodeCreateViaCodePackageCodeInput(BaseModel):
    code_package_code_id: UUID = Field(description="Propagation FK to CodePackageCode")
    relative_path: str
    plan: CodeContentPlan


class CodeCreateViaCodePackageCodeOutput(BaseModel):
    value: Code


FUNCTIONS = {
    "Code": {
        "create_section": {
            "canonical": {
                "name": "create_section",
                "description": "Create a deterministic CodeSection under this Code snapshot.",
                "is_constructor": False,
            },
            "input": CodeCreateSectionInput,
            "output": CodeCreateSectionOutput,
        },
        "create_test": {
            "canonical": {
                "name": "create_test",
                "description": "Create one canonical test surface for this Code object and framework.",
                "is_constructor": False,
            },
            "input": CodeCreateTestInput,
            "output": CodeCreateTestOutput,
        },
        "sync_test_unit": {
            "canonical": {
                "name": "sync_test_unit",
                "description": "Upsert one framework-specific test unit under this Code object.\n\nThis is the Code-owned inventory mutation rail used by CodePackage sync.",
                "is_constructor": False,
            },
            "input": CodeSyncTestUnitInput,
            "output": CodeSyncTestUnitOutput,
        },
        "apply_content_plan": {
            "canonical": {
                "name": "apply_content_plan",
                "description": "Apply a canonical code content materialization plan through the owned Code handler rail.",
                "is_constructor": False,
            },
            "input": CodeApplyContentPlanInput,
            "output": CodeApplyContentPlanOutput,
        },
        "delete": {
            "canonical": {
                "name": "delete",
                "description": "Delete this Code subtree and owned content payloads.",
                "is_constructor": False,
            },
            "input": CodeDeleteInput,
            "output": CodeDeleteOutput,
        },
        "replace_content": {
            "canonical": {
                "name": "replace_content",
                "description": "Compatibility wrapper that parses inline text and delegates to `apply_content_plan(...)`.",
                "is_constructor": False,
            },
            "input": CodeReplaceContentInput,
            "output": CodeReplaceContentOutput,
        },
        "create_via_code_package_code": {
            "canonical": {
                "name": "create_via_code_package_code",
                "description": "Create a Code instance under one CodePackage from a canonical content plan.",
                "is_constructor": True,
            },
            "input": CodeCreateViaCodePackageCodeInput,
            "output": CodeCreateViaCodePackageCodeOutput,
        },
    },
}

__all__ = [
    "Code",
    "CodeCreateSectionInput",
    "CodeCreateSectionOutput",
    "CodeCreateTestInput",
    "CodeCreateTestOutput",
    "CodeSyncTestUnitInput",
    "CodeSyncTestUnitOutput",
    "CodeApplyContentPlanInput",
    "CodeApplyContentPlanOutput",
    "CodeDeleteInput",
    "CodeDeleteOutput",
    "CodeReplaceContentInput",
    "CodeReplaceContentOutput",
    "CodeCreateViaCodePackageCodeInput",
    "CodeCreateViaCodePackageCodeOutput",
    "FUNCTIONS",
]
