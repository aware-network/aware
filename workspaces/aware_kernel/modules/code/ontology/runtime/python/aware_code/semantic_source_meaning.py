from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Literal, cast

from aware_code_ontology.code.code_plan import CodePackageDelta

from aware_code.semantic_capability import (
    SemanticCapabilityActionBinding,
    SemanticCapabilityChangePreview,
    SemanticCapabilityDelta,
    SemanticCapabilityEvent,
    SemanticCapabilityEventVerb,
    SemanticCapabilityFunctionCallBinding,
    SemanticCapabilityTypedOperation,
)
from aware_code.semantic_materialization import (
    SEMANTIC_SOURCE_SESSION_SOURCE_INDEX_CACHE_KIND,
    SemanticSourceSessionContext,
)
from aware_code.source_index import (
    CodeGrammarAnchorQuery,
    CodeGrammarAnchorResolution,
    CodeGrammarGraphSelector,
    CodeGrammarSourceIndex,
    CodeGrammarSourceIndexCache,
    CodeGrammarSource,
)


CODE_SEMANTIC_SOURCE_MEANING_BINDING_CONTRACT_VERSION = (
    "aware.code.semantic-source-meaning-binding.v1"
)
CODE_SEMANTIC_SOURCE_DELTA_MEANING_CONTRACT_VERSION = (
    "aware.code.semantic-source-delta-meaning.v1"
)
_CONTRACT_SOURCE = "aware_code.semantic_source_meaning"
_IDENTITY_RENAME_POLICY_KEY = "identity_rename_policy"
_IDENTITY_RENAME_POLICIES = frozenset(
    {
        "block",
        "explicit_fallback_required",
        "block_explicit_policy_required",
        "fail_closed",
        "emit_rename",
    }
)
_SOURCE_INDEX_CACHE = CodeGrammarSourceIndexCache(max_entries=64)
CodeSemanticSourceDeltaMeaningResolutionMode = Literal[
    "source_pair_snapshot",
    "delta_with_snapshot_fallback",
    "delta_with_index_ref",
    "blocked",
]


@dataclass(frozen=True, slots=True)
class CodeSemanticSourceMeaningBinding:
    """Declarative source-to-semantic meaning binding over a grammar anchor."""

    binding_key: str
    grammar_rule_name: str
    anchor_field_path: str
    graph_selector: CodeGrammarGraphSelector
    semantic_subject_type: str
    semantic_key_template: str
    semantic_field: str
    language: str = "aware"
    grammar_profile_key: str | None = None
    anchor_role: str | None = None
    value_domain: str | None = None
    event_key_template: str | None = None
    event_type: str = "semantic_change"
    condition_keys: tuple[str, ...] = ()
    required: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)

    def anchor_query(self) -> CodeGrammarAnchorQuery:
        return CodeGrammarAnchorQuery(
            binding_key=self.binding_key,
            language=self.language,
            grammar_profile_key=self.grammar_profile_key,
            grammar_rule_name=self.grammar_rule_name,
            anchor_field_path=self.anchor_field_path,
            graph_selector=self.graph_selector,
            anchor_role=self.anchor_role,
            value_domain=self.value_domain,
        )

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "binding_key": self.binding_key,
            "language": self.language,
            "grammar_rule_name": self.grammar_rule_name,
            "anchor_field_path": self.anchor_field_path,
            "graph_selector": self.graph_selector.evidence_payload(),
            "semantic_subject_type": self.semantic_subject_type,
            "semantic_key_template": self.semantic_key_template,
            "semantic_field": self.semantic_field,
            "event_type": self.event_type,
            "condition_keys": self.condition_keys,
            "required": self.required,
            "metadata": dict(self.metadata),
        }
        if self.grammar_profile_key is not None:
            payload["grammar_profile_key"] = self.grammar_profile_key
        if self.anchor_role is not None:
            payload["anchor_role"] = self.anchor_role
        if self.value_domain is not None:
            payload["value_domain"] = self.value_domain
        if self.event_key_template is not None:
            payload["event_key_template"] = self.event_key_template
        return payload


@dataclass(frozen=True, slots=True)
class CodeSemanticSourceMeaningContract:
    provider_key: str
    semantic_owner: str
    bindings: tuple[CodeSemanticSourceMeaningBinding, ...]
    grammar_profile_key: str | None = None
    supported_languages: tuple[str, ...] = ("aware",)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "contract_version": CODE_SEMANTIC_SOURCE_MEANING_BINDING_CONTRACT_VERSION,
            "provider_key": self.provider_key,
            "semantic_owner": self.semantic_owner,
            "supported_languages": self.supported_languages,
            "binding_count": len(self.bindings),
            "bindings": tuple(binding.evidence_payload() for binding in self.bindings),
            "metadata": dict(self.metadata),
        }
        if self.grammar_profile_key is not None:
            payload["grammar_profile_key"] = self.grammar_profile_key
        return payload


@dataclass(frozen=True, slots=True)
class CodeSemanticSourceMeaningResolution:
    contract: CodeSemanticSourceMeaningContract
    status: Literal["resolved", "blocked"]
    diagnostics: tuple[str, ...] = ()
    semantic_deltas: tuple[SemanticCapabilityDelta, ...] = ()
    semantic_events: tuple[SemanticCapabilityEvent, ...] = ()
    typed_operations: tuple[SemanticCapabilityTypedOperation, ...] = ()
    action_bindings: tuple[SemanticCapabilityActionBinding, ...] = ()
    binding_count: int = 0
    resolved_binding_count: int = 0
    changed_binding_count: int = 0
    source_index_evidence: Mapping[str, object] = field(default_factory=dict)

    @property
    def resolved(self) -> bool:
        return self.status == "resolved"

    def change_preview(self) -> SemanticCapabilityChangePreview:
        return SemanticCapabilityChangePreview(
            changed_source_files=tuple(
                sorted(
                    {
                        source_ref
                        for delta in self.semantic_deltas
                        for source_ref in delta.source_refs
                    }
                )
            ),
            affected_semantic_keys=tuple(
                sorted({delta.semantic_key for delta in self.semantic_deltas})
            ),
            semantic_deltas=self.semantic_deltas,
            semantic_events=self.semantic_events,
            typed_operations=self.typed_operations,
            action_bindings=self.action_bindings,
            metadata={
                "source": _CONTRACT_SOURCE,
                "contract_version": (
                    CODE_SEMANTIC_SOURCE_MEANING_BINDING_CONTRACT_VERSION
                ),
                "binding_count": self.binding_count,
                "resolved_binding_count": self.resolved_binding_count,
                "changed_binding_count": self.changed_binding_count,
            },
        )

    def evidence_payload(self) -> dict[str, object]:
        return {
            "source": _CONTRACT_SOURCE,
            "contract_version": CODE_SEMANTIC_SOURCE_MEANING_BINDING_CONTRACT_VERSION,
            "status": self.status,
            "diagnostics": self.diagnostics,
            "provider_key": self.contract.provider_key,
            "semantic_owner": self.contract.semantic_owner,
            "binding_count": self.binding_count,
            "resolved_binding_count": self.resolved_binding_count,
            "changed_binding_count": self.changed_binding_count,
            "semantic_deltas": tuple(
                delta.evidence_payload() for delta in self.semantic_deltas
            ),
            "semantic_events": tuple(
                event.evidence_payload() for event in self.semantic_events
            ),
            "typed_operations": tuple(
                operation.evidence_payload() for operation in self.typed_operations
            ),
            "action_bindings": tuple(
                action_binding.evidence_payload()
                for action_binding in self.action_bindings
            ),
            "source_index_evidence": dict(self.source_index_evidence),
            "contract": self.contract.evidence_payload(),
        }


