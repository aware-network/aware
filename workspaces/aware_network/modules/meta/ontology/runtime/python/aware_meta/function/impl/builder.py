"""Build function-impl invocation rails from canonical function body text."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Literal
from uuid import UUID

from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_meta_ontology.stable_ids import (
    stable_class_config_attribute_config_id,
    stable_function_impl_id,
    stable_function_impl_instruction_id,
    stable_function_impl_instruction_construct_assignment_id,
    stable_function_impl_instruction_construct_id,
    stable_function_impl_instruction_let_id,
    stable_function_impl_instruction_invoke_id,
    stable_function_impl_instruction_invoke_attribute_config_id,
    stable_function_impl_instruction_set_id,
    stable_function_impl_instruction_require_id,
    stable_function_impl_instruction_require_operand_id,
    stable_function_impl_value_source_id,
    stable_function_impl_value_source_literal_primitive_id,
    stable_function_impl_value_source_read_path_id,
    stable_function_impl_value_source_read_path_segment_id,
    stable_function_impl_value_source_transform_id,
    stable_function_impl_value_source_transform_operand_id,
)
from aware_content.builder import get_segment_text
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_storage.blob_store import LocalBlobStore
from aware_meta.graph.config.stable_ids import (
    stable_function_impl_instruction_delete_id,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionIdentityKeyOrigin,
)
from aware_meta_ontology.function.function_config_invocation import (
    FunctionConfigInvocation,
)
from aware_meta_ontology.function.function_config_invocation_enums import (
    FunctionInvocationKind,
    FunctionInvocationRootKind,
)
from aware_meta_ontology.function.function_impl import FunctionImpl
from aware_meta_ontology.function.function_impl_instruction import (
    FunctionImplInstruction,
)
from aware_meta_ontology.function.function_impl_instruction_enums import (
    FunctionImplInstructionType,
    FunctionImplInvokeKind,
    FunctionImplRequireCompareOperator,
    FunctionImplRequireKind,
    FunctionImplValueSourceReadPathRootKind,
    FunctionImplValueSourceKind,
    FunctionImplValueTransformKind,
)
from aware_meta_ontology.function.function_impl_instruction_construct import (
    FunctionImplInstructionConstruct,
)
from aware_meta_ontology.function.function_impl_instruction_construct_assignment import (
    FunctionImplInstructionConstructAssignment,
)
from aware_meta_ontology.function.function_impl_instruction_invoke import (
    FunctionImplInstructionInvoke,
)
from aware_meta_ontology.function.function_impl_instruction_invoke_attribute_config import (
    FunctionImplInstructionInvokeAttributeConfig,
)
from aware_meta_ontology.function.function_impl_instruction_let import (
    FunctionImplInstructionLet,
)
from aware_meta_ontology.function.function_impl_instruction_require import (
    FunctionImplInstructionRequire,
)
from aware_meta_ontology.function.function_impl_instruction_require_operand import (
    FunctionImplInstructionRequireOperand,
)
from aware_meta_ontology.function.function_impl_instruction_set import (
    FunctionImplInstructionSet,
)
from aware_meta_ontology.function.function_impl_value_source import (
    FunctionImplValueSource,
)
from aware_meta_ontology.function.function_impl_value_source_literal_primitive import (
    FunctionImplValueSourceLiteralPrimitive,
)
from aware_meta_ontology.function.function_impl_value_source_read_path import (
    FunctionImplValueSourceReadPath,
)
from aware_meta_ontology.function.function_impl_value_source_read_path_segment import (
    FunctionImplValueSourceReadPathSegment,
)
from aware_meta_ontology.function.function_impl_value_source_transform import (
    FunctionImplValueSourceTransform,
)
from aware_meta_ontology.function.function_impl_value_source_transform_operand import (
    FunctionImplValueSourceTransformOperand,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta.primitive.config.builder import build_primitive_config

from aware_meta_ontology.stable_ids import (
    stable_function_config_invocation_id,
)

try:
    from aware_grammar.function.parser import (
        FunctionBodyCallArg,
        FunctionBodyExpression,
        FunctionBodyStatement,
        FunctionParseError,
        parse_function_statements_from_block,
        parse_function_invocations_from_block,
    )
except Exception:
    FunctionBodyCallArg = object
    FunctionBodyExpression = object
    FunctionBodyStatement = object
    FunctionParseError = ValueError
    parse_function_statements_from_block = None
    parse_function_invocations_from_block = None


@dataclass(frozen=True, slots=True)
class _InvocationSpec:
    position: int
    line_number: int
    kind: FunctionInvocationKind
    target_path: tuple[str, ...]
    capture_name: str | None


@dataclass(frozen=True, slots=True)
class _RawInvocationSpec:
    line_number: int
    column_number: int
    kind: FunctionInvocationKind
    target_path: tuple[str, ...]
    capture_name: str | None


@dataclass(frozen=True, slots=True)
class _InvocationParseIssue:
    line_number: int
    message: str


@dataclass(frozen=True, slots=True)
class _ResolvedInvocation:
    spec: _InvocationSpec
    target_function: FunctionConfig
    relationship: ClassConfigRelationship | None


@dataclass(frozen=True, slots=True)
class _LetBinding:
    payload: FunctionImplInstructionLet
    primitive_base_type: CodePrimitiveBaseType | None = None
    type_descriptor: AttributeTypeDescriptor | None = None
    captures_construct_output: bool = False


@dataclass(frozen=True, slots=True)
class _ValueSourceBuildResult:
    payload: FunctionImplValueSource
    primitive_base_type: CodePrimitiveBaseType | None = None
    type_descriptor: AttributeTypeDescriptor | None = None


@dataclass(frozen=True, slots=True)
class _ReadPathRoot:
    root_kind: FunctionImplValueSourceReadPathRootKind
    root_function_config_attribute_config: FunctionConfigAttributeConfig | None = None
    root_instruction_let: FunctionImplInstructionLet | None = None
    root_class_config_attribute_config: ClassConfigAttributeConfig | None = None
    type_descriptor: AttributeTypeDescriptor | None = None


def _value_source_result_sources(
    result: _ValueSourceBuildResult,
) -> tuple[FunctionImplValueSource, ...]:
    return (result.payload,)


def _build_synthetic_invoke_capture_let(
    *,
    function_impl_id: object,
    capture_token: str,
    binding_name: str,
) -> FunctionImplInstructionLet:
    """Create metadata for invoke-result bindings without emitting a standalone let instruction."""
    synthetic_instruction_id = stable_function_impl_instruction_id(
        function_impl_id=function_impl_id,
        sequence=0,
        type=f"invoke_capture:{capture_token}",
    )
    return FunctionImplInstructionLet(
        id=stable_function_impl_instruction_let_id(
            function_impl_instruction_id=synthetic_instruction_id
        ),
        function_impl_instruction_id=synthetic_instruction_id,
        name=binding_name,
        value_expr={"kind": "reference", "name": binding_name},
    )


def _enum_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw).strip().lower()


FunctionImplKindName = Literal["instruction_body", "auto_constructor"]


def _function_impl_kind_value(kind: FunctionImplKindName) -> object:
    """Return generated enum value when available, with a raw-token fallback.

    The authored Meta ontology owns `FunctionImplKind`, but generated Meta
    Python may lag until the next lock/materialization advance. Keeping this
    helper local lets the builder emit the canonical value as soon as the
    generated field exists without breaking current generated imports.
    """
    try:
        enum_module = import_module("aware_meta_ontology.function.function_impl_enums")
    except Exception:
        return kind
    enum_cls = getattr(enum_module, "FunctionImplKind", None)
    if enum_cls is None:
        return kind
    return getattr(enum_cls, kind, kind)


def _function_impl_model_has_kind() -> bool:
    return "kind" in getattr(FunctionImpl, "model_fields", {})


def _set_function_impl_kind(
    function_impl: FunctionImpl, kind: FunctionImplKindName
) -> None:
    kind_value = _function_impl_kind_value(kind)
    if not _function_impl_model_has_kind():
        kind_value = _enum_value(kind_value)
    object.__setattr__(function_impl, "kind", kind_value)


def _function_impl_delete_target_self() -> object:
    try:
        enum_module = import_module(
            "aware_meta_ontology.function.function_impl_instruction_enums"
        )
    except Exception:
        return "self"
    enum_cls = getattr(enum_module, "FunctionImplDeleteTargetKind", None)
    if enum_cls is None:
        return "self"
    return getattr(enum_cls, "self", "self")


def _build_function_impl_instruction_delete(
    *,
    id: UUID,
    function_impl_instruction_id: UUID,
    target_kind: object,
) -> object:
    try:
        delete_module = import_module(
            "aware_meta_ontology.function.function_impl_instruction_delete"
        )
    except Exception as exc:
        raise ValueError(
            "FunctionImplInstructionDelete generated model is unavailable; "
            "materialize meta-ontology before lowering `delete self`."
        ) from exc
    delete_cls = getattr(delete_module, "FunctionImplInstructionDelete", None)
    if delete_cls is None:
        raise ValueError(
            "FunctionImplInstructionDelete generated model is unavailable; "
            "materialize meta-ontology before lowering `delete self`."
        )
    return delete_cls(
        id=id,
        function_impl_instruction_id=function_impl_instruction_id,
        target_kind=target_kind,
    )


def _build_function_impl_shell(
    *,
    function_impl_id: UUID,
    function_config_id: UUID,
    key: str,
    kind: FunctionImplKindName,
) -> FunctionImpl:
    function_impl = FunctionImpl(
        id=function_impl_id,
        key=(key or "").strip() or "default",
        function_config_id=function_config_id,
    )
    _set_function_impl_kind(function_impl, kind)
    return function_impl


def _function_config_is_constructor(
    function_config: FunctionConfig,
    *,
    is_constructor: bool | None = None,
) -> bool:
    if is_constructor is not None:
        return bool(is_constructor)
    return str(function_config.verb or "").strip().casefold() == "construct"


def _classify_function_impl_kind(
    *,
    function_config: FunctionConfig,
    instruction_count: int,
    is_constructor: bool | None = None,
) -> FunctionImplKindName:
    if (
        _function_config_is_constructor(function_config, is_constructor=is_constructor)
        and instruction_count == 0
    ):
        return "auto_constructor"
    return "instruction_body"


def _function_impl_kind_name(
    function_impl: FunctionImpl,
    *,
    default: FunctionImplKindName,
) -> FunctionImplKindName:
    raw_kind = _enum_value(getattr(function_impl, "kind", ""))
    if raw_kind == "instruction_body":
        return "instruction_body"
    if raw_kind == "auto_constructor":
        return "auto_constructor"
    return default


def apply_function_impl_kind(
    *,
    function_config: FunctionConfig,
    function_impl: FunctionImpl,
    is_constructor: bool | None = None,
) -> FunctionImplKindName:
    """Normalize FunctionImpl.kind once class-function edge truth is known."""
    kind = _classify_function_impl_kind(
        function_config=function_config,
        instruction_count=len(function_impl.instructions),
        is_constructor=is_constructor,
    )
    _set_function_impl_kind(function_impl, kind)
    return kind


def _parse_invocation_specs(body_text: str) -> tuple[list[_InvocationSpec], list[str]]:
    tree_specs, tree_issues = _parse_invocation_specs_tree_sitter(body_text)

    merged_specs: list[_RawInvocationSpec] = list(tree_specs)
    merged_issues: list[_InvocationParseIssue] = list(tree_issues)
    merged_specs.sort(key=lambda spec: (spec.line_number, spec.column_number))
    specs = [
        _InvocationSpec(
            position=position,
            line_number=spec.line_number,
            kind=spec.kind,
            target_path=spec.target_path,
            capture_name=spec.capture_name,
        )
        for position, spec in enumerate(merged_specs)
    ]

    seen_issues: set[tuple[int, str]] = set()
    errors: list[str] = []
    for issue in sorted(
        merged_issues, key=lambda entry: (entry.line_number, entry.message)
    ):
        issue_key = (issue.line_number, issue.message)
        if issue_key in seen_issues:
            continue
        seen_issues.add(issue_key)
        errors.append(f"line {issue.line_number}: {issue.message}")
    return specs, errors


def _parse_invocation_specs_tree_sitter(
    body_text: str,
) -> tuple[list[_RawInvocationSpec], list[_InvocationParseIssue]]:
    if parse_function_invocations_from_block is None:
        return [], [
            _InvocationParseIssue(
                line_number=1,
                message=(
                    "function invocation parser is unavailable; cannot derive "
                    "canonical call/construct propagation."
                ),
            )
        ]

    try:
        parsed = parse_function_invocations_from_block(body_text or "")
    except FunctionParseError as exc:
        message = str(exc).strip() or "Aware function body source contains parse errors"
        return [], [
            _InvocationParseIssue(
                line_number=1,
                message=f"function body parse error: {message}",
            )
        ]
    except Exception as exc:
        return [], [
            _InvocationParseIssue(
                line_number=1,
                message=(
                    "function body parse error: unexpected parser failure "
                    f"({type(exc).__name__})"
                ),
            )
        ]

    specs: list[_RawInvocationSpec] = []
    issues: list[_InvocationParseIssue] = []
    for item in parsed:
        kind_raw = (item.kind or "").strip().lower()
        kind = (
            FunctionInvocationKind.construct
            if kind_raw == "construct"
            else FunctionInvocationKind.call
        )
        target_path = tuple(part for part in item.target_path if part)
        target_raw = ".".join(target_path)
        if len(target_path) not in {1, 2}:
            issues.append(
                _InvocationParseIssue(
                    line_number=max(1, item.line_number),
                    message=(
                        f"invocation target '{target_raw}' must be either owner-local (`function`) "
                        "or single-hop (`receiver.function`)."
                    ),
                )
            )
            continue

        specs.append(
            _RawInvocationSpec(
                line_number=max(1, item.line_number),
                column_number=max(1, item.column_number),
                kind=kind,
                target_path=target_path,
                capture_name=item.capture_name,
            )
        )
    return specs, issues


def _parse_function_statements(
    body_text: str,
) -> tuple[list[FunctionBodyStatement], list[str]]:
    if parse_function_statements_from_block is None:
        return [], [
            "line 1: function statement parser is unavailable; cannot derive canonical FunctionImpl instructions.",
        ]

    try:
        parsed = parse_function_statements_from_block(body_text or "")
    except FunctionParseError as exc:
        message = str(exc).strip() or "Aware function body source contains parse errors"
        return [], [f"line 1: function body parse error: {message}"]
    except Exception as exc:
        return [], [
            f"line 1: function body parse error: unexpected parser failure ({type(exc).__name__})",
        ]
    return list(parsed), []


def _line_is_ignorable(raw_line: str) -> bool:
    stripped = raw_line.strip()
    if not stripped:
        return True
    compact = stripped.replace(" ", "")
    if compact in {"{", "}", "{}"}:
        return True
    if stripped.startswith("//"):
        return True
    if (
        stripped.startswith("/*")
        or stripped.startswith("*")
        or stripped.startswith("*/")
    ):
        return True
    return False


def _line_starts_with_known_statement(raw_line: str) -> bool:
    stripped = raw_line.strip()
    return stripped.startswith(
        ("let ", "call ", "construct ", "set ", "require ", "delete ")
    )


def _statement_coverage_errors(
    *, body_text: str, statements: list[FunctionBodyStatement]
) -> list[str]:
    recognized_lines: set[int] = set()
    for stmt in statements:
        start_line = max(1, int(getattr(stmt, "line_number", 1)))
        end_line_raw = getattr(stmt, "end_line_number", None)
        end_line = (
            start_line if end_line_raw is None else max(start_line, int(end_line_raw))
        )
        recognized_lines.update(range(start_line, end_line + 1))

    inside_multiline_literal_delim: str | None = None
    errors: list[str] = []
    for line_index, raw_line in enumerate((body_text or "").splitlines(), start=1):
        if inside_multiline_literal_delim is not None:
            if raw_line.count(inside_multiline_literal_delim) % 2 == 1:
                inside_multiline_literal_delim = None
            continue

        stripped = raw_line.strip()
        if stripped.startswith('"""'):
            if raw_line.count('"""') % 2 == 1:
                inside_multiline_literal_delim = '"""'
            continue
        if stripped.startswith("$$"):
            if raw_line.count("$$") % 2 == 1:
                inside_multiline_literal_delim = "$$"
            continue

        if _line_is_ignorable(raw_line):
            continue
        if line_index in recognized_lines:
            continue
        if _line_starts_with_known_statement(raw_line):
            errors.append(
                f"line {line_index}: statement could not be parsed into canonical FunctionImpl instruction form."
            )
            continue
        errors.append(
            f"line {line_index}: unsupported function body statement for FunctionImpl v0 "
            f"({raw_line.strip()!r})."
        )
    return errors


