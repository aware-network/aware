"""
Python runtime-handlers renderer (AWARE-managed).

Goal: generate *managed* handler implementation stubs + a generated registry module so:
- Devs edit only:
  - USER_IMPORTS block
  - LOGIC blocks inside handler bodies
- Signatures + file layout are compiler-owned and rewritten deterministically from the OCG.

This renderer is opt-in via workflows: `renderer_kind="runtime_handlers_aware"` and
`source="runtime_handlers_aware"`.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import keyword
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from uuid import UUID
from typing_extensions import override

# Code Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage

# Code Runtime
from aware_code.section.writer import CodeSectionWriter

# Content Runtime
# Meta Ontology
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.function.function_config_invocation_enums import (
    FunctionInvocationKind,
)
from aware_meta_ontology.function.function_impl_instruction_enums import (
    FunctionImplInstructionType,
    FunctionImplInvokeKind,
    FunctionImplRequireCompareOperator,
    FunctionImplRequireKind,
    FunctionImplValueTransformKind,
)
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

# Meta Runtime
from aware_meta.attribute.config.type_descriptor_helpers import (
    AttributeTypeInfo,
    resolve_type_info,
)
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
    build_renderer_empty_code,
)
from aware_meta.function.impl.builder import build_function_impl_from_body

# Python Grammar
from python_grammar.primitive_codec import PythonPrimitiveCodec
from python_grammar.renderer_runtime_handlers import (
    _normalize_runtime_handler_imports,
    runtime_handler_impl_module_import,
    runtime_handler_impl_relative_path,
)
from python_grammar.import_grouping import (
    PythonImportGroupingPolicy,
    group_python_imports,
    semantic_import_roots_from_renderer_inputs,
)
from python_grammar.renderer_policy import DEFAULT_ORM_SUPPORT_IMPORT_ROOTS

# Aware Utils
from aware_utils.string_transform import to_snake_case

_PRIMITIVE_CODEC = PythonPrimitiveCodec()
_DOCSTRING_WRAP_WIDTH = 100
_MAX_IMPORT_LINE_LENGTH = 120


def _wrap_docstring_lines(description: str) -> list[str]:
    lines: list[str] = []
    for raw_line in description.strip("\n").splitlines():
        if not raw_line.strip():
            lines.append("")
            continue
        lines.extend(
            textwrap.wrap(
                raw_line,
                width=_DOCSTRING_WRAP_WIDTH,
                break_long_words=False,
                break_on_hyphens=False,
            )
            or [""]
        )
    return lines


_USER_IMPORTS_START = "# --- AWARE: USER_IMPORTS START"
_USER_IMPORTS_END = "# --- AWARE: USER_IMPORTS END"
_MANAGED_IMPORTS_START = "# --- AWARE: MANAGED_IMPORTS START"
_MANAGED_IMPORTS_END = "# --- AWARE: MANAGED_IMPORTS END"


def _logic_start(name: str) -> str:
    return f"# --- AWARE: LOGIC START {name}"


def _logic_end(name: str) -> str:
    return f"# --- AWARE: LOGIC END {name}"


def _safe_identifier(name: str) -> str:
    if not name:
        return name
    if keyword.iskeyword(name):
        return f"{name}_"
    return name


def _emit_token(writer: CodeSectionWriter, txt: str) -> None:
    _ = writer.token(txt)


class _IndentWriter:
    def __init__(self, writer: CodeSectionWriter, *, indent_size: int):
        self._writer: CodeSectionWriter = writer
        self._indent_size: int = indent_size
        self._level: int = 0

    @contextmanager
    def indent(self):
        self._level += 1
        try:
            yield
        finally:
            self._level -= 1

    def write(self, txt: str) -> None:
        if self._level <= 0:
            _emit_token(self._writer, txt)
            return

        prefix = " " * (self._level * self._indent_size)
        lines = txt.splitlines(keepends=True)
        out: list[str] = []
        for line in lines:
            if line.strip():
                out.append(prefix + line)
            else:
                out.append(line)
        _emit_token(self._writer, "".join(out))


@dataclass(frozen=True)
class _RenderedParam:
    name: str
    type_annotation: str
    default_expr: str | None
    type_id: UUID | None
    type_name: str | None


@dataclass(frozen=True)
class _RenderedSignature:
    params: list[_RenderedParam]
    return_type: str
    return_type_id: UUID | None
    return_type_name: str | None


@dataclass(frozen=True)
class _GeneratedImplLogic:
    body: str
    runtime_imports: dict[str, set[str]]


@dataclass(frozen=True)
class _ConstructorRelationshipBinding:
    member_name: str
    member_identifier: str
    input_name: str
    target_class: ClassConfig


def _parse_user_imports(src: str) -> str:
    """Return the raw user-imports block (without markers)."""
    lines = src.splitlines(keepends=True)
    try:
        start = next(
            i for i, line in enumerate(lines) if line.strip() == _USER_IMPORTS_START
        )
        end = next(
            i for i, line in enumerate(lines) if line.strip() == _USER_IMPORTS_END
        )
    except StopIteration:
        return ""
    if end <= start:
        return ""
    return "".join(lines[start + 1 : end])


def _parse_logic_blocks(src: str) -> dict[str, str]:
    """Map `logic_name` -> raw block content (including indentation, without markers)."""
    lines = src.splitlines(keepends=True)
    out: dict[str, str] = {}
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("# --- AWARE: LOGIC START "):
            name = stripped.removeprefix("# --- AWARE: LOGIC START ").strip()
            try:
                end_idx = next(
                    j
                    for j in range(i + 1, len(lines))
                    if lines[j].strip() == _logic_end(name)
                )
            except StopIteration:
                i += 1
                continue
            raw = "".join(lines[i + 1 : end_idx])
            # Stored logic blocks are always nested under an indented function body.
            # Dedent here so regenerated output stays stable (writer re-indents per scope).
            out[name] = textwrap.dedent(raw)
            i = end_idx + 1
            continue
        i += 1
    return out


class PythonRendererRuntimeHandlersAware(ObjectConfigGraphRendererLanguage):
    """
    Emit:
    - `handlers/impl/<schema>/<class>.py`: managed stubs for human-authored logic.
    - `handlers/_generated/handlers.py`: managed wrapper + `AWARE_HANDLERS` registry.
    """

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(layout_strategy)
        self._warnings: list[str] = []
        self._function_impl_ownership: str = "authored"
        self._function_impl_parity_policy: str = "off"
        self._class_by_id: dict[UUID, ClassConfig] = {}
        self._function_by_id: dict[UUID, FunctionConfig] = {}
        self._enum_id_by_name: dict[str, UUID] = {}
        self._owner_by_function_id: dict[UUID, ClassConfig] = {}
        self._link_by_function_id: dict[UUID, ClassConfigFunctionConfig] = {}
        self._impl_name_by_function_id: dict[UUID, str] = {}
        self._rendered_class_by_id: dict[UUID, ClassConfig] = {}

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    @property
    @override
    def indent(self) -> int:
        return 4

    @property
    @override
    def comment_prefix(self) -> str:
        return "#"

    @override
    def define_assemblers(self):
        return None

    @override
    def create_empty_code(self) -> Code:
        return build_renderer_empty_code(
            language=CodeLanguage.python,
            renderer_key=type(self).__name__,
        )

    @override
    def clear_warnings(self) -> None:
        self._warnings = []

    @override
    def get_warnings(self) -> list[str]:
        return list(self._warnings)

    @override
    def set_policy(self, policy) -> None:
        policy_map = policy if isinstance(policy, dict) else {}
        ownership_raw = policy_map.get("function_impl_ownership")
        parity_raw = policy_map.get("function_impl_parity_policy")
        ownership = (
            str(ownership_raw).strip().lower()
            if ownership_raw is not None
            else "authored"
        )
        parity = str(parity_raw).strip().lower() if parity_raw is not None else "off"
        if ownership not in {"authored", "compiler"}:
            raise ValueError(
                "function_impl_ownership must be one of: authored, compiler "
                + f"(got {ownership!r})"
            )
        if parity not in {"off", "warn", "error"}:
            raise ValueError(
                "function_impl_parity_policy must be one of: off, warn, error "
                + f"(got {parity!r})"
            )
        self._function_impl_ownership = ownership
        self._function_impl_parity_policy = parity

    @override
    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        self._class_by_id = {}
        self._function_by_id = {}
        self._enum_id_by_name = {}
        self._owner_by_function_id = {}
        self._link_by_function_id = {}
        self._impl_name_by_function_id = {}
        self._rendered_class_by_id = {}

        # Index classes
        for node in graph.object_config_graph_nodes:
            cc = node.class_config
            if cc is None:
                continue
            self._class_by_id[cc.id] = cc

        # Index enums by name for best-effort type imports.
        for node in graph.object_config_graph_nodes:
            ec = node.enum_config
            if ec is None:
                continue
            self._enum_id_by_name[ec.name] = ec.id

        # Index function ownership and constructor-ness.
        for cc in self._class_by_id.values():
            fn_links = sorted(
                cc.class_config_function_configs,
                key=lambda link: (link.position, str(link.function_config_id)),
            )
            for link in fn_links:
                fn = link.function_config
                self._function_by_id[fn.id] = fn
                self._owner_by_function_id[fn.id] = cc
                self._link_by_function_id[fn.id] = link

            impl_name_by_fn = self._compute_impl_names_for_class(fn_links=fn_links)
            self._impl_name_by_function_id.update(impl_name_by_fn)

    def _compute_impl_names_for_class(
        self, *, fn_links: list[ClassConfigFunctionConfig]
    ) -> dict[UUID, str]:
        proposed_by_fn_id: dict[UUID, str] = {}
        used_names: dict[str, list[UUID]] = {}

        for link in fn_links:
            fn = link.function_config
            proposed = self._propose_impl_name(fn=fn, fn_link=link)
            proposed_by_fn_id[fn.id] = proposed
            used_names.setdefault(proposed, []).append(fn.id)

        out: dict[UUID, str] = {}
        for base_name, fn_ids in used_names.items():
            if len(fn_ids) == 1:
                out[fn_ids[0]] = base_name
                continue

            for fn_id in sorted(fn_ids, key=str):
                suffix = str(fn_id).split("-", 1)[0]
                out[fn_id] = _safe_identifier(f"{base_name}_{suffix}")
        return out

    def _propose_impl_name(
        self, *, fn: FunctionConfig, fn_link: ClassConfigFunctionConfig
    ) -> str:
        fn_name = _safe_identifier(fn.name)
        if not fn_link.is_constructor:
            return fn_name
        if "_via_" not in fn_name:
            return fn_name

        base_name, via_suffix = fn_name.split("_via_", 1)
        owner_token = via_suffix.split("_", 1)[0].strip("_")
        if not owner_token:
            return fn_name

        root = base_name.split("_", 1)[0].strip("_")
        if not root:
            root = "construct"
        return _safe_identifier(f"{root}_via_{owner_token}")

    def _enum_token(self, value: object) -> str:
        raw = getattr(value, "value", value)
        return str(raw).strip().lower()

    def _resolve_relationship_member_name(
        self, relationship: object | None
    ) -> str | None:
        if relationship is None:
            return None
        best: tuple[int, str] | None = None
        for rel_attr in (
            getattr(relationship, "class_config_relationship_attributes", []) or []
        ):
            attr_cfg = getattr(rel_attr, "attribute_config", None)
            attr_name = getattr(attr_cfg, "name", None)
            if not attr_name:
                continue
            direction = self._enum_token(getattr(rel_attr, "direction", ""))
            role = self._enum_token(getattr(rel_attr, "role", ""))
            score = 0
            if direction == "forward":
                score -= 10
            if role == "reference":
                score -= 5
            candidate = (score, str(attr_name))
            if best is None or candidate[0] < best[0]:
                best = candidate
        if best is not None:
            return best[1]
        relationship_key = getattr(relationship, "relationship_key", None)
        if isinstance(relationship_key, str) and relationship_key.strip():
            return relationship_key.strip()
        return None

    def _relationship_member_collection_kind(
        self,
        *,
        relationship: object | None,
        member_name: str,
    ) -> str | None:
        if relationship is None:
            return None
        for rel_attr in (
            getattr(relationship, "class_config_relationship_attributes", []) or []
        ):
            attr_cfg = getattr(rel_attr, "attribute_config", None)
            attr_name = getattr(attr_cfg, "name", None)
            if attr_name != member_name:
                continue
            descriptor = getattr(attr_cfg, "type_descriptor", None)
            kind = self._enum_token(getattr(descriptor, "kind", ""))
            collection_kind = self._enum_token(
                getattr(descriptor, "collection_kind", "")
            )
            if collection_kind == "set":
                return "set"
            if kind == "collection" or collection_kind == "list":
                return "list"
            return None
        return None

    def _append_relationship_construct_attachment(
        self,
        *,
        lines: list[str],
        receiver_expr: str,
        relationship: object | None,
        constructed_expr: str,
        attachment_key: object,
        line_context: str,
    ) -> None:
        raw_member_name = self._resolve_relationship_member_name(relationship)
        if not raw_member_name:
            raise ValueError(
                f"{line_context}: cannot resolve relationship member name for "
                "construct attachment"
            )
        member_name = _safe_identifier(raw_member_name)
        member_expr = f"{receiver_expr}.{member_name}"
        collection_kind = self._relationship_member_collection_kind(
            relationship=relationship,
            member_name=raw_member_name,
        )
        if collection_kind is None:
            lines.append(f"{member_expr} = {constructed_expr}")
            return

        member_var = _safe_identifier(f"_aware_relationship_member_{attachment_key}")
        lines.append(f"{member_var} = {member_expr}")
        lines.append(f"if {member_var} is None:")
        initializer_expr = "set()" if collection_kind == "set" else "[]"
        lines.append(f"    {member_expr} = {initializer_expr}")
        lines.append(f"    {member_var} = {member_expr}")
        lines.append(
            "if all("
            f"getattr(item, 'id', None) != getattr({constructed_expr}, 'id', None) "
            f"for item in {member_var}):"
        )
        lines.append(f"    if hasattr({member_var}, 'append'):")
        lines.append(f"        {member_var}.append({constructed_expr})")
        lines.append(f"    elif hasattr({member_var}, 'add'):")
        lines.append(f"        {member_var}.add({constructed_expr})")
        lines.append("    else:")
        lines.append(
            "        raise RuntimeError("
            + repr(
                f"{line_context}: relationship member '{member_name}' is not "
                "appendable"
            )
            + ")"
        )

    def _resolve_relationship_foreign_key_name(
        self,
        *,
        class_config: ClassConfig,
        reference_attribute_config_id: object,
    ) -> str | None:
        relationships = []
        for relationship in class_config.class_config_relationships:
            has_forward_reference = False
            for rel_attr in (
                getattr(relationship, "class_config_relationship_attributes", []) or []
            ):
                if self._enum_token(getattr(rel_attr, "direction", "")) != "forward":
                    continue
                if self._enum_token(getattr(rel_attr, "role", "")) != "reference":
                    continue
                if (
                    getattr(rel_attr, "attribute_config_id", None)
                    == reference_attribute_config_id
                ):
                    has_forward_reference = True
                    break
            if has_forward_reference:
                relationships.append(relationship)

        if not relationships:
            return None
        if len(relationships) > 1:
            raise ValueError(
                "relationship set target is ambiguous by reference attribute: "
                + f"class_config_id={class_config.id} attribute_config_id={reference_attribute_config_id}"
            )

        foreign_key_names: list[str] = []
        for rel_attr in (
            getattr(relationships[0], "class_config_relationship_attributes", []) or []
        ):
            if self._enum_token(getattr(rel_attr, "direction", "")) != "forward":
                continue
            if self._enum_token(getattr(rel_attr, "role", "")) != "foreign_key":
                continue
            attr_cfg = getattr(rel_attr, "attribute_config", None)
            if attr_cfg is None:
                attr_cfg = next(
                    (
                        link.attribute_config
                        for link in class_config.class_config_attribute_configs
                        if link.attribute_config_id
                        == getattr(rel_attr, "attribute_config_id", None)
                    ),
                    None,
                )
            attr_name = getattr(attr_cfg, "name", None)
            if not attr_name:
                raise ValueError(
                    "relationship set target foreign-key attribute is missing AttributeConfig name: "
                    + f"relationship_id={relationships[0].id}"
                )
            foreign_key_names.append(str(attr_name))

        if not foreign_key_names:
            raise ValueError(
                "relationship set target requires an explicit forward foreign-key attribute: "
                + f"relationship_id={relationships[0].id}"
            )
        if len(foreign_key_names) > 1:
            raise ValueError(
                "relationship set target has ambiguous forward foreign-key attributes: "
                + f"relationship_id={relationships[0].id} count={len(foreign_key_names)}"
            )
        return foreign_key_names[0]

    def _constructor_relationship_bindings(
        self,
        *,
        class_config: ClassConfig,
        input_names: set[str],
    ) -> list[_ConstructorRelationshipBinding]:
        bindings: list[_ConstructorRelationshipBinding] = []
        seen: set[str] = set()
        for relationship in class_config.class_config_relationships or []:
            member_name = self._resolve_relationship_member_name(relationship)
            if not member_name:
                continue
            member_identifier = _safe_identifier(member_name)
            if member_identifier == _safe_identifier(to_snake_case(class_config.name)):
                continue
            if not bool(getattr(relationship, "forward_required", False)):
                continue
            input_name = f"{member_identifier}_id"
            if input_name not in input_names:
                continue
            target_class = getattr(relationship, "target_class_config", None)
            if target_class is None:
                target_class_id = getattr(relationship, "target_class_config_id", None)
                if isinstance(target_class_id, UUID):
                    target_class = self._class_by_id.get(target_class_id)
            if target_class is None:
                continue
            if member_identifier in seen:
                raise ValueError(
                    "constructor relationship hydration is ambiguous: "
                    + f"class_config={class_config.name} member={member_name}"
                )
            seen.add(member_identifier)
            bindings.append(
                _ConstructorRelationshipBinding(
                    member_name=member_name,
                    member_identifier=member_identifier,
                    input_name=input_name,
                    target_class=target_class,
                )
            )
        bindings.sort(key=lambda binding: binding.member_identifier)
        return bindings

    def _emit_constructor_relationship_hydration(
        self,
        *,
        lines: list[str],
        runtime_imports: dict[str, set[str]],
        class_config: ClassConfig,
        input_names: set[str],
        line_context: str,
    ) -> dict[str, str]:
        bindings = self._constructor_relationship_bindings(
            class_config=class_config,
            input_names=input_names,
        )
        if not bindings:
            return {}

        runtime_imports.setdefault("aware_meta.runtime.handler_context", set()).add(
            "current_handler_session"
        )
        lines.append("_aware_handler_session = current_handler_session()")
        hydrated: dict[str, str] = {}
        for binding in bindings:
            module = (self.import_overrides or {}).get(str(binding.target_class.id))
            if not module:
                raise ValueError(
                    f"{line_context}: cannot import relationship target "
                    f"{binding.target_class.name} for constructor member "
                    f"{binding.member_name}"
                )
            runtime_imports.setdefault(module, set()).add(binding.target_class.name)
            lines.append(
                f"{binding.member_identifier} = _aware_handler_session.imap_get("
                f"{binding.target_class.name}, {binding.input_name})"
            )
            lines.append(f"if {binding.member_identifier} is None:")
            lines.append(
                "    raise RuntimeError("
                + repr(
                    f"{line_context} requires existing {binding.target_class.name}: "
                    f"{binding.input_name}="
                )
                + f" + str({binding.input_name}))"
            )
            hydrated[binding.member_identifier] = binding.member_identifier
        return hydrated

    def _resolve_stable_ids_module_for_class(
        self, class_config: ClassConfig
    ) -> str | None:
        class_module = (self.import_overrides or {}).get(str(class_config.id))
        if not class_module:
            return None
        root_package = class_module.split(".", 1)[0].strip()
        if not root_package:
            return None
        return f"{root_package}.stable_ids"

    def _render_json_literal(self, value: object) -> str:
        return _PRIMITIVE_CODEC.to_literal_string(value)

    def _render_invoke_value_expr(
        self,
        *,
        value_expr: object,
        line_context: str,
    ) -> str:
        if not isinstance(value_expr, dict):
            raise ValueError(
                f"{line_context}: invoke argument value expression must be JsonObject"
            )
        kind = str(value_expr.get("kind", "")).strip().lower()
        if kind == "reference":
            name = str(value_expr.get("name", "")).strip()
            if not name:
                raise ValueError(
                    f"{line_context}: invoke reference value expression requires non-empty name"
                )
            return _safe_identifier(name)
        if kind == "self_id":
            return "__aware_self_id__"
        if kind == "literal":
            return self._render_json_literal(value_expr.get("value"))
        raise ValueError(
            f"{line_context}: unsupported invoke argument value expression kind {kind!r}"
        )

    def _render_value_source_expr(
        self,
        *,
        value_source: object,
        line_context: str,
    ) -> str:
        kind = self._enum_token(getattr(value_source, "kind", ""))
        if kind == "function_input_ref":
            link = getattr(
                value_source, "source_function_config_attribute_config", None
            )
            attr_cfg = (
                getattr(link, "attribute_config", None) if link is not None else None
            )
            attr_name = getattr(attr_cfg, "name", None)
            if not attr_name:
                raise ValueError(
                    f"{line_context}: function_input_ref is missing AttributeConfig.name"
                )
            return _safe_identifier(str(attr_name))
        if kind == "let_ref":
            let_payload = getattr(value_source, "source_instruction_let", None)
            let_name = getattr(let_payload, "name", None)
            if not let_name:
                raise ValueError(
                    f"{line_context}: let_ref is missing instruction_let.name"
                )
            return _safe_identifier(str(let_name))
        if kind == "literal":
            literal_payload = getattr(value_source, "source_literal_primitive", None)
            literal_box = (
                getattr(literal_payload, "value", None)
                if literal_payload is not None
                else None
            )
            literal_value = (
                literal_box.get("value")
                if isinstance(literal_box, dict)
                else literal_box
            )
            return self._render_json_literal(literal_value)
        if kind == "transform":
            transform = getattr(value_source, "source_transform", None)
            if transform is None:
                raise ValueError(
                    f"{line_context}: transform is missing source_transform payload"
                )
            operation = self._enum_token(getattr(transform, "operation", ""))
            operands = sorted(
                getattr(transform, "operands", ()),
                key=lambda operand: (
                    int(operand.position) if operand.position is not None else 999999,
                    str(operand.id),
                ),
            )
            rendered_operands = [
                self._render_value_source_expr(
                    value_source=operand.value_source,
                    line_context=f"{line_context}: transform operand {operand.position}",
                )
                for operand in operands
            ]

            def text_expr(expr: str) -> str:
                # JSON string literals are already valid text values; wrapping them in
                # `is None` checks produces SyntaxWarning for literal identity tests.
                if expr.startswith(('"', "'")):
                    return expr
                return f'("" if {expr} is None else {expr})'

            if operation == self._enum_token(FunctionImplValueTransformKind.text_strip):
                if len(rendered_operands) != 1:
                    raise ValueError(f"{line_context}: text.strip expects 1 operand")
                return f"{text_expr(rendered_operands[0])}.strip()"
            if operation == self._enum_token(
                FunctionImplValueTransformKind.text_casefold
            ):
                if len(rendered_operands) != 1:
                    raise ValueError(f"{line_context}: text.casefold expects 1 operand")
                return f"{text_expr(rendered_operands[0])}.casefold()"
            if operation == self._enum_token(FunctionImplValueTransformKind.text_lower):
                if len(rendered_operands) != 1:
                    raise ValueError(f"{line_context}: text.lower expects 1 operand")
                return f"{text_expr(rendered_operands[0])}.lower()"
            if operation == self._enum_token(
                FunctionImplValueTransformKind.text_default_if_blank
            ):
                if len(rendered_operands) != 2:
                    raise ValueError(
                        f"{line_context}: text.default_if_blank expects 2 operands"
                    )
                value_expr = text_expr(rendered_operands[0])
                default_expr = text_expr(rendered_operands[1])
                return (
                    f"({default_expr} if {value_expr}.strip() == '' else {value_expr})"
                )
            if operation == self._enum_token(FunctionImplValueTransformKind.text_slice):
                if len(rendered_operands) not in {2, 3}:
                    raise ValueError(
                        f"{line_context}: text.slice expects 2 or 3 operands"
                    )
                end_expr = "" if len(rendered_operands) == 2 else rendered_operands[2]
                return f"{text_expr(rendered_operands[0])}[{rendered_operands[1]}:{end_expr}]"
            if operation == self._enum_token(
                FunctionImplValueTransformKind.text_concat
            ):
                if not rendered_operands:
                    raise ValueError(
                        f"{line_context}: text.concat expects at least 1 operand"
                    )
                return (
                    '"".join("" if operand is None else operand '
                    f"for operand in ({', '.join(rendered_operands)},))"
                )
            raise ValueError(
                f"{line_context}: unsupported transform operation {operation!r}"
            )
        raise ValueError(
            f"{line_context}: unsupported FunctionImplValueSource kind {kind!r}"
        )

    @override
    def extra_output_paths(self) -> list[Path]:
        ext = self.layout_strategy.get_file_extension()
        return [Path("handlers") / "_generated" / f"handlers{ext}"]

    @override
    def emit_file(
        self,
        meta_objects: list[object],
        writer: CodeSectionWriter,
        schema: str = "default",
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
    ) -> None:
        _ = schema, class_to_class_config_map, base_class_module, base_class_name

        cls = next(
            (obj for obj in meta_objects if isinstance(obj, ClassConfig)),
            None,
        )
        if cls is not None:
            self._emit_impl_file(writer=writer, class_config=cls)
            return

        # Emit generated registry for:
        # - explicit extra output path (empty meta_objects), and
        # - function-mapped generated path (meta_objects contains FunctionConfig entries).
        if not meta_objects or all(
            isinstance(obj, FunctionConfig) for obj in meta_objects
        ):
            self._emit_generated_handlers_file(writer=writer)
        return

    # ---------------------------------------------------------------------
    # Impl stubs
    # ---------------------------------------------------------------------
    def _emit_impl_file(
        self, *, writer: CodeSectionWriter, class_config: ClassConfig
    ) -> None:
        self._rendered_class_by_id[class_config.id] = class_config
        fn_links = sorted(
            class_config.class_config_function_configs,
            key=lambda link: (
                link.position,
                str(link.function_config_id),
            ),
        )
        # Do not emit stubs for classes that have no functions.
        # This keeps `handlers/impl/**` minimal and avoids generating empty "placeholder" files.
        if not fn_links:
            return

        file_path = runtime_handler_impl_relative_path(
            layout_strategy=self.layout_strategy,
            class_config=class_config,
        )
        output_path = (
            Path(self.layout_strategy.base_dir).resolve() / file_path
        ).resolve()

        existing_src = ""
        if output_path.exists():
            try:
                existing_src = output_path.read_text(encoding="utf-8")
            except Exception:
                existing_src = ""

        preserved_imports = _parse_user_imports(existing_src) if existing_src else ""
        preserved_logic = _parse_logic_blocks(existing_src) if existing_src else {}

        impl_name_by_fn_id = self._compute_impl_names_for_class(fn_links=fn_links)
        allowed_logic_names: set[str] = set()
        for link in fn_links:
            fn = link.function_config
            allowed_logic_names.add(_safe_identifier(fn.name))
            allowed_logic_names.add(
                impl_name_by_fn_id.get(fn.id, _safe_identifier(fn.name))
            )
        unknown_logic_names = set(preserved_logic.keys()) - allowed_logic_names
        if unknown_logic_names:
            message = (
                f"AWARE runtime handler impl contains unknown/legacy logic blocks: {sorted(unknown_logic_names)}. "
                + f"Rename the blocks to match the current function names: {sorted(allowed_logic_names)}."
            )
            raise ValueError(message)

        generated_logic_by_fn_id: dict[UUID, _GeneratedImplLogic] = {}
        generated_runtime_imports: dict[str, set[str]] = {}
        for link in fn_links:
            fn = link.function_config
            generated = self._build_generated_impl_logic(
                class_config=class_config,
                fn_link=link,
                fn=fn,
            )
            if generated is None:
                continue
            generated_logic_by_fn_id[fn.id] = generated
            generated_runtime_imports = self._merge_imports(
                generated_runtime_imports,
                generated.runtime_imports,
            )

        # Managed header
        _emit_token(writer, "from __future__ import annotations\n\n")

        # Managed imports: required at runtime for default expressions (e.g. EnumType.DEFAULT),
        # plus TYPE_CHECKING imports for signatures (compiler-owned).
        runtime_imports: dict[str, set[str]] = dict(generated_runtime_imports)
        for link in fn_links:
            fn = link.function_config
            sig = self._render_signature(fn=fn)
            for p in sig.params:
                if p.default_expr is None:
                    continue
                # Enum defaults are emitted as `EnumName.VALUE` and must be importable at runtime.
                if (
                    p.type_id
                    and p.type_name
                    and p.default_expr.startswith(f"{p.type_name}.")
                ):
                    mod = self._resolve_type_module_by_id(p.type_id)
                    if mod:
                        runtime_imports.setdefault(mod, set()).add(p.type_name)

        # Type-only imports (best-effort; full import graph is owned by the generated ontology/DTO packages).
        type_imports: dict[str, set[str]] = {}

        # Import the owning class type for instance handler `self` params (when available).
        class_mod = (self.import_overrides or {}).get(str(class_config.id))
        if class_mod:
            type_imports.setdefault(class_mod, set()).add(class_config.name)

        # Import types referenced by function signatures (inputs + outputs).
        for link in fn_links:
            fn = link.function_config
            sig = self._render_signature(fn=fn)
            for p in sig.params:
                self._collect_type_imports(
                    type_imports, type_annotation=p.type_annotation
                )
                self._collect_type_imports_by_id(
                    type_imports,
                    type_id=p.type_id,
                    type_name=p.type_name,
                )
            self._collect_type_imports(type_imports, type_annotation=sig.return_type)
            self._collect_type_imports_by_id(
                type_imports,
                type_id=sig.return_type_id,
                type_name=sig.return_type_name,
            )

        # Avoid duplicating runtime imports inside TYPE_CHECKING when possible.
        for module in list(type_imports.keys()):
            if module in runtime_imports:
                type_imports[module] = type_imports[module] - runtime_imports[module]
                if not type_imports[module]:
                    del type_imports[module]

        _emit_token(writer, f"{_MANAGED_IMPORTS_START}\n")
        _emit_token(writer, "# fmt: off\n")
        combined_imports = self._merge_imports(runtime_imports, type_imports)
        self._emit_grouped_imports(writer=writer, imports=combined_imports)
        _emit_token(writer, "# fmt: on\n")
        _emit_token(writer, f"{_MANAGED_IMPORTS_END}\n\n")

        _emit_token(writer, f"{_USER_IMPORTS_START}\n")
        _emit_token(writer, preserved_imports if preserved_imports else "")
        if preserved_imports and not preserved_imports.endswith("\n"):
            _emit_token(writer, "\n")
        _emit_token(writer, f"{_USER_IMPORTS_END}\n\n")

        # Emit functions
        for link in fn_links:
            fn = link.function_config

            impl_name = impl_name_by_fn_id.get(fn.id, _safe_identifier(fn.name))
            preserved = preserved_logic.get(impl_name, "")
            if not preserved.strip():
                preserved = preserved_logic.get(_safe_identifier(fn.name), "")
            self._emit_impl_function(
                writer=writer,
                class_config=class_config,
                fn_link=link,
                fn=fn,
                impl_name=_safe_identifier(impl_name),
                preserved_logic=preserved,
                generated_logic=generated_logic_by_fn_id.get(fn.id),
            )
            _emit_token(writer, "\n\n")

    def _emit_impl_function(
        self,
        *,
        writer: CodeSectionWriter,
        class_config: ClassConfig,
        fn_link: ClassConfigFunctionConfig,
        fn: FunctionConfig,
        impl_name: str,
        preserved_logic: str,
        generated_logic: _GeneratedImplLogic | None,
    ) -> None:
        sig = self._render_signature(fn=fn)

        # Build signature string
        params: list[str] = []
        if not fn_link.is_constructor:
            self_name = _safe_identifier(to_snake_case(class_config.name))
            params.append(f"{self_name}: {class_config.name}")
        for p in sig.params:
            part = f"{_safe_identifier(p.name)}: {p.type_annotation}"
            if p.default_expr is not None:
                part += f" = {p.default_expr}"
            params.append(part)
        signature = "(" + (", ".join(params)) + ")"

        # Runtime handler implementations are always async (even for non-async `.aware`),
        # because propagation and runtime IO are async and wrappers always `await` the impl.
        _emit_token(writer, f"async def {impl_name}{signature} -> {sig.return_type}:\n")

        iw = _IndentWriter(writer, indent_size=self.indent)
        with iw.indent():
            if fn.description:
                iw.write('"""\n')
                for line in _wrap_docstring_lines(fn.description):
                    iw.write(f"{line}\n" if line else "\n")
                iw.write('"""\n\n')

            logic_name = impl_name
            iw.write(f"{_logic_start(logic_name)}\n")

            if generated_logic is not None:
                generated = (
                    generated_logic.body
                    if generated_logic.body.endswith("\n")
                    else generated_logic.body + "\n"
                )
                iw.write(generated)
            elif preserved_logic.strip():
                if self._function_impl_ownership == "compiler":
                    self._warnings.append(
                        f"FunctionImpl compiler ownership unresolved for {class_config.name}.{fn.name}: using preserved manual logic"
                    )
                preserved = (
                    preserved_logic
                    if preserved_logic.endswith("\n")
                    else preserved_logic + "\n"
                )
                iw.write(preserved)
            else:
                if self._function_impl_ownership == "compiler":
                    self._warnings.append(
                        f"FunctionImpl compiler ownership unresolved for {class_config.name}.{fn.name}: generated logic missing (stub emitted)"
                    )
                    iw.write(
                        "# AWARE: compiler-owned FunctionImpl lowering unavailable for this function; "
                        "manual implementation required until support lands.\n"
                    )
                iw.write(
                    'raise NotImplementedError("AWARE: implement handler logic")\n'
                )

            iw.write(f"{_logic_end(logic_name)}\n")

    def _build_generated_impl_logic(
        self,
        *,
        class_config: ClassConfig,
        fn_link: ClassConfigFunctionConfig,
        fn: FunctionConfig,
    ) -> _GeneratedImplLogic | None:
        function_impl = None
        # Compiler-owned rail should always prefer fresh body->FunctionImpl lowering
        # so renderer output tracks current `.aware` intent even when attached
        # FunctionImpl payloads are stale or gated elsewhere in OCG build.
        if self._function_impl_ownership == "compiler":
            try:
                function_impl = build_function_impl_from_body(
                    function_config=fn,
                    owner_class_config=class_config,
                    fail_on_unresolved=True,
                )
            except Exception as exc:
                self._warnings.append(
                    f"FunctionImpl lowering unavailable for {class_config.name}.{fn.name}: {exc}"
                )
                function_impl = None
            if function_impl is None:
                function_impl = fn.function_impl
        else:
            function_impl = fn.function_impl
            if function_impl is None:
                try:
                    function_impl = build_function_impl_from_body(
                        function_config=fn,
                        owner_class_config=class_config,
                        fail_on_unresolved=True,
                    )
                except Exception as exc:
                    self._warnings.append(
                        f"FunctionImpl lowering unavailable for {class_config.name}.{fn.name}: {exc}"
                    )
                    function_impl = None
        if function_impl is None:
            try:
                return self._build_generated_impl_logic_from_invocations(
                    class_config=class_config,
                    fn_link=fn_link,
                    fn=fn,
                )
            except Exception as exc:
                self._warnings.append(
                    f"FunctionImpl invocation fallback unavailable for {class_config.name}.{fn.name}: {exc}"
                )
                return None

        instructions = sorted(
            function_impl.instructions,
            key=lambda ins: (int(ins.sequence), str(ins.id)),
        )
        capture_name_by_sequence = {
            int(inv.position): (inv.capture_name.strip() if inv.capture_name else None)
            for inv in fn.invocations
        }
        input_edges = [
            edge
            for edge in fn.function_config_attribute_configs
            if edge.type == FunctionAttributeType.input
            and edge.attribute_config is not None
        ]
        input_edges.sort(key=lambda edge: (int(edge.position), str(edge.id)))
        runtime_imports: dict[str, set[str]] = {}
        lines: list[str] = []
        self_name = _safe_identifier(to_snake_case(class_config.name))
        has_return_stmt = False
        last_value_expr: str | None = None
        sig = self._render_signature(fn=fn)
        expects_return = sig.return_type != "None"
        signature_input_names = {param.name for param in sig.params}
        class_attribute_names = {
            _safe_identifier(link.attribute_config.name)
            for link in class_config.class_config_attribute_configs
            if link.attribute_config is not None
            and getattr(link.attribute_config, "name", None)
        }
        constructor_self_id_emitted = False
        constructor_self_id_name = "_aware_self_id"

        def _require_class_import(target_class: ClassConfig | None) -> None:
            if target_class is None:
                return
            module = (self.import_overrides or {}).get(str(target_class.id))
            if module:
                runtime_imports.setdefault(module, set()).add(target_class.name)

        def _class_attribute_names(target_class: ClassConfig) -> set[str]:
            return {
                _safe_identifier(link.attribute_config.name)
                for link in target_class.class_config_attribute_configs
                if link.attribute_config is not None
                and getattr(link.attribute_config, "name", None)
            }

        def _ensure_constructor_self_id(line_context: str) -> str:
            nonlocal constructor_self_id_emitted
            if not fn_link.is_constructor:
                return f"{self_name}.id"
            if constructor_self_id_emitted:
                return constructor_self_id_name
            stable_ids_module = self._resolve_stable_ids_module_for_class(class_config)
            if stable_ids_module is None:
                raise ValueError(
                    f"{line_context}: constructor self_id requires stable-id bindings "
                    f"for {class_config.name}"
                )
            runtime_imports.setdefault("importlib", set()).add("import_module")
            runtime_imports.setdefault(stable_ids_module, set()).add(
                "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID"
            )
            input_names = [
                _safe_identifier(edge.attribute_config.name)
                for edge in input_edges
                if edge.attribute_config is not None
            ]
            values_expr = ", ".join(f"{name!r}: {name}" for name in input_names)
            lines.append(f"_aware_self_values = {{{values_expr}}}")
            lines.append(
                "_aware_self_binding = "
                "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID.get("
                + f"{str(class_config.id)!r})"
            )
            lines.append("if _aware_self_binding is None:")
            lines.append(
                "    raise RuntimeError("
                + repr(
                    f"{class_config.name}.{fn.name} cannot resolve constructor self id: "
                    "missing stable-id binding"
                )
                + ")"
            )
            lines.append("_aware_self_fn, _aware_self_key_names = _aware_self_binding")
            lines.append(
                "_aware_missing_self_keys = ["
                "key for key in _aware_self_key_names "
                "if key not in _aware_self_values"
                "]"
            )
            lines.append("if _aware_missing_self_keys:")
            lines.append(
                "    raise RuntimeError("
                + repr(
                    f"{class_config.name}.{fn.name} cannot resolve constructor self id: "
                    "missing stable identity values"
                )
                + " + f': {_aware_missing_self_keys}')"
            )
            lines.append(
                "_aware_self_stable_values = {"
                "key: getattr(_aware_self_values[key], 'value', _aware_self_values[key]) "
                "for key in _aware_self_key_names"
                "}"
            )
            lines.append(
                f"{constructor_self_id_name} = getattr("
                f"import_module({stable_ids_module!r}), _aware_self_fn"
                ")(**_aware_self_stable_values)"
            )
            constructor_self_id_emitted = True
            return constructor_self_id_name

        def _receiver_input_expr(value_expr: str) -> str:
            if fn_link.is_constructor or value_expr in signature_input_names:
                return value_expr
            if value_expr in {"class_fqn", "owner_key"}:
                return f"{self_name}.{value_expr}"
            if value_expr in class_attribute_names:
                return f"getattr({self_name}.{value_expr}, 'value', {self_name}.{value_expr})"
            return value_expr

        try:
            for instruction in instructions:
                ins_kind = self._enum_token(instruction.type)

                if ins_kind == self._enum_token(FunctionImplInstructionType.let):
                    payload = instruction.instruction_let
                    if payload is None:
                        raise ValueError(
                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: missing let payload"
                        )
                    let_name = _safe_identifier((payload.name or "").strip())
                    if not let_name:
                        raise ValueError(
                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: let payload has empty name"
                        )
                    let_expr = payload.value_expr
                    if not isinstance(let_expr, dict):
                        raise ValueError(
                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: let value_expr must be JsonObject"
                        )
                    let_kind = str(let_expr.get("kind", "")).strip().lower()
                    if let_kind == "reference":
                        ref_name = _safe_identifier(
                            str(let_expr.get("name", "")).strip()
                        )
                        if not ref_name:
                            raise ValueError(
                                f"{class_config.name}.{fn.name} sequence={instruction.sequence}: let reference name is empty"
                            )
                        if (
                            not fn_link.is_constructor
                            and ref_name in class_attribute_names
                            and ref_name not in signature_input_names
                        ):
                            lines.append(
                                f"{let_name} = getattr({self_name}.{ref_name}, "
                                f"'value', {self_name}.{ref_name})"
                            )
                            continue
                        lines.append(f"{let_name} = {ref_name}")
                        continue
                    if let_kind == "literal":
                        lines.append(
                            f"{let_name} = {self._render_json_literal(let_expr.get('value'))}"
                        )
                        continue
                    if let_kind == "value_source":
                        value_sources = list(getattr(instruction, "value_sources", ()))
                        if len(value_sources) != 1:
                            raise ValueError(
                                f"{class_config.name}.{fn.name} sequence={instruction.sequence}: "
                                "let value_source expects exactly one value source"
                            )
                        value_expr = self._render_value_source_expr(
                            value_source=value_sources[0],
                            line_context=f"{class_config.name}.{fn.name} sequence={instruction.sequence}",
                        )
                        lines.append(f"{let_name} = {value_expr}")
                        continue
                    raise ValueError(
                        f"{class_config.name}.{fn.name} sequence={instruction.sequence}: unsupported let value kind {let_kind!r}"
                    )

                if ins_kind == self._enum_token(FunctionImplInstructionType.invoke):
                    payload = instruction.instruction_invoke
                    if payload is None:
                        raise ValueError(
                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: missing invoke payload"
                        )
                    target_fn = payload.target_function_config
                    if target_fn is None:
                        target_fn = next(
                            (
                                link.function_config
                                for owner in self._class_by_id.values()
                                for link in owner.class_config_function_configs
                                if link.function_config_id
                                == payload.target_function_config_id
                            ),
                            None,
                        )
                    if target_fn is None:
                        raise ValueError(
                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: cannot resolve target function for invoke"
                        )

                    target_owner = self._owner_by_function_id.get(target_fn.id)
                    target_link = self._link_by_function_id.get(target_fn.id)
                    if target_owner is None or target_link is None:
                        raise ValueError(
                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: cannot resolve target owner/link for invoke"
                        )

                    _require_class_import(target_owner)

                    invoke_bindings = sorted(
                        payload.attribute_configs,
                        key=lambda binding: (
                            (
                                int(binding.position)
                                if binding.position is not None
                                else 999999
                            ),
                            str(binding.id),
                        ),
                    )
                    rendered_args: list[str] = []
                    for binding in invoke_bindings:
                        attr_cfg = binding.attribute_config
                        if attr_cfg is None:
                            attr_cfg = next(
                                (
                                    edge.attribute_config
                                    for edge in target_fn.function_config_attribute_configs
                                    if edge.attribute_config_id
                                    == binding.attribute_config_id
                                ),
                                None,
                            )
                        if attr_cfg is None:
                            raise ValueError(
                                f"{class_config.name}.{fn.name} sequence={instruction.sequence}: invoke binding missing AttributeConfig"
                            )
                        arg_name = _safe_identifier(attr_cfg.name)
                        value_expr = self._render_invoke_value_expr(
                            value_expr=binding.value_expr,
                            line_context=(
                                f"{class_config.name}.{fn.name} sequence={instruction.sequence} "
                                f"invoke arg {attr_cfg.name}"
                            ),
                        )
                        if value_expr == "__aware_self_id__":
                            value_expr = _ensure_constructor_self_id(
                                f"{class_config.name}.{fn.name} sequence={instruction.sequence}"
                            )
                        value_expr = _receiver_input_expr(value_expr)
                        rendered_args.append(f"{arg_name}={value_expr}")
                    args_text = ", ".join(rendered_args)

                    invoke_kind = self._enum_token(payload.kind)
                    target_is_constructor = bool(target_link.is_constructor)
                    relationship_construct_attachment = None
                    call_expr: str
                    if invoke_kind == self._enum_token(
                        FunctionImplInvokeKind.construct
                    ):
                        if not target_is_constructor:
                            raise ValueError(
                                f"{class_config.name}.{fn.name} sequence={instruction.sequence}: construct invoke target is not constructor"
                            )
                        if payload.class_config_relationship_id is not None:
                            if fn_link.is_constructor:
                                raise ValueError(
                                    f"{class_config.name}.{fn.name} sequence={instruction.sequence}: "
                                    "relationship construct requires instance context"
                                )
                            relationship_construct_attachment = (
                                payload.class_config_relationship
                            )
                        call_expr = (
                            f"await {target_owner.name}.{target_fn.name}({args_text})"
                            if args_text
                            else (f"await {target_owner.name}.{target_fn.name}()")
                        )
                    else:
                        if payload.class_config_relationship_id is None:
                            if target_is_constructor:
                                relationship_construct_attachment = (
                                    payload.class_config_relationship
                                )
                                call_expr = (
                                    f"await {target_owner.name}.{target_fn.name}({args_text})"
                                    if args_text
                                    else f"await {target_owner.name}.{target_fn.name}()"
                                )
                            else:
                                if fn_link.is_constructor:
                                    raise ValueError(
                                        f"{class_config.name}.{fn.name} sequence={instruction.sequence}: owner-local instance call is not available in constructor context"
                                    )
                                call_expr = (
                                    f"await {self_name}.{target_fn.name}({args_text})"
                                    if args_text
                                    else f"await {self_name}.{target_fn.name}()"
                                )
                        else:
                            rel_member = self._resolve_relationship_member_name(
                                payload.class_config_relationship
                            )
                            if not rel_member:
                                raise ValueError(
                                    f"{class_config.name}.{fn.name} sequence={instruction.sequence}: cannot resolve relationship member name for invoke"
                                )
                            if fn_link.is_constructor:
                                raise ValueError(
                                    f"{class_config.name}.{fn.name} sequence={instruction.sequence}: relationship invoke requires instance context"
                                )
                            if not target_is_constructor:
                                for rel_attr in (
                                    getattr(
                                        payload.class_config_relationship,
                                        "class_config_relationship_attributes",
                                        [],
                                    )
                                    or []
                                ):
                                    attr_cfg = getattr(
                                        rel_attr, "attribute_config", None
                                    )
                                    if getattr(attr_cfg, "name", None) != rel_member:
                                        continue
                                    descriptor = getattr(
                                        attr_cfg, "type_descriptor", None
                                    )
                                    if (
                                        getattr(descriptor, "collection_kind", None)
                                        is not None
                                    ):
                                        raise ValueError(
                                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: "
                                            f"relationship member '{rel_member}' is a collection and cannot be used "
                                            "as a direct instance-call receiver in renderer v0."
                                        )
                            rel_expr = f"{self_name}.{_safe_identifier(rel_member)}"
                            if target_is_constructor:
                                call_expr = (
                                    f"await {target_owner.name}.{target_fn.name}({args_text})"
                                    if args_text
                                    else f"await {target_owner.name}.{target_fn.name}()"
                                )
                            else:
                                lines.append(f"if {rel_expr} is None:")
                                lines.append(
                                    "    raise RuntimeError("
                                    + repr(
                                        f"{class_config.name}.{fn.name} cannot call relationship function "
                                        f"'{target_fn.name}' because '{rel_member}' is None"
                                    )
                                    + ")"
                                )
                                call_expr = (
                                    f"await {rel_expr}.{target_fn.name}({args_text})"
                                    if args_text
                                    else f"await {rel_expr}.{target_fn.name}()"
                                )

                    capture_name = capture_name_by_sequence.get(
                        int(instruction.sequence)
                    )
                    if relationship_construct_attachment is not None:
                        constructed_expr = (
                            _safe_identifier(capture_name)
                            if capture_name
                            else f"_aware_constructed_{int(instruction.sequence)}"
                        )
                        lines.append(f"{constructed_expr} = {call_expr}")
                        self._append_relationship_construct_attachment(
                            lines=lines,
                            receiver_expr=self_name,
                            relationship=relationship_construct_attachment,
                            constructed_expr=constructed_expr,
                            attachment_key=f"instruction_{int(instruction.sequence)}",
                            line_context=(
                                f"{class_config.name}.{fn.name} "
                                f"sequence={instruction.sequence}"
                            ),
                        )
                        last_value_expr = constructed_expr
                    elif capture_name:
                        constructed_expr = _safe_identifier(capture_name)
                        lines.append(f"{constructed_expr} = {call_expr}")
                        last_value_expr = constructed_expr
                    else:
                        lines.append(call_expr)
                    continue

                if ins_kind == self._enum_token(FunctionImplInstructionType.construct):
                    payload = instruction.instruction_construct
                    if payload is None:
                        raise ValueError(
                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: missing construct payload"
                        )
                    target_class = payload.target_class_config
                    if target_class is None:
                        target_class = self._class_by_id.get(
                            payload.target_class_config_id
                        )
                    if target_class is None:
                        raise ValueError(
                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: cannot resolve construct target class"
                        )
                    _require_class_import(target_class)
                    rendered_args: list[str] = []
                    rendered_arg_names: set[str] = set()
                    assignments = sorted(
                        payload.assignments,
                        key=lambda assignment: (
                            (
                                int(assignment.position)
                                if assignment.position is not None
                                else 999999
                            ),
                            str(assignment.id),
                        ),
                    )
                    for assignment in assignments:
                        target_link = assignment.target_class_config_attribute_config
                        target_attr = (
                            target_link.attribute_config
                            if target_link is not None
                            else None
                        )
                        target_name = (
                            _safe_identifier(target_attr.name)
                            if target_attr is not None
                            else ""
                        )
                        if not target_name:
                            raise ValueError(
                                f"{class_config.name}.{fn.name} sequence={instruction.sequence}: construct assignment target is unresolved"
                            )
                        value_expr = self._render_value_source_expr(
                            value_source=assignment.value_source,
                            line_context=(
                                f"{class_config.name}.{fn.name} sequence={instruction.sequence} "
                                f"construct assignment {target_name}"
                            ),
                        )
                        value_expr = _receiver_input_expr(value_expr)
                        rendered_args.append(f"{target_name!r}: {value_expr}")
                        rendered_arg_names.add(target_name)
                    target_attribute_names = _class_attribute_names(target_class)
                    for param in sig.params:
                        input_name = _safe_identifier(param.name)
                        if input_name in rendered_arg_names:
                            continue
                        if input_name not in target_attribute_names:
                            continue
                        rendered_args.append(f"{input_name!r}: {input_name}")
                        rendered_arg_names.add(input_name)
                    constructed_name = f"_aware_constructed_{int(instruction.sequence)}"
                    values_name = f"_aware_construct_values_{int(instruction.sequence)}"
                    lines.append(f"{values_name} = {{{', '.join(rendered_args)}}}")
                    stable_ids_module = self._resolve_stable_ids_module_for_class(
                        target_class
                    )
                    if stable_ids_module is not None:
                        runtime_imports.setdefault("importlib", set()).add(
                            "import_module"
                        )
                        runtime_imports.setdefault(stable_ids_module, set()).add(
                            "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID"
                        )
                        binding_name = (
                            f"_aware_stable_binding_{int(instruction.sequence)}"
                        )
                        stable_fn_name = f"_aware_stable_fn_{int(instruction.sequence)}"
                        stable_key_names = (
                            f"_aware_stable_key_names_{int(instruction.sequence)}"
                        )
                        missing_name = (
                            f"_aware_missing_stable_keys_{int(instruction.sequence)}"
                        )
                        identity_values_name = f"_aware_construct_identity_values_{int(instruction.sequence)}"
                        stable_values_name = (
                            f"_aware_stable_values_{int(instruction.sequence)}"
                        )
                        construct_id_name = (
                            f"_aware_construct_id_{int(instruction.sequence)}"
                        )
                        identity_input_args = [
                            f"{_safe_identifier(param.name)!r}: {_safe_identifier(param.name)}"
                            for param in sig.params
                            if _safe_identifier(param.name) not in rendered_arg_names
                        ]
                        if identity_input_args:
                            lines.append(
                                f"{identity_values_name} = {{**{values_name}, "
                                + ", ".join(identity_input_args)
                                + "}"
                            )
                        else:
                            lines.append(f"{identity_values_name} = {values_name}")
                        lines.append(
                            f"{binding_name} = CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID.get({str(target_class.id)!r})"
                        )
                        lines.append(f"if {binding_name} is not None:")
                        lines.append(
                            f"    {stable_fn_name}, {stable_key_names} = {binding_name}"
                        )
                        lines.append(
                            f"    {missing_name} = [key for key in {stable_key_names} if key not in {identity_values_name}]"
                        )
                        lines.append(f"    if {missing_name}:")
                        lines.append(
                            "        raise RuntimeError("
                            + repr(
                                f"{class_config.name}.{fn.name} cannot construct {target_class.name}: "
                                "missing stable identity values"
                            )
                            + f" + f': {{{missing_name}}}')"
                        )
                        lines.append(
                            f"    {stable_values_name} = {{key: {identity_values_name}[key] for key in {stable_key_names}}}"
                        )
                        lines.append(
                            f"    {construct_id_name} = getattr(import_module({stable_ids_module!r}), {stable_fn_name})(**{stable_values_name})"
                        )
                        lines.append(
                            f"    {constructed_name} = {target_class.name}.get_by_id_cached({construct_id_name})"
                        )
                        lines.append(f"    if {constructed_name} is None:")
                        lines.append(
                            f"        {constructed_name} = {target_class.name}(id={construct_id_name}, **{values_name})"
                        )
                        lines.append("else:")
                        lines.append(
                            f"    {constructed_name} = {target_class.name}(**{values_name})"
                        )
                    else:
                        lines.append(
                            f"{constructed_name} = {target_class.name}(**{values_name})"
                        )
                    last_value_expr = constructed_name
                    continue

                if ins_kind == self._enum_token(FunctionImplInstructionType.set):
                    payload = instruction.instruction_set
                    if payload is None:
                        raise ValueError(
                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: missing set payload"
                        )
                    target_link = payload.target_class_config_attribute_config
                    if target_link is None:
                        raise ValueError(
                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: set target link is unresolved"
                        )
                    target_attr = target_link.attribute_config
                    target_name = (
                        _safe_identifier(target_attr.name)
                        if target_attr is not None
                        else ""
                    )
                    if not target_name:
                        raise ValueError(
                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: set target attribute is unresolved"
                        )
                    if fn_link.is_constructor:
                        raise ValueError(
                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: set is only supported on instance functions in renderer v0"
                        )
                    value_expr = self._render_value_source_expr(
                        value_source=payload.value_source,
                        line_context=f"{class_config.name}.{fn.name} sequence={instruction.sequence}",
                    )
                    relationship_fk_name = self._resolve_relationship_foreign_key_name(
                        class_config=class_config,
                        reference_attribute_config_id=target_link.attribute_config_id,
                    )
                    if relationship_fk_name is not None:
                        lines.append(
                            f"{self_name}.{_safe_identifier(relationship_fk_name)} = {value_expr}"
                        )
                        lines.append(f"{self_name}.{target_name} = None")
                    else:
                        lines.append(f"{self_name}.{target_name} = {value_expr}")
                    continue

                if ins_kind == self._enum_token(FunctionImplInstructionType.require):
                    payload = instruction.instruction_require
                    if payload is None:
                        raise ValueError(
                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: missing require payload"
                        )
                    operands = sorted(
                        payload.operands,
                        key=lambda op: (int(op.position), str(op.id)),
                    )
                    rendered_operands = [
                        self._render_value_source_expr(
                            value_source=operand.value_source,
                            line_context=(
                                f"{class_config.name}.{fn.name} sequence={instruction.sequence} "
                                f"require operand {operand.position}"
                            ),
                        )
                        for operand in operands
                    ]
                    require_kind = self._enum_token(payload.kind)
                    condition: str
                    if require_kind == self._enum_token(FunctionImplRequireKind.exists):
                        condition = f"{rendered_operands[0]} is not None"
                    elif require_kind == self._enum_token(
                        FunctionImplRequireKind.equals
                    ):
                        condition = f"{rendered_operands[0]} == {rendered_operands[1]}"
                    elif require_kind == self._enum_token(
                        FunctionImplRequireKind.member
                    ):
                        condition = f"{rendered_operands[0]} in {rendered_operands[1]}"
                    elif require_kind == self._enum_token(
                        FunctionImplRequireKind.unique
                    ):
                        condition = f"len(set({rendered_operands[0]})) == len({rendered_operands[0]})"
                    elif require_kind == self._enum_token(
                        FunctionImplRequireKind.compare
                    ):
                        op_map = {
                            self._enum_token(
                                FunctionImplRequireCompareOperator.eq
                            ): "==",
                            self._enum_token(
                                FunctionImplRequireCompareOperator.neq
                            ): "!=",
                            self._enum_token(
                                FunctionImplRequireCompareOperator.gt
                            ): ">",
                            self._enum_token(
                                FunctionImplRequireCompareOperator.gte
                            ): ">=",
                            self._enum_token(
                                FunctionImplRequireCompareOperator.lt
                            ): "<",
                            self._enum_token(
                                FunctionImplRequireCompareOperator.lte
                            ): "<=",
                        }
                        compare_op = op_map.get(
                            self._enum_token(payload.compare_operator)
                        )
                        if compare_op is None:
                            raise ValueError(
                                f"{class_config.name}.{fn.name} sequence={instruction.sequence}: unsupported compare operator"
                            )
                        condition = f"{rendered_operands[0]} {compare_op} {rendered_operands[1]}"
                    elif require_kind == self._enum_token(
                        FunctionImplRequireKind.cardinality
                    ):
                        op_map = {
                            self._enum_token(
                                FunctionImplRequireCompareOperator.eq
                            ): "==",
                            self._enum_token(
                                FunctionImplRequireCompareOperator.neq
                            ): "!=",
                            self._enum_token(
                                FunctionImplRequireCompareOperator.gt
                            ): ">",
                            self._enum_token(
                                FunctionImplRequireCompareOperator.gte
                            ): ">=",
                            self._enum_token(
                                FunctionImplRequireCompareOperator.lt
                            ): "<",
                            self._enum_token(
                                FunctionImplRequireCompareOperator.lte
                            ): "<=",
                        }
                        compare_op = op_map.get(
                            self._enum_token(payload.compare_operator)
                        )
                        if compare_op is None or payload.expected_count is None:
                            raise ValueError(
                                f"{class_config.name}.{fn.name} sequence={instruction.sequence}: cardinality require is missing operator/expected_count"
                            )
                        condition = f"len({rendered_operands[0]}) {compare_op} {int(payload.expected_count)}"
                    elif require_kind == self._enum_token(
                        FunctionImplRequireKind.all_or_none
                    ):
                        terms = ", ".join(rendered_operands)
                        condition = f"(all([{terms}]) or not any([{terms}]))"
                    elif require_kind == self._enum_token(
                        FunctionImplRequireKind.text_matches_regex
                    ):
                        if len(rendered_operands) != 2:
                            raise ValueError(
                                f"{class_config.name}.{fn.name} sequence={instruction.sequence}: "
                                "text_matches_regex expects two operands"
                            )
                        condition = (
                            f"__import__('re').fullmatch({rendered_operands[1]}, "
                            f"{rendered_operands[0]}) is not None"
                        )
                    else:
                        raise ValueError(
                            f"{class_config.name}.{fn.name} sequence={instruction.sequence}: unsupported require kind {require_kind!r}"
                        )

                    message = payload.message or (
                        f"{class_config.name}.{fn.name} require {require_kind} failed"
                    )
                    lines.append(f"if not ({condition}):")
                    lines.append(f"    raise RuntimeError({repr(message)})")
                    continue

                raise ValueError(
                    f"{class_config.name}.{fn.name} sequence={instruction.sequence}: unsupported instruction type {ins_kind!r}"
                )
        except Exception as exc:
            self._warnings.append(
                f"FunctionImpl renderer fallback to manual logic for {class_config.name}.{fn.name}: {exc}"
            )
            return None

        if not instructions:
            if fn_link.is_constructor:
                _require_class_import(class_config)
                ctor_kw_pairs = [
                    f"{_safe_identifier(edge.attribute_config.name)}={_safe_identifier(edge.attribute_config.name)}"
                    for edge in input_edges
                ]
                input_names = {
                    _safe_identifier(edge.attribute_config.name)
                    for edge in input_edges
                    if edge.attribute_config is not None
                }
                stable_ids_module = self._resolve_stable_ids_module_for_class(
                    class_config
                )
                if stable_ids_module is not None:
                    constructor_id_expr = _ensure_constructor_self_id(
                        f"{class_config.name}.{fn.name}"
                    )
                    ctor_kw_pairs.insert(0, f"id={constructor_id_expr}")
                relationship_kwargs = self._emit_constructor_relationship_hydration(
                    lines=lines,
                    runtime_imports=runtime_imports,
                    class_config=class_config,
                    input_names=input_names,
                    line_context=f"{class_config.name}.{fn.name}",
                )
                ctor_kw_pairs.extend(
                    f"{name}={expr}"
                    for name, expr in sorted(relationship_kwargs.items())
                )
                ctor_args = ", ".join(ctor_kw_pairs)
                if ctor_args:
                    lines.append(f"return {class_config.name}({ctor_args})")
                else:
                    lines.append(f"return {class_config.name}()")
                has_return_stmt = True
            elif expects_return and sig.return_type == class_config.name:
                lines.append(f"return {self_name}")
                has_return_stmt = True
            else:
                return None

        if any(line.strip().startswith("return ") for line in lines):
            has_return_stmt = True

        if expects_return and not has_return_stmt:
            captured = [
                _safe_identifier(name)
                for _, name in sorted(
                    capture_name_by_sequence.items(), key=lambda kv: kv[0]
                )
                if name
            ]
            if last_value_expr is not None:
                lines.append(f"return {last_value_expr}")
            elif captured:
                lines.append(f"return {captured[-1]}")
            elif sig.return_type == class_config.name and not fn_link.is_constructor:
                lines.append(f"return {self_name}")
            else:
                lines.append(
                    "raise RuntimeError("
                    + repr(
                        f"{class_config.name}.{fn.name} cannot resolve deterministic return value from FunctionImpl instructions"
                    )
                    + ")"
                )

        return _GeneratedImplLogic(
            body="\n".join(lines),
            runtime_imports=runtime_imports,
        )

    def _build_generated_impl_logic_from_invocations(
        self,
        *,
        class_config: ClassConfig,
        fn_link: ClassConfigFunctionConfig,
        fn: FunctionConfig,
    ) -> _GeneratedImplLogic | None:
        """
        Build deterministic logic from canonical invocation rails when FunctionImpl/body
        is unavailable in the derived graph payload.

        Contract:
        - No guessing: target function must resolve by stable id.
        - Args bind only by exact input-name match.
        - Missing required constructor args fail closed.
        """

        invocations = sorted(
            fn.invocations, key=lambda inv: (int(inv.position), str(inv.id))
        )
        sig = self._render_signature(fn=fn)
        expects_return = sig.return_type != "None"
        self_name = _safe_identifier(to_snake_case(class_config.name))
        runtime_imports: dict[str, set[str]] = {}
        lines: list[str] = []

        signature_input_names = {param.name for param in sig.params}

        def _require_class_import(target_class: ClassConfig | None) -> None:
            if target_class is None:
                return
            module = (self.import_overrides or {}).get(str(target_class.id))
            if module:
                runtime_imports.setdefault(module, set()).add(target_class.name)

        def _fallback_constructor_self_id_expr() -> str | None:
            stable_ids_module = self._resolve_stable_ids_module_for_class(class_config)
            if stable_ids_module is None:
                return None
            runtime_imports.setdefault("importlib", set()).add("import_module")
            runtime_imports.setdefault(stable_ids_module, set()).add(
                "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID"
            )
            input_names = [
                _safe_identifier(edge.attribute_config.name)
                for edge in fn.function_config_attribute_configs
                if edge.type == FunctionAttributeType.input
                and edge.attribute_config is not None
            ]
            values_expr = ", ".join(f"{name!r}: {name}" for name in input_names)
            lines.append(f"_aware_self_values = {{{values_expr}}}")
            lines.append(
                "_aware_self_binding = "
                "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID.get("
                + f"{str(class_config.id)!r})"
            )
            lines.append("if _aware_self_binding is None:")
            lines.append(
                "    raise RuntimeError("
                + repr(
                    f"{class_config.name}.{fn.name} cannot resolve constructor self id: "
                    "missing stable-id binding"
                )
                + ")"
            )
            lines.append("_aware_self_fn, _aware_self_key_names = _aware_self_binding")
            lines.append(
                "_aware_missing_self_keys = ["
                "key for key in _aware_self_key_names "
                "if key not in _aware_self_values"
                "]"
            )
            lines.append("if _aware_missing_self_keys:")
            lines.append(
                "    raise RuntimeError("
                + repr(
                    f"{class_config.name}.{fn.name} cannot resolve constructor self id: "
                    "missing stable identity values"
                )
                + " + f': {_aware_missing_self_keys}')"
            )
            lines.append(
                "_aware_self_stable_values = {"
                "key: getattr(_aware_self_values[key], 'value', _aware_self_values[key]) "
                "for key in _aware_self_key_names"
                "}"
            )
            lines.append(
                "_aware_self_id = getattr("
                f"import_module({stable_ids_module!r}), _aware_self_fn"
                ")(**_aware_self_stable_values)"
            )
            return "_aware_self_id"

        if not invocations:
            if fn_link.is_constructor:
                _require_class_import(class_config)
                constructor_input_edges = [
                    edge
                    for edge in fn.function_config_attribute_configs
                    if edge.type == FunctionAttributeType.input
                    and edge.attribute_config is not None
                ]
                ctor_kw_pairs = [
                    f"{_safe_identifier(edge.attribute_config.name)}={_safe_identifier(edge.attribute_config.name)}"
                    for edge in constructor_input_edges
                ]
                constructor_id_expr = _fallback_constructor_self_id_expr()
                if constructor_id_expr is not None:
                    ctor_kw_pairs.insert(0, f"id={constructor_id_expr}")
                relationship_kwargs = self._emit_constructor_relationship_hydration(
                    lines=lines,
                    runtime_imports=runtime_imports,
                    class_config=class_config,
                    input_names={
                        _safe_identifier(edge.attribute_config.name)
                        for edge in constructor_input_edges
                    },
                    line_context=f"{class_config.name}.{fn.name}",
                )
                ctor_kw_pairs.extend(
                    f"{name}={expr}"
                    for name, expr in sorted(relationship_kwargs.items())
                )
                ctor_args = ", ".join(ctor_kw_pairs)
                if ctor_args:
                    lines.append(f"return {class_config.name}({ctor_args})")
                else:
                    lines.append(f"return {class_config.name}()")
                return _GeneratedImplLogic(
                    body="\n".join(lines), runtime_imports=runtime_imports
                )
            if expects_return and sig.return_type == class_config.name:
                lines.append(f"return {self_name}")
                return _GeneratedImplLogic(
                    body="\n".join(lines), runtime_imports=runtime_imports
                )
            return None

        captured: list[str] = []
        for inv in invocations:
            kind = self._enum_token(inv.kind)
            if kind != self._enum_token(FunctionInvocationKind.construct):
                raise ValueError(
                    f"{class_config.name}.{fn.name} invocation fallback only supports construct rows "
                    f"(got {kind!r} at position={inv.position})"
                )

            target_fn = inv.target_function_config or self._function_by_id.get(
                inv.target_function_config_id
            )
            if target_fn is None:
                raise ValueError(
                    f"{class_config.name}.{fn.name} cannot resolve target function id={inv.target_function_config_id}"
                )
            target_owner = self._owner_by_function_id.get(target_fn.id)
            target_link = self._link_by_function_id.get(target_fn.id)
            if target_owner is None or target_link is None:
                raise ValueError(
                    f"{class_config.name}.{fn.name} cannot resolve owner/link for target {target_fn.name}"
                )
            if not target_link.is_constructor:
                raise ValueError(
                    f"{class_config.name}.{fn.name} construct invocation target {target_owner.name}.{target_fn.name} "
                    "is not a constructor"
                )

            _require_class_import(target_owner)
            source_class = class_config
            relationship = inv.class_config_relationship
            if relationship is not None:
                if fn_link.is_constructor:
                    raise ValueError(
                        f"{class_config.name}.{fn.name} relationship construct "
                        "requires instance context"
                    )
                rel_source_id = getattr(relationship, "class_config_id", None)
                if rel_source_id is not None:
                    rel_source = self._class_by_id.get(rel_source_id)
                    if rel_source is not None:
                        source_class = rel_source

            target_inputs = sorted(
                [
                    edge
                    for edge in target_fn.function_config_attribute_configs
                    if edge.type == FunctionAttributeType.input
                    and edge.attribute_config is not None
                ],
                key=lambda edge: (int(edge.position), str(edge.id)),
            )

            rendered_args: list[str] = []
            for edge in target_inputs:
                target_name = _safe_identifier(edge.attribute_config.name)
                if target_name in signature_input_names:
                    rendered_args.append(f"{target_name}={target_name}")
                    continue
                # Canonical propagation rail: `_via_<owner>` constructors receive owner identity
                # from the invoking instance (`self`) through `<owner>_id`.
                source_id_param = _safe_identifier(
                    f"{to_snake_case(source_class.name)}_id"
                )
                if (
                    not fn_link.is_constructor
                    and source_class.id == class_config.id
                    and target_name == source_id_param
                ):
                    rendered_args.append(f"{target_name}={self_name}.id")
                    continue
                # No explicit binding rail on invocation rows; if target input has no default
                # and no same-name source input, this fallback must fail closed.
                type_info = resolve_type_info(edge.attribute_config)
                default_expr = self._render_default_expr(
                    edge.attribute_config, type_info=type_info
                )
                if default_expr is None:
                    raise ValueError(
                        f"{class_config.name}.{fn.name} missing required constructor arg '{target_name}' "
                        f"for {target_owner.name}.{target_fn.name}"
                    )

            args_text = ", ".join(rendered_args)
            call_expr = (
                f"await {target_owner.name}.{target_fn.name}({args_text})"
                if args_text
                else f"await {target_owner.name}.{target_fn.name}()"
            )

            capture_name = _safe_identifier(inv.capture_name or "")
            if relationship is not None:
                constructed_expr = (
                    capture_name
                    if capture_name
                    else f"_aware_constructed_invocation_{int(inv.position)}"
                )
                lines.append(f"{constructed_expr} = {call_expr}")
                self._append_relationship_construct_attachment(
                    lines=lines,
                    receiver_expr=self_name,
                    relationship=relationship,
                    constructed_expr=constructed_expr,
                    attachment_key=f"invocation_{int(inv.position)}",
                    line_context=(
                        f"{class_config.name}.{fn.name} "
                        f"invocation position={inv.position}"
                    ),
                )
                captured.append(constructed_expr)
            elif capture_name:
                lines.append(f"{capture_name} = {call_expr}")
                captured.append(capture_name)
            else:
                lines.append(call_expr)

        has_return = any(line.strip().startswith("return ") for line in lines)
        if expects_return and not has_return:
            if captured:
                lines.append(f"return {captured[-1]}")
            elif sig.return_type == class_config.name and not fn_link.is_constructor:
                lines.append(f"return {self_name}")
            else:
                raise ValueError(
                    f"{class_config.name}.{fn.name} cannot resolve deterministic return value from invocation fallback"
                )

        return _GeneratedImplLogic(
            body="\n".join(lines), runtime_imports=runtime_imports
        )

    def _render_signature(
        self,
        *,
        fn: FunctionConfig,
    ) -> _RenderedSignature:
        input_edges = [
            e
            for e in fn.function_config_attribute_configs
            if e.type == FunctionAttributeType.input
        ]
        output_edges = [
            e
            for e in fn.function_config_attribute_configs
            if e.type == FunctionAttributeType.output
        ]
        input_edges.sort(key=lambda e: int(e.position))
        output_edges.sort(key=lambda e: int(e.position))

        params: list[_RenderedParam] = []
        for edge in input_edges:
            attr = edge.attribute_config
            assert attr is not None
            name = _safe_identifier(attr.name)
            type_info = resolve_type_info(attr)
            type_annotation = self._render_type_annotation(attr, type_info=type_info)
            default_expr = self._render_default_expr(attr, type_info=type_info)
            type_id, type_name = self._type_ref_from_info(type_info)
            params.append(
                _RenderedParam(
                    name=name,
                    type_annotation=type_annotation,
                    default_expr=default_expr,
                    type_id=type_id,
                    type_name=type_name,
                )
            )

        # Return type: prefer single output, otherwise None/Any.
        return_type = "None"
        return_type_id: UUID | None = None
        return_type_name: str | None = None
        if len(output_edges) == 1:
            out_attr = output_edges[0].attribute_config
            assert out_attr is not None
            type_info = resolve_type_info(out_attr)
            return_type = self._render_type_annotation(out_attr, type_info=type_info)
            return_type_id, return_type_name = self._type_ref_from_info(type_info)
        elif len(output_edges) > 1:
            return_type = "dict[str, Any]"

        return _RenderedSignature(
            params=params,
            return_type=return_type,
            return_type_id=return_type_id,
            return_type_name=return_type_name,
        )

    def _render_type_annotation(
        self, attr: AttributeConfig, *, type_info: AttributeTypeInfo | None = None
    ) -> str:
        type_info = type_info or resolve_type_info(attr)

        base_type = "Any"
        if (
            type_info.kind == AttributeTypeDescriptorKind.primitive
            and type_info.primitive_config
        ):
            prim = CodePrimitiveType.model_validate(
                type_info.primitive_config.primitive_type
            )
            base_type = _PRIMITIVE_CODEC.render(prim) or "Any"
        elif (
            type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config
        ):
            base_type = type_info.enum_config.name
        elif (
            type_info.kind == AttributeTypeDescriptorKind.class_
            and type_info.class_config
        ):
            base_type = type_info.class_config.name

        type_annotation = base_type
        if type_info.is_collection:
            type_annotation = f"list[{type_annotation}]"

        # Nullable if explicitly optional (default_value parses to null) or non-required.
        nullable = False
        if attr.is_required is False:
            nullable = True
        if attr.default_value is not None:
            try:
                if json.loads(attr.default_value) is None:
                    nullable = True
            except Exception:
                pass

        if nullable and not type_info.is_collection:
            type_annotation = f"{type_annotation} | None"
        return type_annotation

    def _render_default_expr(
        self,
        attr: AttributeConfig,
        *,
        type_info: AttributeTypeInfo | None = None,
    ) -> str | None:
        type_info = type_info or resolve_type_info(attr)
        if attr.default_value is not None:
            default_value = cast(object, json.loads(attr.default_value))
            if (
                type_info.kind == AttributeTypeDescriptorKind.enum
                and type_info.enum_config
            ):
                if default_value is None or default_value in {"NULL", "None"}:
                    return "None"
                return f"{type_info.enum_config.name}.{default_value}"
            return _PRIMITIVE_CODEC.to_literal_string(default_value)

        # If optional, default to None.
        if attr.is_required is False:
            return "None"

        # No default.
        return None

    def _type_ref_from_info(
        self, type_info: AttributeTypeInfo
    ) -> tuple[UUID | None, str | None]:
        if (
            type_info.kind == AttributeTypeDescriptorKind.class_
            and type_info.class_config
        ):
            return type_info.class_config.id, type_info.class_config.name
        if type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config:
            return type_info.enum_config.id, type_info.enum_config.name
        return None, None

    def _collect_type_imports(
        self, imports: dict[str, set[str]], *, type_annotation: str
    ) -> None:
        # Very small parser: extract identifiers that are likely class/enum names.
        # We rely on `import_overrides` to provide module paths for ClassConfig/EnumConfig ids.
        tokens: list[str] = []
        buf = ""
        for ch in type_annotation:
            if ch.isalnum() or ch == "_":
                buf += ch
            else:
                if buf:
                    tokens.append(buf)
                    buf = ""
        if buf:
            tokens.append(buf)

        # Skip builtins/typing primitives.
        skip = {
            "Any",
            "None",
            "str",
            "int",
            "float",
            "bool",
            "list",
            "dict",
            "tuple",
            "set",
        }
        for tok in tokens:
            if tok in skip:
                continue

            # Best-effort: resolve class/enum module from the graph indexes.
            mod = self._resolve_type_module_by_name(tok)
            if mod:
                imports.setdefault(mod, set()).add(tok)

    def _collect_type_imports_by_id(
        self,
        imports: dict[str, set[str]],
        *,
        type_id: UUID | None,
        type_name: str | None,
    ) -> None:
        if not type_id or not type_name:
            return
        mod = self._resolve_type_module_by_id(type_id)
        if mod:
            imports.setdefault(mod, set()).add(type_name)

    def _resolve_type_module_by_id(self, type_id: UUID | None) -> str | None:
        if type_id is None:
            return None
        return (self.import_overrides or {}).get(str(type_id))

    def _resolve_type_module_by_name(self, name: str) -> str | None:
        # Built-in library types (not part of the OCG).
        if name == "datetime":
            return "datetime"
        if name == "UUID":
            return "uuid"

        # AWARE primitive helper types.
        if name in {
            "Json",
            "JsonArray",
            "JsonObject",
            "JsonValue",
            "Vector",
            "VectorDim",
        }:
            return "aware_code.types"

        # Try local class configs
        for cc in self._class_by_id.values():
            if cc.name == name:
                mod = (self.import_overrides or {}).get(str(cc.id))
                return mod

        enum_id = self._enum_id_by_name.get(name)
        if enum_id is not None:
            return (self.import_overrides or {}).get(str(enum_id))

        return None

    # ---------------------------------------------------------------------
    # Generated wrapper module
    # ---------------------------------------------------------------------
    def _emit_generated_handlers_file(self, *, writer: CodeSectionWriter) -> None:
        _emit_token(writer, "# This file is generated by AWARE. Do not edit.\n")
        _emit_token(writer, "from __future__ import annotations\n\n")

        # Stable ordering: class name then function position then function name.
        entries: list[
            tuple[str, int, str, ClassConfig, ClassConfigFunctionConfig, FunctionConfig]
        ] = []
        class_pool = (
            list(self._rendered_class_by_id.values())
            if self._rendered_class_by_id
            else list(self._class_by_id.values())
        )
        impl_name_by_fn = dict(self._impl_name_by_function_id)
        for owner in class_pool:
            fn_links = sorted(
                owner.class_config_function_configs,
                key=lambda link: (link.position, str(link.function_config_id)),
            )
            impl_name_by_fn.update(
                self._compute_impl_names_for_class(fn_links=fn_links)
            )
            for link in fn_links:
                fn = link.function_config
                pos = link.position
                entries.append((owner.name, pos, str(fn.id), owner, link, fn))
        entries.sort(key=lambda t: (t[0], t[1], t[2]))

        has_constructor = any(link.is_constructor for _, _, _, _, link, _ in entries)
        has_instance = any(not link.is_constructor for _, _, _, _, link, _ in entries)
        needs_cast = False
        for _, _, _, _, _, fn in entries:
            for edge in fn.function_config_attribute_configs:
                if edge.type != FunctionAttributeType.input:
                    continue
                attr = edge.attribute_config
                if "| None" in self._render_type_annotation(attr):
                    needs_cast = True
                    break
            if needs_cast:
                break
        imports: dict[str, set[str]] = {}
        if entries:
            typing_symbols = {"TYPE_CHECKING"}
            if needs_cast:
                typing_symbols.add("cast")
            imports["typing"] = typing_symbols
            declarative_symbols: set[str] = set()
            if has_constructor:
                declarative_symbols.add("constructor")
            if has_instance:
                declarative_symbols.add("instance")
            if declarative_symbols:
                imports["aware_meta.runtime.generated_handlers"] = declarative_symbols
        if imports:
            self._emit_grouped_imports(writer=writer, imports=imports)
        if entries:
            _emit_token(writer, "if TYPE_CHECKING:\n")
            _emit_token(
                writer,
                "    from aware_meta_ontology.function.function_call import FunctionCall\n",
            )
            _emit_token(writer, "    from aware_orm.models.orm_model import ORMModel\n")
            _emit_token(writer, "    from aware_orm.session.session import Session\n")
            _emit_token(
                writer,
                "    from aware_meta.runtime.generated_handlers import HandlerContext\n\n",
            )

        handler_rows: list[str] = []
        for _owner_name, _pos, _fn_id_str, owner, link, fn in entries:
            snake_class = to_snake_case(owner.name)
            impl_mod = runtime_handler_impl_module_import(
                layout_strategy=self.layout_strategy,
                class_config=owner,
                import_root=self._runtime_handlers_import_root(),
            )
            impl_fn = impl_name_by_fn.get(fn.id, _safe_identifier(fn.name))
            wrapper_name = f"{snake_class}__{fn.name}__handler"
            wrapper_name = _safe_identifier(wrapper_name)

            class_fqn = self._class_fqn(owner)

            self._emit_wrapper_function(
                writer=writer,
                wrapper_name=wrapper_name,
                impl_module=impl_mod,
                impl_function=impl_fn,
                class_config=owner,
                fn_link=link,
                fn=fn,
            )
            _emit_token(writer, "\n\n")

            if link.is_constructor:
                handler_rows.append(
                    f"    constructor({class_fqn!r}, {fn.name!r}, {wrapper_name}),"
                )
            else:
                handler_rows.append(
                    f"    instance({class_fqn!r}, {fn.name!r}, {wrapper_name}),"
                )

        _emit_token(writer, "AWARE_HANDLERS = [\n")
        for row in handler_rows:
            _emit_token(writer, f"{row}\n")
        _emit_token(writer, "]\n\n")
        _emit_token(writer, '__all__ = ["AWARE_HANDLERS"]\n')

    def _emit_wrapper_function(
        self,
        *,
        writer: CodeSectionWriter,
        wrapper_name: str,
        impl_module: str,
        impl_function: str,
        class_config: ClassConfig,
        fn_link: ClassConfigFunctionConfig,
        fn: FunctionConfig,
    ) -> None:
        sig = self._render_signature(fn=fn)
        input_edges = [
            e
            for e in fn.function_config_attribute_configs
            if e.type == FunctionAttributeType.input
        ]
        input_edges.sort(key=lambda e: int(e.position))

        # Wrapper signature is internal to the runtime registry: do not change.
        if fn_link.is_constructor:
            header = (
                "async def {name}(session: Session, ctx: HandlerContext, orm_class: type[ORMModel], "
                "args: list[object], kwargs: dict[str, object], function_call: FunctionCall) "
                "-> tuple[ORMModel, object]:\n"
            ).format(name=wrapper_name)
            ignored_params = "session, ctx, orm_class, kwargs, function_call"
        else:
            header = (
                "async def {name}(session: Session, ctx: HandlerContext, orm_model: ORMModel, "
                "args: list[object], kwargs: dict[str, object], function_call: FunctionCall) -> object:\n"
            ).format(name=wrapper_name)
            ignored_params = "session, ctx, kwargs, function_call"
        _emit_token(writer, header)
        iw = _IndentWriter(writer, indent_size=self.indent)
        with iw.indent():
            iw.write(f"_ = {ignored_params}\n")

            # Local imports keep handler manifest building light (no ontology import at import time).
            if input_edges:
                iw.write("from pydantic import TypeAdapter\n")
            iw.write(f"from {impl_module} import {impl_function} as _impl\n")

            # Import types needed for TypeAdapter expressions.
            needed_imports: dict[str, set[str]] = {}
            for p in sig.params:
                self._collect_type_imports(
                    needed_imports, type_annotation=p.type_annotation
                )
                self._collect_type_imports_by_id(
                    needed_imports,
                    type_id=p.type_id,
                    type_name=p.type_name,
                )
            needed_imports = _normalize_runtime_handler_imports(needed_imports)
            for module, symbols in sorted(needed_imports.items(), key=lambda kv: kv[0]):
                if not module or not symbols:
                    continue
                joined = ", ".join(sorted(symbols))
                iw.write(f"from {module} import {joined}\n")

            # Bind inputs
            for idx, edge in enumerate(input_edges):
                attr = edge.attribute_config
                assert attr is not None
                name = _safe_identifier(attr.name)
                type_annotation = self._render_type_annotation(attr)
                default_expr = self._render_default_expr(attr)

                iw.write(f"_raw_{name}: object | None = None\n")
                iw.write(f"if {json.dumps(attr.name)} in kwargs:\n")
                with iw.indent():
                    iw.write(f"_raw_{name} = kwargs[{json.dumps(attr.name)}]\n")
                iw.write("elif len(args) > {idx}:\n".format(idx=idx))
                with iw.indent():
                    iw.write(f"_raw_{name} = args[{idx}]\n")
                if default_expr is not None:
                    iw.write(f"if _raw_{name} is None:\n")
                    with iw.indent():
                        iw.write(f"_raw_{name} = {default_expr}\n")
                if "| None" in type_annotation:
                    validated_expr = (
                        f"TypeAdapter({type_annotation}).validate_python(_raw_{name})"
                    )
                    iw.write(
                        f"{name}: {type_annotation} = cast({type_annotation}, {validated_expr})\n"
                    )
                else:
                    iw.write(
                        f"{name}: {type_annotation} = TypeAdapter({type_annotation}).validate_python(_raw_{name})\n"
                    )

            # Invoke
            if fn_link.is_constructor:
                call_args = ", ".join(
                    f"{_safe_identifier(e.attribute_config.name)}={_safe_identifier(e.attribute_config.name)}"
                    for e in input_edges
                )  # type: ignore[union-attr]
                iw.write(
                    f"result = await _impl({call_args})\n"
                    if call_args
                    else "result = await _impl()\n"
                )
                iw.write("return result, result\n")
            else:
                self_name = _safe_identifier(to_snake_case(class_config.name))
                call_args = ", ".join(
                    f"{_safe_identifier(e.attribute_config.name)}={_safe_identifier(e.attribute_config.name)}"
                    for e in input_edges
                )  # type: ignore[union-attr]
                if call_args:
                    iw.write(
                        f"result = await _impl({self_name}=orm_model, {call_args})\n"
                    )
                else:
                    iw.write(f"result = await _impl({self_name}=orm_model)\n")
                iw.write("return result\n")

    def _runtime_handlers_import_root(self) -> str:
        # Runtime handler materializations write into a package rooted at the graph fqn_prefix.
        # Import overrides should use that as the package name.
        base = self.layout_strategy.import_root
        if base:
            return base
        # Fall back to parsing from base_dir (best-effort).
        return ""

    def _schema_for_class(self, cc: ClassConfig) -> str:
        rel = runtime_handler_impl_relative_path(
            layout_strategy=self.layout_strategy,
            class_config=cc,
        )
        parts = rel.parts
        try:
            idx = parts.index("impl")
            return parts[idx + 1]
        except Exception:
            return "default"

    def _safe_runtime_impl_path(self, rel: Path) -> Path:
        parts = list(rel.parts)
        if not parts:
            return rel
        if "impl" in parts:
            idx = parts.index("impl") + 1
        else:
            idx = 0
        if idx >= len(parts):
            return rel

        # Keyword-safe module segments for schema/subpackages.
        for seg_idx in range(idx, len(parts) - 1):
            parts[seg_idx] = _safe_identifier(parts[seg_idx])

        # Keyword-safe file stem for `from ... import ...` module imports.
        file_name = parts[-1]
        file_path = Path(file_name)
        if file_path.suffix:
            safe_stem = _safe_identifier(file_path.stem)
            parts[-1] = f"{safe_stem}{file_path.suffix}"
        else:
            parts[-1] = _safe_identifier(file_name)
        return Path(*parts)

    def _class_fqn(self, cc: ClassConfig) -> str:
        module = (self.import_overrides or {}).get(str(cc.id))
        if module:
            return f"{module}.{cc.name}"
        return f"{cc.name}"

    def _merge_imports(self, *imports: dict[str, set[str]]) -> dict[str, set[str]]:
        merged: dict[str, set[str]] = {}
        for bucket in imports:
            for module, symbols in _normalize_runtime_handler_imports(bucket).items():
                if not module or not symbols:
                    continue
                merged.setdefault(module, set()).update(symbols)
        return merged

    def _emit_grouped_imports(
        self, *, writer: CodeSectionWriter, imports: dict[str, set[str]]
    ) -> None:
        if not imports:
            return
        package_groups = group_python_imports(
            imports,
            policy=PythonImportGroupingPolicy(
                semantic_import_roots=semantic_import_roots_from_renderer_inputs(
                    import_root=self.layout_strategy.import_root,
                    import_overrides=self.import_overrides,
                    external_graph_fqn_prefixes=(
                        graph.fqn_prefix for graph in self.external_graphs
                    ),
                ),
                support_import_roots=DEFAULT_ORM_SUPPORT_IMPORT_ROOTS,
            ),
        )
        for package_name, package_imports in package_groups.items():
            if package_name:
                _emit_token(writer, f"# {package_name.replace('_', ' ')}\n")

            def _module_sort_key(m: str) -> tuple[int, str]:
                return (0, m) if m.endswith("_enums") else (1, m)

            for module in sorted(package_imports.keys(), key=_module_sort_key):
                items = sorted(package_imports[module])
                _emit_token(
                    writer, self._render_from_import(module=module, items=items)
                )
            _emit_token(writer, "\n")

    def _render_from_import(self, *, module: str, items: list[str]) -> str:
        items_str = self._render_import_items(items, multiline=len(items) > 1)
        first_line_item = items_str.split("\n", 1)[0]
        import_line = f"from {module} import {first_line_item}"
        if len(import_line) <= _MAX_IMPORT_LINE_LENGTH:
            return f"from {module} import {items_str}\n"

        multiline_items = self._render_import_items(items, multiline=True)
        if len(f"from {module} import (") <= _MAX_IMPORT_LINE_LENGTH:
            return f"from {module} import {multiline_items}\n"

        wrapped_items = self._render_import_items(items, multiline=True, nested=True)
        return self._render_wrapped_from_import_module(
            module=module,
            items_str=wrapped_items,
        )

    def _render_import_items(
        self,
        items: list[str],
        *,
        multiline: bool,
        nested: bool = False,
    ) -> str:
        if not items:
            return ""
        if not multiline:
            return items[0]
        item_indent = "        " if nested else "    "
        close_indent = "    " if nested else ""
        return (
            "(\n"
            + "".join([f"{item_indent}{item},\n" for item in items])
            + f"{close_indent})"
        )

    def _render_wrapped_from_import_module(
        self,
        *,
        module: str,
        items_str: str,
    ) -> str:
        parts = module.split(".")
        if len(parts) <= 1:
            return f"from {module} import {items_str}\n"

        first_line_item = items_str.split("\n", 1)[0]
        lines: list[str] = []
        current = f"from {parts[0]}"
        for index, part in enumerate(parts[1:], start=1):
            is_last = index == len(parts) - 1
            suffix = f" import {first_line_item}" if is_last else ".\\"
            candidate = f"{current}.{part}"
            if (
                len(candidate + suffix) > _MAX_IMPORT_LINE_LENGTH
                and current != f"from {parts[0]}"
            ):
                lines.append(f"{current}.\\")
                current = f"    {part}"
            else:
                current = candidate

        lines.append(f"{current} import {items_str}")
        return "\n".join(lines) + "\n"


__all__ = ["PythonRendererRuntimeHandlersAware"]