@dataclass(frozen=True, slots=True)
class CodeSemanticSourceIndexRef:
    """Opaque source-index reference supplied by Workspace/service session state."""

    ref_kind: str
    cache_kind: str | None = None
    cache_key: str | None = None
    source_session_id: str | None = None
    source_delta_fingerprint: str | None = None
    package_name: str | None = None
    source_revision_id: str | None = None
    source_keys: tuple[str, ...] = ()
    source_hashes: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "ref_kind": self.ref_kind,
            "source_keys": self.source_keys,
            "source_hashes": dict(self.source_hashes),
            "metadata": dict(self.metadata),
        }
        for key, value in (
            ("cache_kind", self.cache_kind),
            ("cache_key", self.cache_key),
            ("source_session_id", self.source_session_id),
            ("source_delta_fingerprint", self.source_delta_fingerprint),
            ("package_name", self.package_name),
            ("source_revision_id", self.source_revision_id),
        ):
            if value is not None:
                payload[key] = value
        return payload


@dataclass(frozen=True, slots=True)
class CodeSemanticSourceDeltaMeaningResolution:
    contract: CodeSemanticSourceMeaningContract
    status: Literal["resolved", "blocked"]
    meaning_resolution_mode: CodeSemanticSourceDeltaMeaningResolutionMode
    diagnostics: tuple[str, ...] = ()
    required_context: tuple[str, ...] = ()
    semantic_deltas: tuple[SemanticCapabilityDelta, ...] = ()
    semantic_events: tuple[SemanticCapabilityEvent, ...] = ()
    typed_operations: tuple[SemanticCapabilityTypedOperation, ...] = ()
    action_bindings: tuple[SemanticCapabilityActionBinding, ...] = ()
    binding_count: int = 0
    resolved_binding_count: int = 0
    changed_binding_count: int = 0
    source_index_evidence: Mapping[str, object] = field(default_factory=dict)

    @property
    def resolved(self) -> bool:
        return self.status == "resolved"

    def change_preview(self) -> SemanticCapabilityChangePreview:
        return SemanticCapabilityChangePreview(
            changed_source_files=tuple(
                sorted(
                    {
                        source_ref
                        for delta in self.semantic_deltas
                        for source_ref in delta.source_refs
                    }
                )
            ),
            affected_semantic_keys=tuple(
                sorted({delta.semantic_key for delta in self.semantic_deltas})
            ),
            semantic_deltas=self.semantic_deltas,
            semantic_events=self.semantic_events,
            typed_operations=self.typed_operations,
            action_bindings=self.action_bindings,
            metadata={
                "source": _CONTRACT_SOURCE,
                "contract_version": CODE_SEMANTIC_SOURCE_DELTA_MEANING_CONTRACT_VERSION,
                "binding_count": self.binding_count,
                "resolved_binding_count": self.resolved_binding_count,
                "changed_binding_count": self.changed_binding_count,
                "meaning_resolution_mode": self.meaning_resolution_mode,
            },
        )

    def evidence_payload(self) -> dict[str, object]:
        return {
            "source": _CONTRACT_SOURCE,
            "contract_version": CODE_SEMANTIC_SOURCE_DELTA_MEANING_CONTRACT_VERSION,
            "status": self.status,
            "meaning_resolution_mode": self.meaning_resolution_mode,
            "diagnostics": self.diagnostics,
            "required_context": self.required_context,
            "provider_key": self.contract.provider_key,
            "semantic_owner": self.contract.semantic_owner,
            "binding_count": self.binding_count,
            "resolved_binding_count": self.resolved_binding_count,
            "changed_binding_count": self.changed_binding_count,
            "semantic_deltas": tuple(
                delta.evidence_payload() for delta in self.semantic_deltas
            ),
            "semantic_events": tuple(
                event.evidence_payload() for event in self.semantic_events
            ),
            "typed_operations": tuple(
                operation.evidence_payload() for operation in self.typed_operations
            ),
            "action_bindings": tuple(
                action_binding.evidence_payload()
                for action_binding in self.action_bindings
            ),
            "source_index_evidence": dict(self.source_index_evidence),
            "contract": self.contract.evidence_payload(),
        }


