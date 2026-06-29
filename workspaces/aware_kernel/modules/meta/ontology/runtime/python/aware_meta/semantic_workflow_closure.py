from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from aware_code.module_semantic_contract import (
    ModuleSemanticContract,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticWorkflowDescriptor,
)


META_SEMANTIC_WORKFLOW_CLOSURE_SOURCE = "aware_meta.semantic_workflow_closure"
META_SEMANTIC_WORKFLOW_CLOSURE_READY = "ready"
META_SEMANTIC_WORKFLOW_CLOSURE_BLOCKED = "blocked"
META_FUNCTION_IMPL_COVERAGE_PROOF_REF = "meta.function_impl.coverage"

_NATIVE_FUNCTION_PROOF_REFS = frozenset({"meta.function_call.proof"})
_FUNCTION_IMPL_COVERAGE_PROOF_REFS = frozenset({META_FUNCTION_IMPL_COVERAGE_PROOF_REF})


@dataclass(frozen=True, slots=True)
class MetaSemanticWorkflowClosureCatalog:
    """Meta-owned evidence catalog for semantic workflow closure checks."""

    ontology_feature_refs: tuple[str, ...] = ()
    graph_binding_refs: tuple[str, ...] = ()
    typed_operation_feature_refs: tuple[str, ...] = ()
    native_function_feature_refs: tuple[str, ...] = ()
    runtime_handler_delegation_feature_refs: tuple[str, ...] = ()
    projection_refs: tuple[str, ...] = ()
    proof_refs: tuple[str, ...] = ()
    diagnostic_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for attr in (
            "ontology_feature_refs",
            "graph_binding_refs",
            "typed_operation_feature_refs",
            "native_function_feature_refs",
            "runtime_handler_delegation_feature_refs",
            "projection_refs",
            "proof_refs",
            "diagnostic_refs",
        ):
            object.__setattr__(self, attr, _normalized_unique(getattr(self, attr)))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @classmethod
    def from_object_config_graphs(
        cls,
        *,
        object_config_graphs: Sequence[object] = (),
        ontology_feature_refs: Sequence[str] = (),
        graph_binding_refs: Sequence[str] = (),
        typed_operation_feature_refs: Sequence[str] = (),
        native_function_feature_refs: Sequence[str] = (),
        runtime_handler_delegation_feature_refs: Sequence[str] = (),
        projection_refs: Sequence[str] = (),
        proof_refs: Sequence[str] = (),
        diagnostic_refs: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> "MetaSemanticWorkflowClosureCatalog":
        """Build feature refs from OCG class nodes plus explicit evidence."""

        return cls(
            ontology_feature_refs=(
                *ontology_feature_refs,
                *_ontology_feature_refs_from_object_config_graphs(object_config_graphs),
            ),
            graph_binding_refs=tuple(graph_binding_refs),
            typed_operation_feature_refs=tuple(typed_operation_feature_refs),
            native_function_feature_refs=tuple(native_function_feature_refs),
            runtime_handler_delegation_feature_refs=(
                tuple(runtime_handler_delegation_feature_refs)
            ),
            projection_refs=tuple(projection_refs),
            proof_refs=tuple(proof_refs),
            diagnostic_refs=tuple(diagnostic_refs),
            metadata=metadata or {},
        )


@dataclass(frozen=True, slots=True)
class MetaSemanticWorkflowClosureDiagnostic:
    severity: str
    code: str
    message: str
    provider_key: str | None = None
    workflow_key: str | None = None
    ref_kind: str | None = None
    ref: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata or {}))


