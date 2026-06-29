from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from uuid import UUID

from aware_meta.fqn_resolver import FqnResolver, NamespacePath
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)


META_OCG_SEMANTIC_SCOPE_CLOSURE_CONTRACT_VERSION = (
    "aware.meta.ocg-semantic-scope-closure.v0"
)

SCOPE_STATUS_READY = "semantic_scope_closure_ready"
SCOPE_STATUS_BLOCKED = "semantic_scope_closure_blocked"

SYMBOL_KIND_CLASS = "class"
SYMBOL_KIND_ENUM = "enum"

SYMBOL_ORIGIN_LOCAL = "local"
SYMBOL_ORIGIN_EXTERNAL = "external"

PROBE_STATUS_RESOLVED = "resolved"
PROBE_STATUS_UNRESOLVED = "unresolved"
PROBE_STATUS_AMBIGUOUS = "ambiguous"
PROBE_STATUS_BLOCKED = "blocked"

SCOPE_GATE_STATUS_READY = "semantic_scope_closure_gate_ready"
SCOPE_GATE_STATUS_BLOCKED = "semantic_scope_closure_gate_blocked"


@dataclass(frozen=True, slots=True)
class MetaOcgSemanticScopeResolutionProbeRequest:
    code_id: UUID
    symbol_kind: str
    identifier: str
    required: bool = True


@dataclass(frozen=True, slots=True)
class MetaOcgSemanticScopeSymbolEvidence:
    symbol_kind: str
    fqn: str
    object_id: str
    origin: str
    package: str
    namespace: str
    name: str

    def evidence_payload(self) -> dict[str, object]:
        return {
            "symbol_kind": self.symbol_kind,
            "fqn": self.fqn,
            "object_id": self.object_id,
            "origin": self.origin,
            "package": self.package,
            "namespace": self.namespace,
            "name": self.name,
        }


@dataclass(frozen=True, slots=True)
class MetaOcgSemanticScopeResolutionProbeEvidence:
    status: str
    symbol_kind: str
    identifier: str
    code_id: str
    namespace_prefix: str | None
    resolved_fqn: str | None
    resolved_object_id: str | None
    reason: str | None
    blockers: tuple[str, ...] = ()

    def evidence_payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "symbol_kind": self.symbol_kind,
            "identifier": self.identifier,
            "code_id": self.code_id,
            "namespace_prefix": self.namespace_prefix,
            "resolved_fqn": self.resolved_fqn,
            "resolved_object_id": self.resolved_object_id,
            "reason": self.reason,
            "blockers": self.blockers,
        }


@dataclass(frozen=True, slots=True)
class MetaOcgSemanticScopeClosureEvidence:
    package_fqn_prefix: str
    status: str
    namespace_count: int
    import_alias_count: int
    local_symbol_count: int
    external_symbol_count: int
    namespace_prefixes: tuple[str, ...]
    symbols: tuple[MetaOcgSemanticScopeSymbolEvidence, ...]
    resolution_probes: tuple[MetaOcgSemanticScopeResolutionProbeEvidence, ...]
    blockers: tuple[str, ...]
    contract_version: str = META_OCG_SEMANTIC_SCOPE_CLOSURE_CONTRACT_VERSION

    @property
    def ready(self) -> bool:
        return self.status == SCOPE_STATUS_READY

    def evidence_payload(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "package_fqn_prefix": self.package_fqn_prefix,
            "status": self.status,
            "ready": self.ready,
            "namespace_count": self.namespace_count,
            "import_alias_count": self.import_alias_count,
            "local_symbol_count": self.local_symbol_count,
            "external_symbol_count": self.external_symbol_count,
            "namespace_prefixes": self.namespace_prefixes,
            "symbols": tuple(symbol.evidence_payload() for symbol in self.symbols),
            "resolution_probes": tuple(
                probe.evidence_payload() for probe in self.resolution_probes
            ),
            "blockers": self.blockers,
        }


