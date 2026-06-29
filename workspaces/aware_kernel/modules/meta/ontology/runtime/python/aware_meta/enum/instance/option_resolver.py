from __future__ import annotations

from dataclasses import dataclass
from enum import Enum as PyEnum
from typing import Any, Iterable, Mapping
from uuid import UUID

from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.enum.enum_option import EnumOption
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)

from aware_meta.attribute.instance.value.builder import EnumOptionResolver


class EnumOptionResolutionError(ValueError):
    pass


@dataclass(frozen=True)
class EnumOptionResolverIndex:
    """
    Precomputed lookup index for resolving runtime enum values → EnumOption.id.

    Keys are EnumConfig.id; values are lookup maps from candidate tokens to EnumOption.id.
    """

    enum_config_id_to_token_to_enum_option_id: Mapping[UUID, Mapping[str, UUID]]


def build_enum_option_resolver_index(
    *,
    object_config_graph: ObjectConfigGraph,
    external_graphs: Iterable[ObjectConfigGraph] | None = None,
) -> EnumOptionResolverIndex:
    graphs: list[ObjectConfigGraph] = [object_config_graph, *(external_graphs or [])]
    enum_configs: list[EnumConfig] = []
    for graph in graphs:
        for node in graph.object_config_graph_nodes:
            if node.type != ObjectConfigGraphNodeType.enum:
                continue
            if node.enum_config is not None:
                enum_configs.append(node.enum_config)

    token_maps: dict[UUID, dict[str, UUID]] = {}
    for enum_config in enum_configs:
        token_map = token_maps.get(enum_config.id)
        if token_map is None:
            token_map = {}
            token_maps[enum_config.id] = token_map
        for opt in enum_config.enum_options:
            _add_enum_option_tokens(token_map, opt)

    return EnumOptionResolverIndex(enum_config_id_to_token_to_enum_option_id=token_maps)


def build_enum_option_resolver(
    *,
    object_config_graph: ObjectConfigGraph,
    external_graphs: Iterable[ObjectConfigGraph] | None = None,
) -> EnumOptionResolver:
    """
    Build an EnumOptionResolver from an ObjectConfigGraph.

    This is the canonical mapping for instance AttributeValue building:
    - Runtime enums are represented as EnumOption ids.
    - Runtime values (wire names) must match canonical EnumOption.value tokens.
    """
    index = build_enum_option_resolver_index(
        object_config_graph=object_config_graph,
        external_graphs=external_graphs,
    )

    def resolver(type_descriptor: AttributeTypeDescriptor, value: Any) -> UUID:
        enum_config_id = _resolve_enum_config_id(type_descriptor)
        if enum_config_id is None:
            raise EnumOptionResolutionError("AttributeTypeDescriptor missing enum_config_id for ENUM kind")

        token_map = index.enum_config_id_to_token_to_enum_option_id.get(enum_config_id)
        if token_map is None:
            raise EnumOptionResolutionError(f"EnumConfig not found in OCG: {enum_config_id}")

        for token in _candidate_tokens(value):
            enum_option_id = token_map.get(token)
            if enum_option_id is not None:
                return enum_option_id

        # Include helpful diagnostics.
        candidates = ", ".join([repr(t) for t in _candidate_tokens(value)])
        known = ", ".join(sorted(token_map.keys())[:10])
        raise EnumOptionResolutionError(
            f"EnumOption not found for value={value!r} (candidates={candidates}) "
            f"under enum_config_id={enum_config_id}; known_tokens(sample)=[{known}]"
        )

    return resolver


def _resolve_enum_config_id(desc: AttributeTypeDescriptor) -> UUID | None:
    if desc.enum_config_id is not None:
        return desc.enum_config_id
    enum_cfg = getattr(desc, "enum_config", None)
    if enum_cfg is not None and getattr(enum_cfg, "id", None) is not None:
        return enum_cfg.id
    return None


def _candidate_tokens(value: Any) -> list[str]:
    """
    Produce a deterministic set of candidate tokens for resolving a runtime enum value.

    Order matters: earliest match wins.
    """
    tokens: list[str] = []
    if value is None:
        return tokens

    if isinstance(value, str):
        raw = value
        tokens.append(raw)
        tokens.append(raw.strip())
        return _dedupe_preserve_order(tokens)

    if isinstance(value, PyEnum):
        # Prefer wire value first, then rendered name.
        raw_val = value.value
        if raw_val is not None:
            tokens.extend(_candidate_tokens(raw_val))
        if value.name:
            tokens.extend(_candidate_tokens(value.name))
        return _dedupe_preserve_order(tokens)

    # Fall back to a `.value` attribute (common for enum-like wrappers).
    maybe_value = getattr(value, "value", None)
    if isinstance(maybe_value, str):
        tokens.extend(_candidate_tokens(maybe_value))
        return _dedupe_preserve_order(tokens)

    return _dedupe_preserve_order([str(value)])


def _add_enum_option_tokens(token_map: dict[str, UUID], opt: EnumOption) -> None:
    if opt.value is None:
        return

    # Canonical value token(s).
    base = opt.value
    variants = [
        base,
        base.strip(),
    ]

    for token in _dedupe_preserve_order(variants):
        existing = token_map.get(token)
        if existing is None:
            token_map[token] = opt.id
        elif existing != opt.id:
            raise EnumOptionResolutionError(
                f"Ambiguous enum option token {token!r}: {existing} vs {opt.id} (enum_config_id={opt.enum_config_id})"
            )


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


__all__ = [
    "EnumOptionResolutionError",
    "EnumOptionResolverIndex",
    "build_enum_option_resolver",
    "build_enum_option_resolver_index",
]