def _primitive_base_type_from_attribute_config(
    attr_cfg: AttributeConfig | None,
) -> CodePrimitiveBaseType | None:
    if attr_cfg is None:
        return None
    descriptor = attr_cfg.type_descriptor
    if descriptor is None:
        return None
    if descriptor.kind != AttributeTypeDescriptorKind.primitive:
        return None
    primitive_config = descriptor.primitive_config
    if primitive_config is None:
        return None
    primitive_type = primitive_config.primitive_type
    if primitive_type is None:
        return None
    return primitive_type.base_type


def _type_descriptor_from_attribute_config(
    attr_cfg: AttributeConfig | None,
) -> AttributeTypeDescriptor | None:
    if attr_cfg is None:
        return None
    return attr_cfg.type_descriptor


def _attribute_type_is_enum(
    descriptor: AttributeTypeDescriptor | None,
) -> bool:
    if descriptor is None:
        return False
    return descriptor.kind == AttributeTypeDescriptorKind.enum


def _enum_literal_error(
    *,
    descriptor: AttributeTypeDescriptor | None,
    token: str,
) -> str | None:
    if descriptor is None:
        return None
    enum_config = descriptor.enum_config
    if enum_config is None or not enum_config.enum_options:
        return None
    candidates = {token, token.strip()}
    for option in enum_config.enum_options:
        option_value = option.value
        if option_value in candidates:
            return None
    known = ", ".join(sorted(option.value for option in enum_config.enum_options)[:10])
    return f"enum literal {token!r} is not declared on target enum [{known}]"


def _primitive_config_for_base_type(
    *,
    primitive_configs_by_base: dict[CodePrimitiveBaseType, object],
    base_type: CodePrimitiveBaseType,
) -> object:
    primitive_config = primitive_configs_by_base.get(base_type)
    if primitive_config is not None:
        return primitive_config
    primitive_config = build_primitive_config(
        build_code_primitive_type(base_type=base_type)
    )
    primitive_configs_by_base[base_type] = primitive_config
    return primitive_config


def _collect_primitive_configs_by_base_type(
    *,
    function_config: FunctionConfig,
    owner_class_config: ClassConfig,
) -> dict[CodePrimitiveBaseType, object]:
    configs: dict[CodePrimitiveBaseType, object] = {}

    def _visit_attr(attr_cfg: AttributeConfig | None) -> None:
        if attr_cfg is None:
            return
        descriptor = attr_cfg.type_descriptor
        if descriptor is None:
            return
        if descriptor.kind != AttributeTypeDescriptorKind.primitive:
            return
        primitive_config = descriptor.primitive_config
        if primitive_config is None:
            return
        primitive_type = primitive_config.primitive_type
        if primitive_type is None:
            return
        base_type = primitive_type.base_type
        if base_type is None:
            return
        configs.setdefault(base_type, primitive_config)

    for link in owner_class_config.class_config_attribute_configs:
        _visit_attr(link.attribute_config)
    for link in function_config.function_config_attribute_configs:
        _visit_attr(link.attribute_config)
    return configs


def _literal_base_type(value: object) -> CodePrimitiveBaseType | None:
    if value is None:
        return CodePrimitiveBaseType.null
    if isinstance(value, bool):
        return CodePrimitiveBaseType.boolean
    if isinstance(value, int):
        return CodePrimitiveBaseType.integer
    if isinstance(value, float):
        return CodePrimitiveBaseType.float
    if isinstance(value, str):
        return CodePrimitiveBaseType.string
    if isinstance(value, list):
        return CodePrimitiveBaseType.array
    if isinstance(value, dict):
        return CodePrimitiveBaseType.dict
    return None


def _literal_matches_base_type(
    *, value: object, base_type: CodePrimitiveBaseType
) -> bool:
    literal_base_type = _literal_base_type(value)
    if literal_base_type is None:
        return False
    if literal_base_type == base_type:
        return True
    # Allow integer literals for float targets as deterministic widening.
    if (
        literal_base_type == CodePrimitiveBaseType.integer
        and base_type == CodePrimitiveBaseType.float
    ):
        return True
    return False


def _base_type_assignable(
    *, source: CodePrimitiveBaseType, target: CodePrimitiveBaseType
) -> bool:
    if source == target:
        return True
    if (
        source == CodePrimitiveBaseType.integer
        and target == CodePrimitiveBaseType.float
    ):
        return True
    return False


def _resolve_class_attribute_by_name(
    *,
    class_config: ClassConfig,
    attribute_name: str,
) -> ClassConfigAttributeConfig | None:
    for link in class_config.class_config_attribute_configs:
        attr_cfg = link.attribute_config
        if attr_cfg is not None and attr_cfg.name == attribute_name:
            return link
    for relationship in class_config.class_config_relationships:
        if relationship.class_config_id != class_config.id:
            continue
        for rel_attr in relationship.class_config_relationship_attributes:
            if _enum_value(rel_attr.direction) != "forward":
                continue
            if _enum_value(rel_attr.role) != "reference":
                continue
            attr_cfg = rel_attr.attribute_config
            if attr_cfg is None or attr_cfg.name != attribute_name:
                continue
            return ClassConfigAttributeConfig(
                id=stable_class_config_attribute_config_id(
                    class_config_id=class_config.id,
                    attribute_config_id=rel_attr.attribute_config_id,
                ),
                class_config_id=class_config.id,
                attribute_config_id=rel_attr.attribute_config_id,
                attribute_config=attr_cfg,
                position=0,
                is_identity_key=False,
            )
    return None


def _resolve_function_inputs_by_name(
    function_config: FunctionConfig,
) -> dict[str, FunctionConfigAttributeConfig]:
    result: dict[str, FunctionConfigAttributeConfig] = {}
    for link in function_config.function_config_attribute_configs:
        if link.type != FunctionAttributeType.input:
            continue
        attr_cfg = link.attribute_config
        if attr_cfg is None:
            continue
        result[attr_cfg.name] = link
    return result


def _resolve_function_inputs_by_position(
    function_config: FunctionConfig,
) -> list[FunctionConfigAttributeConfig]:
    links = [
        link
        for link in function_config.function_config_attribute_configs
        if link.type == FunctionAttributeType.input
    ]
    links.sort(key=lambda link: (int(link.position), str(link.id)))
    return links


def _resolve_single_function_output(
    function_config: FunctionConfig,
) -> FunctionConfigAttributeConfig | None:
    links = [
        link
        for link in function_config.function_config_attribute_configs
        if link.type == FunctionAttributeType.output and link.attribute_config is not None
    ]
    links.sort(key=lambda link: (int(link.position), str(link.id)))
    if len(links) != 1:
        return None
    return links[0]


def _descriptor_member_traversal_class_config(
    descriptor: AttributeTypeDescriptor | None,
) -> ClassConfig | None:
    if descriptor is None:
        return None
    if descriptor.kind == AttributeTypeDescriptorKind.class_:
        return descriptor.class_config
    if descriptor.kind != AttributeTypeDescriptorKind.union:
        return None

    candidate: ClassConfig | None = None
    for link in descriptor.child_links:
        child = link.child
        if child.kind == AttributeTypeDescriptorKind.primitive:
            primitive_config = child.primitive_config
            primitive_type = (
                primitive_config.primitive_type
                if primitive_config is not None
                else None
            )
            if (
                primitive_type is not None
                and primitive_type.base_type == CodePrimitiveBaseType.null
            ):
                continue
            return None
        child_class_config = _descriptor_member_traversal_class_config(child)
        if child_class_config is None:
            return None
        if candidate is not None and candidate.id != child_class_config.id:
            return None
        candidate = child_class_config
    return candidate


def _attribute_member_traversal_class_config(
    attr_cfg: AttributeConfig | None,
) -> ClassConfig | None:
    if attr_cfg is None:
        return None
    return _descriptor_member_traversal_class_config(attr_cfg.type_descriptor)


def _is_implicit_object_identity_member(member_name: str) -> bool:
    return member_name == "id"


def _validate_invoke_reference_source(
    *,
    source_name: str,
    line_number: int,
    owner_class_config: ClassConfig,
    function_inputs_by_name: dict[str, FunctionConfigAttributeConfig],
    let_bindings_by_name: dict[str, _LetBinding],
) -> str | None:
    parts = tuple(part.strip() for part in source_name.split(".") if part.strip())
    if not parts:
        return f"line {line_number}: invoke argument reference must not be empty."

    root_name = parts[0]
    remaining_parts = parts[1:]

    let_binding = let_bindings_by_name.get(root_name)
    if let_binding is not None:
        if not remaining_parts:
            return None
        current_class_config = _descriptor_member_traversal_class_config(
            let_binding.type_descriptor
        )
        if current_class_config is None:
            if (
                let_binding.captures_construct_output
                and len(remaining_parts) == 1
                and _is_implicit_object_identity_member(remaining_parts[0])
            ):
                return None
            return (
                f"line {line_number}: invoke argument reference '{source_name}' cannot traverse let binding "
                f"'{root_name}' because it is not class-valued."
            )
        for index, member_name in enumerate(remaining_parts):
            member_link = _resolve_class_attribute_by_name(
                class_config=current_class_config,
                attribute_name=member_name,
            )
            is_last = index == len(remaining_parts) - 1
            if member_link is None:
                if is_last and _is_implicit_object_identity_member(member_name):
                    return None
                return (
                    f"line {line_number}: invoke argument reference '{source_name}' cannot resolve member "
                    f"'{member_name}' on class '{current_class_config.name}'."
                )
            if is_last:
                return None

            next_class_config = _attribute_member_traversal_class_config(
                member_link.attribute_config
            )
            if next_class_config is None:
                return (
                    f"line {line_number}: invoke argument reference '{source_name}' cannot traverse member "
                    f"'{member_name}' on class '{current_class_config.name}' because it is not class-valued."
                )
            current_class_config = next_class_config
        return None

    root_attr_cfg: AttributeConfig | None = None
    root_label: str | None = None

    input_link = function_inputs_by_name.get(root_name)
    if input_link is not None:
        root_attr_cfg = input_link.attribute_config
        root_label = f"function input '{root_name}'"
    else:
        owner_attr_link = _resolve_class_attribute_by_name(
            class_config=owner_class_config,
            attribute_name=root_name,
        )
        if owner_attr_link is not None:
            root_attr_cfg = owner_attr_link.attribute_config
            root_label = f"owner attribute '{root_name}'"

    if root_label is None:
        return f"line {line_number}: cannot resolve invoke argument reference '{source_name}'."
    if not remaining_parts:
        return None

    current_class_config = _attribute_member_traversal_class_config(root_attr_cfg)
    if current_class_config is None:
        return (
            f"line {line_number}: invoke argument reference '{source_name}' cannot traverse {root_label} "
            "because it is not a class-valued attribute."
        )

    for index, member_name in enumerate(remaining_parts):
        member_link = _resolve_class_attribute_by_name(
            class_config=current_class_config,
            attribute_name=member_name,
        )
        is_last = index == len(remaining_parts) - 1
        if member_link is None:
            if is_last and _is_implicit_object_identity_member(member_name):
                return None
            return (
                f"line {line_number}: invoke argument reference '{source_name}' cannot resolve member "
                f"'{member_name}' on class '{current_class_config.name}'."
            )
        if is_last:
            return None

        next_class_config = _attribute_member_traversal_class_config(
            member_link.attribute_config
        )
        if next_class_config is None:
            return (
                f"line {line_number}: invoke argument reference '{source_name}' cannot traverse member "
                f"'{member_name}' on class '{current_class_config.name}' because it is not class-valued."
            )
        current_class_config = next_class_config

    return None


