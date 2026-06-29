"""Canonical annotation compiler (generic, grammar-agnostic).

Converts primitive `CodeSectionAnnotation` entries into ontology-level annotation views
(load/overlay/override/...) and wraps them as `ObjectConfigGraphAnnotation` records.

Genesis invariant:
- `ann ... project ...` is deprecated and rejected; projections must be declared via
  first-class `projection { ... }` blocks.

Key invariants:
- Grammar emits primitive CodeSectionAnnotation sections (path/verb/args).
- Canonical meta layer resolves targets deterministically via FqnResolver/FqnScope.
    - The compiled views persist fully qualified namespace fields (fqn_prefix/namespace)
  so downstream consumers never need to re-guess resolution.
"""

import json
from dataclasses import dataclass
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.annotation.code_section_annotation import CodeSectionAnnotation

# Meta Ontology (annotations)
from aware_meta_ontology.annotation.code_section_annotation_load import (
    CodeSectionAnnotationLoad,
)
from aware_meta_ontology.annotation.code_section_annotation_overlay import (
    CodeSectionAnnotationOverlay,
)
from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.annotation.code_section_annotation_override import (
    CodeSectionAnnotationOverride,
)
from aware_meta_ontology.annotation.code_section_annotation_override_enums import (
    CodeSectionAnnotationOverrideTarget,
)
from aware_meta_ontology.annotation.code_section_annotation_discriminate import (
    CodeSectionAnnotationDiscriminate,
)
from aware_meta_ontology.annotation.code_section_annotation_identity import (
    CodeSectionAnnotationIdentity,
)
from aware_meta_ontology.annotation.code_section_annotation_oneof import (
    CodeSectionAnnotationOneOf,
)
from aware_meta_ontology.annotation.code_section_annotation_oneof_enums import (
    CodeSectionAnnotationOneOfMode,
)
from aware_meta_ontology.annotation.code_section_annotation_reference import (
    CodeSectionAnnotationReference,
)
from aware_meta_ontology.annotation.code_section_annotation_index import (
    CodeSectionAnnotationIndex,
)
from aware_meta_ontology.annotation.code_section_annotation_storage import (
    CodeSectionAnnotationStorage,
)
from aware_meta_ontology.annotation.code_section_annotation_storage_enums import (
    CodeSectionAnnotationStorageOperation,
)
from aware_meta_ontology.annotation.code_section_annotation_reference_enums import (
    CodeSectionAnnotationReferenceMode,
)

from aware_meta_ontology.graph.config.object_config_graph_annotation import (
    ObjectConfigGraphAnnotation,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassIdentityMode
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipSideLoadingStrategy,
)

# Meta Runtime (FQN resolution)
from aware_meta.fqn_resolver import FqnResolver, FqnScope

from aware_meta.graph.config.stable_ids import ocg_stable_uuid


def _split_member_path(path: str) -> tuple[str, list[str]]:
    """
    Split an annotation path into a type reference and optional member segments.

    Canonical rule:
    - Dots belong to the type reference (FQN-style): package.namespace.Name
    - `::` separates members within a type (attribute/function/edge/etc)
    """
    raw = (path or "").strip()
    if not raw:
        return "", []
    parts = [p for p in raw.split("::") if p]
    type_ref = parts[0].strip()
    members = [p.strip() for p in parts[1:]]
    return type_ref, members


def _parse_strategy(value: str) -> ClassConfigRelationshipSideLoadingStrategy | None:
    if not value:
        return None
    lowered = value.strip().lower()
    if lowered == "eager":
        return ClassConfigRelationshipSideLoadingStrategy.eager
    if lowered == "lazy":
        return ClassConfigRelationshipSideLoadingStrategy.lazy
    return None


def parse_load_args(args: list[str]):
    """
    Interpret ANN `load` arguments into forward/reverse strategies.

    Contract (current canonical representation):
    - `load` is the SSOT for relationship pointer semantics on the canonical model.
    - Loading semantics are also serialization semantics for the canonical model
      (round-trippable by design; we use Pydantic to enforce deterministic shapes).
    - Import strategy is separate (language/runtime concern) and must NOT be inferred
      from `load` annotations.

    Supported forms:
    - load lazy                     -> forward=LAZY
    - load eager                    -> forward=EAGER
    - load forward lazy             -> forward=LAZY
    - load reverse eager            -> reverse=EAGER
    - load forward eager reverse lazy -> forward=EAGER, reverse=LAZY
    - load both eager               -> forward=EAGER, reverse=EAGER
    """
    forward = None
    reverse = None

    if not args:
        return forward, reverse

    head = args[0].strip().lower()

    if head not in {"forward", "reverse", "both"}:
        strategy = _parse_strategy(args[0])
        if strategy is not None:
            forward = strategy
        return forward, reverse

    if head == "both" and len(args) >= 2:
        strategy = _parse_strategy(args[1])
        if strategy is not None:
            forward = strategy
            reverse = strategy
        return forward, reverse

    idx = 0
    length = len(args)
    while idx + 1 < length:
        side = args[idx].strip().lower()
        strategy = _parse_strategy(args[idx + 1])
        if strategy is not None:
            if side == "forward":
                forward = strategy
            elif side == "reverse":
                reverse = strategy
        idx += 2

    return forward, reverse


def parse_discriminate_args(args: list[str]) -> tuple[str, str | None]:
    """
    Interpret ANN `discriminate` arguments.

    Canonical forms:
    - discriminate key
    - discriminate tag <tag_value>
    """
    tokens = [(a or "").strip() for a in (args or []) if (a or "").strip()]
    if not tokens:
        raise ValueError("discriminate annotation requires either 'key' or 'tag <value>'")
    head = tokens[0].lower()
    if head == "key":
        if len(tokens) != 1:
            raise ValueError("discriminate key annotation does not accept extra arguments")
        return "key", None
    if head == "tag":
        if len(tokens) != 2:
            raise ValueError("discriminate tag annotation requires exactly one tag value")
        tag_value = tokens[1].strip()
        if not tag_value:
            raise ValueError("discriminate tag value cannot be empty")
        return "tag", tag_value
    raise ValueError(f"Unknown discriminate argument: {tokens[0]!r}")