def build_meta_ocg_semantic_scope_closure(
    *,
    package_fqn_prefix: str,
    namespace_by_code_id: Mapping[UUID, NamespacePath],
    class_configs: Iterable[ClassConfig] = (),
    enum_configs: Iterable[EnumConfig] = (),
    imports_by_code_id: Mapping[UUID, Mapping[str, str]] | None = None,
    external_graphs: Iterable[ObjectConfigGraph] = (),
    probes: Iterable[MetaOcgSemanticScopeResolutionProbeRequest] = (),
) -> MetaOcgSemanticScopeClosureEvidence:
    """Build read-only namespace/FQN closure evidence for OCG provider deltas.

    The builder still computes much of this state today. This contract extracts
    the resolver inputs/outputs into stable evidence so typed-operation planners
    can later consume semantic scope truth without calling builder internals.
    """

    normalized_prefix = package_fqn_prefix.strip()
    namespaces = dict(namespace_by_code_id)
    imports = {
        code_id: dict(aliases)
        for code_id, aliases in (imports_by_code_id or {}).items()
    }
    blockers: list[str] = []

    if not normalized_prefix:
        blockers.append("package_fqn_prefix_missing")
    if not namespaces:
        blockers.append("namespace_closure_empty")

    for code_id, namespace in namespaces.items():
        if normalized_prefix and not _namespace_matches_prefix(
            namespace=namespace,
            package_fqn_prefix=normalized_prefix,
        ):
            blockers.append(
                "namespace_package_mismatch:"
                f"{code_id}:{namespace.prefix()}"
            )

    classes_by_fqn: dict[str, ClassConfig] = {}
    enums_by_fqn: dict[str, EnumConfig] = {}
    symbol_evidence: list[MetaOcgSemanticScopeSymbolEvidence] = []

    for class_config in class_configs:
        _add_class_symbol(
            classes_by_fqn=classes_by_fqn,
            symbols=symbol_evidence,
            blockers=blockers,
            class_config=class_config,
            origin=SYMBOL_ORIGIN_LOCAL,
        )
    for enum_config in enum_configs:
        _add_enum_symbol(
            enums_by_fqn=enums_by_fqn,
            symbols=symbol_evidence,
            blockers=blockers,
            enum_config=enum_config,
            origin=SYMBOL_ORIGIN_LOCAL,
        )
    for graph in external_graphs:
        _add_external_graph_symbols(
            classes_by_fqn=classes_by_fqn,
            enums_by_fqn=enums_by_fqn,
            symbols=symbol_evidence,
            blockers=blockers,
            graph=graph,
        )

    resolver = FqnResolver(
        namespace_by_code_id=namespaces,
        classes_by_fqn=classes_by_fqn,
        enums_by_fqn=enums_by_fqn,
        imports_by_code_id=imports,
    )
    probe_evidence = tuple(
        _resolve_probe(
            resolver=resolver,
            namespaces=namespaces,
            probe=probe,
        )
        for probe in probes
    )
    for probe in probe_evidence:
        if probe.blockers:
            blockers.extend(probe.blockers)

    local_symbol_count = sum(
        1 for symbol in symbol_evidence if symbol.origin == SYMBOL_ORIGIN_LOCAL
    )
    external_symbol_count = sum(
        1 for symbol in symbol_evidence if symbol.origin == SYMBOL_ORIGIN_EXTERNAL
    )
    stable_blockers = _unique_sorted(blockers)
    status = SCOPE_STATUS_BLOCKED if stable_blockers else SCOPE_STATUS_READY

    return MetaOcgSemanticScopeClosureEvidence(
        package_fqn_prefix=normalized_prefix,
        status=status,
        namespace_count=len(namespaces),
        import_alias_count=sum(len(aliases) for aliases in imports.values()),
        local_symbol_count=local_symbol_count,
        external_symbol_count=external_symbol_count,
        namespace_prefixes=tuple(
            sorted(namespace.prefix() for namespace in namespaces.values())
        ),
        symbols=tuple(
            sorted(
                symbol_evidence,
                key=lambda symbol: (
                    symbol.origin,
                    symbol.symbol_kind,
                    symbol.fqn,
                    symbol.object_id,
                ),
            )
        ),
        resolution_probes=probe_evidence,
        blockers=stable_blockers,
    )