def resolve_code_semantic_source_meaning(
    *,
    contract: CodeSemanticSourceMeaningContract,
    current_source_index: CodeGrammarSourceIndex,
    baseline_source_index: CodeGrammarSourceIndex | None = None,
    include_noop: bool = False,
) -> CodeSemanticSourceMeaningResolution:
    diagnostics = _validate_contract(contract=contract)
    semantic_deltas: list[SemanticCapabilityDelta] = []
    semantic_events: list[SemanticCapabilityEvent] = []
    typed_operations: list[SemanticCapabilityTypedOperation] = []
    action_bindings: list[SemanticCapabilityActionBinding] = []
    resolved_binding_count = 0

    for binding in contract.bindings:
        query = binding.anchor_query()
        before_resolutions = (
            baseline_source_index.resolve_anchors(query=query)
            if baseline_source_index is not None
            else ()
        )
        after_resolutions = current_source_index.resolve_anchors(query=query)
        before_resolutions = _filter_resolutions_for_required_template_values(
            binding=binding,
            resolutions=before_resolutions,
        )
        after_resolutions = _filter_resolutions_for_required_template_values(
            binding=binding,
            resolutions=after_resolutions,
        )
        before_by_key = _resolutions_by_semantic_key(
            contract=contract,
            binding=binding,
            resolutions=before_resolutions,
            side="baseline",
            diagnostics=diagnostics,
        )
        after_by_key = _resolutions_by_semantic_key(
            contract=contract,
            binding=binding,
            resolutions=after_resolutions,
            side="current",
            diagnostics=diagnostics,
        )
        if before_resolutions or after_resolutions:
            resolved_binding_count += 1
        if not before_resolutions and not after_resolutions:
            if binding.required:
                diagnostics.append(
                    f"binding {binding.binding_key!r} did not resolve in current "
                    "or baseline source index."
                )
            continue
        rename_pair = _identity_rename_pair(
            binding=binding,
            before_by_key=before_by_key,
            after_by_key=after_by_key,
        )
        if rename_pair is not None:
            before, after = rename_pair
            delta = _semantic_delta_for_binding(
                contract=contract,
                binding=binding,
                before=before,
                after=after,
                verb="rename",
            )
            event = _semantic_event_for_delta(
                contract=contract,
                binding=binding,
                delta=delta,
                before=before,
                after=after,
            )
            semantic_deltas.append(delta)
            semantic_events.append(event)
            typed_operations.extend(
                _typed_operations_for_event(
                    contract=contract,
                    binding=binding,
                    delta=delta,
                    event=event,
                    resolution=after,
                )
            )
            action_bindings.extend(
                _action_bindings_for_event(
                    contract=contract,
                    binding=binding,
                    event=event,
                    resolution=after,
                )
            )
            continue
        semantic_keys = tuple(sorted({*before_by_key, *after_by_key}))
        for semantic_key in semantic_keys:
            before = before_by_key.get(semantic_key)
            after = after_by_key.get(semantic_key)
            verb = _meaning_verb(binding=binding, before=before, after=after)
            if verb == "noop" and not include_noop:
                continue
            delta = _semantic_delta_for_binding(
                contract=contract,
                binding=binding,
                before=before,
                after=after,
                verb=verb,
            )
            event = _semantic_event_for_delta(
                contract=contract,
                binding=binding,
                delta=delta,
                before=before,
                after=after,
            )
            semantic_deltas.append(delta)
            semantic_events.append(event)
            typed_operations.extend(
                _typed_operations_for_event(
                    contract=contract,
                    binding=binding,
                    delta=delta,
                    event=event,
                    resolution=after or before,
                )
            )
            action_bindings.extend(
                _action_bindings_for_event(
                    contract=contract,
                    binding=binding,
                    event=event,
                    resolution=after or before,
                )
            )

    return CodeSemanticSourceMeaningResolution(
        contract=contract,
        status="blocked" if diagnostics else "resolved",
        diagnostics=tuple(diagnostics),
        semantic_deltas=tuple(semantic_deltas),
        semantic_events=tuple(semantic_events),
        typed_operations=tuple(typed_operations),
        action_bindings=tuple(action_bindings),
        binding_count=len(contract.bindings),
        resolved_binding_count=resolved_binding_count,
        changed_binding_count=len(semantic_deltas),
        source_index_evidence=current_source_index.evidence_payload(),
    )


def resolve_code_semantic_source_delta_meaning(
    *,
    contract: CodeSemanticSourceMeaningContract,
    code_package_delta: CodePackageDelta,
    baseline_source_index: CodeGrammarSourceIndex | None = None,
    current_source_index: CodeGrammarSourceIndex | None = None,
    baseline_sources: Iterable[CodeGrammarSource] = (),
    current_sources: Iterable[CodeGrammarSource] = (),
    baseline_source_index_ref: CodeSemanticSourceIndexRef | None = None,
    current_source_index_ref: CodeSemanticSourceIndexRef | None = None,
    session_context: SemanticSourceSessionContext | None = None,
    include_noop: bool = False,
) -> CodeSemanticSourceDeltaMeaningResolution:
    diagnostics: list[str] = []
    required_context: list[str] = []
    paths = tuple(code_package_delta.paths)
    if not paths:
        diagnostics.append("CodePackageDelta must include at least one path.")

    baseline_sources_tuple = tuple(baseline_sources)
    current_sources_tuple = tuple(current_sources) or _current_sources_from_delta(
        delta=code_package_delta,
        diagnostics=diagnostics,
        require_content=(
            current_source_index is None and current_source_index_ref is None
        ),
    )

    diagnostics.extend(
        _delta_source_hash_diagnostics(
            paths=paths,
            baseline_sources=baseline_sources_tuple,
            current_sources=current_sources_tuple,
        )
    )
    resolved_baseline_source_index = _delta_source_index_for_side(
        explicit_source_index=baseline_source_index,
        sources=baseline_sources_tuple,
        source_index_ref=baseline_source_index_ref,
        session_context=session_context,
    )
    resolved_current_source_index = _delta_source_index_for_side(
        explicit_source_index=current_source_index,
        sources=current_sources_tuple,
        source_index_ref=current_source_index_ref,
        session_context=session_context,
    )
    _collect_delta_context_requirements(
        paths=paths,
        baseline_source_index=resolved_baseline_source_index,
        baseline_source_index_ref=baseline_source_index_ref,
        current_source_index=resolved_current_source_index,
        current_source_index_ref=current_source_index_ref,
        required_context=required_context,
    )
    if diagnostics or required_context:
        return _blocked_delta_meaning_resolution(
            contract=contract,
            diagnostics=tuple(diagnostics),
            required_context=tuple(dict.fromkeys(required_context)),
            baseline_source_index=resolved_baseline_source_index,
            current_source_index=resolved_current_source_index,
            baseline_source_index_ref=baseline_source_index_ref,
            current_source_index_ref=current_source_index_ref,
        )
    if resolved_current_source_index is None:
        resolved_current_source_index = CodeGrammarSourceIndex.from_sources(
            (),
            session_context=session_context,
        )
    resolution = resolve_code_semantic_source_meaning(
        contract=contract,
        current_source_index=resolved_current_source_index,
        baseline_source_index=resolved_baseline_source_index,
        include_noop=include_noop,
    )
    mode: CodeSemanticSourceDeltaMeaningResolutionMode = (
        "delta_with_index_ref"
        if (
            baseline_source_index is not None
            or current_source_index is not None
            or baseline_source_index_ref is not None
            or current_source_index_ref is not None
        )
        else "delta_with_snapshot_fallback"
    )
    return CodeSemanticSourceDeltaMeaningResolution(
        contract=contract,
        status=resolution.status,
        meaning_resolution_mode=mode if resolution.resolved else "blocked",
        diagnostics=resolution.diagnostics,
        semantic_deltas=resolution.semantic_deltas,
        semantic_events=resolution.semantic_events,
        typed_operations=resolution.typed_operations,
        action_bindings=resolution.action_bindings,
        binding_count=resolution.binding_count,
        resolved_binding_count=resolution.resolved_binding_count,
        changed_binding_count=resolution.changed_binding_count,
        source_index_evidence=_delta_source_index_evidence(
            baseline_source_index=resolved_baseline_source_index,
            current_source_index=resolved_current_source_index,
            baseline_source_index_ref=baseline_source_index_ref,
            current_source_index_ref=current_source_index_ref,
            code_package_delta=code_package_delta,
            mode=mode,
        ),
    )