def parse_oneof_args(
    *,
    args: list[str],
    class_config: ClassConfig,
) -> tuple[CodeSectionAnnotationOneOfMode, list[str], str | None, tuple[tuple[str, str], ...]]:
    """
    Interpret ANN `oneof` arguments.

    Canonical forms:
    - oneof <attribute_name_1> <attribute_name_2> ...
    - oneof identity <attribute_name_1> <attribute_name_2> ...
    - oneof identity <member_attr_1> ... discriminator <disc_attr> <variant> <member_attr> ...

    Semantics:
    - Exactly one attribute in the group must be set (not None).
    """
    tokens = [(a or "").strip() for a in (args or []) if (a or "").strip()]
    mode = CodeSectionAnnotationOneOfMode.validation
    if tokens and tokens[0].casefold() in {"validation", "identity"}:
        mode = CodeSectionAnnotationOneOfMode(tokens[0].casefold())
        tokens = tokens[1:]
    discriminator_attribute_name: str | None = None
    discriminator_cases: list[tuple[str, str]] = []
    if "discriminator" in [t.casefold() for t in tokens]:
        if mode != CodeSectionAnnotationOneOfMode.identity:
            raise ValueError("oneof discriminator is only allowed in identity mode")
        disc_positions = [i for i, t in enumerate(tokens) if t.casefold() == "discriminator"]
        if len(disc_positions) > 1:
            raise ValueError("oneof annotation supports at most one discriminator clause")
        disc_pos = disc_positions[0]
        if disc_pos == 0:
            raise ValueError("oneof annotation discriminator clause requires member attributes before discriminator")
        member_tokens = tokens[:disc_pos]
        discriminator_tail = tokens[disc_pos + 1 :]
        if len(discriminator_tail) < 2:
            raise ValueError(
                "oneof annotation discriminator clause requires '<disc_attr> <variant> <member_attr> ...'"
            )
        discriminator_attribute_name = discriminator_tail[0].strip()
        if not discriminator_attribute_name:
            raise ValueError("oneof annotation discriminator attribute name cannot be empty")
        mapping_tokens = discriminator_tail[1:]
        if "=" in " ".join(mapping_tokens):
            idx = 0
            while idx < len(mapping_tokens):
                token = mapping_tokens[idx]
                variant_raw: str
                member_raw: str
                if "=" in token and token != "=":
                    variant_raw, member_raw = token.split("=", 1)
                    if not member_raw and idx + 1 < len(mapping_tokens):
                        member_raw = mapping_tokens[idx + 1]
                        idx += 1
                    idx += 1
                elif idx + 2 < len(mapping_tokens) and mapping_tokens[idx + 1] == "=":
                    variant_raw = mapping_tokens[idx]
                    member_raw = mapping_tokens[idx + 2]
                    idx += 3
                else:
                    raise ValueError(
                        "oneof annotation discriminator mapping must use '<variant> <member_attr>' pairs "
                        + f"(got token sequence starting at {token!r})"
                    )
                variant = variant_raw.strip()
                member_attr_name = member_raw.strip()
                if not variant or not member_attr_name:
                    raise ValueError(
                        "oneof annotation discriminator mapping must provide non-empty variant/member names "
                        + f"(got token sequence starting at {token!r})"
                    )
                discriminator_cases.append((variant, member_attr_name))
        else:
            if len(mapping_tokens) % 2 != 0:
                raise ValueError(
                    "oneof annotation discriminator mapping must provide '<variant> <member_attr>' pairs "
                    + f"(got odd number of tokens={len(mapping_tokens)})"
                )
            idx = 0
            while idx < len(mapping_tokens):
                variant = mapping_tokens[idx].strip()
                member_attr_name = mapping_tokens[idx + 1].strip()
                if not variant or not member_attr_name:
                    raise ValueError(
                        "oneof annotation discriminator mapping must provide non-empty variant/member names "
                        + f"(got token pair at index {idx})"
                    )
                discriminator_cases.append((variant, member_attr_name))
                idx += 2
        tokens = member_tokens

    if len(tokens) < 2:
        raise ValueError("oneof annotation requires at least two member attributes")

    # Enforce uniqueness while preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for t in tokens:
        if t in seen:
            raise ValueError(f"oneof annotation contains duplicate attribute name: {t!r}")
        seen.add(t)
        ordered.append(t)

    # Fail fast if any attribute name does not exist on the target class.
    attr_by_name = {
        (link.attribute_config.name or "").strip(): link.attribute_config
        for link in class_config.class_config_attribute_configs
        if link.attribute_config is not None and not link.attribute_config.is_virtual
    }
    available = set(attr_by_name.keys())
    missing = [name for name in ordered if name not in available]
    if missing:
        raise ValueError(
            f"oneof annotation references unknown attributes on {class_config.name}: {missing} "
            f"(available={sorted(a for a in available if a)})"
        )

    required = [name for name in ordered if attr_by_name[name].is_required]
    if required:
        raise ValueError(
            f"oneof annotation requires optional attributes (got required={required}) on {class_config.name}"
        )

    if discriminator_attribute_name is not None:
        discriminator_attr = attr_by_name.get(discriminator_attribute_name)
        if discriminator_attr is None:
            raise ValueError(
                f"oneof annotation discriminator attribute does not exist on {class_config.name}: "
                + f"{discriminator_attribute_name!r}"
            )
        if discriminator_attribute_name in ordered:
            raise ValueError(
                "oneof annotation discriminator attribute must not be part of the oneof member list "
                + f"(class={class_config.name}, attribute={discriminator_attribute_name!r})"
            )
        if not discriminator_cases:
            raise ValueError("oneof annotation discriminator clause requires at least one variant mapping")
        seen_variants: set[str] = set()
        seen_member_attrs: set[str] = set()
        for variant, member_attr_name in discriminator_cases:
            if variant in seen_variants:
                raise ValueError(
                    "oneof annotation discriminator mapping contains duplicate variant "
                    + f"(class={class_config.name}, variant={variant!r})"
                )
            if member_attr_name in seen_member_attrs:
                raise ValueError(
                    "oneof annotation discriminator mapping contains duplicate member attribute "
                    + f"(class={class_config.name}, attribute={member_attr_name!r})"
                )
            if member_attr_name not in ordered:
                raise ValueError(
                    "oneof annotation discriminator mapping references unknown oneof member attribute "
                    + f"(class={class_config.name}, attribute={member_attr_name!r})"
                )
            seen_variants.add(variant)
            seen_member_attrs.add(member_attr_name)
        if seen_member_attrs != set(ordered):
            missing = sorted(set(ordered) - seen_member_attrs)
            raise ValueError(
                "oneof annotation discriminator mapping must cover all oneof member attributes "
                + f"(class={class_config.name}, missing={missing!r})"
            )

    return mode, ordered, discriminator_attribute_name, tuple(discriminator_cases)