def meta_ocg_class_fqn_scope_closure_gate(
    *,
    package_fqn_prefix: str,
    class_fqn: str,
    semantic_scope_closure: (
        MetaOcgSemanticScopeClosureEvidence | Mapping[str, object] | None
    ),
) -> dict[str, object]:
    payload = _scope_closure_payload(semantic_scope_closure)
    closure_status = _optional_text(payload.get("status"))
    closure_prefix = _optional_text(payload.get("package_fqn_prefix"))
    closure_blockers = _tuple_text(payload.get("blockers"))
    blockers: list[str] = []

    if not payload:
        blockers.append("semantic_scope_closure_missing")
    if payload and closure_status != SCOPE_STATUS_READY:
        blockers.append(
            "semantic_scope_closure_not_ready:"
            f"{closure_status or 'unknown'}"
        )
    if closure_prefix != package_fqn_prefix:
        blockers.append(
            "semantic_scope_closure_package_mismatch:"
            f"{closure_prefix or 'unknown'}"
        )
    blockers.extend(closure_blockers)
    if not _scope_closure_contains_symbol(
        semantic_scope_closure=payload,
        symbol_kind=SYMBOL_KIND_CLASS,
        fqn=class_fqn,
    ):
        blockers.append(f"semantic_scope_closure_missing_class_fqn:{class_fqn}")

    stable_blockers = _unique_sorted(blockers)
    ready = not stable_blockers
    return {
        "gate_kind": "meta_ocg_class_fqn_scope_closure_gate",
        "contract_version": META_OCG_SEMANTIC_SCOPE_CLOSURE_CONTRACT_VERSION,
        "status": (
            SCOPE_GATE_STATUS_READY
            if ready
            else SCOPE_GATE_STATUS_BLOCKED
        ),
        "ready": ready,
        "consumed": True,
        "target_symbol_kind": SYMBOL_KIND_CLASS,
        "target_fqn": class_fqn,
        "package_fqn_prefix": package_fqn_prefix,
        "semantic_scope_closure_status": closure_status,
        "semantic_scope_closure_package_fqn_prefix": closure_prefix,
        "semantic_scope_closure_blockers": closure_blockers,
        "blockers": stable_blockers,
    }


def meta_ocg_enum_fqn_scope_closure_gate(
    *,
    package_fqn_prefix: str,
    enum_fqn: str,
    semantic_scope_closure: (
        MetaOcgSemanticScopeClosureEvidence | Mapping[str, object] | None
    ),
) -> dict[str, object]:
    payload = _scope_closure_payload(semantic_scope_closure)
    closure_status = _optional_text(payload.get("status"))
    closure_prefix = _optional_text(payload.get("package_fqn_prefix"))
    closure_blockers = _tuple_text(payload.get("blockers"))
    blockers: list[str] = []

    if not payload:
        blockers.append("semantic_scope_closure_missing")
    if payload and closure_status != SCOPE_STATUS_READY:
        blockers.append(
            "semantic_scope_closure_not_ready:"
            f"{closure_status or 'unknown'}"
        )
    if closure_prefix != package_fqn_prefix:
        blockers.append(
            "semantic_scope_closure_package_mismatch:"
            f"{closure_prefix or 'unknown'}"
        )
    blockers.extend(closure_blockers)
    if not _scope_closure_contains_symbol(
        semantic_scope_closure=payload,
        symbol_kind=SYMBOL_KIND_ENUM,
        fqn=enum_fqn,
    ):
        blockers.append(f"semantic_scope_closure_missing_enum_fqn:{enum_fqn}")

    stable_blockers = _unique_sorted(blockers)
    ready = not stable_blockers
    return {
        "gate_kind": "meta_ocg_enum_fqn_scope_closure_gate",
        "contract_version": META_OCG_SEMANTIC_SCOPE_CLOSURE_CONTRACT_VERSION,
        "status": (
            SCOPE_GATE_STATUS_READY
            if ready
            else SCOPE_GATE_STATUS_BLOCKED
        ),
        "ready": ready,
        "consumed": True,
        "target_symbol_kind": SYMBOL_KIND_ENUM,
        "target_fqn": enum_fqn,
        "package_fqn_prefix": package_fqn_prefix,
        "semantic_scope_closure_status": closure_status,
        "semantic_scope_closure_package_fqn_prefix": closure_prefix,
        "semantic_scope_closure_blockers": closure_blockers,
        "blockers": stable_blockers,
    }


def _add_external_graph_symbols(
    *,
    classes_by_fqn: dict[str, ClassConfig],
    enums_by_fqn: dict[str, EnumConfig],
    symbols: list[MetaOcgSemanticScopeSymbolEvidence],
    blockers: list[str],
    graph: ObjectConfigGraph,
) -> None:
    for node in graph.object_config_graph_nodes:
        if (
            node.type == ObjectConfigGraphNodeType.class_
            and node.class_config is not None
        ):
            _add_class_symbol(
                classes_by_fqn=classes_by_fqn,
                symbols=symbols,
                blockers=blockers,
                class_config=node.class_config,
                origin=SYMBOL_ORIGIN_EXTERNAL,
            )
        elif node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
            _add_enum_symbol(
                enums_by_fqn=enums_by_fqn,
                symbols=symbols,
                blockers=blockers,
                enum_config=node.enum_config,
                origin=SYMBOL_ORIGIN_EXTERNAL,
            )