def _read_path_root_for_name(
    *,
    root_name: str,
    owner_class_config: ClassConfig,
    function_inputs_by_name: dict[str, FunctionConfigAttributeConfig],
    let_bindings_by_name: dict[str, _LetBinding],
) -> _ReadPathRoot | None:
    let_binding = let_bindings_by_name.get(root_name)
    if let_binding is not None:
        return _ReadPathRoot(
            root_kind=FunctionImplValueSourceReadPathRootKind.let_binding,
            root_instruction_let=let_binding.payload,
            type_descriptor=let_binding.type_descriptor,
        )

    input_link = function_inputs_by_name.get(root_name)
    if input_link is not None:
        return _ReadPathRoot(
            root_kind=FunctionImplValueSourceReadPathRootKind.function_input,
            root_function_config_attribute_config=input_link,
            type_descriptor=_type_descriptor_from_attribute_config(
                input_link.attribute_config
            ),
        )

    owner_attr_link = _resolve_class_attribute_by_name(
        class_config=owner_class_config,
        attribute_name=root_name,
    )
    if owner_attr_link is not None:
        return _ReadPathRoot(
            root_kind=FunctionImplValueSourceReadPathRootKind.target_attribute,
            root_class_config_attribute_config=owner_attr_link,
            type_descriptor=_type_descriptor_from_attribute_config(
                owner_attr_link.attribute_config
            ),
        )
    return None


def _resolve_read_path_source(
    *,
    source_name: str,
    owner_class_config: ClassConfig,
    function_inputs_by_name: dict[str, FunctionConfigAttributeConfig],
    let_bindings_by_name: dict[str, _LetBinding],
) -> tuple[
    _ReadPathRoot | None,
    list[AttributeConfig],
    CodePrimitiveBaseType | None,
    AttributeTypeDescriptor | None,
    str | None,
]:
    parts = tuple(part.strip() for part in source_name.split(".") if part.strip())
    if len(parts) < 2:
        return (
            None,
            [],
            None,
            None,
            "read path source requires a root and at least one member",
        )

    root_name = parts[0]
    root = _read_path_root_for_name(
        root_name=root_name,
        owner_class_config=owner_class_config,
        function_inputs_by_name=function_inputs_by_name,
        let_bindings_by_name=let_bindings_by_name,
    )
    if root is None:
        return None, [], None, None, f"cannot resolve read path root '{root_name}'"

    current_class_config = _descriptor_member_traversal_class_config(
        root.type_descriptor
    )
    if current_class_config is None:
        return (
            None,
            [],
            None,
            None,
            f"read path root '{root_name}' is not class-valued",
        )

    segments: list[AttributeConfig] = []
    final_descriptor: AttributeTypeDescriptor | None = None
    final_primitive_base_type: CodePrimitiveBaseType | None = None
    for position, member_name in enumerate(parts[1:]):
        member_link = _resolve_class_attribute_by_name(
            class_config=current_class_config,
            attribute_name=member_name,
        )
        if member_link is None or member_link.attribute_config is None:
            return (
                None,
                [],
                None,
                None,
                "cannot resolve read path member "
                f"'{member_name}' on class '{current_class_config.name}'",
            )
        member_attr_cfg = member_link.attribute_config
        segments.append(member_attr_cfg)
        final_descriptor = _type_descriptor_from_attribute_config(member_attr_cfg)
        final_primitive_base_type = _primitive_base_type_from_attribute_config(
            member_attr_cfg
        )
        if position == len(parts[1:]) - 1:
            break
        next_class_config = _descriptor_member_traversal_class_config(final_descriptor)
        if next_class_config is None:
            return (
                None,
                [],
                None,
                None,
                "cannot traverse read path member "
                f"'{member_name}' on class '{current_class_config.name}' "
                "because it is not class-valued",
            )
        current_class_config = next_class_config

    return root, segments, final_primitive_base_type, final_descriptor, None


def _build_read_path_value_source(
    *,
    source_name: str,
    function_impl_instruction_id: object,
    key: str,
    owner_class_config: ClassConfig,
    input_by_name: dict[str, FunctionConfigAttributeConfig],
    let_bindings_by_name: dict[str, _LetBinding],
) -> tuple[_ValueSourceBuildResult | None, str | None]:
    root, segments, primitive_base_type, type_descriptor, error = (
        _resolve_read_path_source(
            source_name=source_name,
            owner_class_config=owner_class_config,
            function_inputs_by_name=input_by_name,
            let_bindings_by_name=let_bindings_by_name,
        )
    )
    if error is not None or root is None:
        return None, error or f"cannot resolve read path source '{source_name}'"

    source_id = stable_function_impl_value_source_id(
        function_impl_instruction_id=function_impl_instruction_id,
        key=key,
    )
    source = FunctionImplValueSource(
        id=source_id,
        function_impl_instruction_id=function_impl_instruction_id,
        key=key,
        kind=FunctionImplValueSourceKind.read_path,
    )
    read_path_id = stable_function_impl_value_source_read_path_id(
        function_impl_value_source_id=source_id,
    )
    read_path = FunctionImplValueSourceReadPath(
        id=read_path_id,
        function_impl_value_source_id=source_id,
        root_kind=root.root_kind,
        root_function_config_attribute_config_id=(
            root.root_function_config_attribute_config.id
            if root.root_function_config_attribute_config is not None
            else None
        ),
        root_function_config_attribute_config=(
            root.root_function_config_attribute_config
        ),
        root_instruction_let_id=(
            root.root_instruction_let.id
            if root.root_instruction_let is not None
            else None
        ),
        root_instruction_let=root.root_instruction_let,
        root_class_config_attribute_config_id=(
            root.root_class_config_attribute_config.id
            if root.root_class_config_attribute_config is not None
            else None
        ),
        root_class_config_attribute_config=root.root_class_config_attribute_config,
    )
    for position, attr_cfg in enumerate(segments):
        segment_id = stable_function_impl_value_source_read_path_segment_id(
            function_impl_value_source_read_path_id=read_path_id,
            position=position,
        )
        read_path.segments.append(
            FunctionImplValueSourceReadPathSegment(
                id=segment_id,
                function_impl_value_source_read_path_id=read_path_id,
                position=position,
                attribute_config_id=attr_cfg.id,
                attribute_config=attr_cfg,
            )
        )
    source.source_read_path = read_path
    return (
        _ValueSourceBuildResult(
            payload=source,
            primitive_base_type=primitive_base_type,
            type_descriptor=type_descriptor,
        ),
        None,
    )


def _to_invoke_value_expr(
    *,
    expression: FunctionBodyExpression,
    line_number: int,
    owner_class_config: ClassConfig,
    function_inputs_by_name: dict[str, FunctionConfigAttributeConfig],
    let_bindings_by_name: dict[str, _LetBinding],
) -> tuple[dict[str, object] | None, str | None]:
    if expression.kind == "reference":
        source_name = (expression.text or "").strip()
        if not source_name:
            return (
                None,
                f"line {line_number}: invoke argument reference must not be empty.",
            )
        if (
            source_name == "id"
            and source_name not in let_bindings_by_name
            and source_name not in function_inputs_by_name
            and _resolve_class_attribute_by_name(
                class_config=owner_class_config,
                attribute_name=source_name,
            )
            is None
        ):
            return {"kind": "self_id"}, None
        reference_error = _validate_invoke_reference_source(
            source_name=source_name,
            line_number=line_number,
            owner_class_config=owner_class_config,
            function_inputs_by_name=function_inputs_by_name,
            let_bindings_by_name=let_bindings_by_name,
        )
        if reference_error is not None:
            return None, reference_error
        return {"kind": "reference", "name": source_name}, None

    if expression.kind == "literal":
        if _literal_base_type(expression.literal_value) is None:
            return (
                None,
                f"line {line_number}: unsupported invoke literal value {expression.text!r}.",
            )
        return {"kind": "literal", "value": expression.literal_value}, None

    return None, (
        f"line {line_number}: invoke arguments only support reference/literal expressions in v0 "
        f"(got '{expression.kind}')."
    )


def _build_invoke_argument_bindings(
    *,
    line_number: int,
    invoke_id: object,
    invoke_args: tuple[FunctionBodyCallArg, ...],
    target_function: FunctionConfig,
    invocation_kind: FunctionInvocationKind,
    has_relationship: bool,
    owner_class_config: ClassConfig,
    function_inputs_by_name: dict[str, FunctionConfigAttributeConfig],
    let_bindings_by_name: dict[str, _LetBinding],
) -> tuple[list[FunctionImplInstructionInvokeAttributeConfig], list[str]]:
    if not invoke_args:
        return [], []

    errors: list[str] = []
    bindings: list[FunctionImplInstructionInvokeAttributeConfig] = []

    input_links = _resolve_function_inputs_by_position(target_function)
    input_by_name: dict[str, FunctionConfigAttributeConfig] = {}
    for link in input_links:
        attr = link.attribute_config
        if attr is not None and attr.name not in input_by_name:
            input_by_name[attr.name] = link

    assigned_attr_ids: set[object] = set()
    positional_cursor = 0

    for call_arg in invoke_args:
        target_link: FunctionConfigAttributeConfig | None = None
        arg_name = (call_arg.name or "").strip()
        if arg_name:
            target_link = input_by_name.get(arg_name)
            if target_link is None:
                errors.append(
                    f"line {line_number}: invoke argument '{arg_name}' is not an input on target function "
                    f"'{target_function.name}'."
                )
                continue
        else:
            while positional_cursor < len(input_links):
                candidate = input_links[positional_cursor]
                positional_cursor += 1
                if candidate.attribute_config_id not in assigned_attr_ids:
                    target_link = candidate
                    break
            if target_link is None:
                errors.append(
                    f"line {line_number}: too many positional invoke arguments for target function "
                    f"'{target_function.name}'."
                )
                continue

        attr_cfg = target_link.attribute_config
        if attr_cfg is None:
            errors.append(
                f"line {line_number}: target function input binding is missing AttributeConfig "
                f"(function='{target_function.name}', attribute_config_id={target_link.attribute_config_id})."
            )
            continue

        if target_link.attribute_config_id in assigned_attr_ids:
            errors.append(
                f"line {line_number}: duplicate invoke argument for input '{attr_cfg.name}' "
                f"on target function '{target_function.name}'."
            )
            continue

        value_expr, value_error = _to_invoke_value_expr(
            expression=call_arg.value,
            line_number=line_number,
            owner_class_config=owner_class_config,
            function_inputs_by_name=function_inputs_by_name,
            let_bindings_by_name=let_bindings_by_name,
        )
        if value_error is not None or value_expr is None:
            errors.append(
                value_error
                or f"line {line_number}: invalid invoke argument expression."
            )
            continue

        binding_id = stable_function_impl_instruction_invoke_attribute_config_id(
            function_impl_instruction_invoke_id=invoke_id,
            attribute_config_id=target_link.attribute_config_id,
        )
        bindings.append(
            FunctionImplInstructionInvokeAttributeConfig(
                id=binding_id,
                function_impl_instruction_invoke_id=invoke_id,
                attribute_config_id=target_link.attribute_config_id,
                attribute_config=attr_cfg,
                value_expr=value_expr,
                position=target_link.position,
            )
        )
        assigned_attr_ids.add(target_link.attribute_config_id)

    if errors:
        return [], errors

    for link in input_links:
        if link.attribute_config_id in assigned_attr_ids:
            continue
        attr_cfg = link.attribute_config
        if attr_cfg is None:
            continue
        has_default = attr_cfg.default_value is not None
        description = (attr_cfg.description or "").strip()
        path_injected_parent = (
            invocation_kind == FunctionInvocationKind.construct
            and has_relationship
            and (
                _is_propagated_parent_input(link)
                or "Path-scoped constructor injected parent identifier" in description
            )
        )
        if path_injected_parent:
            binding_id = stable_function_impl_instruction_invoke_attribute_config_id(
                function_impl_instruction_invoke_id=invoke_id,
                attribute_config_id=link.attribute_config_id,
            )
            bindings.append(
                FunctionImplInstructionInvokeAttributeConfig(
                    id=binding_id,
                    function_impl_instruction_invoke_id=invoke_id,
                    attribute_config_id=link.attribute_config_id,
                    attribute_config=attr_cfg,
                    value_expr={"kind": "self_id"},
                    position=link.position,
                )
            )
            assigned_attr_ids.add(link.attribute_config_id)
            continue
        if bool(attr_cfg.is_required) and not has_default:
            errors.append(
                f"line {line_number}: missing required invoke argument '{attr_cfg.name}' "
                f"for target function '{target_function.name}'."
            )

    if errors:
        return [], errors

    bindings.sort(
        key=lambda item: (
            item.position if item.position is not None else 999999,
            str(item.id),
        )
    )
    return bindings, []


def _is_propagated_parent_input(link: FunctionConfigAttributeConfig) -> bool:
    raw_origin = link.identity_key_origin
    origin_value = (
        raw_origin.value
        if isinstance(raw_origin, FunctionIdentityKeyOrigin)
        else str(raw_origin)
    )
    return origin_value == FunctionIdentityKeyOrigin.propagated_parent.value


def _resolve_require_kind(name: str) -> FunctionImplRequireKind | None:
    lookup = {
        "exists": FunctionImplRequireKind.exists,
        "equals": FunctionImplRequireKind.equals,
        "member": FunctionImplRequireKind.member,
        "unique": FunctionImplRequireKind.unique,
        "compare": FunctionImplRequireKind.compare,
        "cardinality": FunctionImplRequireKind.cardinality,
        "all_or_none": FunctionImplRequireKind.all_or_none,
        "text_matches_regex": FunctionImplRequireKind.text_matches_regex,
    }
    return lookup.get((name or "").strip().lower())


