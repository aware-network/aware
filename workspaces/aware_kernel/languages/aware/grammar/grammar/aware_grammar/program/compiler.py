from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Literal, cast
from uuid import UUID

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE
from typing_extensions import override

from aware_grammar.primitive_codec import AWARE_TO_BASE_MAPPING, AwarePrimitiveCodec
from aware_grammar.program.ast import (
    ProgramCall,
    ProgramCallArg,
    ProgramDeclaration,
    ProgramExpectEventConfig,
    ProgramExpr,
    ProgramInput,
    ProgramIntentActionConfig,
    ProgramLet,
    ProgramRef,
)
from aware_grammar.program.parser import parse_program_declarations
from aware_grammar.program.plan import (
    InvocationPlan,
    PlanActorContract,
    PlanCall,
    PlanCallArg,
    PlanExpectEventConfig,
    PlanExpr,
    PlanInput,
    PlanInvoke,
    PlanIntentActionConfig,
    PlanLet,
    PlanLocalRef,
    PlanPortContract,
    PlanPortProjectionNodeContract,
    PlanPortProjectionNodeKey,
    PlanStep,
    PlanValue,
    PlanSymbolRef,
)


@dataclass(frozen=True, slots=True)
class ProgramCompileError(ValueError):
    message: str

    @override
    def __str__(self) -> str:  # pragma: no cover (tiny convenience)
        return self.message


ProgramConfigInstructionType = Literal[
    "input",
    "let",
    "bind",
    "invoke",
    "expect",
    "intent",
]
ProgramInvokeTargetKind = Literal["instance", "construct"]
ProgramSlotOnBind = Literal["replace", "if_empty", "sticky"]


@dataclass(frozen=True, slots=True)
class ProgramConfigInstructionInputAttribute:
    attribute_ref: str
    position: int | None = None
    required: bool = True


@dataclass(frozen=True, slots=True)
class ProgramConfigInstructionInputPayload:
    name: str
    source: str
    required: bool = True
    default_expr: PlanExpr | None = None
    type_ref: str | None = None
    attribute_configs: tuple[ProgramConfigInstructionInputAttribute, ...] = ()


@dataclass(frozen=True, slots=True)
class ProgramConfigInstructionLetPayload:
    name: str
    value_expr: PlanExpr


@dataclass(frozen=True, slots=True)
class ProgramConfigInstructionBindPayload:
    port_ref: PlanExpr
    view_key: str
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class ProgramConfigInstructionInvokePayload:
    function_ref: str
    actor_ref: PlanExpr
    object_ref: PlanExpr
    target_kind: ProgramInvokeTargetKind = "instance"
    args: tuple[PlanCallArg, ...] = ()


@dataclass(frozen=True, slots=True)
class ProgramConfigInstructionExpectPayload:
    event_config_ref: PlanExpr
    required: bool = True


@dataclass(frozen=True, slots=True)
class ProgramConfigInstructionIntentPayload:
    action_config_ref: PlanExpr
    event_config_ref: PlanExpr


@dataclass(frozen=True, slots=True)
class ProgramConfigPortNodeArg:
    name: str
    value_expr: PlanExpr


@dataclass(frozen=True, slots=True)
class ProgramConfigPortProjectionNodeIdentityContract:
    key: str
    identity: str | None = None
    node: str | None = None
    args: tuple[ProgramConfigPortNodeArg, ...] = ()


@dataclass(frozen=True, slots=True)
class ProgramConfigPortContract:
    key: str
    projection: str
    projection_node_identities: tuple[
        ProgramConfigPortProjectionNodeIdentityContract, ...
    ] = ()
    intent: str | None = None


@dataclass(frozen=True, slots=True)
class ProgramConfigActorContract:
    key: str
    actor: str


@dataclass(frozen=True, slots=True)
class ProgramConfigWindowLayoutContract:
    key: str
    is_default: bool = False


@dataclass(frozen=True, slots=True)
class ProgramConfigWindowSectionContract:
    layout_key: str
    key: str
    order: int
    is_visible: bool = True
    flex: float | None = None


@dataclass(frozen=True, slots=True)
class ProgramConfigWindowSlotMappingContract:
    layout_key: str
    port_ref: str
    section_key: str
    on_bind: ProgramSlotOnBind = "replace"
    is_visible_default: bool | None = None


@dataclass(frozen=True, slots=True)
class ProgramConfigInstruction:
    step_id: str
    sequence: int
    type: ProgramConfigInstructionType
    instruction_input: ProgramConfigInstructionInputPayload | None = None
    instruction_let: ProgramConfigInstructionLetPayload | None = None
    instruction_bind: ProgramConfigInstructionBindPayload | None = None
    instruction_invoke: ProgramConfigInstructionInvokePayload | None = None
    instruction_expect: ProgramConfigInstructionExpectPayload | None = None
    instruction_intent: ProgramConfigInstructionIntentPayload | None = None


@dataclass(frozen=True, slots=True)
class ProgramConfigPlan:
    name: str
    key: str
    instructions: tuple[ProgramConfigInstruction, ...]
    actors: tuple[ProgramConfigActorContract, ...] = ()
    ports: tuple[ProgramConfigPortContract, ...] = ()
    layouts: tuple[ProgramConfigWindowLayoutContract, ...] = ()
    sections: tuple[ProgramConfigWindowSectionContract, ...] = ()
    slot_mappings: tuple[ProgramConfigWindowSlotMappingContract, ...] = ()


@dataclass(frozen=True, slots=True)
class ProgramConfigApplyRef:
    name: str


@dataclass(frozen=True, slots=True)
class ProgramConfigApplyCall:
    step_id: str
    target: Literal["constructor", "instance"]
    class_fqn: str
    function_name: str
    args: tuple[object, ...]
    result_ref: ProgramConfigApplyRef | None = None
    object_ref: ProgramConfigApplyRef | None = None


@dataclass(frozen=True, slots=True)
class ProgramConfigReferenceCatalog:
    actor_config_ids: dict[str, object] = field(default_factory=dict)
    function_config_ids: dict[str, object] = field(default_factory=dict)
    function_attribute_config_ids: dict[str, object] = field(default_factory=dict)
    event_config_ids: dict[str, object] = field(default_factory=dict)
    action_config_ids: dict[str, object] = field(default_factory=dict)
    attribute_config_ids: dict[str, object] = field(default_factory=dict)
    enum_config_ids: dict[str, object] = field(default_factory=dict)
    class_config_ids: dict[str, object] = field(default_factory=dict)
    projection_ids: dict[str, object] = field(default_factory=dict)
    projection_node_ids: dict[str, object] = field(default_factory=dict)
    projection_node_identity_ids: dict[str, object] = field(default_factory=dict)
    program_config_actor_config_ids: dict[str, object] = field(default_factory=dict)
    program_config_port_ids: dict[str, object] = field(default_factory=dict)
    program_config_port_projection_node_ids: dict[str, object] = field(
        default_factory=dict
    )
    symbol_values: dict[str, object] = field(default_factory=dict)


_PORT_KEY_RX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PORT_NODE_REF_RX = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*(::[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*)*$"
)
_SNAKE_ACRONYM_RX = re.compile(r"([A-Z]+)([A-Z][a-z])")
_SNAKE_CASE_RX = re.compile(r"([a-z0-9])([A-Z])")
_TYPE_ID_TARGET_RX = re.compile(r"\b([A-Za-z_][A-Za-z0-9_.]*)\.id\s*\(")
_QUALIFIED_NON_PRIMITIVE_TYPE_REF_RX = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+$"
)
_PROGRAM_PRIMITIVE_CODEC = AwarePrimitiveCodec()
_PROGRAM_PRIMITIVE_TYPE_DOC = ", ".join(
    sorted(
        {
            *(token.casefold() for token in AWARE_TO_BASE_MAPPING.keys()),
            *(base.value for base in CodePrimitiveBaseType),
        }
    )
)


@dataclass(frozen=True, slots=True)
class ProgramTypeIdContract:
    class_name: str
    key: str
    namespace: str
    target: str
    source: Literal["id_decl", "constructor_key"] = "id_decl"
    identity_keys: tuple[str, ...] = ()


_type_id_workspace_scanned = False
_TYPE_ID_WORKSPACE_REGISTRY: dict[str, ProgramTypeIdContract] = {}
_TYPE_ID_WORKSPACE_ERRORS: dict[str, str] = {}
_PROGRAM_DECLARATION_TARGETS = {
    "program.actor",
    "program.port",
    "plan.layout",
    "plan.section",
    "plan.slot",
}


def _normalize_port_key(raw: object) -> str:
    if not isinstance(raw, str):
        raise ProgramCompileError("port key must be a string literal")
    key = raw.strip()
    if not key:
        raise ProgramCompileError("port key cannot be empty")
    if _PORT_KEY_RX.match(key) is None:
        raise ProgramCompileError(
            "port key must be a valid identifier " + "(regex: ^[A-Za-z_][A-Za-z0-9_]*$)"
        )
    return key


def _port_symbol_for_key(key: str) -> str:
    return f"program.port.{key}"


def _actor_symbol_for_key(key: str) -> str:
    return f"program.actor.{key}"


def _port_projection_symbol(*, key: str) -> str:
    return f"{_port_symbol_for_key(key)}.projection"


def _port_projection_node_identity_symbol(
    *, key: str, node_key: str | None = None
) -> str:
    base = f"{_port_symbol_for_key(key)}.projection_node_identity"
    node_name = (node_key or "").strip()
    if not node_name:
        return base
    return f"{base}.{node_name}"


def _port_projection_node_symbol(*, key: str, node_key: str | None = None) -> str:
    base = f"{_port_symbol_for_key(key)}.projection_node"
    node_name = (node_key or "").strip()
    if not node_name:
        return base
    return f"{base}.{node_name}"


def _require_literal_string(expr: object, *, label: str) -> str:
    if not isinstance(expr, str):
        raise ProgramCompileError(f"{label} must be a string literal")
    value = expr.strip()
    if not value:
        raise ProgramCompileError(f"{label} cannot be empty")
    return value


def _reject_local_declaration_arg(expr: object, *, label: str) -> None:
    if isinstance(expr, PlanLocalRef):
        raise ProgramCompileError(
            f"{label} cannot reference local bindings; use plan.* symbols or literals"
        )


def _normalize_json_value(value: object) -> PlanValue:
    if isinstance(value, dict):
        # JSON object key order is not semantic; canonicalize deterministically.
        raw_object = cast(dict[object, object], value)
        out: dict[str, object] = {}
        for key_obj in sorted(raw_object.keys(), key=lambda key: str(key)):
            if not isinstance(key_obj, str):
                raise ProgramCompileError("JSON object keys must be strings")
            out[key_obj] = _normalize_json_value(raw_object[key_obj])
        return out
    if isinstance(value, list):
        raw_list = cast(list[object], value)
        return [_normalize_json_value(item) for item in raw_list]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise ProgramCompileError(
        f"Unsupported JSON literal type in program expression: {type(value).__name__}"
    )


def _node_text(node: Node) -> str:
    if node.text is None:
        return ""
    return node.text.decode("utf-8")