def _add_class_symbol(
    *,
    classes_by_fqn: dict[str, ClassConfig],
    symbols: list[MetaOcgSemanticScopeSymbolEvidence],
    blockers: list[str],
    class_config: ClassConfig,
    origin: str,
) -> None:
    fqn = class_config.class_fqn.strip()
    if not fqn:
        blockers.append(f"local_class_missing_fqn:{class_config.id}")
        return
    existing = classes_by_fqn.get(fqn)
    if existing is not None and existing.id != class_config.id:
        blockers.append(f"duplicate_class_fqn:{fqn}")
        return
    classes_by_fqn[fqn] = class_config
    symbols.append(
        _symbol_evidence(
            symbol_kind=SYMBOL_KIND_CLASS,
            fqn=fqn,
            object_id=str(class_config.id),
            origin=origin,
        )
    )


def _add_enum_symbol(
    *,
    enums_by_fqn: dict[str, EnumConfig],
    symbols: list[MetaOcgSemanticScopeSymbolEvidence],
    blockers: list[str],
    enum_config: EnumConfig,
    origin: str,
) -> None:
    fqn = enum_config.enum_fqn.strip()
    if not fqn:
        blockers.append(f"local_enum_missing_fqn:{enum_config.id}")
        return
    existing = enums_by_fqn.get(fqn)
    if existing is not None and existing.id != enum_config.id:
        blockers.append(f"duplicate_enum_fqn:{fqn}")
        return
    enums_by_fqn[fqn] = enum_config
    symbols.append(
        _symbol_evidence(
            symbol_kind=SYMBOL_KIND_ENUM,
            fqn=fqn,
            object_id=str(enum_config.id),
            origin=origin,
        )
    )


def _resolve_probe(
    *,
    resolver: FqnResolver,
    namespaces: Mapping[UUID, NamespacePath],
    probe: MetaOcgSemanticScopeResolutionProbeRequest,
) -> MetaOcgSemanticScopeResolutionProbeEvidence:
    namespace = namespaces.get(probe.code_id)
    namespace_prefix = namespace.prefix() if namespace is not None else None
    if namespace is None:
        return _blocked_probe(
            probe=probe,
            namespace_prefix=namespace_prefix,
            reason="namespace_missing_for_code_id",
        )
    if not probe.identifier.strip():
        return _blocked_probe(
            probe=probe,
            namespace_prefix=namespace_prefix,
            reason="identifier_missing",
        )

    try:
        scope = resolver.scope_for_code_id(probe.code_id)
        if probe.symbol_kind == SYMBOL_KIND_CLASS:
            resolved = scope.try_resolve_class_with_fqn(probe.identifier)
        elif probe.symbol_kind == SYMBOL_KIND_ENUM:
            resolved = scope.try_resolve_enum_with_fqn(probe.identifier)
        else:
            return _blocked_probe(
                probe=probe,
                namespace_prefix=namespace_prefix,
                reason=f"unsupported_symbol_kind:{probe.symbol_kind}",
            )
    except ValueError as exc:
        reason = str(exc)
        status = (
            PROBE_STATUS_AMBIGUOUS
            if reason.startswith("Ambiguous ")
            else PROBE_STATUS_BLOCKED
        )
        return MetaOcgSemanticScopeResolutionProbeEvidence(
            status=status,
            symbol_kind=probe.symbol_kind,
            identifier=probe.identifier,
            code_id=str(probe.code_id),
            namespace_prefix=namespace_prefix,
            resolved_fqn=None,
            resolved_object_id=None,
            reason=reason,
            blockers=_probe_blockers(probe=probe, status=status),
        )

    if resolved is None:
        return MetaOcgSemanticScopeResolutionProbeEvidence(
            status=PROBE_STATUS_UNRESOLVED,
            symbol_kind=probe.symbol_kind,
            identifier=probe.identifier,
            code_id=str(probe.code_id),
            namespace_prefix=namespace_prefix,
            resolved_fqn=None,
            resolved_object_id=None,
            reason="symbol_not_found",
            blockers=_probe_blockers(
                probe=probe,
                status=PROBE_STATUS_UNRESOLVED,
            ),
        )

    resolved_fqn, resolved_config = resolved
    return MetaOcgSemanticScopeResolutionProbeEvidence(
        status=PROBE_STATUS_RESOLVED,
        symbol_kind=probe.symbol_kind,
        identifier=probe.identifier,
        code_id=str(probe.code_id),
        namespace_prefix=namespace_prefix,
        resolved_fqn=resolved_fqn,
        resolved_object_id=str(resolved_config.id),
        reason=None,
        blockers=(),
    )