def _resolve_compare_operator(name: str) -> FunctionImplRequireCompareOperator | None:
    lookup = {
        "eq": FunctionImplRequireCompareOperator.eq,
        "neq": FunctionImplRequireCompareOperator.neq,
        "gt": FunctionImplRequireCompareOperator.gt,
        "gte": FunctionImplRequireCompareOperator.gte,
        "lt": FunctionImplRequireCompareOperator.lt,
        "lte": FunctionImplRequireCompareOperator.lte,
    }
    return lookup.get((name or "").strip().lower())


def _resolve_relationship_member(
    *, class_config: ClassConfig, member_name: str
) -> ClassConfigRelationship | None:
    best: tuple[int, ClassConfigRelationship] | None = None
    for rel in class_config.class_config_relationships:
        for rel_attr in rel.class_config_relationship_attributes:
            attr_cfg = rel_attr.attribute_config
            if attr_cfg is None or attr_cfg.name != member_name:
                continue

            direction = _enum_value(getattr(rel_attr, "direction", None))
            role = _enum_value(getattr(rel_attr, "role", None))
            score = 0
            if direction == "forward":
                score -= 10
            if role == "reference":
                score -= 5
            candidate = (score, rel)
            if best is None or candidate[0] < best[0]:
                best = candidate
    return best[1] if best is not None else None


def _resolve_target_function(
    *, class_config: ClassConfig, function_name: str, kind: FunctionInvocationKind
) -> FunctionConfig | None:
    candidates = [
        link.function_config
        for link in class_config.class_config_function_configs
        if link.function_config is not None
        and link.function_config.name == function_name
    ]
    if not candidates:
        return None

    if kind == FunctionInvocationKind.construct:
        ctor = [fn for fn in candidates if _enum_value(fn.verb) == "construct"]
        if ctor:
            return ctor[0]
    return candidates[0]


def _resolve_association_class_for_relationship(
    *, relationship: ClassConfigRelationship
) -> ClassConfig | None:
    assoc_edge = relationship.class_config_relationship_association_edge
    if assoc_edge is None:
        return None
    return assoc_edge.class_config


def _resolve_explicit_construct_class_target(
    *,
    owner_class_config: ClassConfig,
    class_name: str,
    line_number: int,
) -> tuple[ClassConfig | None, str | None]:
    normalized_name = class_name.strip()
    if not normalized_name:
        return (
            None,
            f"line {line_number}: construct target class name must not be empty.",
        )

    candidates_by_id: dict[object, ClassConfig] = {}
    if owner_class_config.name == normalized_name:
        candidates_by_id[owner_class_config.id] = owner_class_config

    for relationship in owner_class_config.class_config_relationships:
        target_class = relationship.target_class_config
        if target_class is not None and target_class.name == normalized_name:
            candidates_by_id[target_class.id] = target_class

        association_class = _resolve_association_class_for_relationship(
            relationship=relationship
        )
        if association_class is not None and association_class.name == normalized_name:
            candidates_by_id[association_class.id] = association_class

    candidates = list(candidates_by_id.values())
    if not candidates:
        return None, None
    if len(candidates) > 1:
        candidate_names = ", ".join(
            sorted({candidate.name for candidate in candidates})
        )
        return (
            None,
            f"line {line_number}: construct target '{normalized_name}' is ambiguous across candidates: "
            f"{candidate_names}.",
        )

    has_owner_function_name_conflict = any(
        link.function_config is not None
        and link.function_config.name == normalized_name
        for link in owner_class_config.class_config_function_configs
    )
    if has_owner_function_name_conflict:
        return (
            None,
            f"line {line_number}: construct target '{normalized_name}' is ambiguous between class construction "
            "and owner-local function invocation.",
        )

    return candidates[0], None


def _resolve_invocation_target(
    *,
    owner_class_config: ClassConfig,
    kind: FunctionInvocationKind,
    target_path: tuple[str, ...],
    line_number: int,
) -> tuple[FunctionConfig | None, ClassConfigRelationship | None, str | None]:
    receiver_member: str | None = target_path[0] if len(target_path) == 2 else None
    target_function_name = target_path[-1]
    relationship: ClassConfigRelationship | None = None
    target_class_config: ClassConfig = owner_class_config

    if receiver_member is not None:
        relationship = _resolve_relationship_member(
            class_config=owner_class_config, member_name=receiver_member
        )
        if relationship is None or relationship.target_class_config is None:
            if kind == FunctionInvocationKind.construct:
                explicit_construct_class, construct_error = (
                    _resolve_explicit_construct_class_target(
                        owner_class_config=owner_class_config,
                        class_name=receiver_member,
                        line_number=line_number,
                    )
                )
                if construct_error is not None:
                    return None, None, construct_error
                if explicit_construct_class is not None:
                    target_function = _resolve_target_function(
                        class_config=explicit_construct_class,
                        function_name=target_function_name,
                        kind=kind,
                    )
                    if target_function is None:
                        return (
                            None,
                            None,
                            f"line {line_number}: function '{target_function_name}' not found "
                            f"on class '{explicit_construct_class.name}' for invocation target "
                            f"'{'.'.join(target_path)}'.",
                        )
                    return target_function, None, None
            return (
                None,
                None,
                f"line {line_number}: cannot resolve receiver relationship "
                f"'{receiver_member}' on class '{owner_class_config.name}' "
                f"for invocation target '{'.'.join(target_path)}'.",
            )
        target_class_config = relationship.target_class_config

    target_function = _resolve_target_function(
        class_config=target_class_config,
        function_name=target_function_name,
        kind=kind,
    )
    if kind == FunctionInvocationKind.construct and relationship is not None:
        association_class = _resolve_association_class_for_relationship(
            relationship=relationship
        )
        if association_class is not None:
            target_function = _resolve_target_function(
                class_config=association_class,
                function_name=target_function_name,
                kind=kind,
            )
            target_class_config = association_class

    if target_function is None:
        return (
            None,
            None,
            f"line {line_number}: function '{target_function_name}' not found "
            f"on class '{target_class_config.name}' for invocation target '{'.'.join(target_path)}'.",
        )

    return target_function, relationship, None


@lru_cache(maxsize=32)
def _local_blob_store_for_root(root: str) -> LocalBlobStore:
    return LocalBlobStore(Path(root))


def _segment_text_with_blob_fallback(
    *, body_segment: ContentPartTextSegment
) -> str | None:
    """Read function body text from inline or blob-backed content segments."""

    try:
        return get_segment_text(body_segment)
    except Exception:
        pass

    content_part_text = body_segment.content_part_text
    blob = content_part_text.blob
    path_local = blob.path_local if blob is not None else None
    if not path_local:
        return None

    blob_path = Path(path_local).resolve()
    # Blob paths follow `<root>/<sha[:2]>/<sha[2:]>`; root is two levels up.
    blob_root = blob_path.parent.parent
    if not blob_root.exists():
        return None

    try:
        blob_store = _local_blob_store_for_root(str(blob_root))
        return get_segment_text(body_segment, blob_store=blob_store)
    except Exception:
        return None


def build_function_invocation_plan_from_body(
    *,
    function_config: FunctionConfig,
    owner_class_config: ClassConfig,
    fail_on_unresolved: bool = True,
) -> list[FunctionConfigInvocation]:
    resolved, parse_errors, unresolved_errors = _resolve_invocations_from_body(
        function_config=function_config,
        owner_class_config=owner_class_config,
    )
    if not fail_on_unresolved and (parse_errors or unresolved_errors):
        # Canonical pre-runtime callers use this mode as a compatibility probe only.
        # If the body cannot be resolved honestly against the current topology, emit no
        # invocation rows rather than a partial/stale subset. Runtime transform owns the
        # authoritative lowering once the derived topology exists.
        return []
    if fail_on_unresolved and (parse_errors or unresolved_errors):
        owner_name = owner_class_config.name
        function_name = function_config.name
        details = "\n".join(
            [
                *(f"- {msg}" for msg in parse_errors),
                *(f"- {msg}" for msg in unresolved_errors),
            ]
        )
        raise ValueError(
            f"Unresolved function invocation(s) in {owner_name}.{function_name}:\n{details}"
        )
    return _build_function_invocations_from_resolved(
        function_config=function_config, resolved=resolved
    )


def _build_instruction(
    *,
    function_impl_id: object,
    sequence: int,
    instruction_type: FunctionImplInstructionType,
) -> FunctionImplInstruction:
    instruction_id = stable_function_impl_instruction_id(
        function_impl_id=function_impl_id,
        type=instruction_type.value,
        sequence=sequence,
    )
    return FunctionImplInstruction(
        id=instruction_id,
        function_impl_id=function_impl_id,
        type=instruction_type,
        sequence=sequence,
    )


_TEXT_TRANSFORMS_BY_TARGET: dict[tuple[str, ...], FunctionImplValueTransformKind] = {
    ("text", "strip"): FunctionImplValueTransformKind.text_strip,
    ("text", "casefold"): FunctionImplValueTransformKind.text_casefold,
    ("text", "lower"): FunctionImplValueTransformKind.text_lower,
    ("text", "default_if_blank"): FunctionImplValueTransformKind.text_default_if_blank,
    ("text", "slice"): FunctionImplValueTransformKind.text_slice,
    ("text", "concat"): FunctionImplValueTransformKind.text_concat,
}


def _transform_operand_target_base_types(
    operation: FunctionImplValueTransformKind,
    arity: int,
) -> tuple[CodePrimitiveBaseType, ...] | str:
    if operation in {
        FunctionImplValueTransformKind.text_strip,
        FunctionImplValueTransformKind.text_casefold,
        FunctionImplValueTransformKind.text_lower,
    }:
        return (CodePrimitiveBaseType.string,)
    if operation == FunctionImplValueTransformKind.text_default_if_blank:
        return (CodePrimitiveBaseType.string, CodePrimitiveBaseType.string)
    if operation == FunctionImplValueTransformKind.text_slice:
        if arity == 2:
            return (CodePrimitiveBaseType.string, CodePrimitiveBaseType.integer)
        if arity == 3:
            return (
                CodePrimitiveBaseType.string,
                CodePrimitiveBaseType.integer,
                CodePrimitiveBaseType.integer,
            )
        return "invalid"
    if operation == FunctionImplValueTransformKind.text_concat:
        if arity < 1:
            return "invalid"
        return tuple(CodePrimitiveBaseType.string for _ in range(arity))
    return "invalid"