@dataclass(frozen=True, slots=True)
class MetaSemanticWorkflowClosureEntry:
    provider_key: str
    workflow_key: str
    semantic_owner: str
    status: str
    ready: bool
    stage_keys: tuple[str, ...]
    ontology_feature_refs: tuple[str, ...]
    graph_binding_refs: tuple[str, ...]
    typed_operation_feature_refs: tuple[str, ...]
    native_function_feature_refs: tuple[str, ...]
    runtime_handler_delegation_feature_refs: tuple[str, ...]
    function_impl_coverage_feature_refs: tuple[str, ...]
    required_projection_refs: tuple[str, ...]
    expected_proof_refs: tuple[str, ...]
    diagnostic_refs: tuple[str, ...]
    blocker_refs: tuple[str, ...]
    diagnostics: tuple[MetaSemanticWorkflowClosureDiagnostic, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata or {}))


@dataclass(frozen=True, slots=True)
class MetaSemanticWorkflowClosureResult:
    status: str
    ready: bool
    provider_count: int
    workflow_count: int
    ready_workflow_count: int
    blocked_workflow_count: int
    entries: tuple[MetaSemanticWorkflowClosureEntry, ...]
    diagnostics: tuple[MetaSemanticWorkflowClosureDiagnostic, ...] = ()
    missing_provider_keys: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata or {}))


def resolve_meta_semantic_workflow_closure(
    *,
    semantic_contracts: Sequence[ModuleSemanticContract],
    catalog: MetaSemanticWorkflowClosureCatalog,
    provider_keys: Sequence[str] = (),
    workflow_keys: Sequence[str] = (),
    severity: str = "error",
) -> MetaSemanticWorkflowClosureResult:
    """Validate workflow refs against Meta closure evidence."""

    requested_provider_keys = _normalized_unique(provider_keys)
    requested_workflow_keys = frozenset(_normalized_unique(workflow_keys))
    contracts_by_provider = {
        provider_key: contract
        for contract in semantic_contracts
        if (provider_key := _normalize_text(contract.provider_key)) is not None
    }
    missing_provider_keys = tuple(
        provider_key
        for provider_key in requested_provider_keys
        if provider_key not in contracts_by_provider
    )
    selected_contracts = tuple(
        contracts_by_provider[provider_key]
        for provider_key in requested_provider_keys
        if provider_key in contracts_by_provider
    )
    if not requested_provider_keys:
        selected_contracts = tuple(
            sorted(contracts_by_provider.values(), key=lambda item: item.provider_key)
        )

    diagnostics: list[MetaSemanticWorkflowClosureDiagnostic] = [
        _diagnostic(
            severity=severity,
            code="aware_meta.workflow_closure.provider_contract_missing",
            message=(
                "Meta semantic workflow closure could not resolve semantic "
                f"contract provider {provider_key!r}."
            ),
            provider_key=provider_key,
            ref_kind="provider",
            ref=provider_key,
        )
        for provider_key in missing_provider_keys
    ]

    entries: list[MetaSemanticWorkflowClosureEntry] = []
    for contract in selected_contracts:
        projection_names_by_owner = _required_projection_names_by_owner(contract)
        for workflow in sorted(
            contract.semantic_workflows,
            key=lambda item: (item.priority, item.semantic_owner, item.workflow_key),
        ):
            if (
                requested_workflow_keys
                and _normalize_text(workflow.workflow_key)
                not in requested_workflow_keys
            ):
                continue
            entry = _workflow_closure_entry(
                contract=contract,
                workflow=workflow,
                catalog=catalog,
                required_projection_names=projection_names_by_owner.get(
                    workflow.semantic_owner,
                    projection_names_by_owner.get("", ()),
                ),
                severity=severity,
            )
            entries.append(entry)
            diagnostics.extend(entry.diagnostics)

    if not entries and not missing_provider_keys:
        diagnostics.append(
            _diagnostic(
                severity=severity,
                code="aware_meta.workflow_closure.semantic_workflow_unavailable",
                message="No semantic workflows matched the Meta closure request.",
                ref_kind="workflow",
                metadata={
                    "provider_keys": requested_provider_keys,
                    "workflow_keys": tuple(requested_workflow_keys),
                },
            )
        )

    ready = bool(entries) and not diagnostics and not missing_provider_keys
    status = (
        META_SEMANTIC_WORKFLOW_CLOSURE_READY
        if ready
        else META_SEMANTIC_WORKFLOW_CLOSURE_BLOCKED
    )
    return MetaSemanticWorkflowClosureResult(
        status=status,
        ready=ready,
        provider_count=len(selected_contracts),
        workflow_count=len(entries),
        ready_workflow_count=sum(1 for entry in entries if entry.ready),
        blocked_workflow_count=sum(1 for entry in entries if not entry.ready),
        entries=tuple(entries),
        diagnostics=tuple(diagnostics),
        missing_provider_keys=missing_provider_keys,
        metadata={
            "source": META_SEMANTIC_WORKFLOW_CLOSURE_SOURCE,
            "catalog": dict(catalog.metadata),
        },
    )