def _validate_contract(*, contract: CodeSemanticSourceMeaningContract) -> list[str]:
    diagnostics: list[str] = []
    if not contract.provider_key.strip():
        diagnostics.append("provider_key is required.")
    if not contract.semantic_owner.strip():
        diagnostics.append("semantic_owner is required.")
    if not contract.bindings:
        diagnostics.append("bindings must include at least one meaning binding.")
    seen_keys: set[str] = set()
    for index, binding in enumerate(contract.bindings):
        prefix = f"bindings[{index}]"
        if not binding.binding_key.strip():
            diagnostics.append(f"{prefix}.binding_key is required.")
        elif binding.binding_key in seen_keys:
            diagnostics.append(
                f"{prefix}.binding_key {binding.binding_key!r} is duplicated."
            )
        seen_keys.add(binding.binding_key)
        if binding.language not in contract.supported_languages:
            diagnostics.append(
                f"{prefix}.language {binding.language!r} is not supported."
            )
        if not binding.grammar_rule_name.strip():
            diagnostics.append(f"{prefix}.grammar_rule_name is required.")
        if not binding.anchor_field_path.strip():
            diagnostics.append(f"{prefix}.anchor_field_path is required.")
        if not binding.semantic_subject_type.strip():
            diagnostics.append(f"{prefix}.semantic_subject_type is required.")
        if not binding.semantic_key_template.strip():
            diagnostics.append(f"{prefix}.semantic_key_template is required.")
        if not binding.semantic_field.strip():
            diagnostics.append(f"{prefix}.semantic_field is required.")
    return diagnostics


def _resolutions_by_semantic_key(
    *,
    contract: CodeSemanticSourceMeaningContract,
    binding: CodeSemanticSourceMeaningBinding,
    resolutions: tuple[CodeGrammarAnchorResolution, ...],
    side: str,
    diagnostics: list[str],
) -> dict[str, CodeGrammarAnchorResolution]:
    by_key: dict[str, CodeGrammarAnchorResolution] = {}
    ambiguous_keys: set[str] = set()
    for resolution in resolutions:
        semantic_key = _render_template(
            binding.semantic_key_template,
            contract=contract,
            binding=binding,
            resolution=resolution,
        )
        if semantic_key in ambiguous_keys:
            continue
        if semantic_key in by_key:
            diagnostics.append(
                f"binding {binding.binding_key!r} resolved ambiguous {side} "
                f"semantic key {semantic_key!r}."
            )
            ambiguous_keys.add(semantic_key)
            by_key.pop(semantic_key, None)
            continue
        by_key[semantic_key] = resolution
    return by_key


def _identity_rename_pair(
    *,
    binding: CodeSemanticSourceMeaningBinding,
    before_by_key: Mapping[str, CodeGrammarAnchorResolution],
    after_by_key: Mapping[str, CodeGrammarAnchorResolution],
) -> tuple[CodeGrammarAnchorResolution, CodeGrammarAnchorResolution] | None:
    if not _binding_emits_identity_rename(binding=binding):
        return None
    before_keys = set(before_by_key)
    after_keys = set(after_by_key)
    if before_keys & after_keys:
        return None
    before_only = tuple(sorted(before_keys - after_keys))
    after_only = tuple(sorted(after_keys - before_keys))
    if len(before_only) != 1 or len(after_only) != 1:
        return None
    before = before_by_key[before_only[0]]
    after = after_by_key[after_only[0]]
    if before.text == after.text:
        return None
    if not _same_identity_anchor_position(before=before, after=after):
        return None
    return before, after


def _binding_emits_identity_rename(
    *,
    binding: CodeSemanticSourceMeaningBinding,
) -> bool:
    policy = _optional_text(binding.metadata.get(_IDENTITY_RENAME_POLICY_KEY))
    return policy in _IDENTITY_RENAME_POLICIES


def _same_identity_anchor_position(
    *,
    before: CodeGrammarAnchorResolution,
    after: CodeGrammarAnchorResolution,
) -> bool:
    return (
        _resolution_source_ref(before) == _resolution_source_ref(after)
        and before.language == after.language
        and before.grammar_rule_name == after.grammar_rule_name
        and before.anchor_field_path == after.anchor_field_path
        and before.parser_node_kind == after.parser_node_kind
        and before.anchor_node_kind == after.anchor_node_kind
        and before.byte_start == after.byte_start
    )


def _resolution_source_ref(resolution: CodeGrammarAnchorResolution) -> str:
    return resolution.relative_path or resolution.source_key


def _blocked_delta_meaning_resolution(
    *,
    contract: CodeSemanticSourceMeaningContract,
    diagnostics: tuple[str, ...],
    required_context: tuple[str, ...],
    baseline_source_index: CodeGrammarSourceIndex | None,
    current_source_index: CodeGrammarSourceIndex | None,
    baseline_source_index_ref: CodeSemanticSourceIndexRef | None,
    current_source_index_ref: CodeSemanticSourceIndexRef | None,
) -> CodeSemanticSourceDeltaMeaningResolution:
    return CodeSemanticSourceDeltaMeaningResolution(
        contract=contract,
        status="blocked",
        meaning_resolution_mode="blocked",
        diagnostics=diagnostics,
        required_context=required_context,
        binding_count=len(contract.bindings),
        source_index_evidence=_delta_source_index_evidence(
            baseline_source_index=baseline_source_index,
            current_source_index=current_source_index,
            baseline_source_index_ref=baseline_source_index_ref,
            current_source_index_ref=current_source_index_ref,
            code_package_delta=None,
            mode="blocked",
        ),
    )


def _delta_source_index_for_side(
    *,
    explicit_source_index: CodeGrammarSourceIndex | None,
    sources: tuple[CodeGrammarSource, ...],
    source_index_ref: CodeSemanticSourceIndexRef | None,
    session_context: SemanticSourceSessionContext | None,
) -> CodeGrammarSourceIndex | None:
    if explicit_source_index is not None:
        _SOURCE_INDEX_CACHE.store(
            source_index=explicit_source_index,
            cache_keys=_source_index_ref_cache_keys(source_index_ref),
        )
        return explicit_source_index
    cache_keys = _source_index_ref_cache_keys(source_index_ref)
    if sources:
        return _SOURCE_INDEX_CACHE.get_or_build(
            sources=sources,
            session_context=session_context,
            cache_keys=cache_keys,
        )
    for cache_key in cache_keys:
        source_index = _SOURCE_INDEX_CACHE.get_by_cache_key(
            cache_key=cache_key,
            session_context=session_context,
        )
        if source_index is not None:
            return source_index
    return None


def _source_index_ref_cache_keys(
    source_index_ref: CodeSemanticSourceIndexRef | None,
) -> tuple[str, ...]:
    if (
        source_index_ref is None
        or source_index_ref.cache_kind
        != SEMANTIC_SOURCE_SESSION_SOURCE_INDEX_CACHE_KIND
        or source_index_ref.cache_key is None
    ):
        return ()
    cache_key = source_index_ref.cache_key.strip()
    return (cache_key,) if cache_key else ()


