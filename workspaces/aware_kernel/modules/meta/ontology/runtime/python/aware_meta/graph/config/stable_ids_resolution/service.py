"""Centralized stable-id orchestration service.

This service owns stable-id ownership-mode routing and fail-closed graph derivation
contracts. Renderer modules must consume this service and remain pure emitters.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import cast
from uuid import UUID
import ast
import re

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType

# Meta Runtime
from aware_meta.graph.config.namespace.builder import (
    build_namespace_bundle_from_ocg_topology,
)
from aware_meta.manifest.loader import load_aware_toml_spec
from aware_meta.manifest.spec import AwarePackageKind
from aware_meta.graph.config.stable_ids_resolution.contracts import (
    StableIdsOwnershipMode,
    StableIdsResolutionPolicy,
    StableIdsServiceHooks,
)
from aware_meta.graph.config.stable_ids_spec.loader import (
    count_authored_functions_in_spec_path,
    load_stable_ids_spec_from_path,
    resolve_stable_ids_toml_path_for_fqn_prefix,
)
from aware_meta.graph.config.stable_ids_spec.spec import (
    FunctionSpec,
    LetSpec,
    NamespaceSpec,
    ParamSpec,
    ParsedDefaultPrimitive,
    StableIdsSpec,
)
from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info

# Meta Ontology
from aware_meta_ontology.annotation.code_section_annotation_oneof_enums import (
    CodeSectionAnnotationOneOfMode,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_enums import (
    ClassIdentityMode,
    ClassValueMode,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipIdentityRail,
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionIdentityKeyOrigin,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig

_SNAKE_ACRONYM_RX = re.compile(r"([A-Z]+)([A-Z][a-z])")
_SNAKE_CASE_RX = re.compile(r"([a-z0-9])([A-Z])")
_MODULE_ID_RX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_AWARE_REPO_ROOT_ENV = "AWARE_REPO_ROOT"


@dataclass(frozen=True, slots=True)
class _MissingDefaultType:
    pass


_MISSING_DEFAULT = _MissingDefaultType()

_FQN_MODULE_ID_INDEX: dict[Path, dict[str, str]] = {}

_IdentitySignature = tuple[
    tuple[str, ...], tuple[ParamSpec, ...], tuple[LetSpec, ...], tuple[str, ...]
]
_IdentitySignatureBody = tuple[
    tuple[ParamSpec, ...], tuple[LetSpec, ...], tuple[str, ...]
]


@dataclass(frozen=True, slots=True)
class _ConstructorIdentitySignatures:
    full: _IdentitySignature
    standalone: _IdentitySignature
    has_multiple_signatures: bool = False


@dataclass(frozen=True, slots=True)
class _IdentityOneOfGroupSpec:
    member_attrs: tuple[str, ...]
    discriminator_attribute_name: str | None = None
    discriminator_cases: tuple[tuple[str, str], ...] = ()


def _resolve_explicit_repo_root(repo_root: Path | None) -> Path | None:
    if repo_root is not None:
        return Path(repo_root).expanduser().resolve()
    raw_repo_root = (os.getenv(_AWARE_REPO_ROOT_ENV) or "").strip()
    if raw_repo_root:
        return Path(raw_repo_root).expanduser().resolve()
    return None


def _missing_repo_root_for_default_hooks() -> None:
    raise RuntimeError(
        "stable-id authored spec lookup requires explicit repo_root, "
        f"{_AWARE_REPO_ROOT_ENV}, or caller-provided StableIdsServiceHooks"
    )


def _default_service_hooks(*, repo_root: Path | None = None) -> StableIdsServiceHooks:
    resolved_repo_root = _resolve_explicit_repo_root(repo_root)

    def _resolve_spec_path_for_fqn_prefix(fqn_prefix: str) -> Path | None:
        if resolved_repo_root is None:
            _missing_repo_root_for_default_hooks()
        return resolve_stable_ids_toml_path_for_fqn_prefix(
            fqn_prefix=fqn_prefix,
            repo_root=cast(Path, resolved_repo_root),
        )

    return StableIdsServiceHooks(
        resolve_spec_path_for_fqn_prefix=_resolve_spec_path_for_fqn_prefix,
        load_spec_from_path=lambda spec_path: load_stable_ids_spec_from_path(
            spec_path=spec_path
        ),
        count_authored_functions_in_path=lambda spec_path: count_authored_functions_in_spec_path(
            spec_path=spec_path
        ),
    )


def _to_snake_case(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return raw
    step = _SNAKE_ACRONYM_RX.sub(r"\1_\2", raw)
    step = _SNAKE_CASE_RX.sub(r"\1_\2", step)
    return step.replace("-", "_").casefold()


def _normalize_module_id(raw_module_id: str, *, ctx: str) -> str:
    module_id = (raw_module_id or "").strip().casefold().replace("-", "_")
    if not module_id:
        raise ValueError(f"module id is empty ({ctx})")
    if _MODULE_ID_RX.match(module_id) is None:
        raise ValueError(
            "module id must be identifier-compatible (regex: ^[A-Za-z_][A-Za-z0-9_]*$) "
            + f"({ctx}, got {raw_module_id!r})"
        )
    return module_id


def _module_id_from_fqn_prefix(*, fqn_prefix: str) -> str:
    raw = (fqn_prefix or "").strip()
    if not raw:
        return "module"
    token = raw
    if token.startswith("aware_"):
        token = token[len("aware_") :]
    if not token:
        token = raw
    return _normalize_module_id(token, ctx=f"fqn_prefix={raw!r}")


def _build_fqn_module_id_index(*, repo_root: Path) -> dict[str, str]:
    idx: dict[str, str] = {}
    modules_root = (repo_root / "modules").resolve()
    if not modules_root.exists():
        return idx
    for module_root in sorted(modules_root.iterdir(), key=lambda p: p.as_posix()):
        if not module_root.is_dir():
            continue
        aware_toml = module_root / "structure" / "ontology" / "aware.toml"
        if not aware_toml.exists():
            continue
        try:
            spec = load_aware_toml_spec(toml_path=aware_toml)
        except Exception:
            continue
        if spec.package.kind != AwarePackageKind.ontology:
            continue
        module_id = _normalize_module_id(module_root.name, ctx=str(module_root))
        idx[spec.package.fqn_prefix] = module_id
    return idx


def _resolve_module_id_for_fqn_prefix(*, repo_root: Path, fqn_prefix: str) -> str:
    key = (fqn_prefix or "").strip()
    if not key:
        return "module"
    idx = _FQN_MODULE_ID_INDEX.get(repo_root)
    if idx is None:
        idx = _build_fqn_module_id_index(repo_root=repo_root)
        _FQN_MODULE_ID_INDEX[repo_root] = idx
    module_id = idx.get(key)
    if module_id is not None:
        return module_id
    return _module_id_from_fqn_prefix(fqn_prefix=key)


def _parse_default_value(
    *,
    raw_default: str | None,
    param_type: str,
) -> ParsedDefaultPrimitive | _MissingDefaultType:
    raw = (raw_default or "").strip()
    if not raw or raw.casefold() == "null":
        return _MISSING_DEFAULT
    if param_type == "str":
        if raw[:1] in {'"', "'"}:
            try:
                parsed = cast(object, ast.literal_eval(raw))
            except Exception as exc:  # noqa: BLE001
                raise ValueError(f"invalid string default literal {raw!r}") from exc
            if not isinstance(parsed, str):
                raise ValueError(f"default literal is not a string: {raw!r}")
            return parsed
        return raw
    if param_type == "bool":
        norm = raw.casefold()
        if norm in {"true", "1"}:
            return True
        if norm in {"false", "0"}:
            return False
        raise ValueError(f"invalid bool default literal {raw!r}")
    if param_type == "int":
        try:
            return int(raw)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"invalid int default literal {raw!r}") from exc
    if param_type == "float":
        try:
            return float(raw)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"invalid float default literal {raw!r}") from exc
    return _MISSING_DEFAULT


def _final_default(
    value: ParsedDefaultPrimitive | _MissingDefaultType,
) -> ParsedDefaultPrimitive:
    if isinstance(value, _MissingDefaultType):
        return None
    return value


def _function_attr_position_sort_key(edge: FunctionConfigAttributeConfig) -> int:
    return edge.position


def _class_identity_mode(*, class_config: ClassConfig) -> ClassIdentityMode:
    raw_mode = getattr(class_config, "identity_mode", None)
    if isinstance(raw_mode, ClassIdentityMode):
        return raw_mode
    raw_value = getattr(raw_mode, "value", raw_mode)
    token = str(raw_value or "").strip().casefold()
    if token == ClassIdentityMode.standalone.value:
        return ClassIdentityMode.standalone
    return ClassIdentityMode.contained


def _parse_oneof_discriminator_cases(
    *,
    class_name: str,
    member_attrs: tuple[str, ...],
    raw_cases: tuple[str, ...],
) -> tuple[tuple[str, str], ...]:
    if not raw_cases:
        return ()
    seen_variants: set[str] = set()
    seen_member_attrs: set[str] = set()
    parsed_cases: list[tuple[str, str]] = []
    for raw in raw_cases:
        token = str(raw).strip()
        if "=" not in token:
            raise ValueError(
                "identity oneof discriminator case must use '<variant>=<member_attr>' "
                + f"(class={class_name!r}, case={token!r})"
            )
        variant_raw, member_raw = token.split("=", 1)
        variant = variant_raw.strip()
        member_attr = member_raw.strip()
        if not variant or not member_attr:
            raise ValueError(
                "identity oneof discriminator case requires non-empty variant/member "
                + f"(class={class_name!r}, case={token!r})"
            )
        if variant in seen_variants:
            raise ValueError(
                "identity oneof discriminator case variants must be unique "
                + f"(class={class_name!r}, variant={variant!r})"
            )
        if member_attr in seen_member_attrs:
            raise ValueError(
                "identity oneof discriminator case members must be unique "
                + f"(class={class_name!r}, member={member_attr!r})"
            )
        if member_attr not in member_attrs:
            raise ValueError(
                "identity oneof discriminator case references attribute outside oneof members "
                + f"(class={class_name!r}, member={member_attr!r})"
            )
        seen_variants.add(variant)
        seen_member_attrs.add(member_attr)
        parsed_cases.append((variant, member_attr))
    missing_member_attrs = sorted(set(member_attrs) - seen_member_attrs)
    if missing_member_attrs:
        raise ValueError(
            "identity oneof discriminator cases must cover all oneof members "
            + f"(class={class_name!r}, missing={missing_member_attrs!r})"
        )
    return tuple(sorted(parsed_cases, key=lambda item: item[0]))


def _annotation_namespace_required(value: object, *, context: str) -> str:
    namespace = getattr(value, "namespace", None)
    if not isinstance(namespace, str):
        raise ValueError(f"{context} requires namespace")
    return namespace.strip()


def _collect_identity_oneof_groups_by_class_id(
    *,
    graph: ObjectConfigGraph,
) -> dict[UUID, tuple[_IdentityOneOfGroupSpec, ...]]:
    oneof_views = [
        ann.code_section_annotation_oneof
        for ann in graph.object_config_graph_annotations
        if ann.kind == ObjectConfigGraphAnnotationKind.oneof
        and ann.code_section_annotation_oneof is not None
    ]
    if not oneof_views:
        return {}

    bundle = build_namespace_bundle_from_ocg_topology(ocg=graph)
    class_by_key: dict[tuple[str, str, str], ClassConfig] = {}
    for node in graph.object_config_graph_nodes:
        if node.class_config is None:
            continue
        namespace = bundle.namespace_by_class_config_id.get(node.class_config.id)
        if namespace is None:
            continue
        key = (
            namespace.package,
            namespace.namespace,
            node.class_config.name,
        )
        _ = class_by_key.setdefault(key, node.class_config)

    grouped: dict[UUID, list[_IdentityOneOfGroupSpec]] = {}
    for view in oneof_views:
        if view.mode != CodeSectionAnnotationOneOfMode.identity:
            continue
        class_lookup_key = (
            view.fqn_prefix,
            _annotation_namespace_required(
                view,
                context="identity oneof stable-id resolution",
            ),
            view.class_name,
        )
        cls = class_by_key.get(class_lookup_key)
        if cls is None:
            raise ValueError(
                "Identity oneof annotation target not found: "
                + f"{view.fqn_prefix}.{class_lookup_key[1]}.{view.class_name}"
            )
        attrs = tuple(str(a).strip() for a in view.attribute_names)
        if len(attrs) < 2:
            continue
        discriminator_attribute_name_raw = view.discriminator_attribute_name
        discriminator_attribute_name = discriminator_attribute_name_raw or None
        raw_cases = tuple(
            str(c).strip() for c in view.discriminator_cases if str(c).strip()
        )
        if discriminator_attribute_name is None and raw_cases:
            raise ValueError(
                "identity oneof discriminator cases require discriminator attribute name "
                + f"(class={cls.name!r})"
            )
        if discriminator_attribute_name is not None and not raw_cases:
            raise ValueError(
                "identity oneof discriminator attribute requires cases "
                + f"(class={cls.name!r}, discriminator={discriminator_attribute_name!r})"
            )
        parsed_cases = _parse_oneof_discriminator_cases(
            class_name=cls.name,
            member_attrs=attrs,
            raw_cases=raw_cases,
        )
        grouped.setdefault(cls.id, []).append(
            _IdentityOneOfGroupSpec(
                member_attrs=attrs,
                discriminator_attribute_name=discriminator_attribute_name,
                discriminator_cases=parsed_cases,
            )
        )

    normalized: dict[UUID, tuple[_IdentityOneOfGroupSpec, ...]] = {}
    for class_id, groups in grouped.items():
        seen_members: set[str] = set()
        stable_groups: list[_IdentityOneOfGroupSpec] = []
        for group in groups:
            for attr_name in group.member_attrs:
                if attr_name in seen_members:
                    raise ValueError(
                        "identity oneof annotation groups must not overlap attributes "
                        + f"(class_config_id={class_id}, attribute={attr_name!r})"
                    )
                seen_members.add(attr_name)
            stable_groups.append(group)
        normalized[class_id] = tuple(stable_groups)
    return normalized


def _collect_identity_structural_relations_by_class_id(
    *,
    graph: ObjectConfigGraph,
) -> dict[UUID, str]:
    identity_views = [
        ann.code_section_annotation_identity
        for ann in graph.object_config_graph_annotations
        if ann.kind == ObjectConfigGraphAnnotationKind.identity
        and ann.code_section_annotation_identity is not None
    ]
    if not identity_views:
        return {}

    bundle = build_namespace_bundle_from_ocg_topology(ocg=graph)
    class_by_key: dict[tuple[str, str, str], ClassConfig] = {}
    for node in graph.object_config_graph_nodes:
        if node.class_config is None:
            continue
        namespace = bundle.namespace_by_class_config_id.get(node.class_config.id)
        if namespace is None:
            continue
        key = (
            namespace.package,
            namespace.namespace,
            node.class_config.name,
        )
        _ = class_by_key.setdefault(key, node.class_config)

    relation_by_class_id: dict[UUID, str] = {}
    for view in identity_views:
        relation_name = str(view.structural_relation_name or "").strip()
        if not relation_name:
            continue
        class_lookup_key = (
            view.fqn_prefix,
            _annotation_namespace_required(
                view,
                context="identity structural stable-id resolution",
            ),
            view.class_name,
        )
        cls = class_by_key.get(class_lookup_key)
        if cls is None:
            raise ValueError(
                "Identity annotation target not found: "
                + f"{view.fqn_prefix}.{class_lookup_key[1]}.{view.class_name}"
            )
        prev = relation_by_class_id.get(cls.id)
        if prev is not None and prev != relation_name:
            raise ValueError(
                "identity structural relation must be unique per class "
                + f"(class={cls.name!r}, existing={prev!r}, new={relation_name!r})"
            )
        relation_by_class_id[cls.id] = relation_name
    return relation_by_class_id


def _derive_param_and_template_key(
    *,
    class_name: str,
    function_name: str,
    attr_name: str,
    attr_config: AttributeConfig,
    allow_nullable_uuid: bool = False,
) -> tuple[ParamSpec, LetSpec | None, str]:
    type_info = resolve_type_info(attr_config)
    nullable = bool(type_info.nullable)
    if type_info.enum_config is not None:
        default_value = _parse_default_value(
            raw_default=attr_config.default_value,
            param_type="str",
        )
        optional = nullable and default_value is _MISSING_DEFAULT
        param = ParamSpec(
            name=attr_name,
            type="str",
            optional=optional,
            default=_final_default(default_value),
        )
        norm_name = f"{attr_name}_norm"
        if default_value is _MISSING_DEFAULT:
            let = LetSpec(
                op="normalize",
                name=norm_name,
                param=attr_name,
                normalize=("casefold", "strip"),
            )
        else:
            let = LetSpec(
                op="normalize_default",
                name=norm_name,
                param=attr_name,
                normalize=("casefold", "strip"),
                default=str(default_value),
            )
        return param, let, norm_name

    if type_info.primitive_config is None:
        raise ValueError(
            "constructor identity keys must be primitive/enum-compatible "
            + f"(class={class_name!r}, function={function_name!r}, attribute={attr_name!r})"
        )
    primitive = CodePrimitiveType.model_validate(
        type_info.primitive_config.primitive_type
    )
    base = primitive.base_type

    if type_info.is_collection:
        if base != CodePrimitiveBaseType.string:
            raise ValueError(
                "constructor identity key collection type is unsupported (only collection of string is allowed): "
                + f"class={class_name!r}, function={function_name!r}, attribute={attr_name!r}, base={base.value!r}"
            )
        param = ParamSpec(name=attr_name, type="str_list", optional=nullable)
        let_name = f"{attr_name}_joined"
        let = LetSpec(
            op="list_join",
            name=let_name,
            param=attr_name,
            normalize=("casefold", "strip"),
            sep=":",
            unique=True,
            sort=True,
        )
        return param, let, let_name

    if base == CodePrimitiveBaseType.string:
        default_value = _parse_default_value(
            raw_default=attr_config.default_value,
            param_type="str",
        )
        optional = nullable and default_value is _MISSING_DEFAULT
        param = ParamSpec(
            name=attr_name,
            type="str",
            optional=optional,
            default=_final_default(default_value),
        )
        norm_name = f"{attr_name}_norm"
        if default_value is _MISSING_DEFAULT:
            let = LetSpec(
                op="normalize",
                name=norm_name,
                param=attr_name,
                normalize=("casefold", "strip"),
            )
        else:
            let = LetSpec(
                op="normalize_default",
                name=norm_name,
                param=attr_name,
                normalize=("casefold", "strip"),
                default=str(default_value),
            )
        return param, let, norm_name

    if base == CodePrimitiveBaseType.uuid:
        if nullable:
            if not allow_nullable_uuid:
                raise ValueError(
                    "nullable UUID identity keys are unsupported in auto-generated stable-id formulas "
                    + f"(class={class_name!r}, function={function_name!r}, attribute={attr_name!r})"
                )
            return (
                ParamSpec(name=attr_name, type="uuid", optional=True),
                LetSpec(
                    op="uuid_str_default",
                    name=f"{attr_name}_str",
                    param=attr_name,
                    default="",
                ),
                f"{attr_name}_str",
            )
        if (
            _parse_default_value(
                raw_default=attr_config.default_value,
                param_type="str",
            )
            is not _MISSING_DEFAULT
        ):
            raise ValueError(
                "UUID defaults are unsupported in auto-generated stable-id formulas "
                + f"(class={class_name!r}, function={function_name!r}, attribute={attr_name!r})"
            )
        return ParamSpec(name=attr_name, type="uuid"), None, attr_name

    if base == CodePrimitiveBaseType.bytes:
        if nullable:
            raise ValueError(
                "nullable bytes identity keys are unsupported in auto-generated stable-id formulas "
                + f"(class={class_name!r}, function={function_name!r}, attribute={attr_name!r})"
            )
        if (
            _parse_default_value(
                raw_default=attr_config.default_value,
                param_type="str",
            )
            is not _MISSING_DEFAULT
        ):
            raise ValueError(
                "bytes defaults are unsupported in auto-generated stable-id formulas "
                + f"(class={class_name!r}, function={function_name!r}, attribute={attr_name!r})"
            )
        hex_name = f"{attr_name}_hex"
        return (
            ParamSpec(name=attr_name, type="bytes"),
            LetSpec(op="hex", name=hex_name, param=attr_name),
            hex_name,
        )

    if base == CodePrimitiveBaseType.boolean:
        default_value = _parse_default_value(
            raw_default=attr_config.default_value,
            param_type="bool",
        )
        if nullable and default_value is _MISSING_DEFAULT:
            raise ValueError(
                "nullable bool identity keys require a non-null default in auto-generated stable-id formulas "
                + f"(class={class_name!r}, function={function_name!r}, attribute={attr_name!r})"
            )
        param = ParamSpec(
            name=attr_name,
            type="bool",
            optional=nullable and default_value is _MISSING_DEFAULT,
            default=_final_default(default_value),
        )
        int_name = f"{attr_name}_int"
        return (
            param,
            LetSpec(op="bool_int", name=int_name, param=attr_name),
            int_name,
        )

    if base == CodePrimitiveBaseType.integer:
        default_value = _parse_default_value(
            raw_default=attr_config.default_value,
            param_type="int",
        )
        if nullable and default_value is _MISSING_DEFAULT:
            raise ValueError(
                "nullable int identity keys require a non-null default in auto-generated stable-id formulas "
                + f"(class={class_name!r}, function={function_name!r}, attribute={attr_name!r})"
            )
        return (
            ParamSpec(
                name=attr_name,
                type="int",
                optional=nullable and default_value is _MISSING_DEFAULT,
                default=_final_default(default_value),
            ),
            None,
            attr_name,
        )

    if base == CodePrimitiveBaseType.float:
        default_value = _parse_default_value(
            raw_default=attr_config.default_value,
            param_type="float",
        )
        if nullable and default_value is _MISSING_DEFAULT:
            raise ValueError(
                "nullable float identity keys require a non-null default in auto-generated stable-id formulas "
                + f"(class={class_name!r}, function={function_name!r}, attribute={attr_name!r})"
            )
        return (
            ParamSpec(
                name=attr_name,
                type="float",
                optional=nullable and default_value is _MISSING_DEFAULT,
                default=_final_default(default_value),
            ),
            None,
            attr_name,
        )

    raise ValueError(
        "unsupported identity key primitive type for auto-generated stable-id formulas "
        + f"(class={class_name!r}, function={function_name!r}, attribute={attr_name!r}, base={base.value!r})"
    )


def _derive_class_identity_signature(
    *,
    class_config: ClassConfig,
    class_name: str,
    identity_oneof_groups: tuple[_IdentityOneOfGroupSpec, ...] = (),
    identity_structural_relation_name: str | None = None,
) -> (
    tuple[tuple[str, ...], tuple[ParamSpec, ...], tuple[LetSpec, ...], tuple[str, ...]]
    | None
):
    identity_params: list[ParamSpec] = []
    identity_lets: list[LetSpec] = []
    identity_keys: list[str] = []
    template_keys: list[str] = []
    class_identity_mode = _class_identity_mode(class_config=class_config)
    class_attrs = list(class_config.class_config_attribute_configs)
    class_attr_by_attribute_id: dict[str, ClassConfigAttributeConfig] = {
        str(edge.attribute_config_id): edge for edge in class_attrs
    }
    # Ordering rail for identity attributes:
    # 0 = containment parent FK anchors
    # 1 = non-containment FK identity attributes
    # 2 = non-FK class identity attributes
    fk_attr_rank_by_attr_id: dict[str, int] = {}
    containment_fk_attr_ids: set[str] = set()
    for relationship in class_config.class_config_relationships:
        identity_rail = relationship.identity_rail
        if identity_rail is ClassConfigRelationshipIdentityRail.containment:
            fk_rank = 0
        elif (
            identity_rail is ClassConfigRelationshipIdentityRail.reference
            or identity_rail is None
        ):
            fk_rank = 1
        else:
            raise ValueError(
                "unsupported relationship identity_rail for stable-id ordering "
                + f"(relationship_id={relationship.id}, identity_rail={identity_rail!r})"
            )
        for rel_attr in relationship.class_config_relationship_attributes:
            if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                continue
            rel_attr_id = str(rel_attr.attribute_config_id)
            if rel_attr_id in class_attr_by_attribute_id:
                prev_rank = fk_attr_rank_by_attr_id.get(rel_attr_id)
                if prev_rank is None or fk_rank < prev_rank:
                    fk_attr_rank_by_attr_id[rel_attr_id] = fk_rank
                if identity_rail is ClassConfigRelationshipIdentityRail.containment:
                    containment_fk_attr_ids.add(rel_attr_id)
    class_attrs.sort(
        key=lambda edge: (
            fk_attr_rank_by_attr_id.get(str(edge.attribute_config_id), 2),
            edge.position,
            str(edge.attribute_config.name or "").casefold(),
            str(edge.id),
        )
    )
    class_attr_by_name: dict[str, ClassConfigAttributeConfig] = {}
    for class_attr in class_attrs:
        attr_name = str(class_attr.attribute_config.name or "").strip()
        if not attr_name:
            continue
        _ = class_attr_by_name.setdefault(attr_name, class_attr)
    legacy_identity_oneof_attr_names: set[str] = set()
    discriminated_identity_oneof_groups: list[_IdentityOneOfGroupSpec] = []
    discriminated_identity_oneof_attr_names: set[str] = set()
    for group in identity_oneof_groups:
        for attr_name in group.member_attrs:
            class_attr = class_attr_by_name.get(attr_name)
            if class_attr is None:
                raise ValueError(
                    "identity oneof annotation references unknown class attribute for stable-id derivation "
                    + f"(class={class_name!r}, attribute={attr_name!r})"
                )
        if group.discriminator_attribute_name is None:
            legacy_identity_oneof_attr_names.update(group.member_attrs)
            continue
        discriminator_attribute_name = str(group.discriminator_attribute_name).strip()
        discriminator_class_attr = class_attr_by_name.get(discriminator_attribute_name)
        if discriminator_class_attr is None:
            raise ValueError(
                "identity oneof discriminator attribute does not exist on class "
                + f"(class={class_name!r}, attribute={discriminator_attribute_name!r})"
            )
        if not discriminator_class_attr.is_identity_key:
            raise ValueError(
                "identity oneof discriminator attribute must be declared as class identity key "
                + f"(class={class_name!r}, attribute={discriminator_attribute_name!r})"
            )
        discriminated_identity_oneof_groups.append(group)
        discriminated_identity_oneof_attr_names.update(group.member_attrs)
    for attr_name in legacy_identity_oneof_attr_names:
        class_attr = class_attr_by_name.get(attr_name)
        if class_attr is None:
            continue
        if not class_attr.is_identity_key:
            raise ValueError(
                "identity oneof annotation requires each member attribute to be declared as class identity key "
                + f"(class={class_name!r}, attribute={attr_name!r})"
            )
    seen_identity_attr_names: set[str] = set()
    seen_identity_source_attr_names: set[str] = set()
    for class_attr in class_attrs:
        if not class_attr.is_identity_key:
            continue
        if (
            class_identity_mode is ClassIdentityMode.standalone
            and str(class_attr.attribute_config_id) in containment_fk_attr_ids
        ):
            continue
        source_attr_name = str(class_attr.attribute_config.name or "").strip()
        if source_attr_name in discriminated_identity_oneof_attr_names:
            raise ValueError(
                "discriminator-based identity oneof member attributes must not be direct class identity keys "
                + f"(class={class_name!r}, attribute={source_attr_name!r})"
            )
        attr_config = class_attr.attribute_config
        type_info = resolve_type_info(attr_config)
        if type_info.enum_config is None and type_info.primitive_config is None:
            fk_attr = _resolve_relationship_identity_key_fk_attribute(
                class_config=class_config,
                class_attr=class_attr,
                class_name=class_name,
                class_attr_by_attribute_id=class_attr_by_attribute_id,
            )
            attr_config = fk_attr.attribute_config
        attr_name = str(attr_config.name or "").strip()
        if not attr_name:
            continue
        if attr_name in seen_identity_attr_names:
            continue
        param, let, template_key = _derive_param_and_template_key(
            class_name=class_name,
            function_name="<class_identity_keys>",
            attr_name=attr_name,
            attr_config=attr_config,
            allow_nullable_uuid=source_attr_name in legacy_identity_oneof_attr_names,
        )
        seen_identity_attr_names.add(attr_name)
        if source_attr_name:
            seen_identity_source_attr_names.add(source_attr_name)
        identity_keys.append(attr_name)
        identity_params.append(param)
        if let is not None:
            identity_lets.append(let)
        template_keys.append(template_key)
    missing_identity_oneof_attrs = sorted(
        legacy_identity_oneof_attr_names - seen_identity_source_attr_names
    )
    if missing_identity_oneof_attrs:
        raise ValueError(
            "identity oneof annotation members must resolve to stable-id identity parameters "
            + f"(class={class_name!r}, missing={missing_identity_oneof_attrs!r})"
        )
    total_discriminated_groups = len(discriminated_identity_oneof_groups)
    if total_discriminated_groups > 1:
        raise ValueError(
            "multiple discriminator-based identity oneof groups are not supported yet "
            + f"(class={class_name!r}, groups={total_discriminated_groups})"
        )
    has_structural_relation = bool((identity_structural_relation_name or "").strip())
    for group in discriminated_identity_oneof_groups:
        discriminator_attribute_name = str(
            group.discriminator_attribute_name or ""
        ).strip()
        if discriminator_attribute_name not in seen_identity_source_attr_names:
            raise ValueError(
                "identity oneof discriminator attribute must resolve to an identity parameter "
                + f"(class={class_name!r}, attribute={discriminator_attribute_name!r})"
            )
        for _variant, member_attr_name in group.discriminator_cases:
            member_class_attr = class_attr_by_name.get(member_attr_name)
            if member_class_attr is None:
                raise ValueError(
                    "identity oneof discriminator case references unknown class attribute "
                    + f"(class={class_name!r}, attribute={member_attr_name!r})"
                )
            member_attr_config = member_class_attr.attribute_config
            member_type_info = resolve_type_info(member_attr_config)
            if (
                member_type_info.enum_config is None
                and member_type_info.primitive_config is None
            ):
                resolved_fk_attr = _resolve_relationship_identity_key_fk_attribute(
                    class_config=class_config,
                    class_attr=member_class_attr,
                    class_name=class_name,
                    class_attr_by_attribute_id=class_attr_by_attribute_id,
                )
                member_attr_config = resolved_fk_attr.attribute_config
                member_type_info = resolve_type_info(member_attr_config)
            if (
                member_type_info.is_collection
                or member_type_info.primitive_config is None
            ):
                raise ValueError(
                    "identity oneof discriminator members must resolve to scalar UUID identity anchors "
                    + f"(class={class_name!r}, member={member_attr_name!r})"
                )
            primitive = CodePrimitiveType.model_validate(
                member_type_info.primitive_config.primitive_type
            )
            if primitive.base_type != CodePrimitiveBaseType.uuid:
                raise ValueError(
                    "identity oneof discriminator members must resolve to UUID identity anchors "
                    + f"(class={class_name!r}, member={member_attr_name!r}, base={primitive.base_type.value!r})"
                )
        entity_param_name = (
            "entity_id"
            if total_discriminated_groups == 1
            else f"{discriminator_attribute_name}_entity_id"
        )
        if entity_param_name in seen_identity_attr_names:
            raise ValueError(
                "identity oneof discriminator synthetic parameter collides with existing identity parameter "
                + f"(class={class_name!r}, param={entity_param_name!r})"
            )
        seen_identity_attr_names.add(entity_param_name)
        identity_keys.append(entity_param_name)
        if has_structural_relation:
            entity_template_key = f"{entity_param_name}_str"
            identity_params.append(
                ParamSpec(name=entity_param_name, type="uuid", optional=True)
            )
            identity_lets.append(
                LetSpec(
                    op="uuid_str_default",
                    name=entity_template_key,
                    param=entity_param_name,
                    default="",
                )
            )
            template_keys.append(entity_template_key)
        else:
            identity_params.append(ParamSpec(name=entity_param_name, type="uuid"))
            template_keys.append(entity_param_name)
    if has_structural_relation:
        relation_name = str(identity_structural_relation_name or "").strip()
        reference_relation_attrs: list[AttributeConfig] = []
        for relationship in class_config.class_config_relationships:
            for rel_attr in relationship.class_config_relationship_attributes:
                if rel_attr.role != ClassConfigRelationshipAttributeRole.reference:
                    continue
                class_attr_edge = class_attr_by_attribute_id.get(
                    str(rel_attr.attribute_config_id)
                )
                relation_attr = (
                    class_attr_edge.attribute_config
                    if class_attr_edge is not None
                    and class_attr_edge.attribute_config is not None
                    else rel_attr.attribute_config
                )
                if relation_attr is None:
                    continue
                if str(relation_attr.name or "").strip() != relation_name:
                    continue
                reference_relation_attrs.append(relation_attr)
        if not reference_relation_attrs:
            raise ValueError(
                "identity structural relation annotation references unknown relation "
                + f"(class={class_name!r}, relation={relation_name!r})"
            )
        if len(reference_relation_attrs) > 1:
            raise ValueError(
                "identity structural relation annotation resolved to multiple relation rails "
                + f"(class={class_name!r}, relation={relation_name!r})"
            )
        relation_attr = reference_relation_attrs[0]
        relation_type_info = resolve_type_info(relation_attr)
        if not relation_type_info.is_collection:
            raise ValueError(
                "identity structural relation must target a collection rail "
                + f"(class={class_name!r}, relation={relation_name!r})"
            )
        fingerprint_param_name = f"{relation_name}_fingerprint"
        if fingerprint_param_name in seen_identity_attr_names:
            raise ValueError(
                "identity structural relation synthetic parameter collides with existing identity parameter "
                + f"(class={class_name!r}, param={fingerprint_param_name!r})"
            )
        seen_identity_attr_names.add(fingerprint_param_name)
        identity_keys.append(fingerprint_param_name)
        identity_params.append(
            ParamSpec(name=fingerprint_param_name, type="str", default="")
        )
        template_keys.append(fingerprint_param_name)
    if not identity_keys:
        return None
    return (
        tuple(identity_keys),
        tuple(identity_params),
        tuple(identity_lets),
        tuple(template_keys),
    )


def _resolve_relationship_identity_key_fk_attribute(
    *,
    class_config: ClassConfig,
    class_attr: ClassConfigAttributeConfig,
    class_name: str,
    class_attr_by_attribute_id: dict[str, ClassConfigAttributeConfig],
) -> ClassConfigAttributeConfig:
    reference_attr_id = str(class_attr.attribute_config_id)
    candidate_fk_edges: dict[str, ClassConfigAttributeConfig] = {}

    for relationship in class_config.class_config_relationships:
        reference_match = False
        for rel_attr in relationship.class_config_relationship_attributes:
            if rel_attr.role != ClassConfigRelationshipAttributeRole.reference:
                continue
            side = (
                relationship.class_config_id == class_config.id
                and rel_attr.direction == ClassConfigRelationshipDirection.forward
            ) or (
                relationship.target_class_config_id == class_config.id
                and rel_attr.direction == ClassConfigRelationshipDirection.reverse
            )
            if not side:
                continue
            if str(rel_attr.attribute_config_id) != reference_attr_id:
                continue
            reference_match = True
            break
        if not reference_match:
            continue

        for rel_attr in relationship.class_config_relationship_attributes:
            if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                continue
            fk_edge = class_attr_by_attribute_id.get(str(rel_attr.attribute_config_id))
            if fk_edge is None:
                continue
            candidate_fk_edges[str(fk_edge.attribute_config_id)] = fk_edge

    if not candidate_fk_edges:
        raise ValueError(
            "class identity key on relationship reference must resolve to a class-owned foreign key "
            + "(post-transform runtime graph contract); "
            + f"class={class_name!r}, reference_attribute={class_attr.attribute_config.name!r}"
        )
    if len(candidate_fk_edges) > 1:
        candidate_names = ", ".join(
            sorted(edge.attribute_config.name for edge in candidate_fk_edges.values())
        )
        raise ValueError(
            "class identity key on relationship reference resolved to multiple class-owned foreign keys; "
            + f"class={class_name!r}, reference_attribute={class_attr.attribute_config.name!r}, "
            + f"candidates=[{candidate_names}]"
        )
    return next(iter(candidate_fk_edges.values()))


def _identity_key_origin_for_function_attribute(
    *, fn_attr: FunctionConfigAttributeConfig
) -> FunctionIdentityKeyOrigin:
    raw_origin = fn_attr.identity_key_origin
    origin_value = str(raw_origin.value).strip().casefold()
    if origin_value in {"", FunctionIdentityKeyOrigin.standalone.value}:
        return FunctionIdentityKeyOrigin.standalone
    if origin_value == FunctionIdentityKeyOrigin.propagated_parent.value:
        return FunctionIdentityKeyOrigin.propagated_parent
    raise ValueError(
        "unsupported function identity_key_origin for stable-id derivation "
        + f"(fn_attr_id={fn_attr.id}, value={raw_origin!r})"
    )


def _derive_constructor_identity_signature(
    *,
    class_config: ClassConfig,
    class_name: str,
    allow_multiple_signatures: bool = False,
) -> _ConstructorIdentitySignatures | None:
    signatures: dict[
        tuple[str, ...],
        tuple[
            _IdentitySignatureBody,
            _IdentitySignature,
        ],
    ] = {}
    signature_functions: dict[tuple[str, ...], list[str]] = {}
    fn_links: list[ClassConfigFunctionConfig] = list(
        class_config.class_config_function_configs
    )
    fn_links.sort(
        key=lambda edge: (
            str(edge.function_config.name),
            str(edge.id),
        )
    )
    for fn_link in fn_links:
        function_config: FunctionConfig = fn_link.function_config
        verb = str(function_config.verb or "").strip().casefold()
        is_constructor = bool(fn_link.is_constructor)
        if not is_constructor and verb != "construct":
            continue
        function_name = str(function_config.name or "").strip()
        if not function_name:
            function_name = "<anonymous>"

        identity_params: list[ParamSpec] = []
        identity_lets: list[LetSpec] = []
        identity_keys: list[str] = []
        template_keys: list[str] = []
        standalone_params: list[ParamSpec] = []
        standalone_lets: list[LetSpec] = []
        standalone_keys: list[str] = []
        standalone_template_keys: list[str] = []
        fn_attrs: list[FunctionConfigAttributeConfig] = list(
            function_config.function_config_attribute_configs
        )
        fn_attrs.sort(key=_function_attr_position_sort_key)
        for fn_attr in fn_attrs:
            if fn_attr.type != FunctionAttributeType.input:
                continue
            attr_config = fn_attr.attribute_config
            attr_name = attr_config.name.strip()
            try:
                param, let, template_key = _derive_param_and_template_key(
                    class_name=class_name,
                    function_name=function_name,
                    attr_name=attr_name,
                    attr_config=attr_config,
                )
            except ValueError:
                if fn_attr.is_identity_key:
                    raise
                continue
            if not fn_attr.is_identity_key:
                continue
            identity_keys.append(attr_name)
            identity_params.append(param)
            if let is not None:
                identity_lets.append(let)
            template_keys.append(template_key)
            origin = _identity_key_origin_for_function_attribute(fn_attr=fn_attr)
            if origin == FunctionIdentityKeyOrigin.propagated_parent:
                continue
            standalone_keys.append(attr_name)
            standalone_params.append(param)
            if let is not None:
                standalone_lets.append(let)
            standalone_template_keys.append(template_key)

        if not identity_keys:
            continue
        key_tuple = tuple(identity_keys)
        signature_functions.setdefault(key_tuple, []).append(function_name)
        full_signature_body: _IdentitySignatureBody = (
            tuple(identity_params),
            tuple(identity_lets),
            tuple(template_keys),
        )
        standalone_signature: _IdentitySignature = (
            tuple(standalone_keys),
            tuple(standalone_params),
            tuple(standalone_lets),
            tuple(standalone_template_keys),
        )
        signature = (full_signature_body, standalone_signature)
        existing = signatures.get(key_tuple)
        if existing is None:
            signatures[key_tuple] = signature
        elif existing != signature:
            raise ValueError(
                "constructor identity keys resolve to conflicting stable-id formula semantics "
                + f"(class={class_name!r}, function={function_name!r}, keys={list(key_tuple)!r})"
            )

    if not signatures:
        return None
    if len(signatures) > 1 and not allow_multiple_signatures:
        details = ", ".join(
            f"{'/'.join(sorted(signature_functions[keys]))}({', '.join(keys)})"
            for keys in sorted(signatures.keys())
        )
        raise ValueError(
            f"class {class_name!r} has multiple constructor identity key signatures ({details})"
        )

    signature_keys = next(
        iter(sorted(signatures.keys()))
        if len(signatures) > 1
        else iter(signatures.keys())
    )
    full_signature_body, standalone_signature = signatures[signature_keys]
    return _ConstructorIdentitySignatures(
        full=(
            signature_keys,
            full_signature_body[0],
            full_signature_body[1],
            full_signature_body[2],
        ),
        standalone=standalone_signature,
        has_multiple_signatures=len(signatures) > 1,
    )


def _signature_shape_relaxed(
    signature: tuple[
        tuple[str, ...], tuple[ParamSpec, ...], tuple[LetSpec, ...], tuple[str, ...]
    ],
) -> tuple[tuple[str, str, str], ...]:
    _signature_keys, params, _lets, template_keys = signature
    if len(params) != len(template_keys):
        raise ValueError(
            "stable-id signature internal mismatch: params/template cardinality diverged "
            + f"(params={len(params)}, template_keys={len(template_keys)})"
        )
    entries = tuple(
        sorted(
            (param.name, param.type, template_keys[idx])
            for idx, param in enumerate(params)
        )
    )
    return entries


def _derive_functions_from_graph(
    *,
    graph: ObjectConfigGraph,
    resolution_policy: StableIdsResolutionPolicy = "class_strict",
) -> tuple[FunctionSpec, ...]:
    _ = resolution_policy
    class_nodes: list[ObjectConfigGraphNode] = list(graph.object_config_graph_nodes)
    class_configs: list[ClassConfig] = [
        node.class_config for node in class_nodes if node.class_config is not None
    ]
    class_configs.sort(key=lambda cc: (str(cc.name or "").casefold(), str(cc.id)))
    identity_oneof_groups_by_class_id = _collect_identity_oneof_groups_by_class_id(
        graph=graph
    )
    identity_structural_relations_by_class_id = (
        _collect_identity_structural_relations_by_class_id(graph=graph)
    )
    strict_missing_graph_ref_class_identity: list[str] = []
    strict_constructor_without_class_identity: list[str] = []
    functions: list[FunctionSpec] = []
    for class_config in class_configs:
        class_name = class_config.name.strip()
        class_value_mode = class_config.value_mode
        class_identity_mode = _class_identity_mode(class_config=class_config)
        class_signature = _derive_class_identity_signature(
            class_config=class_config,
            class_name=class_name,
            identity_oneof_groups=identity_oneof_groups_by_class_id.get(
                class_config.id, ()
            ),
            identity_structural_relation_name=identity_structural_relations_by_class_id.get(
                class_config.id
            ),
        )
        identity_oneof_groups = identity_oneof_groups_by_class_id.get(
            class_config.id, ()
        )
        has_discriminator_identity_oneof = any(
            bool(group.discriminator_attribute_name) for group in identity_oneof_groups
        )
        constructor_signatures = _derive_constructor_identity_signature(
            class_config=class_config,
            class_name=class_name,
            allow_multiple_signatures=has_discriminator_identity_oneof,
        )
        constructor_signature = (
            constructor_signatures.full if constructor_signatures is not None else None
        )
        constructor_standalone_signature = (
            constructor_signatures.standalone
            if constructor_signatures is not None
            else None
        )

        if class_value_mode == ClassValueMode.graph_ref and class_signature is None:
            strict_missing_graph_ref_class_identity.append(class_name)
        if class_signature is None and constructor_signature is not None:
            constructor_signature_keys = ", ".join(constructor_signature[0]) or "<none>"
            strict_constructor_without_class_identity.append(
                f"{class_name}(constructor_keys=[{constructor_signature_keys}])"
            )
        if class_signature is None:
            continue
        if (
            constructor_signature is not None
            and constructor_standalone_signature is not None
            and class_identity_mode is ClassIdentityMode.contained
            and _signature_shape_relaxed(class_signature)
            == _signature_shape_relaxed(constructor_standalone_signature)
            and _signature_shape_relaxed(constructor_signature)
            != _signature_shape_relaxed(constructor_standalone_signature)
        ):
            signature_keys, params, lets, signature_template_keys = (
                constructor_signature
            )
            doc_prefix = "Compiler-generated from constructor identity keys: "
        else:
            signature_keys, params, lets, signature_template_keys = class_signature
            doc_prefix = "Compiler-generated from class-attribute identity keys: "
        class_snake = _to_snake_case(class_name)
        if not class_snake:
            raise ValueError(
                f"class name cannot be normalized for stable-id generation: {class_name!r}"
            )
        if signature_template_keys:
            template = f"aware:{class_snake}:" + ":".join(
                f"{{{key}}}" for key in signature_template_keys
            )
        else:
            template = f"aware:{class_snake}"
        functions.append(
            FunctionSpec(
                name=f"stable_{class_snake}_id",
                namespace="",
                template=template,
                params=params,
                lets=lets,
                doc=(doc_prefix + ", ".join(signature_keys)),
            )
        )
    error_parts: list[str] = []
    if strict_missing_graph_ref_class_identity:
        missing = ", ".join(sorted(set(strict_missing_graph_ref_class_identity)))
        error_parts.append(f"missing_graph_ref_class_identity_keys=[{missing}]")
    if strict_constructor_without_class_identity:
        constructor_only = ", ".join(
            sorted(set(strict_constructor_without_class_identity))
        )
        error_parts.append(
            f"constructor_identity_without_class_identity=[{constructor_only}]"
        )
    if error_parts:
        raise ValueError(
            "class_strict stable-id resolution failed; " + "; ".join(error_parts)
        )
    return tuple(functions)


def _derive_stable_ids_spec_from_graph(
    *,
    graph: ObjectConfigGraph,
    fqn_prefix: str,
    base_spec: StableIdsSpec | None,
    repo_root: Path | None = None,
    resolution_policy: StableIdsResolutionPolicy = "class_strict",
) -> StableIdsSpec | None:
    derived_functions = _derive_functions_from_graph(
        graph=graph,
        resolution_policy=resolution_policy,
    )
    if not derived_functions:
        return base_spec

    if repo_root is None:
        module_id = _module_id_from_fqn_prefix(fqn_prefix=fqn_prefix)
    else:
        module_id = _resolve_module_id_for_fqn_prefix(
            repo_root=repo_root,
            fqn_prefix=fqn_prefix,
        )
    namespace_name = f"NS_{module_id.upper()}"
    namespaces: list[NamespaceSpec] = []
    if base_spec is not None:
        namespaces.extend(base_spec.namespaces)

    if not any(ns.name == namespace_name for ns in namespaces):
        namespaces.append(
            NamespaceSpec(
                name=namespace_name,
                kind="ns_url",
                value=f"aware://{module_id}/v1",
            )
        )
    normalized_functions = tuple(
        FunctionSpec(
            name=fn.name,
            namespace=namespace_name,
            template=fn.template,
            params=fn.params,
            lets=fn.lets,
            doc=fn.doc,
            dart_name=fn.dart_name,
        )
        for fn in derived_functions
    )
    return StableIdsSpec(
        version=1,
        namespaces=tuple(namespaces),
        functions=normalized_functions,
    )


def _normalize_ownership_mode(*, ownership: str) -> StableIdsOwnershipMode:
    ownership_mode = str(ownership or "authored").strip().lower() or "authored"
    if ownership_mode not in {"authored", "compiler"}:
        raise ValueError(
            f"stable_ids ownership must be one of authored|compiler (got {ownership!r})"
        )
    return cast(StableIdsOwnershipMode, ownership_mode)


def _normalize_resolution_policy(
    *, resolution_policy: str
) -> StableIdsResolutionPolicy:
    mode = str(resolution_policy or "class_strict").strip().lower() or "class_strict"
    if mode != "class_strict":
        raise ValueError(
            f"stable_ids resolution policy must be class_strict (got {resolution_policy!r})"
        )
    return cast(StableIdsResolutionPolicy, mode)


def _resolve_stable_ids_spec(
    *,
    fqn_prefix: str,
    graph: ObjectConfigGraph | None,
    ownership: str,
    resolution_policy: str,
    hooks: StableIdsServiceHooks,
    repo_root: Path | None = None,
) -> StableIdsSpec | None:
    ownership_mode = _normalize_ownership_mode(ownership=ownership)
    resolution_mode = _normalize_resolution_policy(resolution_policy=resolution_policy)
    if ownership_mode == "compiler":
        # Compiler ownership is single-rail fail-closed graph-derivation only.
        # Source must be the post-aware_to_runtime Aware graph provided by the caller.
        if graph is None:
            raise ValueError(
                "compiler-owned stable ids require an explicit source graph "
                + f"(fqn_prefix={fqn_prefix!r})"
            )
        if graph.language != CodeLanguage.aware:
            raise ValueError(
                "compiler-owned stable ids require an Aware source graph "
                + f"(fqn_prefix={fqn_prefix!r}, language={graph.language.value!r})"
            )
        derived_spec = _derive_stable_ids_spec_from_graph(
            graph=graph,
            fqn_prefix=fqn_prefix,
            base_spec=None,
            repo_root=repo_root,
            resolution_policy=resolution_mode,
        )
        if derived_spec is None:
            spec_path = hooks.resolve_spec_path_for_fqn_prefix(fqn_prefix)
            authored_function_count = (
                hooks.count_authored_functions_in_path(spec_path)
                if spec_path is not None
                else 0
            )
            if authored_function_count > 0:
                raise ValueError(
                    "compiler-owned stable ids derived no formulas from class-attribute identity keys "
                    + f"(fqn_prefix={fqn_prefix!r}, authored_functions={authored_function_count}). "
                    + "Migrate legacy formulas to key+propagation contracts before enabling compiler ownership."
                )
        return derived_spec

    spec_path = hooks.resolve_spec_path_for_fqn_prefix(fqn_prefix)
    source_spec: StableIdsSpec | None = None
    if spec_path is not None:
        source_spec = hooks.load_spec_from_path(spec_path)
        if source_spec.functions:
            return source_spec
    if graph is None:
        return source_spec
    return _derive_stable_ids_spec_from_graph(
        graph=graph,
        fqn_prefix=fqn_prefix,
        base_spec=source_spec,
        repo_root=repo_root,
        resolution_policy=resolution_mode,
    )


def load_stable_ids_spec_for_fqn_prefix(
    *,
    fqn_prefix: str,
    ownership: str = "authored",
    resolution_policy: str = "class_strict",
    hooks: StableIdsServiceHooks | None = None,
    repo_root: Path | None = None,
) -> StableIdsSpec | None:
    resolved_repo_root = _resolve_explicit_repo_root(repo_root)
    service_hooks = hooks or _default_service_hooks(repo_root=resolved_repo_root)
    return _resolve_stable_ids_spec(
        fqn_prefix=fqn_prefix,
        graph=None,
        ownership=ownership,
        resolution_policy=resolution_policy,
        hooks=service_hooks,
        repo_root=resolved_repo_root,
    )


def load_stable_ids_spec_for_graph(
    *,
    graph: ObjectConfigGraph,
    ownership: str = "authored",
    resolution_policy: str = "class_strict",
    hooks: StableIdsServiceHooks | None = None,
    repo_root: Path | None = None,
) -> StableIdsSpec | None:
    resolved_repo_root = _resolve_explicit_repo_root(repo_root)
    service_hooks = hooks or _default_service_hooks(repo_root=resolved_repo_root)
    return _resolve_stable_ids_spec(
        fqn_prefix=graph.fqn_prefix,
        graph=graph,
        ownership=ownership,
        resolution_policy=resolution_policy,
        hooks=service_hooks,
        repo_root=resolved_repo_root,
    )


__all__ = [
    "load_stable_ids_spec_for_graph",
    "load_stable_ids_spec_for_fqn_prefix",
]