def _workflow_closure_entry(
    *,
    contract: ModuleSemanticContract,
    workflow: ModuleSemanticWorkflowDescriptor,
    catalog: MetaSemanticWorkflowClosureCatalog,
    required_projection_names: Sequence[str],
    severity: str,
) -> MetaSemanticWorkflowClosureEntry:
    provider_key = _normalize_text(contract.provider_key) or contract.provider_key
    workflow_key = workflow.workflow_key
    diagnostics: list[MetaSemanticWorkflowClosureDiagnostic] = []

    ontology_feature_refs = _normalized_unique(workflow.ontology_feature_refs)
    graph_binding_refs = _normalized_unique(workflow.graph_binding_refs)
    expected_proof_refs = _normalized_unique(workflow.expected_proof_refs)
    diagnostic_refs = _normalized_unique(workflow.diagnostic_refs)
    required_projection_refs = _normalized_unique(required_projection_names)
    native_function_required = bool(
        _NATIVE_FUNCTION_PROOF_REFS.intersection(expected_proof_refs)
    )
    function_impl_coverage_required = bool(
        _FUNCTION_IMPL_COVERAGE_PROOF_REFS.intersection(expected_proof_refs)
    )

    for ref in ontology_feature_refs:
        if ref not in catalog.ontology_feature_refs:
            diagnostics.append(
                _workflow_ref_diagnostic(
                    severity=severity,
                    code="aware_meta.workflow_closure.ontology_feature_ref_missing",
                    provider_key=provider_key,
                    workflow_key=workflow_key,
                    ref_kind="ontology_feature",
                    ref=ref,
                    message=(
                        "Semantic workflow ontology feature ref is not present "
                        f"in the Meta closure catalog: {ref}"
                    ),
                )
            )
        if ref not in catalog.typed_operation_feature_refs:
            diagnostics.append(
                _workflow_ref_diagnostic(
                    severity=severity,
                    code="aware_meta.workflow_closure.typed_operation_missing",
                    provider_key=provider_key,
                    workflow_key=workflow_key,
                    ref_kind="typed_operation_feature",
                    ref=ref,
                    message=(
                        "Semantic workflow ontology feature has no typed "
                        f"operation closure evidence: {ref}"
                    ),
                )
            )
        if native_function_required and ref not in catalog.native_function_feature_refs:
            diagnostics.append(
                _workflow_ref_diagnostic(
                    severity=severity,
                    code="aware_meta.workflow_closure.native_function_missing",
                    provider_key=provider_key,
                    workflow_key=workflow_key,
                    ref_kind="native_function_feature",
                    ref=ref,
                    message=(
                        "Semantic workflow expects Meta FunctionCall proof but "
                        f"the feature has no native function evidence: {ref}"
                    ),
                )
            )
        if (
            function_impl_coverage_required
            and ref not in catalog.native_function_feature_refs
            and ref not in catalog.runtime_handler_delegation_feature_refs
        ):
            diagnostics.append(
                _workflow_ref_diagnostic(
                    severity=severity,
                    code=(
                        "aware_meta.workflow_closure." "function_impl_coverage_missing"
                    ),
                    provider_key=provider_key,
                    workflow_key=workflow_key,
                    ref_kind="function_impl_coverage_feature",
                    ref=ref,
                    message=(
                        "Semantic workflow expects FunctionImpl coverage but "
                        "the feature has neither native .aware FunctionImpl "
                        f"evidence nor strict runtime-handler delegation: {ref}"
                    ),
                )
            )

    for ref in graph_binding_refs:
        if ref not in catalog.graph_binding_refs:
            diagnostics.append(
                _workflow_ref_diagnostic(
                    severity=severity,
                    code="aware_meta.workflow_closure.graph_binding_ref_missing",
                    provider_key=provider_key,
                    workflow_key=workflow_key,
                    ref_kind="graph_binding",
                    ref=ref,
                    message=(
                        "Semantic workflow graph-binding ref is not present in "
                        f"the closure catalog: {ref}"
                    ),
                )
            )

    for ref in diagnostic_refs:
        if ref not in catalog.diagnostic_refs:
            diagnostics.append(
                _workflow_ref_diagnostic(
                    severity=severity,
                    code="aware_meta.workflow_closure.diagnostic_ref_missing",
                    provider_key=provider_key,
                    workflow_key=workflow_key,
                    ref_kind="diagnostic",
                    ref=ref,
                    message=(
                        "Semantic workflow diagnostic ref is not present in "
                        f"the closure catalog: {ref}"
                    ),
                )
            )

    for ref in expected_proof_refs:
        if ref not in catalog.proof_refs:
            diagnostics.append(
                _workflow_ref_diagnostic(
                    severity=severity,
                    code="aware_meta.workflow_closure.proof_ref_missing",
                    provider_key=provider_key,
                    workflow_key=workflow_key,
                    ref_kind="proof",
                    ref=ref,
                    message=(
                        "Semantic workflow expected proof ref is not present in "
                        f"the closure catalog: {ref}"
                    ),
                )
            )

    for ref in required_projection_refs:
        if not _projection_ref_available(
            provider_key=provider_key,
            projection_name=ref,
            projection_refs=catalog.projection_refs,
        ):
            diagnostics.append(
                _workflow_ref_diagnostic(
                    severity=severity,
                    code="aware_meta.workflow_closure.projection_ref_missing",
                    provider_key=provider_key,
                    workflow_key=workflow_key,
                    ref_kind="projection",
                    ref=ref,
                    message=(
                        "Semantic workflow materialization requires projection "
                        f"closure evidence that is not available: {ref}"
                    ),
                )
            )

    ready = not diagnostics
    return MetaSemanticWorkflowClosureEntry(
        provider_key=provider_key,
        workflow_key=workflow_key,
        semantic_owner=workflow.semantic_owner,
        status=(
            META_SEMANTIC_WORKFLOW_CLOSURE_READY
            if ready
            else META_SEMANTIC_WORKFLOW_CLOSURE_BLOCKED
        ),
        ready=ready,
        stage_keys=_normalized_unique(workflow.stage_keys),
        ontology_feature_refs=ontology_feature_refs,
        graph_binding_refs=graph_binding_refs,
        typed_operation_feature_refs=tuple(
            ref
            for ref in ontology_feature_refs
            if ref in catalog.typed_operation_feature_refs
        ),
        native_function_feature_refs=tuple(
            ref
            for ref in ontology_feature_refs
            if ref in catalog.native_function_feature_refs
        ),
        runtime_handler_delegation_feature_refs=tuple(
            ref
            for ref in ontology_feature_refs
            if ref in catalog.runtime_handler_delegation_feature_refs
        ),
        function_impl_coverage_feature_refs=tuple(
            ref
            for ref in ontology_feature_refs
            if ref in catalog.native_function_feature_refs
            or ref in catalog.runtime_handler_delegation_feature_refs
        ),
        required_projection_refs=required_projection_refs,
        expected_proof_refs=expected_proof_refs,
        diagnostic_refs=diagnostic_refs,
        blocker_refs=tuple(
            dict.fromkeys(
                f"{diagnostic.ref_kind}:{diagnostic.ref}"
                for diagnostic in diagnostics
                if diagnostic.ref_kind and diagnostic.ref
            )
        ),
        diagnostics=tuple(diagnostics),
        metadata={"source": META_SEMANTIC_WORKFLOW_CLOSURE_SOURCE},
    )