def _build_value_source_from_expression(
    *,
    expression: FunctionBodyExpression,
    function_impl_instruction_id: object,
    key: str,
    owner_class_config: ClassConfig,
    input_by_name: dict[str, FunctionConfigAttributeConfig],
    let_bindings_by_name: dict[str, _LetBinding],
    primitive_configs_by_base: dict[CodePrimitiveBaseType, object],
    target_base_type: CodePrimitiveBaseType | None = None,
    target_type_descriptor: AttributeTypeDescriptor | None = None,
    require_target_primitive_for_literals: bool = False,
) -> tuple[_ValueSourceBuildResult | None, str | None]:
    target_is_enum = _attribute_type_is_enum(target_type_descriptor)
    if expression.kind == "reference":
        source_name = (expression.text or "").strip()
        if not source_name:
            return None, "reference expression must not be empty"
        if "." in source_name:
            return _build_read_path_value_source(
                source_name=source_name,
                function_impl_instruction_id=function_impl_instruction_id,
                key=key,
                owner_class_config=owner_class_config,
                input_by_name=input_by_name,
                let_bindings_by_name=let_bindings_by_name,
            )

        let_binding = let_bindings_by_name.get(source_name)
        if let_binding is not None:
            source_id = stable_function_impl_value_source_id(
                function_impl_instruction_id=function_impl_instruction_id,
                key=key,
            )
            source = FunctionImplValueSource(
                id=source_id,
                function_impl_instruction_id=function_impl_instruction_id,
                key=key,
                kind=FunctionImplValueSourceKind.let_ref,
                source_instruction_let_id=let_binding.payload.id,
                source_instruction_let=let_binding.payload,
            )
            return (
                _ValueSourceBuildResult(
                    payload=source,
                    primitive_base_type=let_binding.primitive_base_type,
                    type_descriptor=let_binding.type_descriptor,
                ),
                None,
            )

        input_link = input_by_name.get(source_name)
        if input_link is not None:
            primitive_base_type = _primitive_base_type_from_attribute_config(
                input_link.attribute_config
            )
            source_id = stable_function_impl_value_source_id(
                function_impl_instruction_id=function_impl_instruction_id,
                key=key,
            )
            source = FunctionImplValueSource(
                id=source_id,
                function_impl_instruction_id=function_impl_instruction_id,
                key=key,
                kind=FunctionImplValueSourceKind.function_input_ref,
                source_function_config_attribute_config_id=input_link.id,
                source_function_config_attribute_config=input_link,
            )
            return (
                _ValueSourceBuildResult(
                    payload=source,
                    primitive_base_type=primitive_base_type,
                    type_descriptor=_type_descriptor_from_attribute_config(
                        input_link.attribute_config
                    ),
                ),
                None,
            )

        if target_is_enum:
            enum_error = _enum_literal_error(
                descriptor=target_type_descriptor,
                token=source_name,
            )
            if enum_error is not None:
                return None, enum_error
            source_id = stable_function_impl_value_source_id(
                function_impl_instruction_id=function_impl_instruction_id,
                key=key,
            )
            source = FunctionImplValueSource(
                id=source_id,
                function_impl_instruction_id=function_impl_instruction_id,
                key=key,
                kind=FunctionImplValueSourceKind.literal,
            )
            primitive_config = _primitive_config_for_base_type(
                primitive_configs_by_base=primitive_configs_by_base,
                base_type=CodePrimitiveBaseType.string,
            )
            literal_payload_id = stable_function_impl_value_source_literal_primitive_id(
                function_impl_value_source_id=source_id
            )
            literal_payload = FunctionImplValueSourceLiteralPrimitive(
                id=literal_payload_id,
                function_impl_value_source_id=source_id,
                primitive_config_id=primitive_config.id,
                primitive_config=primitive_config,
                value={"value": source_name},
            )
            source.source_literal_primitive = literal_payload
            return (
                _ValueSourceBuildResult(
                    payload=source,
                    primitive_base_type=CodePrimitiveBaseType.string,
                ),
                None,
            )

        return None, f"cannot resolve value source reference '{source_name}'"

    if expression.kind == "intrinsic" and expression.target_path in {
        ("list", "of"),
        ("array", "of"),
    }:
        items: list[object] = []
        for position, call_arg in enumerate(expression.args):
            if call_arg.name is not None:
                return None, "list.of operands must be positional"
            value_expr = call_arg.value
            if value_expr.kind == "literal":
                items.append(value_expr.literal_value)
                continue
            if value_expr.kind == "reference":
                token = (value_expr.text or "").strip()
                if not token:
                    return None, f"list.of operand {position} must not be empty"
                if "." in token:
                    return None, (
                        f"list.of operand {position} must be a local token "
                        f"or literal, got dotted reference '{token}'"
                    )
                items.append(token)
                continue
            return None, (
                f"list.of operand {position} must be a literal or local token, "
                f"got {value_expr.kind!r}"
            )

        primitive_config = _primitive_config_for_base_type(
            primitive_configs_by_base=primitive_configs_by_base,
            base_type=CodePrimitiveBaseType.array,
        )
        source_id = stable_function_impl_value_source_id(
            function_impl_instruction_id=function_impl_instruction_id,
            key=key,
        )
        source = FunctionImplValueSource(
            id=source_id,
            function_impl_instruction_id=function_impl_instruction_id,
            key=key,
            kind=FunctionImplValueSourceKind.literal,
        )
        literal_payload_id = stable_function_impl_value_source_literal_primitive_id(
            function_impl_value_source_id=source_id
        )
        literal_payload = FunctionImplValueSourceLiteralPrimitive(
            id=literal_payload_id,
            function_impl_value_source_id=source_id,
            primitive_config_id=primitive_config.id,
            primitive_config=primitive_config,
            value={"value": items},
        )
        source.source_literal_primitive = literal_payload
        return (
            _ValueSourceBuildResult(
                payload=source,
                primitive_base_type=CodePrimitiveBaseType.array,
            ),
            None,
        )

    if expression.kind == "literal":
        literal_value = expression.literal_value
        literal_base_type = _literal_base_type(literal_value)
        if literal_base_type is None:
            return (
                None,
                f"unsupported literal value for value source: {expression.text!r}",
            )

        if target_is_enum:
            if not isinstance(literal_value, str):
                return None, "enum target literals must be string option tokens"
            enum_error = _enum_literal_error(
                descriptor=target_type_descriptor,
                token=literal_value,
            )
            if enum_error is not None:
                return None, enum_error
            primitive_lookup_base = CodePrimitiveBaseType.string
            primitive_config = _primitive_config_for_base_type(
                primitive_configs_by_base=primitive_configs_by_base,
                base_type=primitive_lookup_base,
            )
            source_id = stable_function_impl_value_source_id(
                function_impl_instruction_id=function_impl_instruction_id,
                key=key,
            )
            source = FunctionImplValueSource(
                id=source_id,
                function_impl_instruction_id=function_impl_instruction_id,
                key=key,
                kind=FunctionImplValueSourceKind.literal,
            )

            literal_payload_id = stable_function_impl_value_source_literal_primitive_id(
                function_impl_value_source_id=source_id
            )
            literal_payload = FunctionImplValueSourceLiteralPrimitive(
                id=literal_payload_id,
                function_impl_value_source_id=source_id,
                primitive_config_id=primitive_config.id,
                primitive_config=primitive_config,
                value={"value": literal_value},
            )
            source.source_literal_primitive = literal_payload

            return (
                _ValueSourceBuildResult(
                    payload=source,
                    primitive_base_type=literal_base_type,
                ),
                None,
            )

        if target_base_type is not None and not _literal_matches_base_type(
            value=literal_value, base_type=target_base_type
        ):
            return None, (
                "literal value type is incompatible with target attribute primitive type "
                f"({literal_base_type.value} -> {target_base_type.value})"
            )

        if require_target_primitive_for_literals and target_base_type is None:
            return None, "literal assignment requires primitive target attribute type"

        primitive_lookup_base = target_base_type or literal_base_type
        primitive_config = primitive_configs_by_base.get(primitive_lookup_base)
        if primitive_config is None:
            return (
                None,
                f"missing primitive config for literal base type '{primitive_lookup_base.value}'",
            )

        source_id = stable_function_impl_value_source_id(
            function_impl_instruction_id=function_impl_instruction_id,
            key=key,
        )
        source = FunctionImplValueSource(
            id=source_id,
            function_impl_instruction_id=function_impl_instruction_id,
            key=key,
            kind=FunctionImplValueSourceKind.literal,
        )

        literal_payload_id = stable_function_impl_value_source_literal_primitive_id(
            function_impl_value_source_id=source_id
        )
        literal_payload = FunctionImplValueSourceLiteralPrimitive(
            id=literal_payload_id,
            function_impl_value_source_id=source_id,
            primitive_config_id=primitive_config.id,
            primitive_config=primitive_config,
            value={"value": literal_value},
        )
        source.source_literal_primitive = literal_payload

        return (
            _ValueSourceBuildResult(
                payload=source, primitive_base_type=literal_base_type
            ),
            None,
        )

    if expression.kind == "intrinsic":
        transform_kind = _TEXT_TRANSFORMS_BY_TARGET.get(expression.target_path)
        if transform_kind is None:
            return None, (
                "unsupported FunctionImpl value-source intrinsic "
                f"'{'.'.join(expression.target_path)}'"
            )
        for call_arg in expression.args:
            if call_arg.name is not None:
                return None, "value-source transform operands must be positional"

        operand_target_base_types = _transform_operand_target_base_types(
            operation=transform_kind,
            arity=len(expression.args),
        )
        if operand_target_base_types == "invalid":
            return None, (
                f"invalid operand arity for transform '{'.'.join(expression.target_path)}'"
            )
        if target_base_type is not None and not _base_type_assignable(
            source=CodePrimitiveBaseType.string,
            target=target_base_type,
        ):
            return None, (
                "transform output type is incompatible with target attribute primitive type "
                f"(string -> {target_base_type.value})"
            )

        output_primitive_config = primitive_configs_by_base.get(
            CodePrimitiveBaseType.string
        )
        source_id = stable_function_impl_value_source_id(
            function_impl_instruction_id=function_impl_instruction_id,
            key=key,
        )
        source = FunctionImplValueSource(
            id=source_id,
            function_impl_instruction_id=function_impl_instruction_id,
            key=key,
            kind=FunctionImplValueSourceKind.transform,
        )
        transform_id = stable_function_impl_value_source_transform_id(
            function_impl_value_source_id=source_id,
        )
        transform_payload = FunctionImplValueSourceTransform(
            id=transform_id,
            function_impl_value_source_id=source_id,
            operation=transform_kind,
            output_primitive_config_id=(
                output_primitive_config.id
                if output_primitive_config is not None
                else None
            ),
            output_primitive_config=output_primitive_config,
        )

        for operand_position, (call_arg, operand_base_type) in enumerate(
            zip(expression.args, operand_target_base_types, strict=True)
        ):
            operand_result, operand_error = _build_value_source_from_expression(
                expression=call_arg.value,
                function_impl_instruction_id=function_impl_instruction_id,
                key=f"{key}_operand_{operand_position}",
                owner_class_config=owner_class_config,
                input_by_name=input_by_name,
                let_bindings_by_name=let_bindings_by_name,
                primitive_configs_by_base=primitive_configs_by_base,
                target_base_type=operand_base_type,
                target_type_descriptor=None,
                require_target_primitive_for_literals=True,
            )
            if operand_error is not None or operand_result is None:
                return None, (
                    f"cannot resolve transform operand {operand_position}: "
                    f"{operand_error or 'unknown error'}"
                )
            if (
                operand_result.primitive_base_type is not None
                and not _base_type_assignable(
                    source=operand_result.primitive_base_type,
                    target=operand_base_type,
                )
            ):
                return None, (
                    f"transform operand {operand_position} type "
                    f"{operand_result.primitive_base_type.value!r} is incompatible with "
                    f"expected {operand_base_type.value!r}"
                )
            operand_id = stable_function_impl_value_source_transform_operand_id(
                function_impl_value_source_transform_id=transform_id,
                position=operand_position,
            )
            operand_payload = FunctionImplValueSourceTransformOperand(
                id=operand_id,
                function_impl_value_source_transform_id=transform_id,
                position=operand_position,
                value_source_id=operand_result.payload.id,
                value_source=operand_result.payload,
            )
            transform_payload.operands.append(operand_payload)

        source.source_transform = transform_payload
        return (
            _ValueSourceBuildResult(
                payload=source,
                primitive_base_type=CodePrimitiveBaseType.string,
            ),
            None,
        )

    return None, (
        f"unsupported value expression kind '{expression.kind}' for FunctionImpl value source "
        f"(only reference/literal/intrinsic are supported in v0)"
    )