def clear_code_semantic_source_index_cache_for_tests() -> None:
    _SOURCE_INDEX_CACHE.clear()


def _collect_delta_context_requirements(
    *,
    paths: tuple[object, ...],
    baseline_source_index: CodeGrammarSourceIndex | None,
    baseline_source_index_ref: CodeSemanticSourceIndexRef | None,
    current_source_index: CodeGrammarSourceIndex | None,
    current_source_index_ref: CodeSemanticSourceIndexRef | None,
    required_context: list[str],
) -> None:
    has_baseline_context = baseline_source_index is not None
    has_current_context = current_source_index is not None
    for path in paths:
        kind = _delta_path_kind(path)
        relative_path = _delta_path_relative_path(path)
        if kind in {"update", "delete"} and not has_baseline_context:
            required_context.append(
                "baseline_source_index_ref_hydration"
                if baseline_source_index_ref is not None
                else f"baseline_source:{relative_path}"
            )
        if kind in {"create", "update"} and not has_current_context:
            required_context.append(
                "current_source_index_ref_hydration"
                if current_source_index_ref is not None
                else f"current_source:{relative_path}"
            )


def _current_sources_from_delta(
    *,
    delta: CodePackageDelta,
    diagnostics: list[str],
    require_content: bool = True,
) -> tuple[CodeGrammarSource, ...]:
    sources: list[CodeGrammarSource] = []
    for path in delta.paths:
        kind = _delta_path_kind(path)
        if kind == "delete":
            continue
        relative_path = _delta_path_relative_path(path)
        content_text = _delta_path_content_text(path)
        if content_text is None:
            if require_content:
                diagnostics.append(
                    "CodePackageDelta path requires content_text or content_plan for "
                    f"semantic source delta meaning: {relative_path}"
                )
            continue
        sources.append(
            CodeGrammarSource(
                source_key=relative_path,
                source_text=content_text,
                language=_delta_path_language(path),
                grammar_profile_key=None,
                relative_path=relative_path,
            )
        )
    return tuple(sources)


def _delta_source_hash_diagnostics(
    *,
    paths: tuple[object, ...],
    baseline_sources: tuple[CodeGrammarSource, ...],
    current_sources: tuple[CodeGrammarSource, ...],
) -> tuple[str, ...]:
    diagnostics: list[str] = []
    baseline_by_key = _sources_by_key(sources=baseline_sources)
    current_by_key = _sources_by_key(sources=current_sources)
    for path in paths:
        relative_path = _delta_path_relative_path(path)
        before_hash = _optional_text(getattr(path, "before_hash", None))
        after_hash = _optional_text(getattr(path, "after_hash", None))
        if before_hash is not None:
            source = baseline_by_key.get(relative_path)
            if source is not None:
                actual_hash = _sha256_text(source.source_text)
                if not _hash_matches(expected=before_hash, actual=actual_hash):
                    diagnostics.append(
                        "baseline source hash mismatch for "
                        f"{relative_path}: expected {before_hash}, got {actual_hash}."
                    )
        if after_hash is not None:
            source = current_by_key.get(relative_path)
            if source is not None:
                actual_hash = _sha256_text(source.source_text)
                if not _hash_matches(expected=after_hash, actual=actual_hash):
                    diagnostics.append(
                        "current source hash mismatch for "
                        f"{relative_path}: expected {after_hash}, got {actual_hash}."
                    )
    return tuple(diagnostics)


def _sources_by_key(
    *,
    sources: tuple[CodeGrammarSource, ...],
) -> dict[str, CodeGrammarSource]:
    by_key: dict[str, CodeGrammarSource] = {}
    for source in sources:
        by_key[source.source_key] = source
        if source.relative_path is not None:
            by_key[source.relative_path] = source
    return by_key


def _delta_source_index_evidence(
    *,
    baseline_source_index: CodeGrammarSourceIndex | None,
    current_source_index: CodeGrammarSourceIndex | None,
    baseline_source_index_ref: CodeSemanticSourceIndexRef | None,
    current_source_index_ref: CodeSemanticSourceIndexRef | None,
    code_package_delta: CodePackageDelta | None,
    mode: CodeSemanticSourceDeltaMeaningResolutionMode,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "contract_version": CODE_SEMANTIC_SOURCE_DELTA_MEANING_CONTRACT_VERSION,
        "meaning_resolution_mode": mode,
        "baseline": (
            baseline_source_index.evidence_payload()
            if baseline_source_index is not None
            else None
        ),
        "current": (
            current_source_index.evidence_payload()
            if current_source_index is not None
            else None
        ),
    }
    payload.update(
        _delta_source_index_cache_summary(
            baseline_source_index=baseline_source_index,
            current_source_index=current_source_index,
        )
    )
    if baseline_source_index_ref is not None:
        payload["baseline_source_index_ref"] = (
            baseline_source_index_ref.evidence_payload()
        )
    if current_source_index_ref is not None:
        payload["current_source_index_ref"] = (
            current_source_index_ref.evidence_payload()
        )
    if code_package_delta is not None:
        payload["delta"] = {
            "package_name": code_package_delta.package_name,
            "package_root": code_package_delta.package_root,
            "manifest_relative_path": code_package_delta.manifest_relative_path,
            "source_revision_id": code_package_delta.source_revision_id,
            "path_count": len(code_package_delta.paths),
            "paths": tuple(
                {
                    "relative_path": _delta_path_relative_path(path),
                    "kind": _delta_path_kind(path),
                    "content_text_present": _delta_path_content_text(path) is not None,
                    "before_hash_present": (
                        _optional_text(getattr(path, "before_hash", None)) is not None
                    ),
                    "after_hash_present": (
                        _optional_text(getattr(path, "after_hash", None)) is not None
                    ),
                }
                for path in code_package_delta.paths
            ),
        }
    return payload


def _delta_source_index_cache_summary(
    *,
    baseline_source_index: CodeGrammarSourceIndex | None,
    current_source_index: CodeGrammarSourceIndex | None,
) -> dict[str, object]:
    statuses = tuple(
        status
        for source_index in (baseline_source_index, current_source_index)
        for status in (_source_index_cache_status(source_index),)
        if status is not None
    )
    return {
        "cache_statuses": statuses,
        "cache_hit_count": sum(
            1 for status in statuses if status == "process_cache_hit"
        ),
        "cache_miss_count": sum(
            1 for status in statuses if status == "process_cache_miss"
        ),
    }


def _source_index_cache_status(
    source_index: CodeGrammarSourceIndex | None,
) -> str | None:
    if source_index is None:
        return None
    session = source_index.evidence_payload().get("session")
    if not isinstance(session, Mapping):
        return None
    return _optional_text(session.get("cache_status"))