def _required_projection_names_by_owner(
    contract: ModuleSemanticContract,
) -> dict[str, tuple[str, ...]]:
    by_owner: dict[str, list[str]] = {}
    for descriptor in contract.materialization_runtime:
        if not isinstance(descriptor, ModuleSemanticMaterializationRuntimeDescriptor):
            continue
        owner_key = _normalize_text(descriptor.semantic_owner) or ""
        by_owner.setdefault(owner_key, []).extend(descriptor.required_projection_names)
    if not by_owner:
        return {"": ()}
    return {
        owner_key: _normalized_unique(values) for owner_key, values in by_owner.items()
    }


def _ontology_feature_refs_from_object_config_graphs(
    object_config_graphs: Sequence[object],
) -> tuple[str, ...]:
    refs: list[str] = []
    for graph in object_config_graphs:
        fqn_prefix = _normalize_text(
            getattr(graph, "fqn_prefix", None)
        ) or _normalize_text(getattr(graph, "name", None))
        for node in getattr(graph, "object_config_graph_nodes", ()) or ():
            class_config = getattr(node, "class_config", None)
            if class_config is None:
                continue
            class_name = _normalize_text(getattr(class_config, "name", None))
            class_fqn = _normalize_text(getattr(class_config, "class_fqn", None))
            if class_fqn is not None:
                refs.append(class_fqn)
                class_name = class_name or class_fqn.rsplit(".", 1)[-1]
            if fqn_prefix is not None and class_name is not None:
                refs.append(f"{fqn_prefix}.{class_name}")
    return _normalized_unique(refs)