def parse_identity_args(args: list[str]) -> tuple[ClassIdentityMode, str | None]:
    """
    Interpret ANN `identity` arguments.

    Canonical forms:
    - identity contained
    - identity standalone
    - identity contained structural <relation_name>
    - identity standalone structural <relation_name>
    """
    tokens = [(a or "").strip() for a in (args or []) if (a or "").strip()]
    if not tokens:
        raise ValueError("identity annotation requires a mode argument: 'contained' or 'standalone'")
    token = tokens[0].casefold()
    if token == ClassIdentityMode.contained.value:
        mode = ClassIdentityMode.contained
    elif token == ClassIdentityMode.standalone.value:
        mode = ClassIdentityMode.standalone
    else:
        raise ValueError(f"Unknown identity annotation mode: {tokens[0]!r}")
    if len(tokens) == 1:
        return mode, None
    if len(tokens) != 3 or tokens[1].casefold() != "structural":
        raise ValueError(
            "identity annotation requires either '<mode>' or '<mode> structural <relation_name>'"
        )
    relation_name = tokens[2].strip()
    if not relation_name:
        raise ValueError("identity structural annotation relation name cannot be empty")
    return mode, relation_name


def parse_reference_args(
    args: list[str],
) -> tuple[CodeSectionAnnotationReferenceMode, str | None]:
    tokens = [(a or "").strip() for a in (args or []) if (a or "").strip()]
    if not tokens:
        raise ValueError("reference annotation requires either 'port' or 'bind <target_path>'")
    head = tokens[0].lower()
    if head == "port":
        if len(tokens) != 1:
            raise ValueError("reference port annotation does not accept extra arguments")
        return CodeSectionAnnotationReferenceMode.port, None
    if head == "bind":
        if len(tokens) != 2:
            raise ValueError("reference bind annotation requires exactly one target path")
        target_path = tokens[1].strip()
        if len(target_path) >= 2 and target_path[0] == target_path[-1] and target_path[0] in {'"', "'"}:
            target_path = target_path[1:-1].strip()
        if not target_path:
            raise ValueError("reference bind annotation target path cannot be empty")
        return CodeSectionAnnotationReferenceMode.bind, target_path
    raise ValueError(f"Unknown reference argument: {tokens[0]!r}")


def parse_storage_args(args: list[str]) -> tuple[CodeSectionAnnotationStorageOperation, str, list[str]]:
    """
    Interpret ANN `storage` arguments.

    Canonical forms:
    - storage index <name> <member1> <member2> ...
    - storage unique <name> <member1> <member2> ...
    """
    tokens = [(a or "").strip() for a in (args or []) if (a or "").strip()]
    if len(tokens) < 3:
        raise ValueError("storage annotation requires '<index|unique> <name> <member...>'")

    kind = tokens[0].casefold()
    if kind not in {item.value for item in CodeSectionAnnotationStorageOperation}:
        raise ValueError(f"storage annotation kind must be 'index' or 'unique' (got: {tokens[0]!r})")

    name = tokens[1].strip()
    if not name:
        raise ValueError("storage annotation name cannot be empty")

    members = [m.strip() for m in tokens[2:] if m.strip()]
    if not members:
        raise ValueError("storage annotation requires at least one member name")

    seen: set[str] = set()
    ordered: list[str] = []
    for member in members:
        if member in seen:
            raise ValueError(f"storage annotation contains duplicate member name: {member!r}")
        seen.add(member)
        ordered.append(member)

    return CodeSectionAnnotationStorageOperation(kind), name, ordered


def parse_overlay_args(args: list[str]):
    entity: CodeSectionAnnotationOverlayEntity | None = None
    language: CodeLanguage | None = None
    rename: str | None = None
    wire_name: str | None = None

    if not args:
        return entity, language, rename, wire_name

    idx = 0
    length = len(args)
    while idx < length:
        token = (args[idx] or "").strip()
        lower = token.lower()
        if lower == "language" and idx + 1 < length:
            language = CodeLanguage(args[idx + 1] or "")
            idx += 2
            continue
        if lower == "entity" and idx + 1 < length:
            entity = CodeSectionAnnotationOverlayEntity(args[idx + 1] or "")
            idx += 2
            continue
        if lower == "rename" and idx + 1 < length:
            rename = (args[idx + 1] or "").strip()
            idx += 2
            continue
        if lower == "wire_name" and idx + 1 < length:
            wire_name = (args[idx + 1] or "").strip()
            idx += 2
            continue
        idx += 1

    return entity, language, rename, wire_name