def _to_snake_case(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return raw
    step = _SNAKE_ACRONYM_RX.sub(r"\1_\2", raw)
    step = _SNAKE_CASE_RX.sub(r"\1_\2", step)
    return step.replace("-", "_").casefold()


def _module_id_from_namespace(namespace: str) -> str:
    raw = (namespace or "").strip()
    if not raw.startswith("NS_"):
        raise ProgramCompileError(
            f"ID contract namespace must use NS_* form (got {raw!r})"
        )
    module_id = _normalize_module_id(
        raw[3:],
        ctx=f"namespace {raw!r}",
    )
    if not module_id:
        raise ProgramCompileError(
            f"ID contract namespace must include module id (got {raw!r})"
        )
    return module_id


def _canonical_program_attribute_type_ref(
    type_ref: str,
    *,
    context: str,
) -> str:
    raw = (type_ref or "").strip()
    if not raw:
        raise ProgramCompileError(f"{context}: type cannot be empty")
    try:
        primitive = _PROGRAM_PRIMITIVE_CODEC.parse_exact(raw)
    except ValueError as exc:  # pragma: no cover - defensive codec boundary
        raise ProgramCompileError(f"{context}: invalid type {raw!r}: {exc}") from exc
    if primitive is not None:
        return primitive.base_type.value

    normalized = raw.casefold().replace("_", "").replace(" ", "")
    for base in CodePrimitiveBaseType:
        if base.value.casefold().replace("_", "").replace(" ", "") == normalized:
            return base.value

    if _QUALIFIED_NON_PRIMITIVE_TYPE_REF_RX.match(raw) is not None:
        return raw

    raise ProgramCompileError(
        f"{context}: unsupported type {raw!r}. "
        + "Use canonical primitive types or a fully-qualified class/enum type ref "
        + f"(examples: `alpha.types.Status`, `alpha.types.Profile`). Primitive types: {_PROGRAM_PRIMITIVE_TYPE_DOC}."
    )


def _stable_id_function_name(*, class_name: str, key: str) -> str:
    class_snake = _to_snake_case(class_name)
    if not class_snake:
        raise ProgramCompileError("ID contract class name cannot be empty")
    key_norm = (key or "").strip()
    if not key_norm:
        raise ProgramCompileError("ID contract key cannot be empty")
    if key_norm == "primary":
        return f"stable_{class_snake}_id"
    return f"stable_{class_snake}_{_to_snake_case(key_norm)}_id"


def _normalize_module_id(raw_module_id: str, *, ctx: str) -> str:
    module_id = (raw_module_id or "").strip().casefold().replace("-", "_")
    if not module_id:
        raise ProgramCompileError(f"module id is empty ({ctx})")
    if _PORT_KEY_RX.match(module_id) is None:
        raise ProgramCompileError(
            "module id must be identifier-compatible "
            + f"(regex: ^[A-Za-z_][A-Za-z0-9_]*$) ({ctx}, got {raw_module_id!r})"
        )
    return module_id


def _build_constructor_identity_contract(
    *,
    class_node: Node,
    class_name: str,
    module_id: str | None,
    allow_partial: bool,
    error_sink: dict[str, str] | None,
) -> ProgramTypeIdContract | None:
    if module_id is None:
        return None

    keyed_signatures: dict[tuple[str, ...], list[str]] = {}
    for member in class_node.named_children:
        if member.type != "fn_def":
            continue
        verb_node = member.child_by_field_name("verb")
        if verb_node is None:
            continue
        verb = _node_text(verb_node).strip()
        if verb != "construct":
            continue

        fn_name_node = member.child_by_field_name("name")
        fn_name = _node_text(fn_name_node).strip() if fn_name_node is not None else ""
        if not fn_name:
            fn_name = "<anonymous>"

        signature_node = member.child_by_field_name("sig")
        if signature_node is None:
            continue

        identity_keys: list[str] = []
        for attr in signature_node.named_children:
            if attr.type != "input_attr":
                continue
            if attr.child_by_field_name("identity_key") is None:
                continue
            name_node = attr.child_by_field_name("name")
            if name_node is None:
                continue
            name = _node_text(name_node).strip()
            if name:
                identity_keys.append(name)
        if not identity_keys:
            continue
        key_tuple = tuple(identity_keys)
        keyed_signatures.setdefault(key_tuple, []).append(fn_name)

    if not keyed_signatures:
        return None
    if len(keyed_signatures) > 1:
        signatures = ", ".join(
            f"{'/'.join(sorted(fn_names))}({', '.join(keys)})"
            for keys, fn_names in sorted(
                keyed_signatures.items(),
                key=lambda item: (item[0], tuple(sorted(item[1]))),
            )
        )
        message = (
            f"class {class_name!r} has multiple constructor key signatures ({signatures}). "
            "Use one constructor identity-key signature or declare explicit `id primary(...)`."
        )
        if error_sink is not None:
            error_sink[class_name] = message
        if allow_partial:
            return None
        raise ProgramCompileError(message)

    identity_key_tuple = next(iter(keyed_signatures.keys()))
    namespace = f"NS_{module_id.upper()}"
    return ProgramTypeIdContract(
        class_name=class_name,
        key="primary",
        namespace=namespace,
        target=f"{module_id}.{_stable_id_function_name(class_name=class_name, key='primary')}",
        source="constructor_key",
        identity_keys=identity_key_tuple,
    )


def build_type_id_registry_from_aware_sources(
    *aware_sources: str,
    allow_partial: bool = False,
    default_module_id: str | None = None,
    error_sink: dict[str, str] | None = None,
) -> dict[str, ProgramTypeIdContract]:
    """
    Build `Type.id(...)` lowering registry from `.aware` class ID contracts.

    Contract:
    - Looks for `class <Type> { id <key>(...) { namespace NS_<MODULE> ... } }`.
    - Falls back to constructor identity-key signatures when no explicit primary `id` exists.
    - Registers `primary` key per class for sugar `Type.id(...)`.
    - Lowers to `<module>.stable_<snake_case(type)>[_<snake_case(key)>]_id`.
    """

    parser = Parser(language=AWARE_LANGUAGE)
    registry: dict[str, ProgramTypeIdContract] = {}
    fallback_module_id: str | None = None
    if default_module_id is not None:
        fallback_module_id = _normalize_module_id(
            default_module_id,
            ctx="default_module_id",
        )

    for source in aware_sources:
        tree = parser.parse((source or "").encode("utf-8"))
        if tree.root_node.has_error and not allow_partial:
            raise ProgramCompileError(
                "Aware source contains parse errors while building Type.id registry"
            )

        for node in tree.root_node.named_children:
            if node.type != "class_def":
                continue
            class_name_node = node.child_by_field_name("name")
            if class_name_node is None:
                raise ProgramCompileError(
                    "class_def missing name in ID registry source"
                )
            class_name = _node_text(class_name_node).strip()
            if not class_name:
                raise ProgramCompileError(
                    "class_def name is empty in ID registry source"
                )

            primary_contract: ProgramTypeIdContract | None = None
            for child in node.named_children:
                if child.type != "id_decl":
                    continue
                key_node = child.child_by_field_name("key")
                if key_node is None:
                    raise ProgramCompileError(
                        f"class {class_name!r} id declaration missing key"
                    )
                key = _node_text(key_node).strip()
                if not key:
                    raise ProgramCompileError(
                        f"class {class_name!r} id declaration has empty key"
                    )
                body_node = child.child_by_field_name("body")
                if body_node is None:
                    raise ProgramCompileError(
                        f"class {class_name!r} id declaration {key!r} missing body"
                    )
                namespace: str | None = None
                for stmt in body_node.named_children:
                    if stmt.type != "id_namespace_stmt":
                        continue
                    ns_node = stmt.child_by_field_name("namespace")
                    if ns_node is None:
                        raise ProgramCompileError(
                            f"class {class_name!r} id declaration {key!r} missing namespace value"
                        )
                    namespace = _node_text(ns_node).strip()
                    break
                if not namespace:
                    raise ProgramCompileError(
                        f"class {class_name!r} id declaration {key!r} requires namespace"
                    )

                identity_keys: list[str] = []
                params_node = child.child_by_field_name("params")
                if params_node is not None:
                    for param in params_node.named_children:
                        if param.type != "program_param":
                            continue
                        name_node = param.child_by_field_name("name")
                        if name_node is None:
                            continue
                        param_name = _node_text(name_node).strip()
                        if param_name:
                            identity_keys.append(param_name)

                module_id = _module_id_from_namespace(namespace)
                target = f"{module_id}.{_stable_id_function_name(class_name=class_name, key=key)}"
                declared_contract = ProgramTypeIdContract(
                    class_name=class_name,
                    key=key,
                    namespace=namespace,
                    target=target,
                    source="id_decl",
                    identity_keys=tuple(identity_keys),
                )
                if key != "primary":
                    continue
                primary_contract = declared_contract

            constructor_contract = _build_constructor_identity_contract(
                class_node=node,
                class_name=class_name,
                module_id=fallback_module_id,
                allow_partial=allow_partial,
                error_sink=error_sink,
            )

            contract: ProgramTypeIdContract | None
            if primary_contract is not None:
                if (
                    constructor_contract is not None
                    and primary_contract.target != constructor_contract.target
                ):
                    message = (
                        f"class {class_name!r} primary id contract mismatch: "
                        f"id declaration target={primary_contract.target!r} vs "
                        f"constructor-key target={constructor_contract.target!r}"
                    )
                    if error_sink is not None:
                        error_sink[class_name] = message
                    if not allow_partial:
                        raise ProgramCompileError(message)
                contract = primary_contract
            else:
                contract = constructor_contract

            if contract is None:
                continue
            previous = registry.get(class_name)
            if previous is not None and previous != contract:
                raise ProgramCompileError(
                    f"class {class_name!r} declares conflicting primary id contracts"
                )
            registry[class_name] = contract
    return registry


def _candidate_repo_roots() -> tuple[Path, ...]:
    roots: list[Path] = []
    cwd = Path.cwd().resolve()
    roots.append(cwd)
    roots.extend(cwd.parents)
    here = Path(__file__).resolve()
    roots.append(here.parent)
    roots.extend(here.parents)

    uniq: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if root in seen:
            continue
        seen.add(root)
        uniq.append(root)
    return tuple(uniq)


def _discover_repo_root() -> Path | None:
    for root in _candidate_repo_roots():
        if (root / "modules").is_dir() and (root / "aware.environment.toml").exists():
            return root
    return None


def _discover_workspace_root() -> Path | None:
    for root in _candidate_repo_roots():
        if (root / "aware.workspace.toml").is_file():
            return root
    return None


def _scan_workspace_type_id_registry() -> dict[str, ProgramTypeIdContract]:
    global _type_id_workspace_scanned
    if _type_id_workspace_scanned:
        return _TYPE_ID_WORKSPACE_REGISTRY

    _type_id_workspace_scanned = True
    workspace_root = _discover_workspace_root()
    if workspace_root is None:
        return _TYPE_ID_WORKSPACE_REGISTRY

    _TYPE_ID_WORKSPACE_REGISTRY.clear()
    _TYPE_ID_WORKSPACE_ERRORS.clear()
    for source_root, module_id in _workspace_type_id_source_roots(
        workspace_root=workspace_root
    ):
        for aware_path in sorted(source_root.rglob("*.aware")):
            if _has_ignored_workspace_source_segment(
                aware_path, source_root=source_root
            ):
                continue
            try:
                text = aware_path.read_text(encoding="utf-8")
            except Exception:
                continue
            partial_errors: dict[str, str] = {}
            try:
                partial = build_type_id_registry_from_aware_sources(
                    text,
                    allow_partial=True,
                    default_module_id=module_id,
                    error_sink=partial_errors,
                )
            except ProgramCompileError:
                continue
            for class_name, message in partial_errors.items():
                _ = _TYPE_ID_WORKSPACE_ERRORS.setdefault(class_name, message)
            for class_name, contract in partial.items():
                _merge_workspace_type_id_contract(
                    class_name=class_name,
                    contract=contract,
                )
    return _TYPE_ID_WORKSPACE_REGISTRY


def _workspace_type_id_source_roots(
    *,
    workspace_root: Path,
) -> tuple[tuple[Path, str | None], ...]:
    try:
        from aware_workspace.registry import load_aware_workspace_registry
    except Exception:
        return ()

    try:
        registry = load_aware_workspace_registry(workspace_root=workspace_root)
    except Exception:
        return ()
    if registry is None:
        return ()

    roots: list[tuple[Path, str | None]] = []
    seen: set[Path] = set()
    for entry in registry.semantic_package_entries:
        if entry.semantic_package_family not in {"meta", "ontology"}:
            continue
        metadata = entry.semantic_package_metadata
        source_root_text = _optional_metadata_text(
            metadata.get("sources_root")
        ) or _optional_metadata_text(metadata.get("source_root"))
        if source_root_text is None:
            continue
        source_root = (workspace_root / source_root_text).resolve()
        if source_root in seen or not source_root.is_dir():
            continue
        seen.add(source_root)
        roots.append(
            (
                source_root,
                _workspace_type_id_module_id(
                    workspace_root=workspace_root,
                    source_root=source_root,
                    metadata=metadata,
                ),
            )
        )
    return tuple(roots)


def _workspace_type_id_module_id(
    *,
    workspace_root: Path,
    source_root: Path,
    metadata: Mapping[str, object],
) -> str | None:
    module_id = _optional_metadata_text(metadata.get("module_id"))
    if module_id is not None:
        return module_id

    package_root_text = _optional_metadata_text(metadata.get("package_root"))
    if package_root_text is not None:
        package_root = (workspace_root / package_root_text).resolve()
        try:
            parts = package_root.relative_to(workspace_root / "modules").parts
        except Exception:
            parts = ()
        if parts:
            return parts[0]

    try:
        parts = source_root.relative_to(workspace_root / "modules").parts
    except Exception:
        parts = ()
    return parts[0] if parts else None


def _optional_metadata_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _has_ignored_workspace_source_segment(path: Path, *, source_root: Path) -> bool:
    ignored_segments = {
        ".aware",
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
    }
    try:
        parts = path.resolve().relative_to(source_root.resolve()).parts
    except Exception:
        parts = path.parts
    return any(part in ignored_segments for part in parts)


def _merge_workspace_type_id_contract(
    *,
    class_name: str,
    contract: ProgramTypeIdContract,
) -> None:
    existing = _TYPE_ID_WORKSPACE_REGISTRY.get(class_name)
    if existing is None:
        _TYPE_ID_WORKSPACE_REGISTRY[class_name] = contract
        return
    if existing == contract:
        return
    _ = _TYPE_ID_WORKSPACE_REGISTRY.pop(class_name, None)
    _ = _TYPE_ID_WORKSPACE_ERRORS.setdefault(
        class_name,
        (
            f"class {class_name!r} Type.id contract is ambiguous across workspace packages: "
            f"{existing.target!r} vs {contract.target!r}. "
            "Use explicit type_id_registry for this program until class references are disambiguated."
        ),
    )


def _extract_type_id_class_names_from_source(source: str) -> set[str]:
    out: set[str] = set()
    for match in _TYPE_ID_TARGET_RX.finditer(source or ""):
        raw_owner = (match.group(1) or "").strip()
        if not raw_owner:
            continue
        class_name = raw_owner.rsplit(".", 1)[-1].strip()
        if class_name:
            out.add(class_name)
    return out


def _resolve_type_id_registry_for_source(
    source: str,
    *,
    explicit_registry: Mapping[str, ProgramTypeIdContract] | None,
) -> Mapping[str, ProgramTypeIdContract] | None:
    if explicit_registry is not None:
        return explicit_registry

    type_targets = _extract_type_id_class_names_from_source(source)
    if not type_targets:
        return None

    resolved: dict[str, ProgramTypeIdContract] = {}
    inline_registry = build_type_id_registry_from_aware_sources(
        source,
        allow_partial=True,
    )
    for class_name in type_targets:
        contract = inline_registry.get(class_name)
        if contract is not None:
            resolved[class_name] = contract

    missing = sorted(type_targets.difference(resolved.keys()))
    if missing:
        workspace_registry = _scan_workspace_type_id_registry()
        for class_name in missing:
            contract = workspace_registry.get(class_name)
            if contract is not None:
                resolved[class_name] = contract

    return resolved or None


def _resolve_type_id_target(
    *,
    raw_target: str,
    type_id_registry: Mapping[str, ProgramTypeIdContract] | None,
) -> tuple[str, ProgramTypeIdContract | None]:
    raw = (raw_target or "").strip()
    if not raw.endswith(".id"):
        return raw, None
    class_ref = raw[:-3].strip()
    class_name = class_ref.rsplit(".", 1)[-1].strip()
    if not class_name:
        raise ProgramCompileError(f"Invalid Type.id call target: {raw_target!r}")
    registry = type_id_registry or {}
    contract = registry.get(class_ref)
    if contract is None:
        contract = registry.get(class_name)
    if contract is None:
        if "." not in class_ref:
            qualified_candidates = sorted(
                {
                    key
                    for key in registry.keys()
                    if key.count(".") >= 1 and key.endswith(f".{class_name}")
                }
            )
            if len(qualified_candidates) > 1:
                raise ProgramCompileError(
                    "Ambiguous Type.id sugar target "
                    + f"{raw!r}. Use an explicit qualified owner. "
                    + f"Candidates: {qualified_candidates}"
                )
        workspace_error = _TYPE_ID_WORKSPACE_ERRORS.get(class_name)
        if workspace_error is None:
            workspace_error = _TYPE_ID_WORKSPACE_ERRORS.get(class_ref)
        if workspace_error:
            raise ProgramCompileError(
                f"Cannot resolve Type.id sugar target {raw!r}: {workspace_error}"
            )
        raise ProgramCompileError(
            "Unknown Type.id sugar target "
            + f"{raw!r}. Provide class id contracts via `build_type_id_registry_from_aware_sources(...)` "
            + "using either explicit `id primary(...)` or constructor input `key` annotations."
        )
    return contract.target, contract


def _validate_type_id_call_identity_contract(
    *,
    raw_target: str,
    call: ProgramCall,
    contract: ProgramTypeIdContract | None,
) -> None:
    if contract is None:
        return
    identity_keys = tuple(
        (key or "").strip() for key in contract.identity_keys if (key or "").strip()
    )
    if not identity_keys:
        return

    provided_keys: list[str] = []
    for arg in call.args:
        if arg.name is None:
            raise ProgramCompileError(
                "Type.id sugar calls with identity-key contracts require keyword arguments "
                + f"(target={raw_target!r})"
            )
        key = (arg.name or "").strip()
        if not key:
            raise ProgramCompileError(
                f"Type.id sugar call contains an empty keyword argument name ({raw_target!r})"
            )
        provided_keys.append(key)

    required = set(identity_keys)
    provided = set(provided_keys)
    missing = sorted(required.difference(provided))
    extra = sorted(provided.difference(required))
    if missing or extra:
        detail_parts: list[str] = []
        if missing:
            detail_parts.append(f"missing={missing}")
        if extra:
            detail_parts.append(f"extra={extra}")
        detail = " ".join(detail_parts)
        raise ProgramCompileError(
            "Type.id identity-key contract mismatch "
            + f"(target={raw_target!r}, expected_keys={list(identity_keys)} {detail})"
        )


def _compile_expr(
    expr: ProgramExpr,
    locals_: set[str],
    *,
    type_id_registry: Mapping[str, ProgramTypeIdContract] | None,
) -> PlanExpr:
    if isinstance(expr, ProgramRef):
        name = (expr.value or "").strip()
        if not name:
            raise ProgramCompileError("Empty reference in program expression")
        if name in locals_:
            return PlanLocalRef(name=name)
        return PlanSymbolRef(name=name)

    if isinstance(expr, ProgramCall):
        return _compile_call(expr, locals_, type_id_registry=type_id_registry)

    if isinstance(expr, dict) or isinstance(expr, list):
        return _normalize_json_value(expr)

    # Scalars are carried through as-is.
    return expr


def _compile_call(
    call: ProgramCall,
    locals_: set[str],
    *,
    type_id_registry: Mapping[str, ProgramTypeIdContract] | None,
) -> PlanCall:
    target, id_contract = _resolve_type_id_target(
        raw_target=(call.target or "").strip(),
        type_id_registry=type_id_registry,
    )
    _validate_type_id_call_identity_contract(
        raw_target=(call.target or "").strip(),
        call=call,
        contract=id_contract,
    )
    if not target:
        raise ProgramCompileError("Empty call target in program")

    saw_keyword = False
    kw_names: set[str] = set()
    out_args: list[PlanCallArg] = []

    for arg in call.args:
        out_args.append(
            _compile_call_arg(
                arg,
                locals_,
                type_id_registry=type_id_registry,
            )
        )
        if arg.name is None:
            if saw_keyword:
                raise ProgramCompileError(
                    f"Positional arguments cannot appear after keyword arguments in call to {target}"
                )
            continue

        saw_keyword = True
        name = (arg.name or "").strip()
        if not name:
            raise ProgramCompileError(
                f"Empty keyword argument name in call to {target}"
            )
        if name in kw_names:
            raise ProgramCompileError(
                f"Duplicate keyword argument {name!r} in call to {target}"
            )
        kw_names.add(name)

    compiled_object_expr: PlanExpr | None = None
    if call.object_expr is not None:
        if target in {"bind"}:
            raise ProgramCompileError(
                f"{target} does not accept inline object selector"
            )
        compiled_object_expr = _compile_expr(
            call.object_expr,
            locals_,
            type_id_registry=type_id_registry,
        )

    return PlanCall(
        target=target,
        args=tuple(out_args),
        object_expr=compiled_object_expr,
    )


def _compile_call_arg(
    arg: ProgramCallArg,
    locals_: set[str],
    *,
    type_id_registry: Mapping[str, ProgramTypeIdContract] | None,
) -> PlanCallArg:
    name = (arg.name or "").strip() if arg.name is not None else None
    return PlanCallArg(
        name=name or None,
        value=_compile_expr(
            arg.value,
            locals_,
            type_id_registry=type_id_registry,
        ),
    )


def _step_id(*, sequence: int, instruction_type: ProgramConfigInstructionType) -> str:
    return f"s{sequence:04d}_{instruction_type}"


def _input_source_str(source: PlanExpr) -> str:
    if isinstance(source, PlanSymbolRef):
        name = (source.name or "").strip()
        if not name:
            raise ProgramCompileError("input source symbol cannot be empty")
        return name
    if isinstance(source, str):
        text = source.strip()
        if not text:
            raise ProgramCompileError("input source string cannot be empty")
        return text
    raise ProgramCompileError(
        "input source must be a symbol reference or non-empty string literal"
    )


def _call_kwargs(call: PlanCall) -> dict[str, PlanExpr]:
    kwargs: dict[str, PlanExpr] = {}
    for arg in call.args:
        if arg.name is None:
            raise ProgramCompileError(
                f"{call.target} requires keyword arguments only in ProgramConfig lowering"
            )
        name = arg.name.strip()
        if not name:
            raise ProgramCompileError(f"{call.target} has empty keyword argument name")
        if name in kwargs:
            raise ProgramCompileError(
                f"Duplicate keyword argument {name!r} in call to {call.target}"
            )
        kwargs[name] = arg.value
    return kwargs


def _compile_bind_payload(call: PlanCall) -> ProgramConfigInstructionBindPayload:
    kwargs = _call_kwargs(call)

    port_ref = kwargs.pop("port", None)
    if port_ref is None:
        port_ref = kwargs.pop("port_ref", None)
    if port_ref is None:
        port_ref = kwargs.pop("program_config_port", None)
    if port_ref is None:
        port_ref = kwargs.pop("program_config_port_ref", None)
    if port_ref is None:
        raise ProgramCompileError(
            "bind requires `port` (aliases: `port_ref`, `program_config_port`, `program_config_port_ref`)"
        )
    if isinstance(port_ref, PlanLocalRef):
        raise ProgramCompileError(
            "bind port must be a program port reference (`program.port.<key>`), "
            + "not a local binding"
        )
    if isinstance(port_ref, PlanSymbolRef):
        port_symbol = (port_ref.name or "").strip()
        if (
            not port_symbol.startswith("program.port.")
            or port_symbol == "program.port."
        ):
            raise ProgramCompileError(
                "bind port reference must use `program.port.<key>` symbol form"
            )
    elif isinstance(port_ref, str):
        port_symbol = port_ref.strip()
        if (
            not port_symbol.startswith("program.port.")
            or port_symbol == "program.port."
        ):
            raise ProgramCompileError(
                "bind port reference must use `program.port.<key>` string form"
            )
        port_ref = PlanSymbolRef(name=port_symbol)
    else:
        raise ProgramCompileError(
            "bind port reference must be a symbol/string `program.port.<key>`"
        )

    view_key_expr = kwargs.pop("view_key", None)
    if view_key_expr is None:
        view_key_expr = kwargs.pop("view", None)
    if view_key_expr is None:
        raise ProgramCompileError("bind requires `view_key` (alias: `view`)")
    if not isinstance(view_key_expr, str):
        raise ProgramCompileError("bind view_key must be a string literal")
    view_key = view_key_expr.strip()
    if not view_key:
        raise ProgramCompileError("bind view_key cannot be empty")

    is_active_expr = kwargs.pop("is_active", True)
    if not isinstance(is_active_expr, bool):
        raise ProgramCompileError("bind is_active must be a boolean")

    if kwargs:
        unknown = ", ".join(sorted(kwargs.keys()))
        raise ProgramCompileError(f"bind received unsupported args: {unknown}")

    return ProgramConfigInstructionBindPayload(
        port_ref=port_ref,
        view_key=view_key,
        is_active=is_active_expr,
    )


def _compile_port_contract(
    call: PlanCall,
    *,
    signature_param_names: set[str] | None = None,
) -> ProgramConfigPortContract:
    allowed_locals = signature_param_names or set()

    def _reject_non_param_local(expr: object, *, label: str) -> None:
        if not isinstance(expr, PlanLocalRef):
            return
        local_name = (expr.name or "").strip()
        if local_name and local_name in allowed_locals:
            return
        raise ProgramCompileError(
            f"{label} cannot reference local bindings; use program signature params, plan.* symbols, or literals"
        )

    kwargs = _call_kwargs(call)

    key_expr = kwargs.pop("key", None)
    if key_expr is None:
        raise ProgramCompileError("port declaration requires `key`")
    key = _normalize_port_key(key_expr)

    intent_expr = kwargs.pop("intent", None)
    intent: str | None = None
    if intent_expr is not None:
        if not isinstance(intent_expr, str):
            raise ProgramCompileError("port intent must be a string literal")
        intent = intent_expr.strip() or None

    projection_expr = kwargs.pop("projection", None)
    projection: str | None = None
    if projection_expr is not None:
        _reject_non_param_local(projection_expr, label="port projection")
        projection = _require_literal_string(
            projection_expr,
            label="port projection",
        )
        if _PORT_KEY_RX.match(projection) is None:
            raise ProgramCompileError(
                "port projection must use `<Experience>` identifier form "
                + "(legacy `.main.*` refs are not allowed)"
            )

    branch_expr = kwargs.pop("branch", None)
    if branch_expr is not None:
        _reject_non_param_local(branch_expr, label="port branch")
        raise ProgramCompileError(
            "port branch is not supported in programs; branch orchestration is environment-owned"
        )

    node_expr = kwargs.pop("node", None)
    if node_expr is not None:
        _reject_non_param_local(node_expr, label="port node")
        raise ProgramCompileError(
            "port `node=` field is legacy; use body declarations "
            + "`node <alias> <node>.<identity>` or `node <alias> <node>(<keys...>)`"
        )

    projection_node_identities: list[
        ProgramConfigPortProjectionNodeIdentityContract
    ] = []
    seen_projection_node_names: set[str] = set()
    for call_arg in call.args:
        raw_name = (call_arg.name or "").strip() if call_arg.name is not None else ""
        if not raw_name.startswith("node_") or "_key_" in raw_name:
            continue
        if raw_name not in kwargs:
            continue
        node_key = raw_name.removeprefix("node_").strip()
        if not node_key:
            raise ProgramCompileError(
                "port node declaration requires a non-empty node name"
            )
        if _PORT_KEY_RX.match(node_key) is None:
            raise ProgramCompileError(
                "port node name must be a valid identifier "
                + "(regex: ^[A-Za-z_][A-Za-z0-9_]*$)"
            )
        if node_key in seen_projection_node_names:
            raise ProgramCompileError(f"Duplicate port node declaration: {node_key!r}")
        seen_projection_node_names.add(node_key)
        node_expr_value = kwargs.pop(raw_name)
        _reject_non_param_local(node_expr_value, label=f"port node {node_key}")
        node_ref = _require_literal_string(
            node_expr_value,
            label=f"port node {node_key}",
        )

        node_args: list[ProgramConfigPortNodeArg] = []
        seen_node_arg_names: set[str] = set()
        node_arg_prefix = f"node_{node_key}_key_"
        for node_arg_call in call.args:
            node_raw_name = (
                (node_arg_call.name or "").strip()
                if node_arg_call.name is not None
                else ""
            )
            if not node_raw_name.startswith(node_arg_prefix):
                continue
            if node_raw_name not in kwargs:
                continue
            node_arg_name = node_raw_name.removeprefix(node_arg_prefix).strip()
            if not node_arg_name:
                raise ProgramCompileError(
                    "port node key names must include a suffix "
                    + "(example: node_main_key_environment_id)"
                )
            if _PORT_KEY_RX.match(node_arg_name) is None:
                raise ProgramCompileError(
                    "port node key suffix must be a valid identifier "
                    + "(regex: ^[A-Za-z_][A-Za-z0-9_]*$)"
                )
            if node_arg_name in seen_node_arg_names:
                raise ProgramCompileError(
                    f"Duplicate port node key name for {node_key!r}: {node_arg_name!r}"
                )
            seen_node_arg_names.add(node_arg_name)
            node_arg_expr = kwargs.pop(node_raw_name)
            _reject_non_param_local(
                node_arg_expr,
                label=f"port {node_raw_name}",
            )
            node_args.append(
                ProgramConfigPortNodeArg(
                    name=node_arg_name,
                    value_expr=node_arg_expr,
                )
            )

        projection_node_name, identity_name = _split_port_node_ref(
            node_ref,
            has_resolver_keys=bool(node_args),
        )
        if identity_name is not None and node_args:
            raise ProgramCompileError(
                "port node ref cannot mix explicit identity and resolver keys; "
                + "use either `<node>.<identity>` or `<node>(<keys...>)`"
            )
        if identity_name is None and not node_args:
            raise ProgramCompileError(
                "port node ref must use `<node>.<identity>` or provide resolver keys via `<node>(<keys...>)`; "
                + f"got {node_ref!r}"
            )

        projection_node_identities.append(
            ProgramConfigPortProjectionNodeIdentityContract(
                key=node_key,
                node=projection_node_name,
                identity=identity_name,
                args=tuple(node_args),
            )
        )

    if projection is None:
        raise ProgramCompileError("port declaration requires `projection`")

    if not projection_node_identities:
        raise ProgramCompileError(
            "port declaration requires at least one node contract in body: "
            + "`node <alias> <node>.<identity>` or `node <alias> <node>(<keys...>)`"
        )

    object_id_expr = kwargs.pop("object_id", None)
    if object_id_expr is not None:
        _reject_non_param_local(object_id_expr, label="port object_id")
        raise ProgramCompileError(
            "port object_id is not supported; use inline instance call form `call <object_id> Owner.Class.fn(...)`"
        )

    branch_id_expr = kwargs.pop("branch_id", None)
    if branch_id_expr is not None:
        _reject_non_param_local(branch_id_expr, label="port branch_id")
        raise ProgramCompileError(
            "port branch_id is not supported; program ports are branch-agnostic"
        )

    opg_expr = kwargs.pop("opg", None)
    if opg_expr is not None:
        _reject_non_param_local(opg_expr, label="port opg")
        raise ProgramCompileError(
            "port opg is not supported; lane activation is owned by `bind(...)` from port projection contract"
        )

    description_expr = kwargs.pop("description", None)
    if description_expr is not None and not isinstance(description_expr, str):
        raise ProgramCompileError("port description must be a string literal")

    allowed_runtime_args: set[str] = set()
    for runtime_arg in allowed_runtime_args:
        expr = kwargs.get(runtime_arg)
        _reject_non_param_local(expr, label=f"port {runtime_arg}")
    legacy_head_args = sorted(k for k in kwargs.keys() if k.startswith("key_"))
    if legacy_head_args:
        raise ProgramCompileError(
            "port declaration does not accept head args; move resolver keys into "
            + "`node <alias> <node>(...)` contracts"
        )
    unknown = sorted(k for k in kwargs.keys() if k not in allowed_runtime_args)
    if unknown:
        raise ProgramCompileError(
            f"port declaration received unsupported args: {', '.join(unknown)}"
        )

    return ProgramConfigPortContract(
        key=key,
        projection=projection,
        intent=intent,
        projection_node_identities=tuple(projection_node_identities),
    )


def _compile_actor_contract(call: PlanCall) -> ProgramConfigActorContract:
    kwargs = _call_kwargs(call)

    key_expr = kwargs.pop("key", None)
    if key_expr is None:
        raise ProgramCompileError("actor declaration requires `key`")
    key = _normalize_port_key(key_expr)

    actor_expr = kwargs.pop("actor", None)
    if actor_expr is None:
        raise ProgramCompileError("actor declaration requires `actor`")
    actor = _require_literal_string(actor_expr, label="actor declaration actor")

    if kwargs:
        unknown = ", ".join(sorted(kwargs.keys()))
        raise ProgramCompileError(
            f"actor declaration received unsupported args: {unknown}"
        )

    return ProgramConfigActorContract(
        key=key,
        actor=actor,
    )


def _to_plan_port_contract(
    contract: ProgramConfigPortContract,
) -> PlanPortContract:
    def _node_ref_for_plan(
        node_contract: ProgramConfigPortProjectionNodeIdentityContract,
    ) -> str:
        node_name = (node_contract.node or "").strip()
        identity_name = (node_contract.identity or "").strip()
        if not node_name:
            raise ProgramCompileError(
                f"port node declaration {node_contract.key!r} requires a non-empty node ref"
            )
        if identity_name:
            if node_contract.args:
                raise ProgramCompileError(
                    "port node ref cannot mix explicit identity and resolver keys; "
                    + "use either `<node>.<identity>` or `<node>(<keys...>)`"
                )
            return f"{node_name}.{identity_name}"
        if not node_contract.args:
            raise ProgramCompileError(
                "port node ref must use `<node>.<identity>` or provide resolver keys via `<node>(<keys...>)`"
            )
        return node_name

    return PlanPortContract(
        key=contract.key,
        projection=contract.projection,
        projection_nodes=tuple(
            PlanPortProjectionNodeContract(
                key=node.key,
                node=_node_ref_for_plan(node),
                keys=tuple(
                    PlanPortProjectionNodeKey(
                        name=arg.name,
                        value_expr=arg.value_expr,
                    )
                    for arg in node.args
                ),
            )
            for node in contract.projection_node_identities
        ),
        intent=contract.intent,
    )


def _to_program_config_port_contract(
    contract: PlanPortContract,
) -> ProgramConfigPortContract:
    projection_node_identities: list[
        ProgramConfigPortProjectionNodeIdentityContract
    ] = []
    for node in contract.projection_nodes:
        node_ref = (node.node or "").strip()
        if not node_ref:
            raise ProgramCompileError(
                f"port node declaration {node.key!r} requires a non-empty node ref"
            )
        node_keys = tuple(
            ProgramConfigPortNodeArg(
                name=arg.name,
                value_expr=arg.value_expr,
            )
            for arg in node.keys
        )
        node_name, identity_name = _split_port_node_ref(
            node_ref,
            has_resolver_keys=bool(node_keys),
        )
        if identity_name is not None and node_keys:
            raise ProgramCompileError(
                "port node ref cannot mix explicit identity and resolver keys; "
                + "use either `<node>.<identity>` or `<node>(<keys...>)`"
            )
        if identity_name is None and not node_keys:
            raise ProgramCompileError(
                "port node ref must use `<node>.<identity>` or provide resolver keys via `<node>(<keys...>)`; "
                + f"got {node_ref!r}"
            )
        projection_node_identities.append(
            ProgramConfigPortProjectionNodeIdentityContract(
                key=node.key,
                node=node_name,
                identity=identity_name,
                args=node_keys,
            )
        )

    return ProgramConfigPortContract(
        key=contract.key,
        projection=contract.projection,
        intent=contract.intent,
        projection_node_identities=tuple(projection_node_identities),
    )


def _split_port_node_ref(
    node_ref: str,
    *,
    has_resolver_keys: bool,
) -> tuple[str, str | None]:
    token = (node_ref or "").strip()
    if not token:
        raise ProgramCompileError("port node ref must be non-empty")
    if has_resolver_keys:
        if _PORT_NODE_REF_RX.match(token) is None:
            raise ProgramCompileError(
                "port node ref with resolver keys must use an OPG node path "
                + "like `owner.Class` or `owner.Class::relationship`; "
                + f"got {node_ref!r}"
            )
        return token, None

    node_name, separator, identity_name = token.rpartition(".")
    if not separator:
        raise ProgramCompileError(
            "port node ref must use `<opg-node>.<identity>` or provide resolver keys "
            + f"via `<opg-node>(<keys...>)`; got {node_ref!r}"
        )
    node_name = node_name.strip()
    identity_name = identity_name.strip()
    if (
        _PORT_NODE_REF_RX.match(node_name) is None
        or _PORT_KEY_RX.match(identity_name) is None
    ):
        raise ProgramCompileError(
            "port node ref must use `<opg-node>.<identity>` or provide resolver keys "
            + "via `<opg-node>(<keys...>)`; "
            + f"got {node_ref!r}"
        )
    return node_name, identity_name


def _is_signature_parameter_input(step: PlanInput) -> bool:
    source = step.source
    if not isinstance(source, PlanSymbolRef):
        return False
    return (source.name or "").strip() == (step.name or "").strip()


def _compile_layout_contract(call: PlanCall) -> ProgramConfigWindowLayoutContract:
    kwargs = _call_kwargs(call)

    key_expr = kwargs.pop("key", None)
    if key_expr is None:
        raise ProgramCompileError("plan.layout requires `key`")
    _reject_local_declaration_arg(key_expr, label="plan.layout key")
    key = _require_literal_string(key_expr, label="plan.layout key")

    is_default_expr = kwargs.pop("is_default", False)
    _reject_local_declaration_arg(is_default_expr, label="plan.layout is_default")
    if not isinstance(is_default_expr, bool):
        raise ProgramCompileError("plan.layout is_default must be a boolean")

    if kwargs:
        unknown = ", ".join(sorted(kwargs.keys()))
        raise ProgramCompileError(f"plan.layout received unsupported args: {unknown}")
    return ProgramConfigWindowLayoutContract(key=key, is_default=is_default_expr)


def _compile_section_contract(call: PlanCall) -> ProgramConfigWindowSectionContract:
    kwargs = _call_kwargs(call)

    layout_key_expr = kwargs.pop("layout_key", None)
    if layout_key_expr is None:
        raise ProgramCompileError("plan.section requires `layout_key`")
    _reject_local_declaration_arg(layout_key_expr, label="plan.section layout_key")
    layout_key = _require_literal_string(
        layout_key_expr, label="plan.section layout_key"
    )

    key_expr = kwargs.pop("key", None)
    if key_expr is None:
        raise ProgramCompileError("plan.section requires `key`")
    _reject_local_declaration_arg(key_expr, label="plan.section key")
    key = _require_literal_string(key_expr, label="plan.section key")

    order_expr = kwargs.pop("order", None)
    if order_expr is None:
        raise ProgramCompileError("plan.section requires `order`")
    _reject_local_declaration_arg(order_expr, label="plan.section order")
    if not isinstance(order_expr, int):
        raise ProgramCompileError("plan.section order must be an integer")
    order = int(order_expr)

    is_visible_expr = kwargs.pop("is_visible", True)
    _reject_local_declaration_arg(is_visible_expr, label="plan.section is_visible")
    if not isinstance(is_visible_expr, bool):
        raise ProgramCompileError("plan.section is_visible must be a boolean")

    flex_expr = kwargs.pop("flex", None)
    _reject_local_declaration_arg(flex_expr, label="plan.section flex")
    flex: float | None
    if flex_expr is None:
        flex = None
    elif isinstance(flex_expr, (int, float)):
        flex = float(flex_expr)
    else:
        raise ProgramCompileError("plan.section flex must be a number or null")

    if kwargs:
        unknown = ", ".join(sorted(kwargs.keys()))
        raise ProgramCompileError(f"plan.section received unsupported args: {unknown}")
    return ProgramConfigWindowSectionContract(
        layout_key=layout_key,
        key=key,
        order=order,
        is_visible=is_visible_expr,
        flex=flex,
    )


def _compile_slot_mapping_contract(
    call: PlanCall,
) -> ProgramConfigWindowSlotMappingContract:
    kwargs = _call_kwargs(call)

    layout_key_expr = kwargs.pop("layout_key", None)
    if layout_key_expr is None:
        raise ProgramCompileError("plan.slot requires `layout_key`")
    _reject_local_declaration_arg(layout_key_expr, label="plan.slot layout_key")
    layout_key = _require_literal_string(layout_key_expr, label="plan.slot layout_key")

    port_expr = kwargs.pop("port", None)
    if port_expr is None:
        raise ProgramCompileError("plan.slot requires `port`")
    _reject_local_declaration_arg(port_expr, label="plan.slot port")
    port_ref = _bind_port_symbol(port_expr)

    section_key_expr = kwargs.pop("section_key", None)
    if section_key_expr is None:
        raise ProgramCompileError("plan.slot requires `section_key`")
    _reject_local_declaration_arg(section_key_expr, label="plan.slot section_key")
    section_key = _require_literal_string(
        section_key_expr,
        label="plan.slot section_key",
    )

    on_bind_expr = kwargs.pop("on_bind", None)
    if on_bind_expr is None:
        raise ProgramCompileError("plan.slot requires `on_bind`")
    _reject_local_declaration_arg(on_bind_expr, label="plan.slot on_bind")
    on_bind = _require_literal_string(on_bind_expr, label="plan.slot on_bind")
    if on_bind not in {"replace", "if_empty", "sticky"}:
        raise ProgramCompileError(
            "plan.slot on_bind must be one of: replace, if_empty, sticky"
        )
    on_bind_value = cast(ProgramSlotOnBind, on_bind)

    is_visible_default_expr = kwargs.pop("is_visible_default", None)
    _reject_local_declaration_arg(
        is_visible_default_expr,
        label="plan.slot is_visible_default",
    )
    if is_visible_default_expr is not None and not isinstance(
        is_visible_default_expr, bool
    ):
        raise ProgramCompileError(
            "plan.slot is_visible_default must be a boolean or null"
        )

    if kwargs:
        unknown = ", ".join(sorted(kwargs.keys()))
        raise ProgramCompileError(f"plan.slot received unsupported args: {unknown}")

    return ProgramConfigWindowSlotMappingContract(
        layout_key=layout_key,
        port_ref=port_ref,
        section_key=section_key,
        on_bind=on_bind_value,
        is_visible_default=is_visible_default_expr,
    )


def _bind_port_symbol(expr: PlanExpr) -> str:
    if isinstance(expr, PlanSymbolRef):
        symbol = (expr.name or "").strip()
    elif isinstance(expr, str):
        symbol = expr.strip()
    else:
        raise ProgramCompileError(
            "bind port reference must be a symbol/string `program.port.<key>`"
        )
    if not symbol.startswith("program.port.") or symbol == "program.port.":
        raise ProgramCompileError("bind port reference must use `program.port.<key>`")
    return symbol


def _validate_program_config_surface(program: ProgramDeclaration) -> None:
    for stmt in program.statements:
        if not isinstance(stmt, ProgramCall):
            raise ProgramCompileError(
                "program config declarations cannot include executable statements; "
                + "use signature params + port/layout declarations only"
            )
        target = (stmt.target or "").strip()
        if target not in _PROGRAM_DECLARATION_TARGETS:
            raise ProgramCompileError(
                "program config declarations cannot include executable statements; "
                + f"found {target!r}"
            )


def _validate_program_impl_surface(program: ProgramDeclaration) -> None:
    if program.parameters:
        raise ProgramCompileError(
            f"program impl {program.name!r} cannot declare parameters; "
            + "declare signature args on the referenced config program"
        )

    for stmt in program.statements:
        if isinstance(stmt, ProgramInput):
            raise ProgramCompileError(
                f"program impl {program.name!r} cannot declare input statements; "
                + "declare signature args on the config program"
            )
        if not isinstance(stmt, ProgramCall):
            continue
        target = (stmt.target or "").strip()
        if target in _PROGRAM_DECLARATION_TARGETS:
            raise ProgramCompileError(
                f"program impl {program.name!r} cannot declare {target!r}; "
                + "declare ports/layout in the config program"
            )


def _merge_program_config_and_impl(
    *,
    config: ProgramDeclaration,
    impl: ProgramDeclaration,
) -> ProgramDeclaration:
    return ProgramDeclaration(
        name=impl.name,
        parameters=config.parameters,
        statements=tuple(config.statements + impl.statements),
    )


def _resolve_executable_program_declarations(
    programs: tuple[ProgramDeclaration, ...],
    *,
    require_config_contract_surface: bool = False,
) -> tuple[ProgramDeclaration, ...]:
    if not programs:
        return ()

    by_name: dict[str, ProgramDeclaration] = {}
    for program in programs:
        name = (program.name or "").strip()
        if not name:
            raise ProgramCompileError("Program name is empty")
        if name in by_name:
            raise ProgramCompileError(f"Duplicate program declaration name: {name!r}")
        by_name[name] = program

    impl_programs = tuple(p for p in programs if p.impl_of is not None)
    if not impl_programs and not require_config_contract_surface:
        return programs

    config_programs = {p.name: p for p in programs if p.impl_of is None}
    if require_config_contract_surface or impl_programs:
        for config_program in config_programs.values():
            _validate_program_config_surface(config_program)
    if not impl_programs:
        return tuple(p for p in programs if p.impl_of is None)

    merged: list[ProgramDeclaration] = []
    for impl in impl_programs:
        _validate_program_impl_surface(impl)
        config_name = (impl.impl_of or "").strip()
        if not config_name:
            raise ProgramCompileError(
                f"program impl {impl.name!r} is missing referenced config name"
            )
        matched_config = config_programs.get(config_name)
        if matched_config is None:
            raise ProgramCompileError(
                f"program impl {impl.name!r} references unknown config {config_name!r}"
            )
        merged.append(
            _merge_program_config_and_impl(
                config=matched_config,
                impl=impl,
            )
        )
    return tuple(merged)


def compile_invocation_plan(
    program: ProgramDeclaration,
    *,
    type_id_registry: Mapping[str, ProgramTypeIdContract] | None = None,
) -> InvocationPlan:
    """
    Compile a parsed `program` declaration into a canonical InvocationPlan IR.

    v1 compilation performs lightweight, deterministic validation:
    - `input` names must be unique.
    - `let` names must be unique.
    - call args enforce Python-like rules: no positional args after keywords; no duplicate keyword names.
    - JSON objects are canonicalized by sorting keys recursively.
    """

    name = (program.name or "").strip()
    if not name:
        raise ProgramCompileError("Program name is empty")

    locals_: set[str] = set()
    signature_param_names: set[str] = set()
    steps: list[PlanStep] = []
    actor_contracts: list[PlanActorContract] = []
    actors_by_symbol: set[str] = set()
    declared_actor_keys: set[str] = set()
    port_contracts: list[PlanPortContract] = []
    ports_by_symbol: set[str] = set()
    saw_non_declaration_stmt = False

    for param in program.parameters:
        input_name = (param.name or "").strip()
        if not input_name:
            raise ProgramCompileError("program parameter name is empty")
        if input_name in locals_:
            raise ProgramCompileError(f"Duplicate binding name: {input_name!r}")
        type_ref = _canonical_program_attribute_type_ref(
            (param.type_ref or "").strip(),
            context=f"program parameter {input_name!r}",
        )
        default_expr = (
            _compile_expr(
                param.default,
                locals_,
                type_id_registry=type_id_registry,
            )
            if param.default is not None
            else None
        )
        steps.append(
            PlanInput(
                name=input_name,
                source=PlanSymbolRef(name=input_name),
                default=default_expr,
                required=(param.default is None),
                type_ref=type_ref,
            )
        )
        locals_.add(input_name)
        signature_param_names.add(input_name)

    for stmt in program.statements:
        if isinstance(stmt, ProgramInput):
            saw_non_declaration_stmt = True
            input_name = (stmt.name or "").strip()
            if not input_name:
                raise ProgramCompileError("input name is empty")
            if input_name in locals_:
                raise ProgramCompileError(f"Duplicate binding name: {input_name!r}")
            default_expr = (
                _compile_expr(
                    stmt.default,
                    locals_,
                    type_id_registry=type_id_registry,
                )
                if stmt.default is not None
                else None
            )
            steps.append(
                PlanInput(
                    name=input_name,
                    source=_compile_expr(
                        stmt.source,
                        locals_,
                        type_id_registry=type_id_registry,
                    ),
                    default=default_expr,
                    required=(stmt.default is None),
                    type_ref="any",
                )
            )
            locals_.add(input_name)
            continue

        if isinstance(stmt, ProgramLet):
            saw_non_declaration_stmt = True
            let_name = (stmt.name or "").strip()
            if not let_name:
                raise ProgramCompileError("let name is empty")
            if let_name in locals_:
                raise ProgramCompileError(f"Duplicate let binding: {let_name!r}")

            steps.append(
                PlanLet(
                    name=let_name,
                    value=_compile_expr(
                        stmt.value,
                        locals_,
                        type_id_registry=type_id_registry,
                    ),
                )
            )
            locals_.add(let_name)
            continue

        if isinstance(stmt, ProgramExpectEventConfig):
            saw_non_declaration_stmt = True
            steps.append(
                PlanExpectEventConfig(
                    ref=_compile_expr(
                        stmt.ref,
                        locals_,
                        type_id_registry=type_id_registry,
                    ),
                    required=bool(stmt.required),
                )
            )
            continue

        if isinstance(stmt, ProgramIntentActionConfig):
            saw_non_declaration_stmt = True
            steps.append(
                PlanIntentActionConfig(
                    action_ref=_compile_expr(
                        stmt.action_ref,
                        locals_,
                        type_id_registry=type_id_registry,
                    ),
                    event_ref=_compile_expr(
                        stmt.event_ref,
                        locals_,
                        type_id_registry=type_id_registry,
                    ),
                )
            )
            continue

        if isinstance(stmt, ProgramCall):
            target = (stmt.target or "").strip()
            if target == "program.actor":
                if saw_non_declaration_stmt:
                    raise ProgramCompileError(
                        "actor declarations must appear at top of program body "
                        + "before inputs/contracts/invocations"
                    )
                actor_contract = _compile_actor_contract(
                    _compile_call(
                        ProgramCall(target="plan.actor", args=stmt.args),
                        locals_,
                        type_id_registry=type_id_registry,
                    ),
                )
                actor_symbol = _actor_symbol_for_key(actor_contract.key)
                if actor_symbol in actors_by_symbol:
                    raise ProgramCompileError(
                        f"Duplicate actor key: {actor_contract.key!r}"
                    )
                actors_by_symbol.add(actor_symbol)
                declared_actor_keys.add(actor_contract.key)
                actor_contracts.append(
                    PlanActorContract(
                        key=actor_contract.key,
                        actor=actor_contract.actor,
                    )
                )
                continue
            if target == "program.port":
                if saw_non_declaration_stmt:
                    raise ProgramCompileError(
                        "port declarations must appear at top of program body "
                        + "before inputs/contracts/invocations"
                    )
                port_contract = _compile_port_contract(
                    _compile_call(
                        ProgramCall(target="plan.port", args=stmt.args),
                        locals_,
                        type_id_registry=type_id_registry,
                    ),
                    signature_param_names=signature_param_names,
                )
                port_symbol = _port_symbol_for_key(port_contract.key)
                if port_symbol in ports_by_symbol:
                    raise ProgramCompileError(
                        f"Duplicate port key: {port_contract.key!r}"
                    )
                ports_by_symbol.add(port_symbol)
                port_contracts.append(_to_plan_port_contract(port_contract))
                continue
            if target == "plan.port":
                raise ProgramCompileError(
                    "call plan.port(...) is not allowed; use `port <name> <Experience> { ... }` declarations"
                )
            if target == "plan.actor":
                raise ProgramCompileError(
                    "call plan.actor(...) is not allowed; use `actor <name> <global_actor>` declarations"
                )
            if target == "plan.bind":
                raise ProgramCompileError(
                    "call plan.bind(...) is not allowed; use `bind(...)` statement"
                )
            if target == "plan.lane":
                raise ProgramCompileError(
                    "call plan.lane(...) is not allowed; use `bind(...)` with declared port contract"
                )
            if target == "plan.object":
                raise ProgramCompileError(
                    "call plan.object(...) is not allowed; use `call <object_id> Owner.Class.fn(...)`"
                )
            if target not in _PROGRAM_DECLARATION_TARGETS:
                saw_non_declaration_stmt = True
            call_actor = (stmt.actor or "").strip()
            if call_actor and call_actor not in declared_actor_keys:
                raise ProgramCompileError(
                    f"call references undeclared actor {call_actor!r}; declare it with "
                    + "`actor <alias> <global_actor>` in the config program"
                )
            steps.append(
                PlanInvoke(
                    kind="effect",
                    call=_compile_call(
                        stmt,
                        locals_,
                        type_id_registry=type_id_registry,
                    ),
                    actor=call_actor or None,
                )
            )
            continue

        raise ProgramCompileError(
            f"Unsupported program statement: {type(stmt).__name__}"
        )

    return InvocationPlan(
        name=name,
        steps=tuple(steps),
        actors=tuple(actor_contracts),
        ports=tuple(port_contracts),
    )


def compile_invocation_plans(
    source: str,
    *,
    type_id_registry: Mapping[str, ProgramTypeIdContract] | None = None,
) -> tuple[InvocationPlan, ...]:
    """Parse + compile all `program` declarations found in `source`."""

    resolved_registry = _resolve_type_id_registry_for_source(
        source,
        explicit_registry=type_id_registry,
    )
    parsed_programs = parse_program_declarations(source)
    programs = _resolve_executable_program_declarations(parsed_programs)
    return tuple(
        compile_invocation_plan(p, type_id_registry=resolved_registry) for p in programs
    )


def compile_program_config_plan(
    program: ProgramDeclaration,
    *,
    type_id_registry: Mapping[str, ProgramTypeIdContract] | None = None,
) -> ProgramConfigPlan:
    """
    Compile one parsed program into ProgramConfig-oriented instruction IR.

    Notes:
    - This lowering is pure and deterministic.
    - It preserves contract-vs-effect separation.
    - `port <name> <Experience> { ... }`, `call plan.layout(...)`, `call plan.section(...)`,
      and `call plan.slot(...)` lower to ProgramConfigPlan metadata contracts (not instructions).
    - `bind(...)` lowers to instruction type `bind`.
    - Other calls lower to `invoke`.
    """

    invocation = compile_invocation_plan(
        program,
        type_id_registry=type_id_registry,
    )
    instructions: list[ProgramConfigInstruction] = []
    actors_by_symbol: dict[str, ProgramConfigActorContract] = {}
    ports_by_symbol: dict[str, ProgramConfigPortContract] = {}
    layouts_by_key: dict[str, ProgramConfigWindowLayoutContract] = {}
    sections: list[ProgramConfigWindowSectionContract] = []
    section_keys_by_layout: dict[str, set[str]] = {}
    slot_mappings: list[ProgramConfigWindowSlotMappingContract] = []
    slot_keys: set[tuple[str, str]] = set()
    declaration_targets = {"plan.layout", "plan.section", "plan.slot"}
    saw_non_declaration_stmt = False
    for port in invocation.ports:
        port_contract = _to_program_config_port_contract(port)
        port_symbol = _port_symbol_for_key(port_contract.key)
        if port_symbol in ports_by_symbol:
            raise ProgramCompileError(f"Duplicate port key: {port_contract.key!r}")
        ports_by_symbol[port_symbol] = port_contract
    for actor in invocation.actors:
        actor_symbol = _actor_symbol_for_key(actor.key)
        if actor_symbol in actors_by_symbol:
            raise ProgramCompileError(f"Duplicate actor key: {actor.key!r}")
        actors_by_symbol[actor_symbol] = ProgramConfigActorContract(
            key=actor.key,
            actor=actor.actor,
        )

    sequence = 0
    active_bound_port_symbol: str | None = None
    for step in invocation.steps:
        is_param_input = isinstance(step, PlanInput) and _is_signature_parameter_input(
            step
        )
        if isinstance(step, PlanInvoke) and step.call.target in declaration_targets:
            target = step.call.target
            if saw_non_declaration_stmt:
                label = target
                raise ProgramCompileError(
                    f"{label} declarations must appear at top of program body "
                    + "before inputs/contracts/invocations"
                )
            if target == "plan.layout":
                layout_contract = _compile_layout_contract(step.call)
                if layout_contract.key in layouts_by_key:
                    raise ProgramCompileError(
                        f"Duplicate layout key: {layout_contract.key!r}"
                    )
                layouts_by_key[layout_contract.key] = layout_contract
                continue
            if target == "plan.section":
                section_contract = _compile_section_contract(step.call)
                keys = section_keys_by_layout.setdefault(
                    section_contract.layout_key,
                    set(),
                )
                if section_contract.key in keys:
                    raise ProgramCompileError(
                        "Duplicate section key in layout "
                        + f"{section_contract.layout_key!r}: {section_contract.key!r}"
                    )
                keys.add(section_contract.key)
                sections.append(section_contract)
                continue
            if target == "plan.slot":
                slot_contract = _compile_slot_mapping_contract(step.call)
                slot_key = (slot_contract.layout_key, slot_contract.port_ref)
                if slot_key in slot_keys:
                    raise ProgramCompileError(
                        "Duplicate slot mapping for layout "
                        + f"{slot_contract.layout_key!r} and port {slot_contract.port_ref!r}"
                    )
                slot_keys.add(slot_key)
                slot_mappings.append(slot_contract)
                continue
        if not is_param_input:
            saw_non_declaration_stmt = True

        if isinstance(step, PlanInput):
            instructions.append(
                ProgramConfigInstruction(
                    step_id=_step_id(sequence=sequence, instruction_type="input"),
                    sequence=sequence,
                    type="input",
                    instruction_input=ProgramConfigInstructionInputPayload(
                        name=step.name,
                        source=_input_source_str(step.source),
                        required=step.required,
                        default_expr=step.default,
                        type_ref=step.type_ref,
                    ),
                )
            )
            sequence += 1
            continue

        if isinstance(step, PlanLet):
            instructions.append(
                ProgramConfigInstruction(
                    step_id=_step_id(sequence=sequence, instruction_type="let"),
                    sequence=sequence,
                    type="let",
                    instruction_let=ProgramConfigInstructionLetPayload(
                        name=step.name,
                        value_expr=step.value,
                    ),
                )
            )
            sequence += 1
            continue

        if isinstance(step, PlanExpectEventConfig):
            instructions.append(
                ProgramConfigInstruction(
                    step_id=_step_id(sequence=sequence, instruction_type="expect"),
                    sequence=sequence,
                    type="expect",
                    instruction_expect=ProgramConfigInstructionExpectPayload(
                        event_config_ref=step.ref,
                        required=step.required,
                    ),
                )
            )
            sequence += 1
            continue

        if isinstance(step, PlanIntentActionConfig):
            instructions.append(
                ProgramConfigInstruction(
                    step_id=_step_id(sequence=sequence, instruction_type="intent"),
                    sequence=sequence,
                    type="intent",
                    instruction_intent=ProgramConfigInstructionIntentPayload(
                        action_config_ref=step.action_ref,
                        event_config_ref=step.event_ref,
                    ),
                )
            )
            sequence += 1
            continue

        if step.call.target == "bind":
            bind_payload = _compile_bind_payload(step.call)
            bind_port_symbol = _bind_port_symbol(bind_payload.port_ref)
            bound_port = ports_by_symbol.get(bind_port_symbol)
            if bound_port is None:
                raise ProgramCompileError(
                    "bind references undeclared program port "
                    + f"{bind_port_symbol!r}. Declare it with `port ...` first."
                )
            instructions.append(
                ProgramConfigInstruction(
                    step_id=_step_id(sequence=sequence, instruction_type="bind"),
                    sequence=sequence,
                    type="bind",
                    instruction_bind=bind_payload,
                )
            )
            active_bound_port_symbol = bind_port_symbol
            sequence += 1
            continue

        if not (step.actor or "").strip():
            raise ProgramCompileError(
                "invoke requires actor attribution; use `<actor_alias> call ...`"
            )
        actor_key = (step.actor or "").strip()
        object_ref_expr = step.call.object_expr
        target_kind: ProgramInvokeTargetKind = "instance"
        if object_ref_expr is None:
            if active_bound_port_symbol is None:
                raise ProgramCompileError(
                    "constructor invoke requires active bind context; add `bind <port> <Projection>.<View>` "
                    + "before constructor calls"
                )
            bind_port_key = (
                active_bound_port_symbol.removeprefix("program.port.")
                .split(".", 1)[0]
                .strip()
            )
            if not bind_port_key:
                raise ProgramCompileError(
                    "bind context is invalid; expected `program.port.<key>`"
                )
            object_ref_expr = PlanSymbolRef(
                name=_port_projection_node_symbol(key=bind_port_key)
            )
            target_kind = "construct"

        instructions.append(
            ProgramConfigInstruction(
                step_id=_step_id(sequence=sequence, instruction_type="invoke"),
                sequence=sequence,
                type="invoke",
                instruction_invoke=ProgramConfigInstructionInvokePayload(
                    function_ref=step.call.target,
                    actor_ref=PlanSymbolRef(name=_actor_symbol_for_key(actor_key)),
                    object_ref=object_ref_expr,
                    target_kind=target_kind,
                    args=step.call.args,
                ),
            )
        )
        sequence += 1
        continue

    layout_keys = set(layouts_by_key.keys())
    if layout_keys:
        default_layout_count = sum(
            1 for contract in layouts_by_key.values() if contract.is_default
        )
        if default_layout_count != 1:
            raise ProgramCompileError(
                "Layout declarations require exactly one default layout "
                + f"(found {default_layout_count})"
            )

    for section_contract in sections:
        if section_contract.layout_key not in layout_keys:
            raise ProgramCompileError(
                "plan.section references unknown layout_key "
                + f"{section_contract.layout_key!r}"
            )

    declared_port_symbols = set(ports_by_symbol.keys())
    for slot_contract in slot_mappings:
        if slot_contract.layout_key not in layout_keys:
            raise ProgramCompileError(
                "plan.slot references unknown layout_key "
                + f"{slot_contract.layout_key!r}"
            )
        if slot_contract.port_ref not in declared_port_symbols:
            raise ProgramCompileError(
                "plan.slot references undeclared program port "
                + f"{slot_contract.port_ref!r}"
            )
        section_keys = section_keys_by_layout.get(slot_contract.layout_key, set())
        if slot_contract.section_key not in section_keys:
            raise ProgramCompileError(
                "plan.slot references unknown section_key "
                + f"{slot_contract.section_key!r} in layout {slot_contract.layout_key!r}"
            )

    for instruction in instructions:
        if instruction.type != "bind":
            continue
        payload = instruction.instruction_bind
        if payload is None:
            raise ProgramCompileError(
                f"ProgramConfig instruction {instruction.step_id} is missing bind payload"
            )
        port_symbol = _bind_port_symbol(payload.port_ref)
        if port_symbol not in declared_port_symbols:
            raise ProgramCompileError(
                "bind references undeclared program port "
                + f"{port_symbol!r}. Declare it with `port <key> <Experience> {{ ... }}`."
            )

    return ProgramConfigPlan(
        name=invocation.name,
        key=invocation.name,
        actors=tuple(actors_by_symbol.values()),
        ports=tuple(ports_by_symbol.values()),
        layouts=tuple(layouts_by_key.values()),
        sections=tuple(sections),
        slot_mappings=tuple(slot_mappings),
        instructions=tuple(instructions),
    )


def compile_program_config_plans(
    source: str,
    *,
    type_id_registry: Mapping[str, ProgramTypeIdContract] | None = None,
    require_config_contract_surface: bool = False,
) -> tuple[ProgramConfigPlan, ...]:
    """Parse + compile all programs in `source` into ProgramConfig-oriented IR."""

    resolved_registry = _resolve_type_id_registry_for_source(
        source,
        explicit_registry=type_id_registry,
    )
    parsed_programs = parse_program_declarations(source)
    programs = _resolve_executable_program_declarations(
        parsed_programs,
        require_config_contract_surface=require_config_contract_surface,
    )
    return tuple(
        compile_program_config_plan(p, type_id_registry=resolved_registry)
        for p in programs
    )


def _is_uuid_like(value: str) -> bool:
    try:
        _ = UUID(value)
    except (TypeError, ValueError):
        return False
    return True


def _resolve_id_ref(
    *,
    expr: PlanExpr,
    kind: str,
    mapping: dict[str, object],
    catalog: ProgramConfigReferenceCatalog,
    locals_exprs: dict[str, PlanExpr],
    step_id: str,
    strict_resolution: bool,
    _visited_locals: set[str] | None = None,
) -> object:
    visited = _visited_locals or set()

    if isinstance(expr, PlanLocalRef):
        local_name = (expr.name or "").strip()
        if not local_name:
            raise ProgramCompileError(f"{step_id}: empty local reference for {kind}")
        if local_name in catalog.symbol_values:
            return catalog.symbol_values[local_name]
        if local_name in visited:
            raise ProgramCompileError(
                f"{step_id}: cyclic local reference while resolving {kind}: {local_name}"
            )
        local_expr = locals_exprs.get(local_name)
        if local_expr is None:
            if strict_resolution:
                raise ProgramCompileError(
                    f"{step_id}: unresolved local {local_name!r} for {kind}. "
                    + "Provide ProgramConfigReferenceCatalog.symbol_values[...] or use a resolvable symbol."
                )
            return ProgramConfigApplyRef(name=local_name)
        visited_next = set(visited)
        visited_next.add(local_name)
        return _resolve_id_ref(
            expr=local_expr,
            kind=kind,
            mapping=mapping,
            catalog=catalog,
            locals_exprs=locals_exprs,
            step_id=step_id,
            strict_resolution=strict_resolution,
            _visited_locals=visited_next,
        )

    if isinstance(expr, PlanSymbolRef):
        symbol = (expr.name or "").strip()
        if not symbol:
            raise ProgramCompileError(f"{step_id}: empty symbol reference for {kind}")
        if symbol in mapping:
            return mapping[symbol]
        if symbol in catalog.symbol_values:
            return catalog.symbol_values[symbol]
        if strict_resolution:
            raise ProgramCompileError(
                f"{step_id}: unresolved symbol {symbol!r} for {kind}. "
                + f"Add ProgramConfigReferenceCatalog mapping for {kind}."
            )
        return symbol

    if isinstance(expr, str):
        key = expr.strip()
        if not key:
            raise ProgramCompileError(f"{step_id}: empty string reference for {kind}")
        if key in mapping:
            return mapping[key]
        if _is_uuid_like(key):
            return key
        if strict_resolution:
            raise ProgramCompileError(
                f"{step_id}: unresolved string {key!r} for {kind}. "
                + f"Add ProgramConfigReferenceCatalog mapping for {kind}."
            )
        return key

    if isinstance(expr, PlanCall):
        if strict_resolution:
            raise ProgramCompileError(
                f"{step_id}: cannot resolve computed expression {expr.target!r} for {kind}. "
                + "Resolve this value before apply-call compilation and pass it via symbol_values."
            )
        return expr

    if strict_resolution:
        raise ProgramCompileError(
            f"{step_id}: unsupported expression {type(expr).__name__} for {kind}"
        )
    return expr


def _invoke_args_to_entries(
    *, args: tuple[PlanCallArg, ...], step_id: str
) -> tuple[tuple[str, object], ...]:
    out: dict[str, object] = {}
    for arg in args:
        if arg.name is None:
            raise ProgramCompileError(
                f"{step_id}: invoke lowering requires keyword arguments only"
            )
        key = (arg.name or "").strip()
        if not key:
            raise ProgramCompileError(f"{step_id}: invoke has empty argument name")
        if key in out:
            raise ProgramCompileError(
                f"{step_id}: duplicate invoke argument name {key!r}"
            )
        out[key] = arg.value
    return tuple((key, out[key]) for key in out)


def _function_attribute_symbol(*, function_ref: str, attribute_name: str) -> str:
    return f"{function_ref}::{attribute_name}"


def _function_attribute_names_for_function(
    *,
    function_ref: str,
    function_attribute_config_ids: dict[str, object],
) -> set[str]:
    prefix = f"{function_ref}::"
    out: set[str] = set()
    for key in function_attribute_config_ids:
        if not key.startswith(prefix):
            continue
        name = key[len(prefix) :].strip()
        if name:
            out.add(name)
    return out


def _resolve_function_attribute_config_id(
    *,
    function_ref: str,
    attribute_name: str,
    function_attribute_config_ids: dict[str, object],
    step_id: str,
    strict_resolution: bool,
) -> object:
    symbol = _function_attribute_symbol(
        function_ref=function_ref,
        attribute_name=attribute_name,
    )
    if symbol in function_attribute_config_ids:
        return function_attribute_config_ids[symbol]
    if strict_resolution:
        raise ProgramCompileError(
            f"{step_id}: unresolved function attribute contract {symbol!r}. "
            + "Add ProgramConfigReferenceCatalog.function_attribute_config_ids entry."
        )
    return symbol


def _resolve_function_target(
    *,
    function_ref: str,
    function_config_ids: dict[str, object],
    step_id: str,
    strict_resolution: bool,
) -> object:
    if function_ref in function_config_ids:
        return function_config_ids[function_ref]
    if _is_uuid_like(function_ref):
        return function_ref
    if strict_resolution:
        raise ProgramCompileError(
            f"{step_id}: unresolved function target {function_ref!r}. "
            + "Add ProgramConfigReferenceCatalog.function_config_ids entry."
        )
    return function_ref


def _resolve_projection_id(
    *,
    port: ProgramConfigPortContract,
    projection_ids: dict[str, object],
    strict_resolution: bool,
) -> object:
    port_symbol = _port_projection_symbol(key=port.key)
    if port_symbol in projection_ids:
        return projection_ids[port_symbol]
    if not strict_resolution:
        return port_symbol

    raise ProgramCompileError(
        "unresolved projection_id for port "
        + f"{port.key!r}. Add ProgramConfigReferenceCatalog.projection_ids[{port_symbol!r}] "
        + "from experience-owned projection contracts (fallback projection symbols are not allowed)."
    )


def _resolve_projection_node_identity_id(
    *,
    port: ProgramConfigPortContract,
    node_contract: ProgramConfigPortProjectionNodeIdentityContract,
    projection_node_identity_ids: dict[str, object],
    strict_resolution: bool,
) -> object:
    port_symbol = _port_projection_node_identity_symbol(
        key=port.key,
        node_key=node_contract.key,
    )
    if port_symbol in projection_node_identity_ids:
        return projection_node_identity_ids[port_symbol]
    if not strict_resolution:
        return port_symbol

    raise ProgramCompileError(
        "unresolved projection_experience_node_identity_id for port node "
        + f"{port.key!r}:{node_contract.key!r}. "
        + "Add ProgramConfigReferenceCatalog.projection_node_identity_ids"
        + f"[{port_symbol!r}] from experience-owned node identity contracts "
        + "(fallback symbols are not allowed)."
    )


def _resolve_projection_node_id(
    *,
    port: ProgramConfigPortContract,
    node_contract: ProgramConfigPortProjectionNodeIdentityContract,
    projection_node_ids: dict[str, object],
    strict_resolution: bool,
) -> object:
    port_symbol = _port_projection_node_symbol(
        key=port.key,
        node_key=node_contract.key,
    )
    if port_symbol in projection_node_ids:
        return projection_node_ids[port_symbol]
    if not strict_resolution:
        return port_symbol

    raise ProgramCompileError(
        "unresolved projection_experience_node_id for port node "
        + f"{port.key!r}:{node_contract.key!r}. "
        + "Add ProgramConfigReferenceCatalog.projection_node_ids"
        + f"[{port_symbol!r}] from experience-owned node contracts "
        + "(fallback symbols are not allowed)."
    )


def _is_canonical_primitive_type_ref(type_ref: str) -> bool:
    normalized = (type_ref or "").strip().casefold().replace("_", "").replace(" ", "")
    if not normalized:
        return False
    return any(
        base.value.casefold().replace("_", "").replace(" ", "") == normalized
        for base in CodePrimitiveBaseType
    )


def _resolve_input_attribute_type_contract(
    *,
    instruction_step_id: str,
    input_name: str,
    type_ref: str,
    catalog: ProgramConfigReferenceCatalog,
    strict_resolution: bool,
) -> tuple[str, object | None, object | None]:
    canonical_type_ref = _canonical_program_attribute_type_ref(
        type_ref,
        context=f"{instruction_step_id} input {input_name!r}",
    )
    if _is_canonical_primitive_type_ref(canonical_type_ref):
        return canonical_type_ref, None, None

    enum_id = catalog.enum_config_ids.get(canonical_type_ref)
    class_id = catalog.class_config_ids.get(canonical_type_ref)
    if enum_id is not None and class_id is not None:
        raise ProgramCompileError(
            f"{instruction_step_id}: attribute type {canonical_type_ref!r} is ambiguously mapped "
            + "to both enum_config_id and class_config_id. Keep only one mapping."
        )
    if enum_id is not None:
        return canonical_type_ref, enum_id, None
    if class_id is not None:
        return canonical_type_ref, None, class_id
    if strict_resolution:
        raise ProgramCompileError(
            f"{instruction_step_id}: unresolved non-primitive attribute type {canonical_type_ref!r}. "
            + "Add ProgramConfigReferenceCatalog.enum_config_ids[...] or class_config_ids[...] mapping."
        )
    raise ProgramCompileError(
        f"{instruction_step_id}: non-primitive attribute type {canonical_type_ref!r} requires explicit "
        + "enum/class config mapping (ProgramConfigReferenceCatalog)."
    )


def compile_program_config_apply_calls(
    plan: ProgramConfigPlan,
    *,
    program_config_id_ref: str = "program_config_id",
    references: ProgramConfigReferenceCatalog | None = None,
    strict_resolution: bool = False,
) -> tuple[ProgramConfigApplyCall, ...]:
    """
    Compile a ProgramConfigPlan into canonical handler-call intents.

    This output is pure and deterministic; execution remains runtime/applier-owned.
    """

    program_config_ref = ProgramConfigApplyRef(name=program_config_id_ref)
    program_impl_ref = ProgramConfigApplyRef(
        name=f"{program_config_id_ref}.program_impl"
    )
    catalog = references or ProgramConfigReferenceCatalog()
    locals_exprs: dict[str, PlanExpr] = {}
    calls: list[ProgramConfigApplyCall] = []
    program_config_actor_config_ids: dict[str, object] = dict(
        catalog.program_config_actor_config_ids
    )
    program_config_port_ids: dict[str, object] = dict(catalog.program_config_port_ids)
    program_config_port_projection_node_ids: dict[str, object] = dict(
        catalog.program_config_port_projection_node_ids
    )
    program_config_port_projection_node_identity_ids: dict[str, object] = {}
    duplicate_projection_node_aliases: set[str] = set()
    program_input_attribute_refs: dict[str, ProgramConfigApplyRef] = {}
    input_name_by_source: dict[str, str] = {}

    attribute_position = 0
    for instruction in plan.instructions:
        if instruction.type != "input":
            continue
        payload = instruction.instruction_input
        if payload is None:
            raise ProgramCompileError(
                f"ProgramConfig instruction {instruction.step_id} is missing input payload"
            )

        attribute_ref = ProgramConfigApplyRef(name=f"program_attribute:{payload.name}")
        attribute_symbol = PlanSymbolRef(name=f"program.input.{payload.name}")
        resolved_attribute_config_id = _resolve_id_ref(
            expr=attribute_symbol,
            kind="attribute_config_id",
            mapping=catalog.attribute_config_ids,
            catalog=catalog,
            locals_exprs=locals_exprs,
            step_id=instruction.step_id,
            strict_resolution=strict_resolution,
        )
        (
            resolved_type_ref,
            resolved_enum_config_id,
            resolved_class_config_id,
        ) = _resolve_input_attribute_type_contract(
            instruction_step_id=instruction.step_id,
            input_name=payload.name,
            type_ref=payload.type_ref or "any",
            catalog=catalog,
            strict_resolution=strict_resolution,
        )
        calls.append(
            ProgramConfigApplyCall(
                step_id=f"program.attribute.{attribute_position:04d}.create",
                target="instance",
                class_fqn="aware_experience_ontology.program.program_config.ProgramConfig",
                function_name="create_attribute_config",
                args=(
                    resolved_attribute_config_id,
                    payload.name,
                    resolved_type_ref,
                    resolved_enum_config_id,
                    resolved_class_config_id,
                    "input",
                    attribute_position,
                    payload.required,
                ),
                object_ref=program_config_ref,
                result_ref=attribute_ref,
            )
        )
        program_input_attribute_refs[payload.name] = attribute_ref
        source = (payload.source or "").strip()
        if source:
            if (
                source in input_name_by_source
                and input_name_by_source[source] != payload.name
            ):
                raise ProgramCompileError(
                    "input attribute contract resolution is ambiguous for source "
                    + f"{source!r} (inputs: {input_name_by_source[source]!r}, {payload.name!r})"
                )
            input_name_by_source[source] = payload.name
        attribute_position += 1

    for idx, actor in enumerate(plan.actors):
        actor_symbol = _actor_symbol_for_key(actor.key)
        actor_ref = ProgramConfigApplyRef(name=f"actor:{actor.key}")
        calls.append(
            ProgramConfigApplyCall(
                step_id=f"actor.{idx:04d}.declare",
                target="instance",
                class_fqn="aware_experience_ontology.program.program_config.ProgramConfig",
                function_name="create_actor_config",
                args=(
                    _resolve_id_ref(
                        expr=PlanSymbolRef(name=actor_symbol),
                        kind="actor_config_id",
                        mapping=catalog.actor_config_ids,
                        catalog=catalog,
                        locals_exprs=locals_exprs,
                        step_id=f"actor.{idx:04d}",
                        strict_resolution=strict_resolution,
                    ),
                    actor.key,
                ),
                object_ref=program_config_ref,
                result_ref=actor_ref,
            )
        )
        program_config_actor_config_ids[actor_symbol] = actor_ref

    for idx, port in enumerate(plan.ports):
        port_ref = ProgramConfigApplyRef(name=f"port:{port.key}")
        port_symbol = _port_symbol_for_key(port.key)
        projection_id = _resolve_projection_id(
            port=port,
            projection_ids=catalog.projection_ids,
            strict_resolution=strict_resolution,
        )
        calls.append(
            ProgramConfigApplyCall(
                step_id=f"port.{idx:04d}.declare",
                target="instance",
                class_fqn="aware_experience_ontology.program.program_config.ProgramConfig",
                function_name="create_port",
                args=(
                    projection_id,
                    port.key,
                    port.intent,
                    "reference",
                ),
                object_ref=program_config_ref,
                result_ref=port_ref,
            )
        )
        program_config_port_ids[port_symbol] = port_ref
        projection_node_identities = tuple(port.projection_node_identities)
        if not projection_node_identities:
            raise ProgramCompileError(
                f"port {port.key!r} requires at least one projection node identity contract"
            )
        single_legacy_shape = (
            len(projection_node_identities) == 1
            and (projection_node_identities[0].key or "").strip() == "main"
        )
        for node_index, node_contract in enumerate(projection_node_identities):
            if single_legacy_shape:
                port_projection_node_identity_ref = ProgramConfigApplyRef(
                    name=f"port_projection_node_identity:{port.key}"
                )
                projection_node_identity_step_id = (
                    f"port.{idx:04d}.projection_node_identity"
                )
            else:
                port_projection_node_identity_ref = ProgramConfigApplyRef(
                    name=(
                        "port_projection_node_identity:"
                        f"{port.key}:{node_contract.key}"
                    )
                )
                projection_node_identity_step_id = (
                    f"port.{idx:04d}.node.{node_index:04d}.projection_node_identity"
                )

            calls.append(
                ProgramConfigApplyCall(
                    step_id=f"port.{idx:04d}.node.{node_index:04d}.projection_node",
                    target="instance",
                    class_fqn=(
                        "aware_experience_ontology.program."
                        "program_config_port.ProgramConfigPort"
                    ),
                    function_name="create_projection_node",
                    args=(
                        _resolve_projection_node_id(
                            port=port,
                            node_contract=node_contract,
                            projection_node_ids=catalog.projection_node_ids,
                            strict_resolution=strict_resolution,
                        ),
                        node_contract.key,
                    ),
                    object_ref=port_ref,
                    result_ref=ProgramConfigApplyRef(
                        name=(
                            f"port_projection_node:{port.key}"
                            if single_legacy_shape
                            else f"port_projection_node:{port.key}:{node_contract.key}"
                        )
                    ),
                )
            )
            port_projection_node_ref = ProgramConfigApplyRef(
                name=(
                    f"port_projection_node:{port.key}"
                    if single_legacy_shape
                    else f"port_projection_node:{port.key}:{node_contract.key}"
                )
            )
            program_config_port_projection_node_ids[
                _port_projection_node_symbol(
                    key=port.key,
                    node_key=node_contract.key,
                )
            ] = port_projection_node_ref
            if single_legacy_shape:
                program_config_port_projection_node_ids[
                    _port_projection_node_symbol(key=port.key)
                ] = port_projection_node_ref
            node_alias = (node_contract.key or "").strip()
            if node_alias:
                existing = program_config_port_projection_node_ids.get(node_alias)
                if existing is None:
                    program_config_port_projection_node_ids[node_alias] = (
                        port_projection_node_ref
                    )
                elif existing != port_projection_node_ref:
                    duplicate_projection_node_aliases.add(node_alias)
                    _ = program_config_port_projection_node_ids.pop(node_alias, None)

            if (node_contract.identity or "").strip():
                projection_node_identity_id = _resolve_projection_node_identity_id(
                    port=port,
                    node_contract=node_contract,
                    projection_node_identity_ids=catalog.projection_node_identity_ids,
                    strict_resolution=strict_resolution,
                )
                calls.append(
                    ProgramConfigApplyCall(
                        step_id=projection_node_identity_step_id,
                        target="instance",
                        class_fqn=(
                            "aware_experience_ontology.program."
                            "program_config_port_projection_experience_node."
                            "ProgramConfigPortProjectionExperienceNode"
                        ),
                        function_name="create_identity",
                        args=(projection_node_identity_id, node_contract.key),
                        object_ref=port_projection_node_ref,
                        result_ref=port_projection_node_identity_ref,
                    )
                )
                program_config_port_projection_node_identity_ids[
                    _port_projection_node_identity_symbol(
                        key=port.key,
                        node_key=node_contract.key,
                    )
                ] = port_projection_node_identity_ref
                if single_legacy_shape:
                    program_config_port_projection_node_identity_ids[
                        _port_projection_node_identity_symbol(key=port.key)
                    ] = port_projection_node_identity_ref

    calls.append(
        ProgramConfigApplyCall(
            step_id="program.impl.create",
            target="constructor",
            class_fqn="aware_experience_ontology.program.impl.program_impl.ProgramImpl",
            function_name="build",
            args=(program_config_ref, plan.key),
            result_ref=program_impl_ref,
        )
    )

    for instruction in plan.instructions:
        instruction_ref = ProgramConfigApplyRef(
            name=f"instruction:{instruction.step_id}"
        )
        calls.append(
            ProgramConfigApplyCall(
                step_id=f"{instruction.step_id}.instruction",
                target="constructor",
                class_fqn=(
                    "aware_experience_ontology.program.impl."
                    "program_impl_instruction.ProgramImplInstruction"
                ),
                function_name="build",
                args=(program_impl_ref, instruction.type, instruction.sequence),
                result_ref=instruction_ref,
            )
        )

        if instruction.type == "input":
            input_payload = instruction.instruction_input
            if input_payload is None:
                raise ProgramCompileError(
                    f"ProgramConfig instruction {instruction.step_id} is missing input payload"
                )
            input_config_ref = ProgramConfigApplyRef(
                name=f"input_config:{instruction.step_id}"
            )
            input_ref = ProgramConfigApplyRef(name=f"input:{instruction.step_id}")
            calls.append(
                ProgramConfigApplyCall(
                    step_id=f"{instruction.step_id}.input_config",
                    target="instance",
                    class_fqn=(
                        "aware_experience_ontology.program."
                        "program_config.ProgramConfig"
                    ),
                    function_name="create_input_config",
                    args=(
                        input_payload.name,
                        input_payload.source,
                        input_payload.required,
                        input_payload.default_expr,
                    ),
                    object_ref=program_config_ref,
                    result_ref=input_config_ref,
                )
            )
            calls.append(
                ProgramConfigApplyCall(
                    step_id=f"{instruction.step_id}.input",
                    target="constructor",
                    class_fqn=(
                        "aware_experience_ontology.program.impl."
                        "program_impl_instruction_input.ProgramImplInstructionInput"
                    ),
                    function_name="build",
                    args=(input_config_ref,),
                    result_ref=input_ref,
                )
            )
            locals_exprs[input_payload.name] = PlanSymbolRef(name=input_payload.source)
            for idx, attr in enumerate(input_payload.attribute_configs):
                resolved_input_attribute_config_id = _resolve_id_ref(
                    expr=attr.attribute_ref,
                    kind="attribute_config_id",
                    mapping=catalog.attribute_config_ids,
                    catalog=catalog,
                    locals_exprs=locals_exprs,
                    step_id=instruction.step_id,
                    strict_resolution=strict_resolution,
                )
                calls.append(
                    ProgramConfigApplyCall(
                        step_id=f"{instruction.step_id}.input_attribute_{idx:04d}",
                        target="instance",
                        class_fqn=(
                            "aware_experience_ontology.program."
                            "program_config_input_config.ProgramConfigInputConfig"
                        ),
                        function_name="add_attribute_config",
                        args=(resolved_input_attribute_config_id, attr.position),
                        object_ref=input_config_ref,
                    )
                )
            continue

        if instruction.type == "let":
            let_payload = instruction.instruction_let
            if let_payload is None:
                raise ProgramCompileError(
                    f"ProgramConfig instruction {instruction.step_id} is missing let payload"
                )
            calls.append(
                ProgramConfigApplyCall(
                    step_id=f"{instruction.step_id}.let",
                    target="constructor",
                    class_fqn=(
                        "aware_experience_ontology.program.impl."
                        "program_impl_instruction_let.ProgramImplInstructionLet"
                    ),
                    function_name="build",
                    args=(instruction_ref, let_payload.name, let_payload.value_expr),
                    result_ref=ProgramConfigApplyRef(name=f"let:{instruction.step_id}"),
                )
            )
            locals_exprs[let_payload.name] = let_payload.value_expr
            continue

        if instruction.type == "bind":
            bind_payload = instruction.instruction_bind
            if bind_payload is None:
                raise ProgramCompileError(
                    f"ProgramConfig instruction {instruction.step_id} is missing bind payload"
                )
            calls.append(
                ProgramConfigApplyCall(
                    step_id=f"{instruction.step_id}.bind",
                    target="constructor",
                    class_fqn=(
                        "aware_experience_ontology.program.impl."
                        "program_impl_instruction_bind.ProgramImplInstructionBind"
                    ),
                    function_name="build",
                    args=(
                        instruction_ref,
                        _resolve_id_ref(
                            expr=bind_payload.port_ref,
                            kind="program_config_port_id",
                            mapping=program_config_port_ids,
                            catalog=catalog,
                            locals_exprs=locals_exprs,
                            step_id=instruction.step_id,
                            strict_resolution=strict_resolution,
                        ),
                        bind_payload.view_key,
                        bind_payload.is_active,
                    ),
                    result_ref=ProgramConfigApplyRef(
                        name=f"bind:{instruction.step_id}"
                    ),
                )
            )
            continue

        if instruction.type == "invoke":
            invoke_payload = instruction.instruction_invoke
            if invoke_payload is None:
                raise ProgramCompileError(
                    f"ProgramConfig instruction {instruction.step_id} is missing invoke payload"
                )
            if isinstance(invoke_payload.object_ref, PlanSymbolRef):
                object_symbol = (invoke_payload.object_ref.name or "").strip()
                if object_symbol in duplicate_projection_node_aliases:
                    raise ProgramCompileError(
                        f"{instruction.step_id}: invoke object alias {object_symbol!r} "
                        + "is ambiguous across port node contracts"
                    )
            resolved_program_config_actor_config_id = _resolve_id_ref(
                expr=invoke_payload.actor_ref,
                kind="program_config_actor_config_id",
                mapping=program_config_actor_config_ids,
                catalog=catalog,
                locals_exprs=locals_exprs,
                step_id=instruction.step_id,
                strict_resolution=True,
            )
            resolved_program_config_port_projection_node_id = _resolve_id_ref(
                expr=invoke_payload.object_ref,
                kind="program_config_port_projection_experience_node_id",
                mapping=program_config_port_projection_node_ids,
                catalog=catalog,
                locals_exprs=locals_exprs,
                step_id=instruction.step_id,
                strict_resolution=True,
            )
            invoke_args = _invoke_args_to_entries(
                args=invoke_payload.args,
                step_id=instruction.step_id,
            )
            if strict_resolution:
                expected_attribute_names = _function_attribute_names_for_function(
                    function_ref=invoke_payload.function_ref,
                    function_attribute_config_ids=catalog.function_attribute_config_ids,
                )
                if not expected_attribute_names:
                    raise ProgramCompileError(
                        f"{instruction.step_id}: missing function attribute contract mappings "
                        + f"for invoke target {invoke_payload.function_ref!r}. "
                        + "Add ProgramConfigReferenceCatalog.function_attribute_config_ids entries."
                    )
                provided_attribute_names = {name for name, _ in invoke_args}
                missing_attribute_names = sorted(
                    expected_attribute_names - provided_attribute_names
                )
                extra_attribute_names = sorted(
                    provided_attribute_names - expected_attribute_names
                )
                if missing_attribute_names or extra_attribute_names:
                    raise ProgramCompileError(
                        f"{instruction.step_id}: invoke kwargs mismatch for {invoke_payload.function_ref!r} "
                        + f"(missing={missing_attribute_names}, extra={extra_attribute_names})"
                    )
            invoke_ref = ProgramConfigApplyRef(name=f"invoke:{instruction.step_id}")
            calls.append(
                ProgramConfigApplyCall(
                    step_id=f"{instruction.step_id}.invoke",
                    target="constructor",
                    class_fqn=(
                        "aware_experience_ontology.program.impl."
                        "program_impl_instruction_invoke.ProgramImplInstructionInvoke"
                    ),
                    function_name="build",
                    args=(
                        instruction_ref,
                        _resolve_function_target(
                            function_ref=invoke_payload.function_ref,
                            function_config_ids=catalog.function_config_ids,
                            step_id=instruction.step_id,
                            strict_resolution=strict_resolution,
                        ),
                        resolved_program_config_actor_config_id,
                        resolved_program_config_port_projection_node_id,
                        invoke_payload.target_kind,
                    ),
                    result_ref=invoke_ref,
                )
            )
            for arg_index, (arg_name, arg_value) in enumerate(invoke_args):
                calls.append(
                    ProgramConfigApplyCall(
                        step_id=f"{instruction.step_id}.invoke_attribute_{arg_index:04d}",
                        target="instance",
                        class_fqn=(
                            "aware_experience_ontology.program.impl."
                            "program_impl_instruction_invoke.ProgramImplInstructionInvoke"
                        ),
                        function_name="add_attribute_config",
                        args=(
                            _resolve_function_attribute_config_id(
                                function_ref=invoke_payload.function_ref,
                                attribute_name=arg_name,
                                function_attribute_config_ids=catalog.function_attribute_config_ids,
                                step_id=instruction.step_id,
                                strict_resolution=strict_resolution,
                            ),
                            arg_value,
                            arg_index,
                        ),
                        object_ref=invoke_ref,
                    )
                )
            continue

        if instruction.type == "expect":
            expect_payload = instruction.instruction_expect
            if expect_payload is None:
                raise ProgramCompileError(
                    f"ProgramConfig instruction {instruction.step_id} is missing expect payload"
                )
            calls.append(
                ProgramConfigApplyCall(
                    step_id=f"{instruction.step_id}.expect",
                    target="constructor",
                    class_fqn=(
                        "aware_experience_ontology.program.impl."
                        "program_impl_instruction_expect.ProgramImplInstructionExpect"
                    ),
                    function_name="build",
                    args=(
                        instruction_ref,
                        _resolve_id_ref(
                            expr=expect_payload.event_config_ref,
                            kind="event_config_id",
                            mapping=catalog.event_config_ids,
                            catalog=catalog,
                            locals_exprs=locals_exprs,
                            step_id=instruction.step_id,
                            strict_resolution=strict_resolution,
                        ),
                        expect_payload.required,
                    ),
                    result_ref=ProgramConfigApplyRef(
                        name=f"expect:{instruction.step_id}"
                    ),
                )
            )
            continue

        if instruction.type == "intent":
            intent_payload = instruction.instruction_intent
            if intent_payload is None:
                raise ProgramCompileError(
                    f"ProgramConfig instruction {instruction.step_id} is missing intent payload"
                )
            _ = _resolve_id_ref(
                expr=intent_payload.event_config_ref,
                kind="event_config_id",
                mapping=catalog.event_config_ids,
                catalog=catalog,
                locals_exprs=locals_exprs,
                step_id=instruction.step_id,
                strict_resolution=strict_resolution,
            )
            calls.append(
                ProgramConfigApplyCall(
                    step_id=f"{instruction.step_id}.intent",
                    target="constructor",
                    class_fqn=(
                        "aware_experience_ontology.program.impl."
                        "program_impl_instruction_intent.ProgramImplInstructionIntent"
                    ),
                    function_name="build",
                    args=(
                        instruction_ref,
                        _resolve_id_ref(
                            expr=intent_payload.action_config_ref,
                            kind="action_config_id",
                            mapping=catalog.action_config_ids,
                            catalog=catalog,
                            locals_exprs=locals_exprs,
                            step_id=instruction.step_id,
                            strict_resolution=strict_resolution,
                        ),
                        _resolve_id_ref(
                            expr=intent_payload.event_config_ref,
                            kind="event_config_id",
                            mapping=catalog.event_config_ids,
                            catalog=catalog,
                            locals_exprs=locals_exprs,
                            step_id=instruction.step_id,
                            strict_resolution=strict_resolution,
                        ),
                    ),
                    result_ref=ProgramConfigApplyRef(
                        name=f"intent:{instruction.step_id}"
                    ),
                )
            )
            continue

        raise ProgramCompileError(
            f"Unsupported ProgramConfig instruction type: {instruction.type}"
        )

    return tuple(calls)


def compile_program_config_graph_apply_calls(
    plan: ProgramConfigPlan,
    *,
    program_config_graph_id_ref: str = "program_config_graph_id",
    program_config_id_ref: str = "program_config_id",
    key: str | None = None,
    title: str | None = None,
    description: str | None = None,
    narrative: str | None = None,
    intent: str | None = None,
    object_projection_graph_identity_id: object | None = None,
    object_instance_graph_branch_id: object | None = None,
    branch_binding_mode: str = "reference",
    position: int | None = None,
    is_default: bool = False,
    references: ProgramConfigReferenceCatalog | None = None,
    strict_resolution: bool = False,
) -> tuple[ProgramConfigApplyCall, ...]:
    """
    Compile a ProgramConfigPlan into graph-anchored canonical handler-call intents.

    Contract:
    - Graph connector ownership is explicit (`ProgramConfigGraph.create_program_config`).
    - Program contract lowering remains delegated to `compile_program_config_apply_calls`.
    """

    resolved_key = key if key is not None else plan.key
    resolved_title = title if title is not None else plan.name

    program_config_graph_ref = ProgramConfigApplyRef(name=program_config_graph_id_ref)
    graph_create_call = ProgramConfigApplyCall(
        step_id="program_config_graph.program_config.create",
        target="instance",
        class_fqn="aware_experience_ontology.program.program_config_graph.ProgramConfigGraph",
        function_name="create_program_config",
        args=(
            resolved_key,
            resolved_title,
            description,
            narrative,
            intent,
            object_projection_graph_identity_id,
            object_instance_graph_branch_id,
            branch_binding_mode,
            position,
            is_default,
        ),
        object_ref=program_config_graph_ref,
        result_ref=ProgramConfigApplyRef(
            name=f"{program_config_id_ref}.graph_program_config"
        ),
    )
    program_config_resolve_call = ProgramConfigApplyCall(
        step_id="program_config_graph.program_config.resolve",
        target="constructor",
        class_fqn="aware_experience_ontology.program.program_config.ProgramConfig",
        function_name="build",
        args=(
            program_config_graph_ref,
            resolved_key,
            resolved_title,
            description,
            narrative,
        ),
        result_ref=ProgramConfigApplyRef(name=program_config_id_ref),
    )

    program_calls = compile_program_config_apply_calls(
        plan,
        program_config_id_ref=program_config_id_ref,
        references=references,
        strict_resolution=strict_resolution,
    )
    return (graph_create_call, program_config_resolve_call, *program_calls)


def compile_program_apply_calls(
    plan: ProgramConfigPlan,
    *,
    program_config_graph_id_ref: str = "program_config_graph_id",
    program_config_id_ref: str = "program_config_id",
    key: str | None = None,
    title: str | None = None,
    description: str | None = None,
    narrative: str | None = None,
    intent: str | None = None,
    object_projection_graph_identity_id: object | None = None,
    object_instance_graph_branch_id: object | None = None,
    branch_binding_mode: str = "reference",
    position: int | None = None,
    is_default: bool = False,
    references: ProgramConfigReferenceCatalog | None = None,
    strict_resolution: bool = False,
) -> tuple[ProgramConfigApplyCall, ...]:
    """
    Canonical program apply entrypoint (graph-first).

    Contract:
    - Program apply always anchors through ProgramConfigGraph membership.
    - ProgramConfig/Port/Instruction lowering remains delegated to config helper.
    """

    return compile_program_config_graph_apply_calls(
        plan,
        program_config_graph_id_ref=program_config_graph_id_ref,
        program_config_id_ref=program_config_id_ref,
        key=key,
        title=title,
        description=description,
        narrative=narrative,
        intent=intent,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        branch_binding_mode=branch_binding_mode,
        position=position,
        is_default=is_default,
        references=references,
        strict_resolution=strict_resolution,
    )