def _projection_ref_available(
    *,
    provider_key: str,
    projection_name: str,
    projection_refs: Sequence[str],
) -> bool:
    candidates = {
        projection_name,
        f"{provider_key}.{projection_name}",
        f"{provider_key}.projection.{projection_name}",
    }
    return any(candidate in projection_refs for candidate in candidates)


def _workflow_ref_diagnostic(
    *,
    severity: str,
    code: str,
    provider_key: str,
    workflow_key: str,
    ref_kind: str,
    ref: str,
    message: str,
) -> MetaSemanticWorkflowClosureDiagnostic:
    return _diagnostic(
        severity=severity,
        code=code,
        message=message,
        provider_key=provider_key,
        workflow_key=workflow_key,
        ref_kind=ref_kind,
        ref=ref,
    )


def _diagnostic(
    *,
    severity: str,
    code: str,
    message: str,
    provider_key: str | None = None,
    workflow_key: str | None = None,
    ref_kind: str | None = None,
    ref: str | None = None,
    metadata: Mapping[str, object] | None = None,
) -> MetaSemanticWorkflowClosureDiagnostic:
    return MetaSemanticWorkflowClosureDiagnostic(
        severity=severity,
        code=code,
        message=message,
        provider_key=provider_key,
        workflow_key=workflow_key,
        ref_kind=ref_kind,
        ref=ref,
        metadata=metadata or {},
    )


def _normalized_unique(values: Sequence[object]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            value
            for value in (_normalize_text(value) for value in values)
            if value is not None
        )
    )


def _normalize_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "META_FUNCTION_IMPL_COVERAGE_PROOF_REF",
    "META_SEMANTIC_WORKFLOW_CLOSURE_BLOCKED",
    "META_SEMANTIC_WORKFLOW_CLOSURE_READY",
    "META_SEMANTIC_WORKFLOW_CLOSURE_SOURCE",
    "MetaSemanticWorkflowClosureCatalog",
    "MetaSemanticWorkflowClosureDiagnostic",
    "MetaSemanticWorkflowClosureEntry",
    "MetaSemanticWorkflowClosureResult",
    "resolve_meta_semantic_workflow_closure",
]