def build_function_impl_from_body(
    *,
    function_config: FunctionConfig,
    owner_class_config: ClassConfig,
    key: str = "default",
    fail_on_unresolved: bool = True,
    is_constructor: bool | None = None,
) -> FunctionImpl | None:
    """Build deterministic FunctionImpl instruction rail from function body text."""
    if function_config.code_section_function is None:
        return None
    body_segment = function_config.code_section_function.body_segment
    if body_segment is None:
        return None
    body_text = _segment_text_with_blob_fallback(body_segment=body_segment)
    if body_text is None:
        return None

    statements, parse_errors = _parse_function_statements(body_text)
    unresolved_errors: list[str] = []
    if not parse_errors:
        unresolved_errors.extend(
            _statement_coverage_errors(body_text=body_text, statements=statements)
        )

    function_impl_id = stable_function_impl_id(function_config_id=function_config.id)
    function_impl = _build_function_impl_shell(
        function_impl_id=function_impl_id,
        function_config_id=function_config.id,
        key=key,
        kind="instruction_body",
    )

    function_inputs_by_name = _resolve_function_inputs_by_name(function_config)
    primitive_configs_by_base = _collect_primitive_configs_by_base_type(
        function_config=function_config,
        owner_class_config=owner_class_config,
    )
    let_bindings_by_name: dict[str, _LetBinding] = {}

    for sequence, statement in enumerate(statements):
        is_invoke_statement = statement.kind == "invoke" or (
            statement.kind == "let"
            and statement.value is not None
            and statement.value.kind in {"call", "construct"}
        )
        if is_invoke_statement:
            if statement.kind == "let" and (
                statement.name is None or not statement.name.strip()
            ):
                unresolved_errors.append(
                    f"line {statement.line_number}: let statement requires non-empty binding name."
                )
                continue
            invoke_kind_text = (
                statement.invoke_kind
                if statement.kind == "invoke"
                else (statement.value.kind if statement.value is not None else None)
            )
            target_path = (
                statement.target_path
                if statement.kind == "invoke"
                else statement.value.target_path
            )
            invoke_args = (
                statement.invoke_args
                if statement.kind == "invoke"
                else statement.value.args
            )
            if invoke_kind_text not in {"call", "construct"}:
                unresolved_errors.append(
                    f"line {statement.line_number}: unsupported invocation kind {invoke_kind_text!r}"
                )
                continue
            if len(target_path) not in {1, 2}:
                unresolved_errors.append(
                    f"line {statement.line_number}: invocation target '{'.'.join(target_path)}' must be "
                    "owner-local (`function`) or one-hop (`receiver.function`)."
                )
                continue

            if invoke_kind_text == "construct" and len(target_path) == 1:
                construct_target_name = target_path[0]
                explicit_construct_class, construct_error = (
                    _resolve_explicit_construct_class_target(
                        owner_class_config=owner_class_config,
                        class_name=construct_target_name,
                        line_number=statement.line_number,
                    )
                )
                if construct_error is not None:
                    unresolved_errors.append(construct_error)
                    continue
                if explicit_construct_class is not None:
                    instruction = _build_instruction(
                        function_impl_id=function_impl_id,
                        sequence=sequence,
                        instruction_type=FunctionImplInstructionType.construct,
                    )
                    construct_payload_id = (
                        stable_function_impl_instruction_construct_id(
                            function_impl_instruction_id=instruction.id,
                        )
                    )
                    construct_payload = FunctionImplInstructionConstruct(
                        id=construct_payload_id,
                        function_impl_instruction_id=instruction.id,
                        target_class_config_id=explicit_construct_class.id,
                        target_class_config=explicit_construct_class,
                    )

                    construct_assignment_errors: list[str] = []
                    assigned_attribute_ids: set[object] = set()
                    for assignment_position, call_arg in enumerate(invoke_args):
                        target_attribute_name = (call_arg.name or "").strip()
                        if not target_attribute_name:
                            construct_assignment_errors.append(
                                f"line {statement.line_number}: explicit construct '{construct_target_name}' "
                                "requires named assignments (positional values are not allowed)."
                            )
                            continue

                        target_link = _resolve_class_attribute_by_name(
                            class_config=explicit_construct_class,
                            attribute_name=target_attribute_name,
                        )
                        if target_link is None:
                            construct_assignment_errors.append(
                                f"line {statement.line_number}: construct target class "
                                f"'{explicit_construct_class.name}' has no attribute '{target_attribute_name}'."
                            )
                            continue
                        if target_link.id in assigned_attribute_ids:
                            construct_assignment_errors.append(
                                f"line {statement.line_number}: duplicate construct assignment for attribute "
                                f"'{target_attribute_name}'."
                            )
                            continue

                        target_base_type = _primitive_base_type_from_attribute_config(
                            target_link.attribute_config
                        )
                        target_type_descriptor = _type_descriptor_from_attribute_config(
                            target_link.attribute_config
                        )
                        value_source_result, source_error = (
                            _build_value_source_from_expression(
                                expression=call_arg.value,
                                function_impl_instruction_id=instruction.id,
                                key=f"assignment_{assignment_position}",
                                owner_class_config=owner_class_config,
                                input_by_name=function_inputs_by_name,
                                let_bindings_by_name=let_bindings_by_name,
                                primitive_configs_by_base=primitive_configs_by_base,
                                target_base_type=target_base_type,
                                target_type_descriptor=target_type_descriptor,
                                require_target_primitive_for_literals=True,
                            )
                        )
                        if source_error is not None or value_source_result is None:
                            construct_assignment_errors.append(
                                f"line {statement.line_number}: cannot resolve construct assignment "
                                f"'{target_attribute_name}': {source_error or 'unknown error'}"
                            )
                            continue

                        if (
                            target_base_type is not None
                            and value_source_result.primitive_base_type is not None
                            and not _base_type_assignable(
                                source=value_source_result.primitive_base_type,
                                target=target_base_type,
                            )
                        ):
                            construct_assignment_errors.append(
                                f"line {statement.line_number}: construct source type "
                                f"{value_source_result.primitive_base_type.value!r} is incompatible with "
                                f"target attribute type {target_base_type.value!r} for "
                                f"'{target_attribute_name}'."
                            )
                            continue

                        assignment_id = stable_function_impl_instruction_construct_assignment_id(
                            function_impl_instruction_construct_id=construct_payload_id,
                            target_class_config_attribute_config_id=target_link.id,
                            value_source_id=value_source_result.payload.id,
                        )
                        assignment_payload = FunctionImplInstructionConstructAssignment(
                            id=assignment_id,
                            function_impl_instruction_construct_id=construct_payload_id,
                            target_class_config_attribute_config_id=target_link.id,
                            target_class_config_attribute_config=target_link,
                            value_source_id=value_source_result.payload.id,
                            value_source=value_source_result.payload,
                            position=assignment_position,
                        )
                        construct_payload.assignments.append(assignment_payload)
                        instruction.value_sources.extend(
                            _value_source_result_sources(value_source_result)
                        )
                        assigned_attribute_ids.add(target_link.id)

                    if construct_assignment_errors:
                        unresolved_errors.extend(construct_assignment_errors)
                        continue

                    construct_payload.assignments.sort(
                        key=lambda assignment: (
                            (
                                assignment.position
                                if assignment.position is not None
                                else 999999
                            ),
                            str(assignment.id),
                        )
                    )
                    instruction.instruction_construct = construct_payload
                    function_impl.instructions.append(instruction)
                    continue

            invocation_kind = (
                FunctionInvocationKind.construct
                if invoke_kind_text == "construct"
                else FunctionInvocationKind.call
            )
            target_function, relationship, unresolved = _resolve_invocation_target(
                owner_class_config=owner_class_config,
                kind=invocation_kind,
                target_path=target_path,
                line_number=statement.line_number,
            )
            if unresolved is not None:
                unresolved_errors.append(unresolved)
                continue

            instruction = _build_instruction(
                function_impl_id=function_impl_id,
                sequence=sequence,
                instruction_type=FunctionImplInstructionType.invoke,
            )
            invoke_id = stable_function_impl_instruction_invoke_id(
                function_impl_instruction_id=instruction.id,
            )
            invoke_payload = FunctionImplInstructionInvoke(
                id=invoke_id,
                function_impl_instruction_id=instruction.id,
                target_function_config_id=target_function.id,
                target_function_config=target_function,
                class_config_relationship_id=(
                    relationship.id if relationship is not None else None
                ),
                class_config_relationship=relationship,
                kind=(
                    FunctionImplInvokeKind.construct
                    if invocation_kind == FunctionInvocationKind.construct
                    else FunctionImplInvokeKind.call
                ),
            )
            invoke_bindings, invoke_binding_errors = _build_invoke_argument_bindings(
                line_number=statement.line_number,
                invoke_id=invoke_id,
                invoke_args=invoke_args,
                target_function=target_function,
                invocation_kind=invocation_kind,
                has_relationship=(relationship is not None),
                owner_class_config=owner_class_config,
                function_inputs_by_name=function_inputs_by_name,
                let_bindings_by_name=let_bindings_by_name,
            )
            if invoke_binding_errors:
                unresolved_errors.extend(invoke_binding_errors)
                continue
            invoke_payload.attribute_configs.extend(invoke_bindings)
            if statement.kind == "let":
                capture_name = statement.name.strip()
                object.__setattr__(invoke_payload, "capture_name", capture_name)
                capture_base_type: CodePrimitiveBaseType | None = None
                capture_type_descriptor: AttributeTypeDescriptor | None = None
                output_link = _resolve_single_function_output(target_function)
                if output_link is not None:
                    capture_base_type = _primitive_base_type_from_attribute_config(
                        output_link.attribute_config
                    )
                    capture_type_descriptor = _type_descriptor_from_attribute_config(
                        output_link.attribute_config
                    )
                let_bindings_by_name[capture_name] = _LetBinding(
                    payload=_build_synthetic_invoke_capture_let(
                        function_impl_id=function_impl_id,
                        capture_token=f"{sequence}:{capture_name}",
                        binding_name=capture_name,
                    ),
                    primitive_base_type=capture_base_type,
                    type_descriptor=capture_type_descriptor,
                    captures_construct_output=(
                        invocation_kind == FunctionInvocationKind.construct
                    ),
                )
            instruction.instruction_invoke = invoke_payload
            function_impl.instructions.append(instruction)
            continue

        if statement.kind == "let":
            if statement.name is None or not statement.name.strip():
                unresolved_errors.append(
                    f"line {statement.line_number}: let statement requires non-empty binding name."
                )
                continue
            if statement.value is None:
                unresolved_errors.append(
                    f"line {statement.line_number}: let statement requires value expression."
                )
                continue
            if statement.value.kind not in {"reference", "literal", "intrinsic"}:
                unresolved_errors.append(
                    f"line {statement.line_number}: let expression kind "
                    f"'{statement.value.kind}' is not supported in v0."
                )
                continue

            instruction = _build_instruction(
                function_impl_id=function_impl_id,
                sequence=sequence,
                instruction_type=FunctionImplInstructionType.let,
            )

            let_expr: dict[str, object]
            inferred_base_type: CodePrimitiveBaseType | None = None
            inferred_type_descriptor: AttributeTypeDescriptor | None = None
            if statement.value.kind == "intrinsic":
                value_source_result, source_error = _build_value_source_from_expression(
                    expression=statement.value,
                    function_impl_instruction_id=instruction.id,
                    key="value",
                    owner_class_config=owner_class_config,
                    input_by_name=function_inputs_by_name,
                    let_bindings_by_name=let_bindings_by_name,
                    primitive_configs_by_base=primitive_configs_by_base,
                )
                if source_error is not None or value_source_result is None:
                    unresolved_errors.append(
                        f"line {statement.line_number}: cannot resolve let value source: "
                        f"{source_error or 'unknown error'}"
                    )
                    continue
                inferred_base_type = value_source_result.primitive_base_type
                inferred_type_descriptor = value_source_result.type_descriptor
                let_expr = {
                    "kind": "value_source",
                    "value_source_id": str(value_source_result.payload.id),
                }
                instruction.value_sources.extend(
                    _value_source_result_sources(value_source_result)
                )
            elif statement.value.kind == "reference":
                source_name = (statement.value.text or "").strip()
                if not source_name:
                    unresolved_errors.append(
                        f"line {statement.line_number}: let reference must not be empty."
                    )
                    continue
                if "." in source_name:
                    value_source_result, source_error = (
                        _build_value_source_from_expression(
                            expression=statement.value,
                            function_impl_instruction_id=instruction.id,
                            key="value",
                            owner_class_config=owner_class_config,
                            input_by_name=function_inputs_by_name,
                            let_bindings_by_name=let_bindings_by_name,
                            primitive_configs_by_base=primitive_configs_by_base,
                        )
                    )
                    if source_error is not None or value_source_result is None:
                        unresolved_errors.append(
                            f"line {statement.line_number}: cannot resolve let value source: "
                            f"{source_error or 'unknown error'}"
                        )
                        continue
                    inferred_base_type = value_source_result.primitive_base_type
                    inferred_type_descriptor = value_source_result.type_descriptor
                    let_expr = {
                        "kind": "value_source",
                        "value_source_id": str(value_source_result.payload.id),
                    }
                    instruction.value_sources.extend(
                        _value_source_result_sources(value_source_result)
                    )
                else:
                    let_binding = let_bindings_by_name.get(source_name)
                    if let_binding is not None:
                        inferred_base_type = let_binding.primitive_base_type
                        inferred_type_descriptor = let_binding.type_descriptor
                    else:
                        input_link = function_inputs_by_name.get(source_name)
                        if input_link is not None:
                            inferred_base_type = (
                                _primitive_base_type_from_attribute_config(
                                    input_link.attribute_config
                                )
                            )
                            inferred_type_descriptor = (
                                _type_descriptor_from_attribute_config(
                                    input_link.attribute_config
                                )
                            )
                        else:
                            owner_link = _resolve_class_attribute_by_name(
                                class_config=owner_class_config,
                                attribute_name=source_name,
                            )
                            if owner_link is None:
                                unresolved_errors.append(
                                    f"line {statement.line_number}: cannot resolve let reference '{source_name}'."
                                )
                                continue
                            inferred_base_type = (
                                _primitive_base_type_from_attribute_config(
                                    owner_link.attribute_config
                                )
                            )
                            inferred_type_descriptor = (
                                _type_descriptor_from_attribute_config(
                                    owner_link.attribute_config
                                )
                            )
                    let_expr = {"kind": "reference", "name": source_name}
            else:
                inferred_base_type = _literal_base_type(statement.value.literal_value)
                if inferred_base_type is None:
                    unresolved_errors.append(
                        f"line {statement.line_number}: unsupported let literal value {statement.value.text!r}."
                    )
                    continue
                let_expr = {"kind": "literal", "value": statement.value.literal_value}

            let_id = stable_function_impl_instruction_let_id(
                function_impl_instruction_id=instruction.id
            )
            let_payload = FunctionImplInstructionLet(
                id=let_id,
                function_impl_instruction_id=instruction.id,
                name=statement.name.strip(),
                value_expr=let_expr,
            )
            instruction.instruction_let = let_payload
            function_impl.instructions.append(instruction)
            let_bindings_by_name[statement.name.strip()] = _LetBinding(
                payload=let_payload,
                primitive_base_type=inferred_base_type,
                type_descriptor=inferred_type_descriptor,
            )
            continue

        if statement.kind == "set":
            target_name = (statement.name or "").strip()
            if not target_name:
                unresolved_errors.append(
                    f"line {statement.line_number}: set statement requires target attribute name."
                )
                continue
            if statement.value is None:
                unresolved_errors.append(
                    f"line {statement.line_number}: set statement requires value expression."
                )
                continue

            target_link = _resolve_class_attribute_by_name(
                class_config=owner_class_config,
                attribute_name=target_name,
            )
            if target_link is None:
                unresolved_errors.append(
                    f"line {statement.line_number}: cannot resolve set target attribute '{target_name}' on class "
                    f"'{owner_class_config.name}'."
                )
                continue
            target_base_type = _primitive_base_type_from_attribute_config(
                target_link.attribute_config
            )
            target_type_descriptor = _type_descriptor_from_attribute_config(
                target_link.attribute_config
            )

            instruction = _build_instruction(
                function_impl_id=function_impl_id,
                sequence=sequence,
                instruction_type=FunctionImplInstructionType.set,
            )

            value_source_result, source_error = _build_value_source_from_expression(
                expression=statement.value,
                function_impl_instruction_id=instruction.id,
                key="value",
                owner_class_config=owner_class_config,
                input_by_name=function_inputs_by_name,
                let_bindings_by_name=let_bindings_by_name,
                primitive_configs_by_base=primitive_configs_by_base,
                target_base_type=target_base_type,
                target_type_descriptor=target_type_descriptor,
                require_target_primitive_for_literals=True,
            )
            if source_error is not None or value_source_result is None:
                unresolved_errors.append(
                    f"line {statement.line_number}: cannot resolve set value source: {source_error or 'unknown error'}"
                )
                continue

            if (
                target_base_type is not None
                and value_source_result.primitive_base_type is not None
                and not _base_type_assignable(
                    source=value_source_result.primitive_base_type,
                    target=target_base_type,
                )
            ):
                unresolved_errors.append(
                    f"line {statement.line_number}: set source type {value_source_result.primitive_base_type.value!r} "
                    f"is incompatible with target type {target_base_type.value!r}."
                )
                continue

            set_payload_id = stable_function_impl_instruction_set_id(
                function_impl_instruction_id=instruction.id
            )
            set_payload = FunctionImplInstructionSet(
                id=set_payload_id,
                function_impl_instruction_id=instruction.id,
                target_class_config_attribute_config_id=target_link.id,
                target_class_config_attribute_config=target_link,
                value_source_id=value_source_result.payload.id,
                value_source=value_source_result.payload,
            )
            instruction.value_sources.extend(
                _value_source_result_sources(value_source_result)
            )
            instruction.instruction_set = set_payload
            function_impl.instructions.append(instruction)
            continue

        if statement.kind == "require":
            require_kind_name = (statement.require_kind or "").strip().lower()
            require_kind = _resolve_require_kind(require_kind_name)
            if require_kind is None:
                unresolved_errors.append(
                    f"line {statement.line_number}: unsupported require predicate '{require_kind_name}'."
                )
                continue

            operand_expressions = list(statement.require_operands)
            compare_operator: FunctionImplRequireCompareOperator | None = None
            expected_count: int | None = None

            if require_kind == FunctionImplRequireKind.compare:
                if len(operand_expressions) != 3:
                    unresolved_errors.append(
                        f"line {statement.line_number}: require compare expects exactly 3 arguments "
                        "(operator, left, right)."
                    )
                    continue
                operator_expr = operand_expressions.pop(0)
                if operator_expr.kind != "reference":
                    unresolved_errors.append(
                        f"line {statement.line_number}: compare operator must be identifier (eq/neq/gt/gte/lt/lte)."
                    )
                    continue
                compare_operator = _resolve_compare_operator(operator_expr.text)
                if compare_operator is None:
                    unresolved_errors.append(
                        f"line {statement.line_number}: unsupported compare operator '{operator_expr.text}'."
                    )
                    continue
            elif require_kind == FunctionImplRequireKind.cardinality:
                if len(operand_expressions) != 3:
                    unresolved_errors.append(
                        f"line {statement.line_number}: require cardinality expects exactly 3 arguments "
                        "(operator, collection, expected_count)."
                    )
                    continue
                operator_expr = operand_expressions.pop(0)
                if operator_expr.kind != "reference":
                    unresolved_errors.append(
                        f"line {statement.line_number}: cardinality operator must be identifier (eq/neq/gt/gte/lt/lte)."
                    )
                    continue
                compare_operator = _resolve_compare_operator(operator_expr.text)
                if compare_operator is None:
                    unresolved_errors.append(
                        f"line {statement.line_number}: unsupported cardinality operator '{operator_expr.text}'."
                    )
                    continue
                expected_expr = operand_expressions.pop()
                if expected_expr.kind != "literal" or not isinstance(
                    expected_expr.literal_value, int
                ):
                    unresolved_errors.append(
                        f"line {statement.line_number}: cardinality expected_count must be integer literal."
                    )
                    continue
                if expected_expr.literal_value < 0:
                    unresolved_errors.append(
                        f"line {statement.line_number}: cardinality expected_count must be >= 0."
                    )
                    continue
                expected_count = expected_expr.literal_value

            expected_arity_by_kind = {
                FunctionImplRequireKind.exists: (1, 1),
                FunctionImplRequireKind.equals: (2, 2),
                FunctionImplRequireKind.member: (2, 2),
                FunctionImplRequireKind.unique: (1, 1),
                FunctionImplRequireKind.compare: (2, 2),
                FunctionImplRequireKind.cardinality: (1, 1),
                FunctionImplRequireKind.all_or_none: (2, None),
                FunctionImplRequireKind.text_matches_regex: (2, 2),
            }
            min_arity, max_arity = expected_arity_by_kind[require_kind]
            if len(operand_expressions) < min_arity or (
                max_arity is not None and len(operand_expressions) > max_arity
            ):
                unresolved_errors.append(
                    f"line {statement.line_number}: require {require_kind.value} has invalid operand arity "
                    f"({len(operand_expressions)})."
                )
                continue

            instruction = _build_instruction(
                function_impl_id=function_impl_id,
                sequence=sequence,
                instruction_type=FunctionImplInstructionType.require,
            )

            operand_sources: list[_ValueSourceBuildResult] = []
            operand_error: str | None = None
            for operand_position, operand_expression in enumerate(operand_expressions):
                source_result, source_error = _build_value_source_from_expression(
                    expression=operand_expression,
                    function_impl_instruction_id=instruction.id,
                    key=f"operand_{operand_position}",
                    owner_class_config=owner_class_config,
                    input_by_name=function_inputs_by_name,
                    let_bindings_by_name=let_bindings_by_name,
                    primitive_configs_by_base=primitive_configs_by_base,
                )
                if source_error is not None or source_result is None:
                    operand_error = source_error or "unknown value source error"
                    break
                operand_sources.append(source_result)
            if operand_error is not None:
                unresolved_errors.append(
                    f"line {statement.line_number}: cannot resolve require operand source: {operand_error}"
                )
                continue

            require_id = stable_function_impl_instruction_require_id(
                function_impl_instruction_id=instruction.id
            )
            require_payload = FunctionImplInstructionRequire(
                id=require_id,
                function_impl_instruction_id=instruction.id,
                kind=require_kind,
                compare_operator=compare_operator,
                expected_count=expected_count,
                message=statement.require_message,
            )

            for operand_position, source_result in enumerate(operand_sources):
                operand_id = stable_function_impl_instruction_require_operand_id(
                    function_impl_instruction_require_id=require_id,
                    position=operand_position,
                )
                operand = FunctionImplInstructionRequireOperand(
                    id=operand_id,
                    function_impl_instruction_require_id=require_id,
                    position=operand_position,
                    value_source_id=source_result.payload.id,
                    value_source=source_result.payload,
                )
                require_payload.operands.append(operand)
                instruction.value_sources.extend(
                    _value_source_result_sources(source_result)
                )

            instruction.instruction_require = require_payload
            function_impl.instructions.append(instruction)
            continue

        if statement.kind == "delete":
            target_path = tuple(
                part for part in getattr(statement, "target_path", ()) if part
            )
            if target_path != ("self",):
                target = ".".join(target_path) if target_path else ""
                unresolved_errors.append(
                    f"line {statement.line_number}: delete target must be `self` "
                    f"(got {target!r})."
                )
                continue

            instruction = _build_instruction(
                function_impl_id=function_impl_id,
                sequence=sequence,
                instruction_type=FunctionImplInstructionType.delete,
            )
            delete_payload = _build_function_impl_instruction_delete(
                id=stable_function_impl_instruction_delete_id(
                    function_impl_instruction_id=instruction.id,
                ),
                function_impl_instruction_id=instruction.id,
                target_kind=_function_impl_delete_target_self(),
            )
            instruction.instruction_delete = delete_payload
            function_impl.instructions.append(instruction)
            continue

        unresolved_errors.append(
            f"line {statement.line_number}: unsupported function statement kind '{statement.kind}'."
        )

    if fail_on_unresolved and (parse_errors or unresolved_errors):
        owner_name = owner_class_config.name
        function_name = function_config.name
        details = "\n".join(
            [
                *(f"- {msg}" for msg in parse_errors),
                *(f"- {msg}" for msg in unresolved_errors),
            ]
        )
        raise ValueError(
            f"Unresolved function impl instruction(s) in {owner_name}.{function_name}:\n{details}"
        )
    if not fail_on_unresolved and (parse_errors or unresolved_errors):
        # Canonical pre-runtime callers must not retain partial/stale FunctionImpl payloads.
        # Returning `None` lets the runtime transform rebuild authoritatively after edge
        # reification / path-constructor lowering has produced the honest topology.
        return None

    apply_function_impl_kind(
        function_config=function_config,
        function_impl=function_impl,
        is_constructor=is_constructor,
    )
    return function_impl