def _delta_path_kind(path: object) -> str:
    return str(getattr(getattr(path, "kind", ""), "value", getattr(path, "kind", "")))


def _delta_path_relative_path(path: object) -> str:
    return str(getattr(path, "relative_path", "")).strip().strip("/")


def _delta_path_language(path: object) -> str:
    language = getattr(path, "language", None)
    if language is None:
        return "aware"
    return str(getattr(language, "value", language)).strip() or "aware"


def _delta_path_content_text(path: object) -> str | None:
    content_text = getattr(path, "content_text", None)
    if isinstance(content_text, str):
        return content_text
    content_plan = getattr(path, "content_plan", None)
    planned_text = getattr(content_plan, "content_text", None)
    if isinstance(planned_text, str):
        return planned_text
    return None


def _meaning_verb(
    *,
    binding: CodeSemanticSourceMeaningBinding,
    before: CodeGrammarAnchorResolution | None,
    after: CodeGrammarAnchorResolution | None,
) -> SemanticCapabilityEventVerb:
    if before is None and after is not None:
        return "upsert"
    if before is not None and after is None:
        return "delete"
    if before is not None and after is not None:
        change_detection_fields = _change_detection_template_fields(binding=binding)
        if change_detection_fields:
            for field_name in change_detection_fields:
                if before.template_values.get(field_name) != after.template_values.get(
                    field_name
                ):
                    return "update"
            return "noop"
        if before.text != after.text:
            return "update"
        for field_name in change_detection_fields:
            if before.template_values.get(field_name) != after.template_values.get(
                field_name
            ):
                return "update"
    return "noop"


def _filter_resolutions_for_required_template_values(
    *,
    binding: CodeSemanticSourceMeaningBinding,
    resolutions: Iterable[CodeGrammarAnchorResolution],
) -> tuple[CodeGrammarAnchorResolution, ...]:
    required_fields = _required_template_values(binding=binding)
    excluded_fields = _excluded_template_values(binding=binding)
    if not required_fields and not excluded_fields:
        return tuple(resolutions)
    return tuple(
        resolution
        for resolution in resolutions
        if all(
            resolution.template_values.get(field_name)
            for field_name in required_fields
        )
        and not any(
            resolution.template_values.get(field_name)
            for field_name in excluded_fields
        )
    )


def _required_template_values(
    *,
    binding: CodeSemanticSourceMeaningBinding,
) -> tuple[str, ...]:
    raw_fields = binding.metadata.get("required_template_values")
    if not isinstance(raw_fields, (list, tuple)):
        return ()
    return tuple(
        field_name.strip()
        for field_name in raw_fields
        if isinstance(field_name, str) and field_name.strip()
    )


def _excluded_template_values(
    *,
    binding: CodeSemanticSourceMeaningBinding,
) -> tuple[str, ...]:
    raw_fields = binding.metadata.get("excluded_template_values")
    if not isinstance(raw_fields, (list, tuple)):
        return ()
    return tuple(
        field_name.strip()
        for field_name in raw_fields
        if isinstance(field_name, str) and field_name.strip()
    )


def _change_detection_template_fields(
    *,
    binding: CodeSemanticSourceMeaningBinding,
) -> tuple[str, ...]:
    raw_fields = binding.metadata.get("change_detection_template_fields")
    if not isinstance(raw_fields, (list, tuple)):
        return ()
    return tuple(
        field_name.strip()
        for field_name in raw_fields
        if isinstance(field_name, str) and field_name.strip()
    )


def _semantic_delta_for_binding(
    *,
    contract: CodeSemanticSourceMeaningContract,
    binding: CodeSemanticSourceMeaningBinding,
    before: CodeGrammarAnchorResolution | None,
    after: CodeGrammarAnchorResolution | None,
    verb: SemanticCapabilityEventVerb,
) -> SemanticCapabilityDelta:
    resolution = after or before
    if resolution is None:
        raise ValueError("semantic delta requires before or after resolution.")
    semantic_key = _render_template(
        binding.semantic_key_template,
        contract=contract,
        binding=binding,
        resolution=resolution,
    )
    delta_key = (
        f"{contract.provider_key}:{binding.binding_key}:"
        f"{semantic_key}:{binding.semantic_field}:{verb}"
    )
    before_semantic_key = (
        _render_template(
            binding.semantic_key_template,
            contract=contract,
            binding=binding,
            resolution=before,
        )
        if before is not None
        else None
    )
    after_semantic_key = (
        _render_template(
            binding.semantic_key_template,
            contract=contract,
            binding=binding,
            resolution=after,
        )
        if after is not None
        else None
    )
    metadata: dict[str, object] = {
        "contract_version": CODE_SEMANTIC_SOURCE_MEANING_BINDING_CONTRACT_VERSION,
        "binding_key": binding.binding_key,
        "semantic_field": binding.semantic_field,
        "provider_key": contract.provider_key,
        "semantic_owner": contract.semantic_owner,
        "grammar_rule_name": binding.grammar_rule_name,
        "anchor_field_path": binding.anchor_field_path,
        "graph_selector": resolution.graph_selector.evidence_payload(),
        "source_index": resolution.evidence_payload(),
    }
    if before_semantic_key is not None and before_semantic_key != semantic_key:
        metadata["before_semantic_key"] = before_semantic_key
    if after_semantic_key is not None and after_semantic_key != semantic_key:
        metadata["after_semantic_key"] = after_semantic_key
    return SemanticCapabilityDelta(
        delta_key=delta_key,
        semantic_key=semantic_key,
        verb=verb,
        subject_type=binding.semantic_subject_type,
        source=_CONTRACT_SOURCE,
        source_refs=_source_refs(before=before, after=after),
        before_payload=_value_payload(binding=binding, resolution=before),
        after_payload=_value_payload(binding=binding, resolution=after),
        metadata=metadata,
    )


def _semantic_event_for_delta(
    *,
    contract: CodeSemanticSourceMeaningContract,
    binding: CodeSemanticSourceMeaningBinding,
    delta: SemanticCapabilityDelta,
    before: CodeGrammarAnchorResolution | None,
    after: CodeGrammarAnchorResolution | None,
) -> SemanticCapabilityEvent:
    resolution = after or before
    if resolution is None:
        raise ValueError("semantic event requires before or after resolution.")
    event_key = (
        _render_template(
            binding.event_key_template,
            contract=contract,
            binding=binding,
            resolution=resolution,
        )
        if binding.event_key_template is not None
        else f"{delta.semantic_key}:{binding.semantic_field}:{delta.verb}"
    )
    return SemanticCapabilityEvent(
        event_key=event_key,
        semantic_key=delta.semantic_key,
        verb=delta.verb,
        subject_type=delta.subject_type,
        source=_CONTRACT_SOURCE,
        event_type=binding.event_type,
        source_refs=delta.source_refs,
        delta_keys=(delta.delta_key,),
        condition_keys=binding.condition_keys,
        payload={
            "semantic_field": binding.semantic_field,
            "before": before.text if before is not None else None,
            "after": after.text if after is not None else None,
            "binding_key": binding.binding_key,
        },
        metadata={
            "contract_version": CODE_SEMANTIC_SOURCE_MEANING_BINDING_CONTRACT_VERSION,
            "source_index": resolution.evidence_payload(),
        },
    )