def parse_override_fk_args(args: list[str]) -> tuple[bool, str | None]:
    """
    Interpret ANN `override fk` arguments into FK override semantics.

    Supported forms (order-insensitive):
    - override fk nullable
    - override fk name some_fk_id
    - override fk nullable name some_fk_id
    """
    nullable = False
    name: str | None = None

    idx = 0
    length = len(args)
    while idx < length:
        token = (args[idx] or "").strip().lower()
        if token == "nullable":
            nullable = True
            idx += 1
            continue
        if token == "name":
            if idx + 1 >= length:
                raise ValueError("override fk annotation missing name value after 'name'")
            name = (args[idx + 1] or "").strip()
            if not name:
                raise ValueError("override fk annotation name value cannot be empty")
            idx += 2
            continue
        raise ValueError(f"Unknown override fk argument: {args[idx]!r}")

    return nullable, name


def parse_override_relationship_args(args: list[str]) -> str:
    """
    Interpret ANN `override relationship` arguments into a deterministic relationship/member rename.

    Supported forms:
    - override relationship name new_name
    """
    idx = 0
    length = len(args)
    name: str | None = None
    while idx < length:
        token = (args[idx] or "").strip().lower()
        if token == "name":
            if idx + 1 >= length:
                raise ValueError("override relationship annotation missing name value after 'name'")
            name = (args[idx + 1] or "").strip()
            if not name:
                raise ValueError("override relationship annotation name value cannot be empty")
            idx += 2
            continue
        raise ValueError(f"Unknown override relationship argument: {args[idx]!r}")
    if not name:
        raise ValueError("override relationship annotation requires 'name <value>'")
    return name


@dataclass(frozen=True, slots=True)
class _ResolvedNamespace:
    fqn_prefix: str
    namespace: str


def _namespace_from_fqn(fqn: str) -> _ResolvedNamespace:
    parts = [p for p in (fqn or "").split(".") if p]
    if len(parts) < 2:
        raise ValueError(f"Expected canonical FQN (fqn_prefix[.namespace].Name), got: {fqn}")
    return _ResolvedNamespace(fqn_prefix=parts[0], namespace=".".join(parts[1:-1]))


def _resolve_class_namespace_from_type_ref(scope: FqnScope, type_ref: str) -> tuple[_ResolvedNamespace, str]:
    resolved = scope.try_resolve_class_with_fqn(type_ref)
    if resolved is None:
        raise ValueError(f"Class not found for annotation target: {type_ref}")
    fqn, cls = resolved
    return _namespace_from_fqn(fqn), cls.name


def _resolve_enum_namespace_from_type_ref(scope: FqnScope, type_ref: str) -> tuple[_ResolvedNamespace, str]:
    resolved = scope.try_resolve_enum_with_fqn(type_ref)
    if resolved is None:
        raise ValueError(f"Enum not found for annotation target: {type_ref}")
    fqn, en = resolved
    return _namespace_from_fqn(fqn), en.name


def _build_override_annotation_view(
    *,
    view_id: UUID,
    code_section_annotation_id: UUID,
    namespace: _ResolvedNamespace,
    class_name: str,
    attribute_name: str,
    edge_name: str | None,
    target: CodeSectionAnnotationOverrideTarget,
    nullable: bool,
    name: str | None,
) -> CodeSectionAnnotationOverride:
    model_fields = getattr(CodeSectionAnnotationOverride, "model_fields", {})
    if "namespace" in model_fields:
        return CodeSectionAnnotationOverride(
            id=view_id,
            code_section_annotation_id=code_section_annotation_id,
            fqn_prefix=namespace.fqn_prefix,
            namespace=namespace.namespace,
            class_name=class_name,
            attribute_name=attribute_name,
            edge_name=edge_name,
            target=target,
            nullable=nullable,
            name=name,
        )
    view = CodeSectionAnnotationOverride.model_construct(
        id=view_id,
        code_section_annotation_id=code_section_annotation_id,
        fqn_prefix=namespace.fqn_prefix,
        class_name=class_name,
        attribute_name=attribute_name,
        edge_name=edge_name,
        target=target,
        nullable=nullable,
        name=name,
    )
    object.__setattr__(view, "namespace", namespace.namespace)
    return view


def _build_reference_annotation_view(
    *,
    view_id: UUID,
    code_section_annotation_id: UUID,
    namespace: _ResolvedNamespace,
    class_name: str,
    attribute_name: str,
    mode: CodeSectionAnnotationReferenceMode,
    target_namespace: _ResolvedNamespace | None,
    target_class_name: str | None,
    target_attribute_name: str | None,
) -> CodeSectionAnnotationReference:
    model_fields = getattr(CodeSectionAnnotationReference, "model_fields", {})
    if "namespace" in model_fields:
        return CodeSectionAnnotationReference(
            id=view_id,
            code_section_annotation_id=code_section_annotation_id,
            fqn_prefix=namespace.fqn_prefix,
            namespace=namespace.namespace,
            class_name=class_name,
            attribute_name=attribute_name,
            mode=mode,
            target_fqn_prefix=(
                target_namespace.fqn_prefix if target_namespace is not None else None
            ),
            target_namespace=(
                target_namespace.namespace if target_namespace is not None else None
            ),
            target_class_name=target_class_name,
            target_attribute_name=target_attribute_name,
        )
    view = CodeSectionAnnotationReference.model_construct(
        id=view_id,
        code_section_annotation_id=code_section_annotation_id,
        fqn_prefix=namespace.fqn_prefix,
        class_name=class_name,
        attribute_name=attribute_name,
        mode=mode,
        target_fqn_prefix=(
            target_namespace.fqn_prefix if target_namespace is not None else None
        ),
        target_class_name=target_class_name,
        target_attribute_name=target_attribute_name,
    )
    object.__setattr__(view, "namespace", namespace.namespace)
    object.__setattr__(
        view,
        "target_namespace",
        target_namespace.namespace if target_namespace is not None else None,
    )
    return view


def _build_namespace_annotation_view(model_type: type, *, namespace: _ResolvedNamespace, values: dict[str, object]):
    model_fields = getattr(model_type, "model_fields", {})
    if "namespace" in model_fields:
        return model_type(
            **values,
            fqn_prefix=namespace.fqn_prefix,
            namespace=namespace.namespace,
        )
    view = model_type.model_construct(**values, fqn_prefix=namespace.fqn_prefix)
    object.__setattr__(view, "namespace", namespace.namespace)
    return view