def _blocked_probe(
    *,
    probe: MetaOcgSemanticScopeResolutionProbeRequest,
    namespace_prefix: str | None,
    reason: str,
) -> MetaOcgSemanticScopeResolutionProbeEvidence:
    return MetaOcgSemanticScopeResolutionProbeEvidence(
        status=PROBE_STATUS_BLOCKED,
        symbol_kind=probe.symbol_kind,
        identifier=probe.identifier,
        code_id=str(probe.code_id),
        namespace_prefix=namespace_prefix,
        resolved_fqn=None,
        resolved_object_id=None,
        reason=reason,
        blockers=_probe_blockers(probe=probe, status=PROBE_STATUS_BLOCKED),
    )


def _symbol_evidence(
    *,
    symbol_kind: str,
    fqn: str,
    object_id: str,
    origin: str,
) -> MetaOcgSemanticScopeSymbolEvidence:
    package, namespace, name = _fqn_parts(fqn)
    return MetaOcgSemanticScopeSymbolEvidence(
        symbol_kind=symbol_kind,
        fqn=fqn,
        object_id=object_id,
        origin=origin,
        package=package,
        namespace=namespace,
        name=name,
    )


def _fqn_parts(fqn: str) -> tuple[str, str, str]:
    parts = [part for part in fqn.split(".") if part]
    package = parts[0] if len(parts) >= 1 else ""
    namespace = ".".join(parts[1:-1])
    name = parts[-1] if parts else ""
    return package, namespace, name


def _namespace_matches_prefix(
    *,
    namespace: NamespacePath,
    package_fqn_prefix: str,
) -> bool:
    return namespace.package == package_fqn_prefix or namespace.prefix().startswith(
        f"{package_fqn_prefix}."
    )


def _scope_closure_payload(
    value: MetaOcgSemanticScopeClosureEvidence | Mapping[str, object] | None,
) -> dict[str, object]:
    if isinstance(value, MetaOcgSemanticScopeClosureEvidence):
        return value.evidence_payload()
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _scope_closure_contains_symbol(
    *,
    semantic_scope_closure: Mapping[str, object],
    symbol_kind: str,
    fqn: str,
) -> bool:
    for symbol in _sequence(semantic_scope_closure.get("symbols")):
        symbol_payload = _mapping_value(symbol)
        if (
            _optional_text(symbol_payload.get("symbol_kind")) == symbol_kind
            and _optional_text(symbol_payload.get("fqn")) == fqn
        ):
            return True
    return False


def _mapping_value(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return ()


def _tuple_text(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item) for item in value if str(item))


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _probe_blocker(
    *,
    probe: MetaOcgSemanticScopeResolutionProbeRequest,
    status: str,
) -> str:
    return (
        "resolution_probe_"
        f"{status}:{probe.symbol_kind}:{probe.code_id}:{probe.identifier}"
    )


def _probe_blockers(
    *,
    probe: MetaOcgSemanticScopeResolutionProbeRequest,
    status: str,
) -> tuple[str, ...]:
    if not probe.required:
        return ()
    return (_probe_blocker(probe=probe, status=status),)


def _unique_sorted(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))


__all__ = [
    "META_OCG_SEMANTIC_SCOPE_CLOSURE_CONTRACT_VERSION",
    "PROBE_STATUS_AMBIGUOUS",
    "PROBE_STATUS_BLOCKED",
    "PROBE_STATUS_RESOLVED",
    "PROBE_STATUS_UNRESOLVED",
    "SCOPE_GATE_STATUS_BLOCKED",
    "SCOPE_GATE_STATUS_READY",
    "SCOPE_STATUS_BLOCKED",
    "SCOPE_STATUS_READY",
    "SYMBOL_KIND_CLASS",
    "SYMBOL_KIND_ENUM",
    "SYMBOL_ORIGIN_EXTERNAL",
    "SYMBOL_ORIGIN_LOCAL",
    "MetaOcgSemanticScopeClosureEvidence",
    "MetaOcgSemanticScopeResolutionProbeEvidence",
    "MetaOcgSemanticScopeResolutionProbeRequest",
    "MetaOcgSemanticScopeSymbolEvidence",
    "build_meta_ocg_semantic_scope_closure",
    "meta_ocg_class_fqn_scope_closure_gate",
    "meta_ocg_enum_fqn_scope_closure_gate",
]