def _action_bindings_for_event(
    *,
    contract: CodeSemanticSourceMeaningContract,
    binding: CodeSemanticSourceMeaningBinding,
    event: SemanticCapabilityEvent,
    resolution: CodeGrammarAnchorResolution | None,
) -> tuple[SemanticCapabilityActionBinding, ...]:
    if resolution is None:
        return ()
    raw_action_bindings = binding.metadata.get("action_bindings")
    if not isinstance(raw_action_bindings, (list, tuple)):
        return ()
    action_bindings: list[SemanticCapabilityActionBinding] = []
    for raw_action_binding in raw_action_bindings:
        if not isinstance(raw_action_binding, Mapping):
            continue
        if not _event_verb_allowed(
            raw_action_binding=raw_action_binding,
            event=event,
        ):
            continue
        action_type = _optional_text(raw_action_binding.get("action_type"))
        if action_type is not None and action_type != "function_call":
            continue
        function_call_binding = _function_call_binding_for_event(
            contract=contract,
            binding=binding,
            event=event,
            resolution=resolution,
            raw_action_binding=raw_action_binding,
        )
        if function_call_binding is None:
            continue
        action_key = _render_metadata_template(
            raw_action_binding.get("action_key_template")
            or raw_action_binding.get("action_key"),
            contract=contract,
            binding=binding,
            event=event,
            resolution=resolution,
        )
        if action_key is None:
            action_key = f"{event.event_key}:function_call"
        action_bindings.append(
            SemanticCapabilityActionBinding(
                action_key=action_key,
                event_key=event.event_key,
                action_type="function_call",
                description=_optional_text(raw_action_binding.get("description")),
                function_call_binding=function_call_binding,
                metadata=_metadata_mapping(raw_action_binding.get("metadata")),
            )
        )
    return tuple(action_bindings)


def _typed_operations_for_event(
    *,
    contract: CodeSemanticSourceMeaningContract,
    binding: CodeSemanticSourceMeaningBinding,
    delta: SemanticCapabilityDelta,
    event: SemanticCapabilityEvent,
    resolution: CodeGrammarAnchorResolution | None,
) -> tuple[SemanticCapabilityTypedOperation, ...]:
    if resolution is None:
        return ()
    raw_typed_operation_bindings = binding.metadata.get("typed_operation_bindings")
    if not isinstance(raw_typed_operation_bindings, (list, tuple)):
        return ()
    operations: list[SemanticCapabilityTypedOperation] = []
    for raw_binding in raw_typed_operation_bindings:
        if not isinstance(raw_binding, Mapping):
            continue
        if not _event_verb_allowed(
            raw_action_binding=raw_binding,
            event=event,
        ):
            continue
        semantic_operation_type = _render_metadata_template(
            raw_binding.get("semantic_operation_type_template")
            or raw_binding.get("semantic_operation_type"),
            contract=contract,
            binding=binding,
            event=event,
            resolution=resolution,
        )
        if semantic_operation_type is None:
            continue
        operation_key = _render_metadata_template(
            raw_binding.get("operation_key_template")
            or raw_binding.get("operation_key"),
            contract=contract,
            binding=binding,
            event=event,
            resolution=resolution,
        )
        if operation_key is None:
            operation_key = f"{event.event_key}:typed_operation"
        operation_metadata = _metadata_mapping(raw_binding.get("metadata"))
        operation_metadata.setdefault("binding_key", binding.binding_key)
        operation_metadata.setdefault("event_type", event.event_type)
        operation_metadata.setdefault(
            "contract_version",
            CODE_SEMANTIC_SOURCE_MEANING_BINDING_CONTRACT_VERSION,
        )
        operations.append(
            SemanticCapabilityTypedOperation(
                operation_key=operation_key,
                operation_family=_typed_operation_family(
                    value=raw_binding.get("operation_family"),
                    event=event,
                ),
                semantic_operation_type=semantic_operation_type,
                semantic_key=event.semantic_key,
                semantic_subject_type=(
                    _optional_text(raw_binding.get("semantic_subject_type"))
                    or event.subject_type
                ),
                field_path=(
                    _optional_text(raw_binding.get("field_path"))
                    or binding.semantic_field
                ),
                event_key=event.event_key,
                source=_CONTRACT_SOURCE,
                source_refs=event.source_refs,
                before_payload=delta.before_payload,
                after_payload=delta.after_payload,
                requires_baseline_object_identity=(
                    raw_binding.get("requires_baseline_object_identity") is True
                ),
                metadata=operation_metadata,
            )
        )
    return tuple(operations)


def _typed_operation_family(
    *,
    value: object,
    event: SemanticCapabilityEvent,
) -> SemanticCapabilityEventVerb:
    text = _optional_text(value) or event.verb
    if text in {"noop", "create", "update", "upsert", "delete", "rename"}:
        return cast(SemanticCapabilityEventVerb, text)
    return event.verb


def _function_call_binding_for_event(
    *,
    contract: CodeSemanticSourceMeaningContract,
    binding: CodeSemanticSourceMeaningBinding,
    event: SemanticCapabilityEvent,
    resolution: CodeGrammarAnchorResolution,
    raw_action_binding: Mapping[str, object],
) -> SemanticCapabilityFunctionCallBinding | None:
    raw_function_call = raw_action_binding.get("function_call_binding")
    if not isinstance(raw_function_call, Mapping):
        return None
    function_ref = _optional_text(raw_function_call.get("function_ref"))
    if function_ref is None:
        return None
    binding_key = _render_metadata_template(
        raw_function_call.get("binding_key_template")
        or raw_function_call.get("binding_key"),
        contract=contract,
        binding=binding,
        event=event,
        resolution=resolution,
    )
    if binding_key is None:
        binding_key = f"{binding.binding_key}:function_call"
    return SemanticCapabilityFunctionCallBinding(
        binding_key=binding_key,
        event_key=event.event_key,
        function_ref=function_ref,
        receiver_semantic_key_template=_optional_text(
            raw_function_call.get("receiver_semantic_key_template")
        ),
        argument_bindings=_metadata_string_mapping(
            raw_function_call.get("argument_bindings")
        ),
        argument_ref_bindings=_metadata_string_mapping(
            raw_function_call.get("argument_ref_bindings")
        ),
        constant_arguments=_metadata_mapping(
            raw_function_call.get("constant_arguments")
        ),
        result_semantic_key_template=_optional_text(
            raw_function_call.get("result_semantic_key_template")
        ),
        metadata=_metadata_mapping(raw_function_call.get("metadata")),
    )


