from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.comment.code_section_comment_enums import CodeSectionCommentType
from aware_code_ontology.expression.code_section_expression_enums import CodeSectionExpressionType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology.annotation.code_section_annotation import CodeSectionAnnotation
    from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
    from aware_code_ontology.binding.code_section_binding import CodeSectionBinding
    from aware_code_ontology.class_.code_section_class import CodeSectionClass
    from aware_code_ontology.comment.code_section_comment import CodeSectionComment
    from aware_code_ontology.decorator.code_section_decorator import CodeSectionDecorator
    from aware_code_ontology.enum.code_section_enum import CodeSectionEnum
    from aware_code_ontology.enum.code_section_enum_value import CodeSectionEnumValue
    from aware_code_ontology.expression.code_section_expression import CodeSectionExpression
    from aware_code_ontology.function.code_section_function import CodeSectionFunction
    from aware_code_ontology.import_.code_section_import import CodeSectionImport
    from aware_code_ontology.mirror.code_section_mirror import CodeSectionMirror
    from aware_code_ontology.projection.code_section_projection import CodeSectionProjection
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


class CodeSection(ORMModel):
    # Relationships
    content_part_text_segment: ContentPartTextSegment
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None, exclude=True)
    code_section_attribute: CodeSectionAttribute | None = Field(default=None, exclude=True)
    code_section_binding: CodeSectionBinding | None = Field(default=None, exclude=True)
    code_section_class: CodeSectionClass | None = Field(default=None, exclude=True)
    code_section_comment: CodeSectionComment | None = Field(default=None, exclude=True)
    code_section_decorator: CodeSectionDecorator | None = Field(default=None, exclude=True)
    code_section_enum: CodeSectionEnum | None = Field(default=None, exclude=True)
    code_section_enum_value: CodeSectionEnumValue | None = Field(default=None, exclude=True)
    code_section_expression: CodeSectionExpression | None = Field(default=None, exclude=True)
    code_section_function: CodeSectionFunction | None = Field(default=None, exclude=True)
    code_section_import: CodeSectionImport | None = Field(default=None, exclude=True)
    code_section_mirror: CodeSectionMirror | None = Field(default=None, exclude=True)
    code_section_projection: CodeSectionProjection | None = Field(default=None, exclude=True)

    # Attributes
    identity_hash: str
    metadata: JsonObject | None = Field(default=None)
    qualname: str
    section_key: str
    type: CodeSectionType

    # Foreign Keys
    code_id: UUID = Field(description="Foreign key for Code.code_sections")
    content_part_text_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSection.content_part_text_segment"
    )

    async def delete(self) -> None:
        """Delete this CodeSection through its owned handler rail."""

        payload = {}
        await invoke_instance(orm_model=self, function_name="delete", payload=payload)
        return None

    async def create_annotation(self, path: str, verb: str, args: list[str]) -> CodeSectionAnnotation:
        """Create the annotation payload for this section."""

        payload = {"path": path, "verb": verb, "args": args}
        result = await invoke_instance(orm_model=self, function_name="create_annotation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.annotation.code_section_annotation import CodeSectionAnnotation

        if isinstance(value, CodeSectionAnnotation):
            return value
        return CodeSectionAnnotation.validate_invocation_value(value)

    async def create_attribute(self) -> CodeSectionAttribute:
        """Create the attribute payload for this section."""

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="create_attribute", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute

        if isinstance(value, CodeSectionAttribute):
            return value
        return CodeSectionAttribute.validate_invocation_value(value)

    async def create_binding(self) -> CodeSectionBinding:
        """Create the binding payload for this section."""

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="create_binding", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.binding.code_section_binding import CodeSectionBinding

        if isinstance(value, CodeSectionBinding):
            return value
        return CodeSectionBinding.validate_invocation_value(value)

    async def create_class(self) -> CodeSectionClass:
        """Create the class payload for this section."""

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="create_class", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.class_.code_section_class import CodeSectionClass

        if isinstance(value, CodeSectionClass):
            return value
        return CodeSectionClass.validate_invocation_value(value)

    async def create_comment(self, type: CodeSectionCommentType) -> CodeSectionComment:
        """Create the comment payload for this section."""

        payload = {"type": type}
        result = await invoke_instance(orm_model=self, function_name="create_comment", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.comment.code_section_comment import CodeSectionComment

        if isinstance(value, CodeSectionComment):
            return value
        return CodeSectionComment.validate_invocation_value(value)

    async def create_decorator(self) -> CodeSectionDecorator:
        """Create the decorator payload for this section."""

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="create_decorator", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.decorator.code_section_decorator import CodeSectionDecorator

        if isinstance(value, CodeSectionDecorator):
            return value
        return CodeSectionDecorator.validate_invocation_value(value)

    async def create_enum(self) -> CodeSectionEnum:
        """Create the enum payload for this section."""

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="create_enum", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.enum.code_section_enum import CodeSectionEnum

        if isinstance(value, CodeSectionEnum):
            return value
        return CodeSectionEnum.validate_invocation_value(value)

    async def create_enum_value(self, value: str, position: int = 0) -> CodeSectionEnumValue:
        """Create the enum-value payload for this section."""

        payload = {"value": value, "position": position}
        result = await invoke_instance(orm_model=self, function_name="create_enum_value", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.enum.code_section_enum_value import CodeSectionEnumValue

        if isinstance(value, CodeSectionEnumValue):
            return value
        return CodeSectionEnumValue.validate_invocation_value(value)

    async def create_expression(self, type: CodeSectionExpressionType) -> CodeSectionExpression:
        """Create the expression payload for this section."""

        payload = {"type": type}
        result = await invoke_instance(orm_model=self, function_name="create_expression", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.expression.code_section_expression import CodeSectionExpression

        if isinstance(value, CodeSectionExpression):
            return value
        return CodeSectionExpression.validate_invocation_value(value)

    async def create_function(self) -> CodeSectionFunction:
        """Create the function payload for this section."""

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="create_function", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.function.code_section_function import CodeSectionFunction

        if isinstance(value, CodeSectionFunction):
            return value
        return CodeSectionFunction.validate_invocation_value(value)

    async def create_import(
        self,
        module_text: str,
        is_from_import: bool,
        module_slot_key: str,
        module_byte_start: int,
        module_byte_end: int,
        is_star_import: bool = False,
        relative_level: int = 0,
    ) -> CodeSectionImport:
        """Create the import payload for this section."""

        payload = {
            "module_text": module_text,
            "is_from_import": is_from_import,
            "module_slot_key": module_slot_key,
            "module_byte_start": module_byte_start,
            "module_byte_end": module_byte_end,
            "is_star_import": is_star_import,
            "relative_level": relative_level,
        }
        result = await invoke_instance(orm_model=self, function_name="create_import", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.import_.code_section_import import CodeSectionImport

        if isinstance(value, CodeSectionImport):
            return value
        return CodeSectionImport.validate_invocation_value(value)

    async def create_mirror(self) -> CodeSectionMirror:
        """Create the mirror payload for this section."""

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="create_mirror", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.mirror.code_section_mirror import CodeSectionMirror

        if isinstance(value, CodeSectionMirror):
            return value
        return CodeSectionMirror.validate_invocation_value(value)

    async def create_projection(self) -> CodeSectionProjection:
        """Create the projection payload for this section."""

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="create_projection", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.projection.code_section_projection import CodeSectionProjection

        if isinstance(value, CodeSectionProjection):
            return value
        return CodeSectionProjection.validate_invocation_value(value)

    @classmethod
    async def build_via_code(
        cls,
        code_id: UUID,
        section_key: str,
        qualname: str,
        type: CodeSectionType,
        identity_hash: str,
        byte_start: int,
        byte_end: int,
        metadata: JsonObject | None = None,
    ) -> CodeSection:
        """Build a deterministic CodeSection under a Code snapshot."""

        payload = {
            "code_id": code_id,
            "section_key": section_key,
            "qualname": qualname,
            "type": type,
            "identity_hash": identity_hash,
            "byte_start": byte_start,
            "byte_end": byte_end,
            "metadata": metadata,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSection):
            return value
        return CodeSection.validate_invocation_value(value)


class CodeSectionDeleteInput(BaseModel):
    pass


class CodeSectionDeleteOutput(BaseModel):
    pass


class CodeSectionCreateAnnotationInput(BaseModel):
    path: str
    verb: str
    args: list[str] = Field(default_factory=list)


class CodeSectionCreateAnnotationOutput(BaseModel):
    value: CodeSectionAnnotation


class CodeSectionCreateAttributeInput(BaseModel):
    pass


class CodeSectionCreateAttributeOutput(BaseModel):
    value: CodeSectionAttribute


class CodeSectionCreateBindingInput(BaseModel):
    pass


class CodeSectionCreateBindingOutput(BaseModel):
    value: CodeSectionBinding


class CodeSectionCreateClassInput(BaseModel):
    pass


class CodeSectionCreateClassOutput(BaseModel):
    value: CodeSectionClass


class CodeSectionCreateCommentInput(BaseModel):
    type: CodeSectionCommentType


class CodeSectionCreateCommentOutput(BaseModel):
    value: CodeSectionComment


class CodeSectionCreateDecoratorInput(BaseModel):
    pass


class CodeSectionCreateDecoratorOutput(BaseModel):
    value: CodeSectionDecorator


class CodeSectionCreateEnumInput(BaseModel):
    pass


class CodeSectionCreateEnumOutput(BaseModel):
    value: CodeSectionEnum


class CodeSectionCreateEnumValueInput(BaseModel):
    value: str
    position: int = Field(default=0)


class CodeSectionCreateEnumValueOutput(BaseModel):
    value: CodeSectionEnumValue


class CodeSectionCreateExpressionInput(BaseModel):
    type: CodeSectionExpressionType


class CodeSectionCreateExpressionOutput(BaseModel):
    value: CodeSectionExpression


class CodeSectionCreateFunctionInput(BaseModel):
    pass


class CodeSectionCreateFunctionOutput(BaseModel):
    value: CodeSectionFunction


class CodeSectionCreateImportInput(BaseModel):
    module_text: str
    is_from_import: bool
    module_slot_key: str
    module_byte_start: int
    module_byte_end: int
    is_star_import: bool = Field(default=False)
    relative_level: int = Field(default=0)


class CodeSectionCreateImportOutput(BaseModel):
    value: CodeSectionImport


class CodeSectionCreateMirrorInput(BaseModel):
    pass


class CodeSectionCreateMirrorOutput(BaseModel):
    value: CodeSectionMirror


class CodeSectionCreateProjectionInput(BaseModel):
    pass


class CodeSectionCreateProjectionOutput(BaseModel):
    value: CodeSectionProjection


class CodeSectionBuildViaCodeInput(BaseModel):
    code_id: UUID = Field(description="Foreign key for Code.code_sections")
    section_key: str
    qualname: str
    type: CodeSectionType
    identity_hash: str
    byte_start: int
    byte_end: int
    metadata: JsonObject | None = Field(default=None)


class CodeSectionBuildViaCodeOutput(BaseModel):
    value: CodeSection


FUNCTIONS = {
    "CodeSection": {
        "delete": {
            "canonical": {
                "name": "delete",
                "description": "Delete this CodeSection through its owned handler rail.",
                "is_constructor": False,
            },
            "input": CodeSectionDeleteInput,
            "output": CodeSectionDeleteOutput,
        },
        "create_annotation": {
            "canonical": {
                "name": "create_annotation",
                "description": "Create the annotation payload for this section.",
                "is_constructor": False,
            },
            "input": CodeSectionCreateAnnotationInput,
            "output": CodeSectionCreateAnnotationOutput,
        },
        "create_attribute": {
            "canonical": {
                "name": "create_attribute",
                "description": "Create the attribute payload for this section.",
                "is_constructor": False,
            },
            "input": CodeSectionCreateAttributeInput,
            "output": CodeSectionCreateAttributeOutput,
        },
        "create_binding": {
            "canonical": {
                "name": "create_binding",
                "description": "Create the binding payload for this section.",
                "is_constructor": False,
            },
            "input": CodeSectionCreateBindingInput,
            "output": CodeSectionCreateBindingOutput,
        },
        "create_class": {
            "canonical": {
                "name": "create_class",
                "description": "Create the class payload for this section.",
                "is_constructor": False,
            },
            "input": CodeSectionCreateClassInput,
            "output": CodeSectionCreateClassOutput,
        },
        "create_comment": {
            "canonical": {
                "name": "create_comment",
                "description": "Create the comment payload for this section.",
                "is_constructor": False,
            },
            "input": CodeSectionCreateCommentInput,
            "output": CodeSectionCreateCommentOutput,
        },
        "create_decorator": {
            "canonical": {
                "name": "create_decorator",
                "description": "Create the decorator payload for this section.",
                "is_constructor": False,
            },
            "input": CodeSectionCreateDecoratorInput,
            "output": CodeSectionCreateDecoratorOutput,
        },
        "create_enum": {
            "canonical": {
                "name": "create_enum",
                "description": "Create the enum payload for this section.",
                "is_constructor": False,
            },
            "input": CodeSectionCreateEnumInput,
            "output": CodeSectionCreateEnumOutput,
        },
        "create_enum_value": {
            "canonical": {
                "name": "create_enum_value",
                "description": "Create the enum-value payload for this section.",
                "is_constructor": False,
            },
            "input": CodeSectionCreateEnumValueInput,
            "output": CodeSectionCreateEnumValueOutput,
        },
        "create_expression": {
            "canonical": {
                "name": "create_expression",
                "description": "Create the expression payload for this section.",
                "is_constructor": False,
            },
            "input": CodeSectionCreateExpressionInput,
            "output": CodeSectionCreateExpressionOutput,
        },
        "create_function": {
            "canonical": {
                "name": "create_function",
                "description": "Create the function payload for this section.",
                "is_constructor": False,
            },
            "input": CodeSectionCreateFunctionInput,
            "output": CodeSectionCreateFunctionOutput,
        },
        "create_import": {
            "canonical": {
                "name": "create_import",
                "description": "Create the import payload for this section.",
                "is_constructor": False,
            },
            "input": CodeSectionCreateImportInput,
            "output": CodeSectionCreateImportOutput,
        },
        "create_mirror": {
            "canonical": {
                "name": "create_mirror",
                "description": "Create the mirror payload for this section.",
                "is_constructor": False,
            },
            "input": CodeSectionCreateMirrorInput,
            "output": CodeSectionCreateMirrorOutput,
        },
        "create_projection": {
            "canonical": {
                "name": "create_projection",
                "description": "Create the projection payload for this section.",
                "is_constructor": False,
            },
            "input": CodeSectionCreateProjectionInput,
            "output": CodeSectionCreateProjectionOutput,
        },
        "build_via_code": {
            "canonical": {
                "name": "build_via_code",
                "description": "Build a deterministic CodeSection under a Code snapshot.",
                "is_constructor": True,
            },
            "input": CodeSectionBuildViaCodeInput,
            "output": CodeSectionBuildViaCodeOutput,
        },
    },
}

__all__ = [
    "CodeSection",
    "CodeSectionDeleteInput",
    "CodeSectionDeleteOutput",
    "CodeSectionCreateAnnotationInput",
    "CodeSectionCreateAnnotationOutput",
    "CodeSectionCreateAttributeInput",
    "CodeSectionCreateAttributeOutput",
    "CodeSectionCreateBindingInput",
    "CodeSectionCreateBindingOutput",
    "CodeSectionCreateClassInput",
    "CodeSectionCreateClassOutput",
    "CodeSectionCreateCommentInput",
    "CodeSectionCreateCommentOutput",
    "CodeSectionCreateDecoratorInput",
    "CodeSectionCreateDecoratorOutput",
    "CodeSectionCreateEnumInput",
    "CodeSectionCreateEnumOutput",
    "CodeSectionCreateEnumValueInput",
    "CodeSectionCreateEnumValueOutput",
    "CodeSectionCreateExpressionInput",
    "CodeSectionCreateExpressionOutput",
    "CodeSectionCreateFunctionInput",
    "CodeSectionCreateFunctionOutput",
    "CodeSectionCreateImportInput",
    "CodeSectionCreateImportOutput",
    "CodeSectionCreateMirrorInput",
    "CodeSectionCreateMirrorOutput",
    "CodeSectionCreateProjectionInput",
    "CodeSectionCreateProjectionOutput",
    "CodeSectionBuildViaCodeInput",
    "CodeSectionBuildViaCodeOutput",
    "FUNCTIONS",
]