def clone_function_impl_from_template(
    *,
    function_config: FunctionConfig,
    template_function: FunctionConfig,
    is_constructor: bool | None = None,
) -> FunctionImpl | None:
    """Clone explicit lowered FunctionImpl truth onto another FunctionConfig."""

    template_impl = template_function.function_impl
    if template_impl is None:
        return None

    target_edges_by_signature: dict[tuple[str, str], FunctionConfigAttributeConfig] = {}
    for edge in function_config.function_config_attribute_configs:
        attr = edge.attribute_config
        if attr is None:
            continue
        target_edges_by_signature[(edge.type.value, attr.name)] = edge

    edge_by_template_id: dict[str, FunctionConfigAttributeConfig] = {}
    for edge in template_function.function_config_attribute_configs:
        attr = edge.attribute_config
        if attr is None:
            continue
        target_edge = target_edges_by_signature.get((edge.type.value, attr.name))
        if target_edge is None:
            continue
        edge_by_template_id[str(edge.id)] = target_edge

    template_kind = _function_impl_kind_name(
        template_impl,
        default=_classify_function_impl_kind(
            function_config=function_config,
            instruction_count=len(template_impl.instructions),
            is_constructor=is_constructor,
        ),
    )
    cloned_impl = _build_function_impl_shell(
        function_impl_id=stable_function_impl_id(function_config_id=function_config.id),
        function_config_id=function_config.id,
        key=template_impl.key,
        kind=template_kind,
    )

    cloned_lets_by_template_id: dict[str, FunctionImplInstructionLet] = {}
    cloned_value_sources_by_template_id: dict[str, FunctionImplValueSource] = {}

    instructions = sorted(
        template_impl.instructions, key=lambda ins: (ins.sequence, str(ins.id))
    )
    for template_instruction in instructions:
        instruction_id = stable_function_impl_instruction_id(
            function_impl_id=cloned_impl.id,
            sequence=template_instruction.sequence,
            type=_enum_value(template_instruction.type),
        )
        cloned_instruction = FunctionImplInstruction(
            id=instruction_id,
            type=template_instruction.type,
            sequence=template_instruction.sequence,
            function_impl_id=cloned_impl.id,
        )

        template_let = template_instruction.instruction_let
        if template_let is not None:
            cloned_let = FunctionImplInstructionLet(
                id=stable_function_impl_instruction_let_id(
                    function_impl_instruction_id=instruction_id
                ),
                name=template_let.name,
                value_expr=template_let.value_expr,
                function_impl_instruction_id=instruction_id,
            )
            cloned_instruction.instruction_let = cloned_let
            cloned_lets_by_template_id[str(template_let.id)] = cloned_let

        for template_value_source in template_instruction.value_sources:
            source_edge_id = (
                template_value_source.source_function_config_attribute_config_id
            )
            cloned_source_edge = (
                edge_by_template_id.get(str(source_edge_id))
                if source_edge_id is not None
                else None
            )
            if source_edge_id is not None and cloned_source_edge is None:
                raise ValueError(
                    "Cannot clone FunctionImplValueSource without target function edge mapping "
                    + f"(template_function={template_function.name!r}, edge_id={source_edge_id})"
                )
            source_let_id = template_value_source.source_instruction_let_id
            cloned_source_let = (
                cloned_lets_by_template_id.get(str(source_let_id))
                if source_let_id is not None
                else None
            )
            if source_let_id is not None and cloned_source_let is None:
                template_source_let = template_value_source.source_instruction_let
                if template_source_let is None:
                    raise ValueError(
                        "Cannot clone FunctionImplValueSource without cloned let mapping "
                        + f"(template_function={template_function.name!r}, let_id={source_let_id})"
                    )
                cloned_source_let = _build_synthetic_invoke_capture_let(
                    function_impl_id=cloned_impl.id,
                    capture_token=str(source_let_id),
                    binding_name=template_source_let.name,
                )
                cloned_lets_by_template_id[str(source_let_id)] = cloned_source_let

            cloned_value_source = FunctionImplValueSource(
                id=stable_function_impl_value_source_id(
                    function_impl_instruction_id=instruction_id,
                    key=template_value_source.key,
                ),
                key=template_value_source.key,
                kind=template_value_source.kind,
                function_impl_instruction_id=instruction_id,
                source_function_config_attribute_config=cloned_source_edge,
                source_function_config_attribute_config_id=(
                    cloned_source_edge.id if cloned_source_edge is not None else None
                ),
                source_instruction_let=cloned_source_let,
                source_instruction_let_id=(
                    cloned_source_let.id if cloned_source_let is not None else None
                ),
            )
            template_literal = template_value_source.source_literal_primitive
            if template_literal is not None:
                cloned_value_source.source_literal_primitive = (
                    FunctionImplValueSourceLiteralPrimitive(
                        id=stable_function_impl_value_source_literal_primitive_id(
                            function_impl_value_source_id=cloned_value_source.id,
                        ),
                        primitive_config=template_literal.primitive_config,
                        primitive_config_id=template_literal.primitive_config_id,
                        value=template_literal.value,
                        function_impl_value_source_id=cloned_value_source.id,
                    )
                )
            cloned_instruction.value_sources.append(cloned_value_source)
            cloned_value_sources_by_template_id[str(template_value_source.id)] = (
                cloned_value_source
            )

        for template_value_source in template_instruction.value_sources:
            template_transform = template_value_source.source_transform
            if template_transform is None:
                continue
            cloned_transform_source = cloned_value_sources_by_template_id.get(
                str(template_value_source.id)
            )
            if cloned_transform_source is None:
                raise ValueError(
                    "Cannot clone FunctionImplValueSourceTransform without cloned parent value source "
                    + f"(template_function={template_function.name!r}, value_source_id={template_value_source.id})"
                )
            cloned_transform = FunctionImplValueSourceTransform(
                id=stable_function_impl_value_source_transform_id(
                    function_impl_value_source_id=cloned_transform_source.id,
                ),
                function_impl_value_source_id=cloned_transform_source.id,
                operation=template_transform.operation,
                output_primitive_config=template_transform.output_primitive_config,
                output_primitive_config_id=template_transform.output_primitive_config_id,
            )
            for template_operand in template_transform.operands:
                cloned_operand_source = cloned_value_sources_by_template_id.get(
                    str(template_operand.value_source_id)
                )
                if cloned_operand_source is None:
                    raise ValueError(
                        "Cannot clone FunctionImplValueSourceTransformOperand without cloned operand source "
                        + (
                            f"(template_function={template_function.name!r}, "
                            f"value_source_id={template_operand.value_source_id})"
                        )
                    )
                cloned_operand = FunctionImplValueSourceTransformOperand(
                    id=stable_function_impl_value_source_transform_operand_id(
                        function_impl_value_source_transform_id=cloned_transform.id,
                        position=template_operand.position,
                    ),
                    function_impl_value_source_transform_id=cloned_transform.id,
                    position=template_operand.position,
                    value_source=cloned_operand_source,
                    value_source_id=cloned_operand_source.id,
                )
                cloned_transform.operands.append(cloned_operand)
            cloned_transform_source.source_transform = cloned_transform

        for template_value_source in template_instruction.value_sources:
            template_read_path = template_value_source.source_read_path
            if template_read_path is None:
                continue
            cloned_read_path_source = cloned_value_sources_by_template_id.get(
                str(template_value_source.id)
            )
            if cloned_read_path_source is None:
                raise ValueError(
                    "Cannot clone FunctionImplValueSourceReadPath without cloned parent value source "
                    + f"(template_function={template_function.name!r}, value_source_id={template_value_source.id})"
                )

            root_edge_id = template_read_path.root_function_config_attribute_config_id
            cloned_root_edge = (
                edge_by_template_id.get(str(root_edge_id))
                if root_edge_id is not None
                else None
            )
            if root_edge_id is not None and cloned_root_edge is None:
                raise ValueError(
                    "Cannot clone FunctionImplValueSourceReadPath without target function root edge mapping "
                    + f"(template_function={template_function.name!r}, edge_id={root_edge_id})"
                )

            root_let_id = template_read_path.root_instruction_let_id
            cloned_root_let = (
                cloned_lets_by_template_id.get(str(root_let_id))
                if root_let_id is not None
                else None
            )
            if root_let_id is not None and cloned_root_let is None:
                template_root_let = template_read_path.root_instruction_let
                if template_root_let is None:
                    raise ValueError(
                        "Cannot clone FunctionImplValueSourceReadPath without cloned root let mapping "
                        + f"(template_function={template_function.name!r}, let_id={root_let_id})"
                    )
                cloned_root_let = _build_synthetic_invoke_capture_let(
                    function_impl_id=cloned_impl.id,
                    capture_token=str(root_let_id),
                    binding_name=template_root_let.name,
                )
                cloned_lets_by_template_id[str(root_let_id)] = cloned_root_let

            cloned_read_path_id = stable_function_impl_value_source_read_path_id(
                function_impl_value_source_id=cloned_read_path_source.id,
            )
            cloned_read_path = FunctionImplValueSourceReadPath(
                id=cloned_read_path_id,
                function_impl_value_source_id=cloned_read_path_source.id,
                root_kind=template_read_path.root_kind,
                root_function_config_attribute_config=cloned_root_edge,
                root_function_config_attribute_config_id=(
                    cloned_root_edge.id if cloned_root_edge is not None else None
                ),
                root_instruction_let=cloned_root_let,
                root_instruction_let_id=(
                    cloned_root_let.id if cloned_root_let is not None else None
                ),
                root_class_config_attribute_config=(
                    template_read_path.root_class_config_attribute_config
                ),
                root_class_config_attribute_config_id=(
                    template_read_path.root_class_config_attribute_config_id
                ),
            )
            for template_segment in template_read_path.segments:
                cloned_read_path.segments.append(
                    FunctionImplValueSourceReadPathSegment(
                        id=stable_function_impl_value_source_read_path_segment_id(
                            function_impl_value_source_read_path_id=(
                                cloned_read_path_id
                            ),
                            position=template_segment.position,
                        ),
                        function_impl_value_source_read_path_id=cloned_read_path_id,
                        position=template_segment.position,
                        attribute_config=template_segment.attribute_config,
                        attribute_config_id=template_segment.attribute_config_id,
                    )
                )
            cloned_read_path_source.source_read_path = cloned_read_path

        template_invoke = template_instruction.instruction_invoke
        if template_invoke is not None:
            cloned_invoke = FunctionImplInstructionInvoke(
                id=stable_function_impl_instruction_invoke_id(
                    function_impl_instruction_id=instruction_id
                ),
                kind=template_invoke.kind,
                function_impl_instruction_id=instruction_id,
                target_function_config=template_invoke.target_function_config,
                target_function_config_id=template_invoke.target_function_config_id,
                class_config_relationship=template_invoke.class_config_relationship,
                class_config_relationship_id=template_invoke.class_config_relationship_id,
            )
            for template_binding in template_invoke.attribute_configs:
                cloned_binding = FunctionImplInstructionInvokeAttributeConfig(
                    id=stable_function_impl_instruction_invoke_attribute_config_id(
                        function_impl_instruction_invoke_id=cloned_invoke.id,
                        attribute_config_id=template_binding.attribute_config_id,
                    ),
                    function_impl_instruction_invoke_id=cloned_invoke.id,
                    attribute_config=template_binding.attribute_config,
                    attribute_config_id=template_binding.attribute_config_id,
                    value_expr=template_binding.value_expr,
                    position=template_binding.position,
                )
                cloned_invoke.attribute_configs.append(cloned_binding)
            capture_name = str(
                getattr(template_invoke, "capture_name", "") or ""
            ).strip()
            if capture_name:
                object.__setattr__(cloned_invoke, "capture_name", capture_name)
            cloned_instruction.instruction_invoke = cloned_invoke

        template_construct = template_instruction.instruction_construct
        if template_construct is not None:
            cloned_construct = FunctionImplInstructionConstruct(
                id=stable_function_impl_instruction_construct_id(
                    function_impl_instruction_id=instruction_id
                ),
                function_impl_instruction_id=instruction_id,
                target_class_config=template_construct.target_class_config,
                target_class_config_id=template_construct.target_class_config_id,
            )
            for template_assignment in template_construct.assignments:
                cloned_value_source = cloned_value_sources_by_template_id.get(
                    str(template_assignment.value_source_id)
                )
                if cloned_value_source is None:
                    raise ValueError(
                        "Cannot clone FunctionImplInstructionConstructAssignment without cloned value source "
                        + (
                            f"(template_function={template_function.name!r}, "
                            f"value_source_id={template_assignment.value_source_id})"
                        )
                    )
                cloned_assignment = FunctionImplInstructionConstructAssignment(
                    id=stable_function_impl_instruction_construct_assignment_id(
                        function_impl_instruction_construct_id=cloned_construct.id,
                        target_class_config_attribute_config_id=(
                            template_assignment.target_class_config_attribute_config_id
                        ),
                        value_source_id=cloned_value_source.id,
                    ),
                    function_impl_instruction_construct_id=cloned_construct.id,
                    target_class_config_attribute_config=template_assignment.target_class_config_attribute_config,
                    target_class_config_attribute_config_id=(
                        template_assignment.target_class_config_attribute_config_id
                    ),
                    value_source=cloned_value_source,
                    value_source_id=cloned_value_source.id,
                    position=template_assignment.position,
                )
                cloned_construct.assignments.append(cloned_assignment)
            cloned_instruction.instruction_construct = cloned_construct

        template_set = template_instruction.instruction_set
        if template_set is not None:
            cloned_value_source = cloned_value_sources_by_template_id.get(
                str(template_set.value_source_id)
            )
            if cloned_value_source is None:
                raise ValueError(
                    "Cannot clone FunctionImplInstructionSet without cloned value source "
                    + f"(template_function={template_function.name!r}, value_source_id={template_set.value_source_id})"
                )
            cloned_instruction.instruction_set = FunctionImplInstructionSet(
                id=stable_function_impl_instruction_set_id(
                    function_impl_instruction_id=instruction_id
                ),
                function_impl_instruction_id=instruction_id,
                target_class_config_attribute_config=template_set.target_class_config_attribute_config,
                target_class_config_attribute_config_id=template_set.target_class_config_attribute_config_id,
                value_source=cloned_value_source,
                value_source_id=cloned_value_source.id,
            )

        template_require = template_instruction.instruction_require
        if template_require is not None:
            cloned_require = FunctionImplInstructionRequire(
                id=stable_function_impl_instruction_require_id(
                    function_impl_instruction_id=instruction_id
                ),
                function_impl_instruction_id=instruction_id,
                kind=template_require.kind,
                compare_operator=template_require.compare_operator,
                expected_count=template_require.expected_count,
                message=template_require.message,
            )
            for template_operand in template_require.operands:
                cloned_value_source = cloned_value_sources_by_template_id.get(
                    str(template_operand.value_source_id)
                )
                if cloned_value_source is None:
                    raise ValueError(
                        "Cannot clone FunctionImplInstructionRequireOperand without cloned value source "
                        + (
                            f"(template_function={template_function.name!r}, "
                            f"value_source_id={template_operand.value_source_id})"
                        )
                    )
                cloned_operand = FunctionImplInstructionRequireOperand(
                    id=stable_function_impl_instruction_require_operand_id(
                        function_impl_instruction_require_id=cloned_require.id,
                        position=template_operand.position,
                    ),
                    function_impl_instruction_require_id=cloned_require.id,
                    position=template_operand.position,
                    value_source=cloned_value_source,
                    value_source_id=cloned_value_source.id,
                )
                cloned_require.operands.append(cloned_operand)
            cloned_instruction.instruction_require = cloned_require

        template_delete = getattr(template_instruction, "instruction_delete", None)
        if template_delete is not None:
            cloned_instruction.instruction_delete = (
                _build_function_impl_instruction_delete(
                    id=stable_function_impl_instruction_delete_id(
                        function_impl_instruction_id=instruction_id
                    ),
                    function_impl_instruction_id=instruction_id,
                    target_kind=template_delete.target_kind,
                )
            )

        cloned_impl.instructions.append(cloned_instruction)

    apply_function_impl_kind(
        function_config=function_config,
        function_impl=cloned_impl,
        is_constructor=is_constructor,
    )
    return cloned_impl