def _event_verb_allowed(
    *,
    raw_action_binding: Mapping[str, object],
    event: SemanticCapabilityEvent,
) -> bool:
    raw_verbs = raw_action_binding.get("event_verbs")
    if raw_verbs is None:
        return True
    if isinstance(raw_verbs, str):
        allowed = {raw_verbs}
    elif isinstance(raw_verbs, (list, tuple, set, frozenset)):
        allowed = {str(item).strip() for item in raw_verbs if str(item).strip()}
    else:
        return False
    return event.verb in allowed


def _render_metadata_template(
    value: object,
    *,
    contract: CodeSemanticSourceMeaningContract,
    binding: CodeSemanticSourceMeaningBinding,
    event: SemanticCapabilityEvent,
    resolution: CodeGrammarAnchorResolution,
) -> str | None:
    text = _optional_text(value)
    if text is None:
        return None
    if text == "event_key":
        return event.event_key
    if text == "semantic_key":
        return event.semantic_key
    try:
        return _render_template(
            text,
            contract=contract,
            binding=binding,
            resolution=resolution,
        )
    except KeyError:
        return text


def _metadata_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _metadata_string_mapping(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): str(item)
        for key, item in value.items()
        if str(key).strip() and str(item).strip()
    }


def _value_payload(
    *,
    binding: CodeSemanticSourceMeaningBinding,
    resolution: CodeGrammarAnchorResolution | None,
) -> Mapping[str, object] | None:
    if resolution is None:
        return None
    payload: dict[str, object] = {
        binding.semantic_field: resolution.text,
        "text_hash": resolution.text_hash,
        "source_hash": resolution.source_hash,
    }
    if binding.metadata.get("include_template_values_in_payload") is True:
        payload.update(dict(resolution.template_values))
    if binding.value_domain == "aware_function_membership_constructor":
        function_verb = resolution.text.strip()
        is_constructor = function_verb == "construct"
        payload.update(
            {
                "verb": function_verb,
                "function_verb": function_verb,
                "is_constructor": is_constructor,
                "function_membership_signature": {
                    "is_constructor": is_constructor,
                },
            }
        )
    if binding.value_domain == "aware_attribute_membership_identity_key":
        is_identity_key = (
            resolution.template_values.get("is_identity_key") == "true"
        )
        payload.update(
            {
                "is_identity_key": is_identity_key,
                "attribute_membership_owner_kind": "class",
                "attribute_membership_signature": {
                    "owner_kind": "class",
                    "is_identity_key": is_identity_key,
                },
            }
        )
    return payload


def _source_refs(
    *,
    before: CodeGrammarAnchorResolution | None,
    after: CodeGrammarAnchorResolution | None,
) -> tuple[str, ...]:
    refs: list[str] = []
    for resolution in (before, after):
        if resolution is None:
            continue
        if resolution.relative_path is not None:
            refs.append(resolution.relative_path)
        else:
            refs.append(resolution.source_key)
    return tuple(dict.fromkeys(refs))


def _render_template(
    template: str,
    *,
    contract: CodeSemanticSourceMeaningContract | None,
    binding: CodeSemanticSourceMeaningBinding,
    resolution: CodeGrammarAnchorResolution,
) -> str:
    selector = resolution.graph_selector
    template_values = dict(resolution.template_values)
    values = {
        "provider_key": "" if contract is None else contract.provider_key,
        "semantic_owner": "" if contract is None else contract.semantic_owner,
        "binding_key": binding.binding_key,
        "semantic_subject_type": binding.semantic_subject_type,
        "semantic_field": binding.semantic_field,
        "subject_kind": selector.subject_kind or "",
        "subject_type": selector.subject_type or "",
        "semantic_key": selector.semantic_key or "",
        "object_key": selector.object_key or "",
        "field_name": selector.field_name
        or selector.attribute_name
        or template_values.get("field_name")
        or "",
        "field_path": selector.field_path
        or selector.attribute_path
        or template_values.get("field_path")
        or "",
        "class_name": selector.class_name
        or _last_segment(selector.class_fqn)
        or template_values.get("class_name")
        or "",
        "class_fqn": selector.class_fqn or "",
        "attribute_name": selector.attribute_name
        or _attribute_name_from_path(selector.attribute_path)
        or template_values.get("attribute_name")
        or "",
        "attribute_path": selector.attribute_path
        or template_values.get("attribute_path")
        or "",
        "function_name": template_values.get("function_name", ""),
        "function_path": template_values.get("function_path", ""),
        "function_verb": template_values.get("function_verb", ""),
        "function_description": template_values.get("function_description", ""),
        "enum_name": template_values.get("enum_name", ""),
        "enum_path": template_values.get("enum_path", ""),
        "enum_fqn": template_values.get("enum_fqn", ""),
        "enum_description": template_values.get("enum_description", ""),
        "enum_option_value": template_values.get("enum_option_value", ""),
        "enum_option_literal": template_values.get("enum_option_literal", ""),
        "enum_option_path": template_values.get("enum_option_path", ""),
        "position": template_values.get("position", ""),
        "relationship_key": template_values.get("relationship_key", ""),
        "relationship_path": template_values.get("relationship_path", ""),
        "relationship_type": template_values.get("relationship_type", ""),
        "target_class_name": template_values.get("target_class_name", ""),
        "target_class_fqn": template_values.get("target_class_fqn", ""),
        "anchor_text": resolution.text,
        "source_key": resolution.source_key,
    }
    return template.format(**values)


def _last_segment(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return value.rsplit(".", maxsplit=1)[-1]


def _attribute_name_from_path(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    parts = [part for part in value.split(".") if part]
    if len(parts) >= 2:
        return parts[-2]
    return parts[-1] if parts else None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _hash_matches(*, expected: str, actual: str) -> bool:
    expected_text = expected.strip()
    actual_text = actual.strip()
    return expected_text == actual_text or expected_text == actual_text.removeprefix(
        "sha256:"
    )


__all__ = [
    "CODE_SEMANTIC_SOURCE_DELTA_MEANING_CONTRACT_VERSION",
    "CODE_SEMANTIC_SOURCE_MEANING_BINDING_CONTRACT_VERSION",
    "CodeSemanticSourceDeltaMeaningResolution",
    "CodeSemanticSourceDeltaMeaningResolutionMode",
    "CodeSemanticSourceIndexRef",
    "CodeSemanticSourceMeaningBinding",
    "CodeSemanticSourceMeaningContract",
    "CodeSemanticSourceMeaningResolution",
    "clear_code_semantic_source_index_cache_for_tests",
    "resolve_code_semantic_source_delta_meaning",
    "resolve_code_semantic_source_meaning",
]