def _stable_ocg_annotation_view_id(
    *,
    object_config_graph_id: UUID,
    kind: ObjectConfigGraphAnnotationKind,
    payload: dict[str, object],
) -> UUID:
    stable_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return ocg_stable_uuid(f"ocg_annotation_view:{object_config_graph_id}:{kind.value}:{stable_payload}")


def _stable_ocg_annotation_id(
    *,
    object_config_graph_id: UUID,
    kind: ObjectConfigGraphAnnotationKind,
    view_id: UUID,
) -> UUID:
    return ocg_stable_uuid(f"ocg_annotation:{object_config_graph_id}:{kind.value}:{view_id}")


def compile_object_config_graph_annotations(
    code_section_annotations: list[CodeSectionAnnotation],
    fqn_resolver: FqnResolver,
    object_config_graph_id: UUID,
) -> list[ObjectConfigGraphAnnotation]:
    """
    Compile CodeSectionAnnotation entries into ObjectConfigGraphAnnotation wrappers.

    Args:
        code_section_annotations: List of CodeSectionAnnotation objects
        fqn_resolver: FQN resolver
        object_config_graph_id: ID of the ObjectConfigGraph
    Returns:
        List of ObjectConfigGraphAnnotation objects
    """
    # Deterministic ordering across files
    annos = sorted(
        [a for a in (code_section_annotations or []) if (a.path or "").strip() and (a.verb or "").strip()],
        key=lambda a: (
            str(a.code_section.code_id) if a.code_section is not None else "",
            (a.verb or "").strip().lower(),
            (a.path or "").strip(),
        ),
    )

    compiled_by_id: dict[UUID, ObjectConfigGraphAnnotation] = {}

    for ann in annos:
        scope = fqn_resolver.scope_for_code_id(ann.code_section.code_id)
        path = (ann.path or "").strip()
        verb = (ann.verb or "").strip().lower()
        args = [(a or "").strip() for a in (ann.args or []) if (a or "").strip()]
        type_ref, members = _split_member_path(path)

        attribute_name: str | None = None
        if verb == "load":
            # Canonical: <type_ref>::<attribute> (optional ::<edge_name>)
            edge_name: str | None = None
            if members:
                attribute_name = members[0]
                edge_name = members[1] if len(members) >= 2 else None
            else:
                raise ValueError(f"Load annotation must use 'TypeRef::attribute' (got: {path})")

            ns, canonical_class_name = _resolve_class_namespace_from_type_ref(scope, type_ref)
            forward, reverse = parse_load_args(args)
            kind = ObjectConfigGraphAnnotationKind.load
            view_id = _stable_ocg_annotation_view_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                payload={
                    "code_section_annotation_id": str(ann.id),
                    "fqn_prefix": ns.fqn_prefix,
                    "namespace": ns.namespace,
                    "class_name": canonical_class_name,
                    "attribute_name": attribute_name,
                    "edge_name": edge_name,
                    "forward_strategy": forward.value if forward is not None else None,
                    "reverse_strategy": reverse.value if reverse is not None else None,
                },
            )
            view = _build_namespace_annotation_view(
                CodeSectionAnnotationLoad,
                namespace=ns,
                values={
                    "id": view_id,
                    "code_section_annotation_id": ann.id,
                    "class_name": canonical_class_name,
                    "attribute_name": attribute_name,
                    "edge_name": edge_name,
                    "forward_strategy": forward,
                    "reverse_strategy": reverse,
                },
            )
            wrapper_id = _stable_ocg_annotation_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                view_id=view_id,
            )
            wrapper = ObjectConfigGraphAnnotation(
                id=wrapper_id,
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                code_section_annotation_load=view,
                code_section_annotation_load_id=view_id,
            )
            compiled_by_id.setdefault(wrapper_id, wrapper)
        elif verb == "project":
            raise ValueError(
                "Legacy `ann ... project ...` is not supported in genesis. "
                "Declare projections via `projection { ... }` blocks."
            )

        elif verb == "discriminate":
            # Canonical: <type_ref>::<attribute>
            if not type_ref or not members or len(members) != 1:
                raise ValueError(f"Discriminate annotation must use 'TypeRef::attribute' (got: {path})")
            attribute_name = members[0]
            ns, canonical_class_name = _resolve_class_namespace_from_type_ref(scope, type_ref)
            mode, tag_value = parse_discriminate_args(args)
            source_position: int | None = None
            if mode == "tag":
                cs = ann.code_section
                seg = cs.content_part_text_segment if cs is not None else None
                if seg is not None and seg.byte_start is not None:
                    source_position = int(seg.byte_start)
            kind = ObjectConfigGraphAnnotationKind.discriminate
            view_id = _stable_ocg_annotation_view_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                payload={
                    "code_section_annotation_id": str(ann.id),
                    "fqn_prefix": ns.fqn_prefix,
                    "namespace": ns.namespace,
                    "class_name": canonical_class_name,
                    "attribute_name": attribute_name,
                    "mode": mode,
                    "tag_value": tag_value,
                    "source_position": source_position,
                },
            )
            view = _build_namespace_annotation_view(
                CodeSectionAnnotationDiscriminate,
                namespace=ns,
                values={
                    "id": view_id,
                    "code_section_annotation_id": ann.id,
                    "class_name": canonical_class_name,
                    "attribute_name": attribute_name,
                    "mode": mode,
                    "tag_value": tag_value,
                    "source_position": source_position,
                },
            )
            wrapper_id = _stable_ocg_annotation_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                view_id=view_id,
            )
            wrapper = ObjectConfigGraphAnnotation(
                id=wrapper_id,
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                code_section_annotation_discriminate=view,
                code_section_annotation_discriminate_id=view_id,
            )
            compiled_by_id.setdefault(wrapper_id, wrapper)

        elif verb == "oneof":
            # Canonical: <type_ref> (no ::members)
            if not type_ref or members:
                raise ValueError(f"oneof annotation must use 'TypeRef' (got: {path})")

            resolved = scope.try_resolve_class_with_fqn(type_ref)
            if resolved is None:
                raise ValueError(f"Class not found for annotation target: {type_ref}")
            fqn, cls = resolved
            ns = _namespace_from_fqn(fqn)

            oneof_mode, attribute_names, discriminator_attribute_name, discriminator_cases = parse_oneof_args(
                args=args,
                class_config=cls,
            )
            kind = ObjectConfigGraphAnnotationKind.oneof
            view_id = _stable_ocg_annotation_view_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                payload={
                    "code_section_annotation_id": str(ann.id),
                    "fqn_prefix": ns.fqn_prefix,
                    "namespace": ns.namespace,
                    "class_name": cls.name,
                    "mode": oneof_mode.value,
                    "attribute_names": list(attribute_names),
                    "discriminator_attribute_name": discriminator_attribute_name or "",
                    "discriminator_cases": [f"{variant}={attr_name}" for variant, attr_name in discriminator_cases],
                },
            )
            view = _build_namespace_annotation_view(
                CodeSectionAnnotationOneOf,
                namespace=ns,
                values={
                    "id": view_id,
                    "code_section_annotation_id": ann.id,
                    "class_name": cls.name,
                    "mode": oneof_mode,
                    "attribute_names": attribute_names,
                    "discriminator_attribute_name": discriminator_attribute_name,
                    "discriminator_cases": [
                        f"{variant}={attr_name}" for variant, attr_name in discriminator_cases
                    ],
                },
            )
            wrapper_id = _stable_ocg_annotation_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                view_id=view_id,
            )
            wrapper = ObjectConfigGraphAnnotation(
                id=wrapper_id,
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                code_section_annotation_oneof=view,
                code_section_annotation_oneof_id=view_id,
            )
            compiled_by_id.setdefault(wrapper_id, wrapper)

        elif verb == "identity":
            # Canonical: <type_ref> (no ::members)
            if not type_ref or members:
                raise ValueError(f"identity annotation must use 'TypeRef' (got: {path})")

            resolved = scope.try_resolve_class_with_fqn(type_ref)
            if resolved is None:
                raise ValueError(f"Class not found for annotation target: {type_ref}")
            fqn, cls = resolved
            ns = _namespace_from_fqn(fqn)

            identity_mode, structural_relation_name = parse_identity_args(args)
            cls.identity_mode = identity_mode
            kind = ObjectConfigGraphAnnotationKind.identity
            payload: dict[str, object] = {
                "code_section_annotation_id": str(ann.id),
                "fqn_prefix": ns.fqn_prefix,
                "namespace": ns.namespace,
                "class_name": cls.name,
                "mode": identity_mode.value,
            }
            if structural_relation_name is not None:
                payload["structural_relation_name"] = structural_relation_name
            view_id = _stable_ocg_annotation_view_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                payload=payload,
            )
            view = _build_namespace_annotation_view(
                CodeSectionAnnotationIdentity,
                namespace=ns,
                values={
                    "id": view_id,
                    "code_section_annotation_id": ann.id,
                    "class_name": cls.name,
                    "mode": identity_mode,
                    "structural_relation_name": structural_relation_name,
                },
            )
            wrapper_id = _stable_ocg_annotation_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                view_id=view_id,
            )
            wrapper = ObjectConfigGraphAnnotation(
                id=wrapper_id,
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                code_section_annotation_identity=view,
                code_section_annotation_identity_id=view_id,
            )
            compiled_by_id.setdefault(wrapper_id, wrapper)

        elif verb == "overlay":
            entity, language, rename, wire_name = parse_overlay_args(args)
            if entity is None or language is None:
                raise ValueError(f"Overlay annotation must use 'entity' and 'language' (got: {path})")

            class_name: str | None = None
            enum_name: str | None = None
            enum_option_name: str | None = None
            function_name: str | None = None

            ns: _ResolvedNamespace | None = None
            if entity == CodeSectionAnnotationOverlayEntity.class_:
                if not type_ref:
                    raise ValueError(f"Overlay annotation must use 'TypeRef' for class (got: {path})")
                ns, class_name = _resolve_class_namespace_from_type_ref(scope, type_ref)
            elif entity == CodeSectionAnnotationOverlayEntity.attribute:
                if not type_ref or not members:
                    raise ValueError(
                        f"Overlay annotation must use 'TypeRef::attribute' or 'TypeRef::function::attribute' "
                        f"for attribute (got: {path})"
                    )
                # Support both:
                # - class attribute: TypeRef::attribute
                # - function IO attribute: TypeRef::function::attribute
                #
                # Extended canonical support for association/edge endpoint overlays:
                # - Source::relationship_attr::EdgeName::edge_member
                # - Source::relationship_attr::EdgeName::edge_fn::edge_fn_attr
                #
                # Rationale:
                # - Edge classes must not declare relationships in SSOT.
                # - Association endpoint members (assoc->target pointer, etc.) are materialized downstream.
                # - These overlays must therefore be expressed from the *source relationship* path.
                if len(members) == 1:
                    # TypeRef::attribute
                    attribute_name = members[0]
                    ns, class_name = _resolve_class_namespace_from_type_ref(scope, type_ref)
                elif len(members) == 2:
                    # TypeRef::function::attribute
                    function_name = members[0]
                    attribute_name = members[1]
                    ns, class_name = _resolve_class_namespace_from_type_ref(scope, type_ref)
                elif len(members) == 3:
                    # TypeRef::relationship_attr::EdgeName::edge_member  (edge endpoint attribute)
                    edge_type_ref = members[1]
                    attribute_name = members[2]
                    ns, class_name = _resolve_class_namespace_from_type_ref(scope, edge_type_ref)
                elif len(members) == 4:
                    # TypeRef::relationship_attr::EdgeName::edge_fn::edge_fn_attr
                    edge_type_ref = members[1]
                    function_name = members[2]
                    attribute_name = members[3]
                    ns, class_name = _resolve_class_namespace_from_type_ref(scope, edge_type_ref)
                else:
                    raise ValueError(
                        "Overlay attribute path must be one of: "
                        "'TypeRef::attribute', 'TypeRef::function::attribute', "
                        "'TypeRef::relationship_attr::EdgeName::edge_member', "
                        "'TypeRef::relationship_attr::EdgeName::edge_fn::edge_fn_attr' "
                        f"(got: {path})"
                    )
            elif entity == CodeSectionAnnotationOverlayEntity.function:
                if not type_ref or not members:
                    raise ValueError(f"Overlay annotation must use 'TypeRef::function' for function (got: {path})")
                function_name = members[0]
                ns, class_name = _resolve_class_namespace_from_type_ref(scope, type_ref)
            elif entity == CodeSectionAnnotationOverlayEntity.enum:
                if not type_ref:
                    raise ValueError(f"Overlay annotation must use 'TypeRef' for enum (got: {path})")
                ns, enum_name = _resolve_enum_namespace_from_type_ref(scope, type_ref)
            elif entity == CodeSectionAnnotationOverlayEntity.enum_option:
                if not type_ref or not members:
                    raise ValueError(
                        f"Overlay annotation must use 'TypeRef::enum_option' for enum option (got: {path})"
                    )
                enum_option_name = members[0]
                ns, enum_name = _resolve_enum_namespace_from_type_ref(scope, type_ref)

            if ns is None:
                raise ValueError(f"Overlay annotation missing namespace for {path}")

            kind = ObjectConfigGraphAnnotationKind.overlay
            view_id = _stable_ocg_annotation_view_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                payload={
                    "code_section_annotation_id": str(ann.id),
                    "source_path": ann.path,
                    "fqn_prefix": ns.fqn_prefix,
                    "namespace": ns.namespace,
                    "language": language.value if language is not None else None,
                    "entity": entity.value if entity is not None else None,
                    "class_name": class_name,
                    "attribute_name": attribute_name,
                    "enum_name": enum_name,
                    "enum_option_name": enum_option_name,
                    "function_name": function_name,
                    "rename": rename,
                    "wire_name": wire_name,
                },
            )
            view = _build_namespace_annotation_view(
                CodeSectionAnnotationOverlay,
                namespace=ns,
                values={
                    "id": view_id,
                    "code_section_annotation_id": ann.id,
                    # Persist raw path onto the overlay view so overlay application can reason about
                    # edge-endpoint overlays without depending on primitive CodeSectionAnnotation graphs.
                    "source_path": ann.path,
                    "language": language,
                    "entity": entity,
                    "class_name": class_name,
                    "attribute_name": attribute_name,
                    "enum_name": enum_name,
                    "enum_option_name": enum_option_name,
                    "function_name": function_name,
                    "rename": rename,
                    "wire_name": wire_name,
                },
            )
            wrapper_id = _stable_ocg_annotation_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                view_id=view_id,
            )
            wrapper = ObjectConfigGraphAnnotation(
                id=wrapper_id,
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                code_section_annotation_overlay=view,
                code_section_annotation_overlay_id=view_id,
            )
            compiled_by_id.setdefault(wrapper_id, wrapper)
        elif verb == "override":
            # Canonical:
            # - override fk <nullable?> <name fk_name?>
            # Target path MUST reference a relationship: <type_ref>::<attribute> (optional ::<edge_name>)
            if not members:
                raise ValueError(f"Override annotation must use 'TypeRef::attribute' (got: {path})")

            kind_token = (args[0] if args else "").strip().lower()
            if kind_token not in {"fk", "relationship"}:
                raise ValueError(
                    f"Override annotation must specify kind 'fk' or 'relationship' as first arg (got: {args[0] if args else None!r})"
                )

            attribute_name = members[0]
            edge_name = members[1] if len(members) >= 2 else None
            ns, canonical_class_name = _resolve_class_namespace_from_type_ref(scope, type_ref)

            if kind_token == "fk":
                nullable, name = parse_override_fk_args(args[1:])
                target = CodeSectionAnnotationOverrideTarget.fk
            else:
                nullable = False
                name = parse_override_relationship_args(args[1:])
                target = CodeSectionAnnotationOverrideTarget.relationship
            kind = ObjectConfigGraphAnnotationKind.override
            view_id = _stable_ocg_annotation_view_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                payload={
                    "code_section_annotation_id": str(ann.id),
                    "fqn_prefix": ns.fqn_prefix,
                    "namespace": ns.namespace,
                    "class_name": canonical_class_name,
                    "attribute_name": attribute_name,
                    "edge_name": edge_name,
                    "target": target.value if target is not None else None,
                    "nullable": nullable,
                    "name": name,
                },
            )
            view = _build_override_annotation_view(
                view_id=view_id,
                code_section_annotation_id=ann.id,
                namespace=ns,
                class_name=canonical_class_name,
                attribute_name=attribute_name,
                edge_name=edge_name,
                target=target,
                nullable=nullable,
                name=name,
            )
            wrapper_id = _stable_ocg_annotation_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                view_id=view_id,
            )
            wrapper = ObjectConfigGraphAnnotation(
                id=wrapper_id,
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                code_section_annotation_override=view,
                code_section_annotation_override_id=view_id,
            )
            compiled_by_id.setdefault(wrapper_id, wrapper)
        elif verb == "reference":
            if not type_ref or not members:
                raise ValueError(f"Reference annotation must use 'TypeRef::attribute' (got: {path})")
            if len(members) != 1:
                raise ValueError(f"Reference annotation must use 'TypeRef::attribute' (got: {path})")

            attribute_name = members[0]
            ns, canonical_class_name = _resolve_class_namespace_from_type_ref(scope, type_ref)
            mode, bind_target_path = parse_reference_args(args)

            target_ns: _ResolvedNamespace | None = None
            target_class_name: str | None = None
            target_attribute_name: str | None = None

            if mode == CodeSectionAnnotationReferenceMode.bind:
                if bind_target_path is None:
                    raise ValueError("reference bind annotation missing target path")
                target_type_ref, target_members = _split_member_path(bind_target_path)
                if not target_type_ref or not target_members or len(target_members) != 1:
                    raise ValueError(
                        "reference bind annotation target must use 'TypeRef::attribute' " f"(got: {bind_target_path})"
                )
                target_attribute_name = target_members[0]
                target_ns, target_class_name = _resolve_class_namespace_from_type_ref(scope, target_type_ref)

            kind = ObjectConfigGraphAnnotationKind.reference
            view_id = _stable_ocg_annotation_view_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                payload={
                    "code_section_annotation_id": str(ann.id),
                    "fqn_prefix": ns.fqn_prefix,
                    "namespace": ns.namespace,
                    "class_name": canonical_class_name,
                    "attribute_name": attribute_name,
                    "mode": mode.value if mode is not None else None,
                    "target_fqn_prefix": (
                        target_ns.fqn_prefix if target_ns is not None else None
                    ),
                    "target_namespace": (
                        target_ns.namespace if target_ns is not None else None
                    ),
                    "target_class_name": target_class_name,
                    "target_attribute_name": target_attribute_name,
                },
            )
            view = _build_reference_annotation_view(
                view_id=view_id,
                code_section_annotation_id=ann.id,
                namespace=ns,
                class_name=canonical_class_name,
                attribute_name=attribute_name,
                mode=mode,
                target_namespace=target_ns,
                target_class_name=target_class_name,
                target_attribute_name=target_attribute_name,
            )
            wrapper_id = _stable_ocg_annotation_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                view_id=view_id,
            )
            wrapper = ObjectConfigGraphAnnotation(
                id=wrapper_id,
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                code_section_annotation_reference=view,
                code_section_annotation_reference_id=view_id,
            )
            compiled_by_id.setdefault(wrapper_id, wrapper)
        elif verb == "index":
            # Canonical forms:
            # - <type_ref>::<member> index
            # - <type_ref> index <member1> <member2> ...
            if not type_ref:
                raise ValueError(f"index annotation must use 'TypeRef' (got: {path})")
            if members and args:
                raise ValueError(f"index annotation cannot specify members in both the path and args (got: {path})")

            member_names = members if members else args
            member_names = [m.strip() for m in member_names if (m or "").strip()]
            if not member_names:
                raise ValueError(f"index annotation requires at least one member name (got: {path})")

            # Enforce uniqueness while preserving order.
            seen: set[str] = set()
            ordered: list[str] = []
            for m in member_names:
                if m in seen:
                    raise ValueError(f"index annotation contains duplicate member name: {m!r} (path={path})")
                seen.add(m)
                ordered.append(m)

            resolved = scope.try_resolve_class_with_fqn(type_ref)
            if resolved is None:
                raise ValueError(f"Class not found for annotation target: {type_ref}")
            fqn, cls = resolved
            ns = _namespace_from_fqn(fqn)

            kind = ObjectConfigGraphAnnotationKind.index
            view_id = _stable_ocg_annotation_view_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                payload={
                    "code_section_annotation_id": str(ann.id),
                    "fqn_prefix": ns.fqn_prefix,
                    "namespace": ns.namespace,
                    "class_name": cls.name,
                    "member_names": list(ordered),
                },
            )
            view = _build_namespace_annotation_view(
                CodeSectionAnnotationIndex,
                namespace=ns,
                values={
                    "id": view_id,
                    "code_section_annotation_id": ann.id,
                    "class_name": cls.name,
                    "member_names": ordered,
                },
            )
            wrapper_id = _stable_ocg_annotation_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                view_id=view_id,
            )
            wrapper = ObjectConfigGraphAnnotation(
                id=wrapper_id,
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                code_section_annotation_index=view,
                code_section_annotation_index_id=view_id,
            )
            compiled_by_id.setdefault(wrapper_id, wrapper)
        elif verb == "storage":
            # Canonical forms:
            # - <type_ref> storage index <name> <member1> <member2> ...
            # - <type_ref> storage unique <name> <member1> <member2> ...
            if not type_ref or members:
                raise ValueError(f"storage annotation must use 'TypeRef' (got: {path})")

            operation, name, ordered = parse_storage_args(args)

            resolved = scope.try_resolve_class_with_fqn(type_ref)
            if resolved is None:
                raise ValueError(f"Class not found for annotation target: {type_ref}")
            fqn, cls = resolved
            ns = _namespace_from_fqn(fqn)

            kind = ObjectConfigGraphAnnotationKind.storage
            view_id = _stable_ocg_annotation_view_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                payload={
                    "code_section_annotation_id": str(ann.id),
                    "fqn_prefix": ns.fqn_prefix,
                    "namespace": ns.namespace,
                    "class_name": cls.name,
                    "name": name,
                    "operation": operation.value,
                    "member_names": list(ordered),
                },
            )
            view = _build_namespace_annotation_view(
                CodeSectionAnnotationStorage,
                namespace=ns,
                values={
                    "id": view_id,
                    "code_section_annotation_id": ann.id,
                    "class_name": cls.name,
                    "name": name,
                    "operation": operation,
                    "member_names": ordered,
                },
            )
            wrapper_id = _stable_ocg_annotation_id(
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                view_id=view_id,
            )
            wrapper = ObjectConfigGraphAnnotation(
                id=wrapper_id,
                object_config_graph_id=object_config_graph_id,
                kind=kind,
                code_section_annotation_storage=view,
                code_section_annotation_storage_id=view_id,
            )
            compiled_by_id.setdefault(wrapper_id, wrapper)
        else:
            raise ValueError(f"Unknown annotation verb: {ann.verb!r} (normalized={verb!r}, path={path})")
    return list(compiled_by_id.values())


__all__ = [
    "compile_object_config_graph_annotations",
    "parse_load_args",
    "parse_overlay_args",
    "parse_override_fk_args",
    "parse_override_relationship_args",
    "parse_oneof_args",
    "parse_identity_args",
    "parse_reference_args",
    "parse_storage_args",
]