def build_function_invocation_plan_from_impl(
    *,
    function_config: FunctionConfig,
    function_impl: FunctionImpl,
    capture_name_by_sequence: dict[int, str | None] | None = None,
) -> list[FunctionConfigInvocation]:
    """Derive invocation index rows from FunctionImpl invoke instructions."""
    invocations: list[FunctionConfigInvocation] = []
    instructions = sorted(
        (
            ins
            for ins in function_impl.instructions
            if ins.type == FunctionImplInstructionType.invoke
        ),
        key=lambda ins: (ins.sequence, str(ins.id)),
    )
    for instruction in instructions:
        payload = instruction.instruction_invoke
        if payload is None:
            continue
        kind = (
            FunctionInvocationKind.construct
            if payload.kind == FunctionImplInvokeKind.construct
            else FunctionInvocationKind.call
        )
        relationship_fingerprint = (
            str(payload.class_config_relationship_id)
            if payload.class_config_relationship_id is not None
            else "owner"
        )
        invocation_id = stable_function_config_invocation_id(
            function_config_id=function_config.id,
            position=instruction.sequence,
            kind=kind.value,
            target_function_config_id=payload.target_function_config_id,
            relationship_fingerprint=relationship_fingerprint,
        )
        invocation = FunctionConfigInvocation(
            id=invocation_id,
            function_config_id=function_config.id,
            position=instruction.sequence,
            kind=kind,
            root_kind=FunctionInvocationRootKind.owner,
            capture_name=(
                capture_name_by_sequence.get(instruction.sequence)
                if capture_name_by_sequence is not None
                else None
            ),
            target_function_config_id=payload.target_function_config_id,
            target_function_config=payload.target_function_config,
            class_config_relationship_id=payload.class_config_relationship_id,
            class_config_relationship=payload.class_config_relationship,
        )
        invocations.append(invocation)
    return invocations


def _resolve_invocations_from_body(
    *,
    function_config: FunctionConfig,
    owner_class_config: ClassConfig,
) -> tuple[list[_ResolvedInvocation], list[str], list[str]]:
    if function_config.code_section_function is None:
        return [], [], []
    body_segment = function_config.code_section_function.body_segment
    if body_segment is None:
        return [], [], []

    body_text = _segment_text_with_blob_fallback(body_segment=body_segment)
    if body_text is None:
        return [], [], []

    specs, parse_errors = _parse_invocation_specs(body_text)
    unresolved_errors: list[str] = []
    resolved: list[_ResolvedInvocation] = []
    for spec in specs:
        if spec.kind == FunctionInvocationKind.construct and len(spec.target_path) == 1:
            construct_target_name = spec.target_path[0]
            explicit_construct_class, construct_error = (
                _resolve_explicit_construct_class_target(
                    owner_class_config=owner_class_config,
                    class_name=construct_target_name,
                    line_number=spec.line_number,
                )
            )
            if construct_error is not None:
                unresolved_errors.append(construct_error)
                continue
            if explicit_construct_class is not None:
                # Explicit object construction (`construct ClassName(...)`) is a FunctionImpl
                # instruction, not a FunctionConfigInvocation row.
                continue

        target_function, relationship, unresolved = _resolve_invocation_target(
            owner_class_config=owner_class_config,
            kind=spec.kind,
            target_path=spec.target_path,
            line_number=spec.line_number,
        )
        if unresolved is not None:
            unresolved_errors.append(unresolved)
            continue

        resolved.append(
            _ResolvedInvocation(
                spec=spec,
                target_function=target_function,
                relationship=relationship,
            )
        )

    return resolved, parse_errors, unresolved_errors


def _build_function_invocations_from_resolved(
    *,
    function_config: FunctionConfig,
    resolved: list[_ResolvedInvocation],
) -> list[FunctionConfigInvocation]:
    invocations: list[FunctionConfigInvocation] = []
    for item in resolved:
        spec = item.spec
        relationship = item.relationship
        relationship_fingerprint = (
            str(relationship.id) if relationship is not None else "owner"
        )
        invocation_id = stable_function_config_invocation_id(
            function_config_id=function_config.id,
            position=spec.position,
            kind=_enum_value(spec.kind),
            target_function_config_id=item.target_function.id,
            relationship_fingerprint=relationship_fingerprint,
        )
        invocation = FunctionConfigInvocation(
            id=invocation_id,
            function_config_id=function_config.id,
            position=spec.position,
            kind=spec.kind,
            root_kind=FunctionInvocationRootKind.owner,
            capture_name=spec.capture_name,
            target_function_config_id=item.target_function.id,
            target_function_config=item.target_function,
            class_config_relationship_id=(
                relationship.id if relationship is not None else None
            ),
            class_config_relationship=relationship,
        )

        invocations.append(invocation)
    return invocations


__all__ = [
    "apply_function_impl_kind",
    "clone_function_impl_from_template",
    "build_function_invocation_plan_from_body",
    "build_function_impl_from_body",
    "build_function_invocation_plan_from_impl",
]
