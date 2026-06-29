from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from aware_meta.materialization.deltas.code_dto import (
    CodeGeneratedMaterializationDeltaMode,
    CodeGeneratedMaterializationDeltaRequest,
    CodeGeneratedMaterializationDeltaResult,
    CodeGrammarAnchorBinding,
    CodeGrammarAnchorRenderReplacement,
    CodeGrammarAnchorRenderSource,
    CodeSectionDeltaEntry,
)
from aware_meta.materialization.deltas.coercion import optional_text
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)

if TYPE_CHECKING:
    from aware_meta.materialization.deltas.ontology_execution.contracts import (
        OntologyExecutionPlanningContext,
        OntologyOperationHandlerResult,
        OntologyTypedOperation,
    )
else:
    OntologyExecutionPlanningContext = Any
    OntologyOperationHandlerResult = Any
    OntologyTypedOperation = Any


META_PROVIDER_DELTA_SOURCE_PROJECTION_FEATURE_RESULT_CONTRACT_VERSION = "v0"
META_PROVIDER_DELTA_GENERATED_MATERIALIZATION_FEATURE_RESULT_CONTRACT_VERSION = (
    "v0"
)
META_PROVIDER_DELTA_GENERATED_MATERIALIZATION_EXPECTATION_CONTRACT_VERSION = (
    "aware.meta.provider-delta-generated-materialization-expectation.v0"
)

GENERATED_MATERIALIZATION_EXPECTATION_REQUIRED = "required"
GENERATED_MATERIALIZATION_EXPECTATION_NOT_REQUIRED = "not_required"
GENERATED_MATERIALIZATION_EXPECTATION_UNSUPPORTED = "unsupported"
GENERATED_MATERIALIZATION_EXPECTATION_DEFERRED = "deferred"

GENERATED_MATERIALIZATION_FULFILLMENT_FULFILLED = "fulfilled"
GENERATED_MATERIALIZATION_FULFILLMENT_MISSING = "missing"
GENERATED_MATERIALIZATION_FULFILLMENT_NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaSourceProjectionContext:
    package_name: str | None = None
    package_root: str | None = None
    sources_root: str | None = None
    target_language: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "package_name", optional_text(self.package_name))
        object.__setattr__(self, "package_root", optional_text(self.package_root))
        object.__setattr__(self, "sources_root", optional_text(self.sources_root))
        object.__setattr__(
            self,
            "target_language",
            optional_text(self.target_language),
        )


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaGeneratedMaterializationContext:
    package_name: str | None = None
    package_root: str | None = None
    sources_root: str | None = None
    target_language: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "package_name", optional_text(self.package_name))
        object.__setattr__(self, "package_root", optional_text(self.package_root))
        object.__setattr__(self, "sources_root", optional_text(self.sources_root))
        object.__setattr__(
            self,
            "target_language",
            optional_text(self.target_language),
        )


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaSourceProjectionFeatureResult:
    feature_key: str
    operation_key: str
    semantic_key: str
    ontology_subject_kind: str
    operation_family: str
    provider_operation_type: str
    status: str
    reason: str
    entries: tuple[CodeSectionDeltaEntry, ...] = ()
    grammar_anchor_bindings: tuple[CodeGrammarAnchorBinding, ...] = ()
    grammar_anchor_sources: tuple[CodeGrammarAnchorRenderSource, ...] = ()
    grammar_anchor_replacements: tuple[CodeGrammarAnchorRenderReplacement, ...] = ()
    event_refs: tuple[str, ...] = ()
    required_evidence_fields: tuple[str, ...] = ()
    missing_evidence_fields: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()

    @classmethod
    def from_projected(
        cls,
        *,
        feature_key: str,
        operation: MetaProviderDeltaTypedOperation,
        entries: tuple[CodeSectionDeltaEntry, ...],
        reason: str,
        grammar_anchor_bindings: tuple[CodeGrammarAnchorBinding, ...] = (),
        grammar_anchor_sources: tuple[CodeGrammarAnchorRenderSource, ...] = (),
        grammar_anchor_replacements: tuple[
            CodeGrammarAnchorRenderReplacement, ...
        ] = (),
        required_evidence_fields: tuple[str, ...] = (),
        diagnostics: tuple[str, ...] = (),
    ) -> "MetaProviderDeltaSourceProjectionFeatureResult":
        event_refs = _projected_event_refs(
            entries=entries,
            grammar_anchor_replacements=grammar_anchor_replacements,
        )
        return cls(
            feature_key=feature_key,
            operation_key=operation.operation_key,
            semantic_key=operation.semantic_key,
            ontology_subject_kind=operation.ontology_subject_kind,
            operation_family=operation.operation_family,
            provider_operation_type=operation.provider_operation_type,
            status="source_projection_projected",
            reason=reason,
            entries=entries,
            grammar_anchor_bindings=grammar_anchor_bindings,
            grammar_anchor_sources=grammar_anchor_sources,
            grammar_anchor_replacements=grammar_anchor_replacements,
            event_refs=event_refs,
            required_evidence_fields=required_evidence_fields,
            diagnostics=diagnostics,
        )

    @classmethod
    def skipped(
        cls,
        *,
        feature_key: str,
        operation: MetaProviderDeltaTypedOperation,
        reason: str,
        event_refs: tuple[str, ...],
        required_evidence_fields: tuple[str, ...] = (),
        missing_evidence_fields: tuple[str, ...] = (),
        diagnostics: tuple[str, ...] = (),
    ) -> "MetaProviderDeltaSourceProjectionFeatureResult":
        return cls(
            feature_key=feature_key,
            operation_key=operation.operation_key,
            semantic_key=operation.semantic_key,
            ontology_subject_kind=operation.ontology_subject_kind,
            operation_family=operation.operation_family,
            provider_operation_type=operation.provider_operation_type,
            status="source_projection_skipped",
            reason=reason,
            event_refs=event_refs,
            required_evidence_fields=required_evidence_fields,
            missing_evidence_fields=missing_evidence_fields,
            diagnostics=diagnostics,
        )

    @property
    def blocked(self) -> bool:
        return self.status == "source_projection_blocked"

    @classmethod
    def from_blocked(
        cls,
        *,
        feature_key: str,
        operation: MetaProviderDeltaTypedOperation,
        reason: str,
        event_refs: tuple[str, ...],
        required_evidence_fields: tuple[str, ...] = (),
        missing_evidence_fields: tuple[str, ...] = (),
        diagnostics: tuple[str, ...] = (),
    ) -> "MetaProviderDeltaSourceProjectionFeatureResult":
        return cls(
            feature_key=feature_key,
            operation_key=operation.operation_key,
            semantic_key=operation.semantic_key,
            ontology_subject_kind=operation.ontology_subject_kind,
            operation_family=operation.operation_family,
            provider_operation_type=operation.provider_operation_type,
            status="source_projection_blocked",
            reason=reason,
            event_refs=event_refs,
            required_evidence_fields=required_evidence_fields,
            missing_evidence_fields=missing_evidence_fields,
            diagnostics=diagnostics,
        )

    @property
    def projected_entry_count(self) -> int:
        return len(self.entries)

    @property
    def grammar_anchor_binding_count(self) -> int:
        return len(self.grammar_anchor_bindings)

    @property
    def grammar_anchor_source_count(self) -> int:
        return len(self.grammar_anchor_sources)

    @property
    def grammar_anchor_replacement_count(self) -> int:
        return len(self.grammar_anchor_replacements)

    @property
    def projected(self) -> bool:
        return bool(self.entries or self.grammar_anchor_replacements)

    def evidence_payload(self) -> dict[str, object]:
        return {
            "contract_version": (
                META_PROVIDER_DELTA_SOURCE_PROJECTION_FEATURE_RESULT_CONTRACT_VERSION
            ),
            "feature_key": self.feature_key,
            "operation_key": self.operation_key,
            "semantic_key": self.semantic_key,
            "ontology_subject_kind": self.ontology_subject_kind,
            "operation_family": self.operation_family,
            "provider_operation_type": self.provider_operation_type,
            "status": self.status,
            "reason": self.reason,
            "projected": self.projected,
            "blocked": self.blocked,
            "projected_entry_count": self.projected_entry_count,
            "grammar_anchor_binding_count": self.grammar_anchor_binding_count,
            "grammar_anchor_source_count": self.grammar_anchor_source_count,
            "grammar_anchor_replacement_count": self.grammar_anchor_replacement_count,
            "event_refs": self.event_refs,
            "required_evidence_fields": self.required_evidence_fields,
            "missing_evidence_fields": self.missing_evidence_fields,
            "diagnostics": self.diagnostics,
            "entries": tuple(entry.model_dump(mode="json") for entry in self.entries),
            "grammar_anchor_bindings": tuple(
                item.model_dump(mode="json")
                for item in self.grammar_anchor_bindings
            ),
            "grammar_anchor_sources": tuple(
                item.model_dump(mode="json")
                for item in self.grammar_anchor_sources
            ),
            "grammar_anchor_replacements": tuple(
                item.model_dump(mode="json")
                for item in self.grammar_anchor_replacements
            ),
        }


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaGeneratedMaterializationFeatureResult:
    feature_key: str
    operation_key: str
    semantic_key: str
    ontology_subject_kind: str
    operation_family: str
    provider_operation_type: str
    status: str
    reason: str
    delta_request: CodeGeneratedMaterializationDeltaRequest | None = None
    result: CodeGeneratedMaterializationDeltaResult | None = None
    event_refs: tuple[str, ...] = ()
    required_evidence_fields: tuple[str, ...] = ()
    missing_evidence_fields: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()

    @classmethod
    def from_evidence(
        cls,
        *,
        feature_key: str,
        operation: MetaProviderDeltaTypedOperation,
        delta_request: CodeGeneratedMaterializationDeltaRequest,
        result: CodeGeneratedMaterializationDeltaResult,
        reason: str,
        required_evidence_fields: tuple[str, ...] = (),
        missing_evidence_fields: tuple[str, ...] = (),
    ) -> "MetaProviderDeltaGeneratedMaterializationFeatureResult":
        return cls(
            feature_key=feature_key,
            operation_key=operation.operation_key,
            semantic_key=operation.semantic_key,
            ontology_subject_kind=operation.ontology_subject_kind,
            operation_family=operation.operation_family,
            provider_operation_type=operation.provider_operation_type,
            status=_generated_materialization_status_from_result(result),
            reason=reason,
            delta_request=delta_request,
            result=result,
            event_refs=_generated_materialization_event_refs(
                delta_request=delta_request,
                result=result,
            ),
            required_evidence_fields=required_evidence_fields,
            missing_evidence_fields=missing_evidence_fields,
            diagnostics=tuple(result.diagnostics),
        )

    @classmethod
    def skipped(
        cls,
        *,
        feature_key: str,
        operation: MetaProviderDeltaTypedOperation,
        reason: str,
        event_refs: tuple[str, ...],
        required_evidence_fields: tuple[str, ...] = (),
        missing_evidence_fields: tuple[str, ...] = (),
        diagnostics: tuple[str, ...] = (),
    ) -> "MetaProviderDeltaGeneratedMaterializationFeatureResult":
        return cls(
            feature_key=feature_key,
            operation_key=operation.operation_key,
            semantic_key=operation.semantic_key,
            ontology_subject_kind=operation.ontology_subject_kind,
            operation_family=operation.operation_family,
            provider_operation_type=operation.provider_operation_type,
            status="generated_materialization_skipped",
            reason=reason,
            event_refs=event_refs,
            required_evidence_fields=required_evidence_fields,
            missing_evidence_fields=missing_evidence_fields,
            diagnostics=diagnostics,
        )

    @classmethod
    def from_blocked(
        cls,
        *,
        feature_key: str,
        operation: MetaProviderDeltaTypedOperation,
        reason: str,
        event_refs: tuple[str, ...],
        required_evidence_fields: tuple[str, ...] = (),
        missing_evidence_fields: tuple[str, ...] = (),
        diagnostics: tuple[str, ...] = (),
    ) -> "MetaProviderDeltaGeneratedMaterializationFeatureResult":
        return cls(
            feature_key=feature_key,
            operation_key=operation.operation_key,
            semantic_key=operation.semantic_key,
            ontology_subject_kind=operation.ontology_subject_kind,
            operation_family=operation.operation_family,
            provider_operation_type=operation.provider_operation_type,
            status="generated_materialization_blocked",
            reason=reason,
            event_refs=event_refs,
            required_evidence_fields=required_evidence_fields,
            missing_evidence_fields=missing_evidence_fields,
            diagnostics=diagnostics,
        )

    @property
    def blocked(self) -> bool:
        return self.status == "generated_materialization_blocked"

    @property
    def projected(self) -> bool:
        return bool(self.entry_count or self.renderer_operation_count)

    @property
    def target_count(self) -> int:
        return len(self.delta_request.targets) if self.delta_request is not None else 0

    @property
    def entry_count(self) -> int:
        return len(self.result.entries) if self.result is not None else 0

    @property
    def skipped_target_count(self) -> int:
        return len(self.result.skipped_targets) if self.result is not None else 0

    @property
    def renderer_operation_count(self) -> int:
        if self.result is None:
            return 0
        return sum(len(entry.renderer_operations) for entry in self.result.entries)

    def evidence_payload(self) -> dict[str, object]:
        return {
            "contract_version": (
                META_PROVIDER_DELTA_GENERATED_MATERIALIZATION_FEATURE_RESULT_CONTRACT_VERSION
            ),
            "feature_key": self.feature_key,
            "operation_key": self.operation_key,
            "semantic_key": self.semantic_key,
            "ontology_subject_kind": self.ontology_subject_kind,
            "operation_family": self.operation_family,
            "provider_operation_type": self.provider_operation_type,
            "status": self.status,
            "reason": self.reason,
            "projected": self.projected,
            "blocked": self.blocked,
            "target_count": self.target_count,
            "entry_count": self.entry_count,
            "skipped_target_count": self.skipped_target_count,
            "renderer_operation_count": self.renderer_operation_count,
            "event_refs": self.event_refs,
            "required_evidence_fields": self.required_evidence_fields,
            "missing_evidence_fields": self.missing_evidence_fields,
            "diagnostics": self.diagnostics,
            "delta_request": (
                self.delta_request.model_dump(mode="json")
                if self.delta_request is not None
                else None
            ),
            "result": (
                self.result.model_dump(mode="json")
                if self.result is not None
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaGeneratedMaterializationExpectation:
    feature_key: str
    operation_key: str
    semantic_key: str
    ontology_subject_kind: str
    operation_family: str
    provider_operation_type: str
    expectation: str
    fulfillment: str
    reason: str
    next_capability_ref: str | None = None
    diagnostics: tuple[str, ...] = ()
    event_refs: tuple[str, ...] = ()
    contract_version: str = (
        META_PROVIDER_DELTA_GENERATED_MATERIALIZATION_EXPECTATION_CONTRACT_VERSION
    )

    @classmethod
    def from_feature_result(
        cls,
        feature_result: MetaProviderDeltaGeneratedMaterializationFeatureResult,
    ) -> "MetaProviderDeltaGeneratedMaterializationExpectation":
        if feature_result.projected:
            return cls(
                feature_key=feature_result.feature_key,
                operation_key=feature_result.operation_key,
                semantic_key=feature_result.semantic_key,
                ontology_subject_kind=feature_result.ontology_subject_kind,
                operation_family=feature_result.operation_family,
                provider_operation_type=feature_result.provider_operation_type,
                expectation=GENERATED_MATERIALIZATION_EXPECTATION_REQUIRED,
                fulfillment=GENERATED_MATERIALIZATION_FULFILLMENT_FULFILLED,
                reason=(
                    "meta_generated_materialization_required_output_fulfilled"
                ),
                diagnostics=feature_result.diagnostics,
                event_refs=feature_result.event_refs,
            )
        if feature_result.blocked:
            return cls(
                feature_key=feature_result.feature_key,
                operation_key=feature_result.operation_key,
                semantic_key=feature_result.semantic_key,
                ontology_subject_kind=feature_result.ontology_subject_kind,
                operation_family=feature_result.operation_family,
                provider_operation_type=feature_result.provider_operation_type,
                expectation=GENERATED_MATERIALIZATION_EXPECTATION_REQUIRED,
                fulfillment=GENERATED_MATERIALIZATION_FULFILLMENT_MISSING,
                reason=feature_result.reason,
                next_capability_ref=feature_result.reason,
                diagnostics=feature_result.diagnostics,
                event_refs=feature_result.event_refs,
            )
        if _feature_result_is_not_required(feature_result):
            return cls(
                feature_key=feature_result.feature_key,
                operation_key=feature_result.operation_key,
                semantic_key=feature_result.semantic_key,
                ontology_subject_kind=feature_result.ontology_subject_kind,
                operation_family=feature_result.operation_family,
                provider_operation_type=feature_result.provider_operation_type,
                expectation=GENERATED_MATERIALIZATION_EXPECTATION_NOT_REQUIRED,
                fulfillment=(
                    GENERATED_MATERIALIZATION_FULFILLMENT_NOT_APPLICABLE
                ),
                reason=feature_result.reason,
                diagnostics=feature_result.diagnostics,
                event_refs=feature_result.event_refs,
            )
        return cls(
            feature_key=feature_result.feature_key,
            operation_key=feature_result.operation_key,
            semantic_key=feature_result.semantic_key,
            ontology_subject_kind=feature_result.ontology_subject_kind,
            operation_family=feature_result.operation_family,
            provider_operation_type=feature_result.provider_operation_type,
            expectation=GENERATED_MATERIALIZATION_EXPECTATION_UNSUPPORTED,
            fulfillment=GENERATED_MATERIALIZATION_FULFILLMENT_NOT_APPLICABLE,
            reason=feature_result.reason,
            next_capability_ref=feature_result.reason,
            diagnostics=feature_result.diagnostics,
            event_refs=feature_result.event_refs,
        )

    @property
    def required(self) -> bool:
        return self.expectation == GENERATED_MATERIALIZATION_EXPECTATION_REQUIRED

    @property
    def fulfilled(self) -> bool:
        return (
            self.fulfillment
            == GENERATED_MATERIALIZATION_FULFILLMENT_FULFILLED
        )

    @property
    def missing(self) -> bool:
        return (
            self.expectation == GENERATED_MATERIALIZATION_EXPECTATION_REQUIRED
            and self.fulfillment
            == GENERATED_MATERIALIZATION_FULFILLMENT_MISSING
        )

    @property
    def unsupported(self) -> bool:
        return (
            self.expectation
            == GENERATED_MATERIALIZATION_EXPECTATION_UNSUPPORTED
        )

    @property
    def deferred(self) -> bool:
        return (
            self.expectation == GENERATED_MATERIALIZATION_EXPECTATION_DEFERRED
        )

    @property
    def not_required(self) -> bool:
        return (
            self.expectation
            == GENERATED_MATERIALIZATION_EXPECTATION_NOT_REQUIRED
        )

    def evidence_payload(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "feature_key": self.feature_key,
            "operation_key": self.operation_key,
            "semantic_key": self.semantic_key,
            "ontology_subject_kind": self.ontology_subject_kind,
            "operation_family": self.operation_family,
            "provider_operation_type": self.provider_operation_type,
            "expectation": self.expectation,
            "fulfillment": self.fulfillment,
            "required": self.required,
            "fulfilled": self.fulfilled,
            "missing": self.missing,
            "unsupported": self.unsupported,
            "deferred": self.deferred,
            "not_required": self.not_required,
            "reason": self.reason,
            "next_capability_ref": self.next_capability_ref,
            "diagnostics": self.diagnostics,
            "event_refs": self.event_refs,
        }


def _entry_event_refs(
    entries: tuple[CodeSectionDeltaEntry, ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                event_ref
                for entry in entries
                if entry.event_ref is not None
                for event_ref in (entry.event_ref,)
            }
        )
    )


def _projected_event_refs(
    *,
    entries: tuple[CodeSectionDeltaEntry, ...],
    grammar_anchor_replacements: tuple[CodeGrammarAnchorRenderReplacement, ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                event_ref
                for entry in entries
                if entry.event_ref is not None
                for event_ref in (entry.event_ref,)
            }
            | {
                event_ref
                for replacement in grammar_anchor_replacements
                if replacement.event_ref is not None
                for event_ref in (replacement.event_ref,)
            }
        )
    )


def _generated_materialization_status_from_result(
    result: CodeGeneratedMaterializationDeltaResult,
) -> str:
    if result.mode is CodeGeneratedMaterializationDeltaMode.blocked:
        return "generated_materialization_blocked"
    if result.mode is CodeGeneratedMaterializationDeltaMode.not_required:
        return "generated_materialization_skipped"
    if result.entries:
        return "generated_materialization_projected"
    if result.skipped_targets:
        return "generated_materialization_skipped"
    return "generated_materialization_skipped"


def _generated_materialization_event_refs(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    result: CodeGeneratedMaterializationDeltaResult,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                event.event_key
                for event in delta_request.events
                if event.event_key is not None
            }
            | {
                event_ref
                for entry in result.entries
                for event_ref in entry.event_refs
            }
            | {
                event_ref
                for skipped in result.skipped_targets
                for event_ref in skipped.event_refs
            }
        )
    )


def _feature_result_is_not_required(
    feature_result: MetaProviderDeltaGeneratedMaterializationFeatureResult,
) -> bool:
    return (
        feature_result.result is not None
        and feature_result.result.mode
        is CodeGeneratedMaterializationDeltaMode.not_required
    )


def meta_provider_delta_world_change_event_key(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str:
    return (
        "aware_meta.provider_delta.world_change."
        f"{operation.ontology_subject_kind}.{operation.operation_family}"
    )


MetaProviderDeltaOntologyOperationPlanner = Callable[
    [OntologyTypedOperation, OntologyExecutionPlanningContext],
    OntologyOperationHandlerResult,
]
MetaProviderDeltaTypedOperationDirtyEntryPlanner = Callable[
    [Mapping[str, object]],
    tuple[dict[str, object], ...],
]
MetaProviderDeltaSourceProjectionBuilder = Callable[
    [MetaProviderDeltaTypedOperation, MetaProviderDeltaSourceProjectionContext],
    tuple[MetaProviderDeltaSourceProjectionFeatureResult, ...],
]
MetaProviderDeltaGeneratedMaterializationBuilder = Callable[
    [
        MetaProviderDeltaTypedOperation,
        MetaProviderDeltaGeneratedMaterializationContext,
    ],
    tuple[MetaProviderDeltaGeneratedMaterializationFeatureResult, ...],
]
MetaProviderDeltaSemanticOperationResolver = Callable[..., object]


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaSemanticOperationResolverRegistration:
    handler_key: str
    semantic_operation_types: tuple[str, ...]
    resolver: MetaProviderDeltaSemanticOperationResolver

    def handles_operation_type(self, semantic_operation_type: str) -> bool:
        return semantic_operation_type in self.semantic_operation_types

    def evidence_payload(self) -> dict[str, object]:
        return {
            "handler_key": self.handler_key,
            "semantic_operation_types": self.semantic_operation_types,
        }


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaOntologyOperationRegistration:
    handler_key: str
    ontology_subject_kind: str
    operation_families: tuple[str, ...]
    planner: MetaProviderDeltaOntologyOperationPlanner

    def registration_keys(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            (self.ontology_subject_kind, operation_family)
            for operation_family in self.operation_families
        )

    def evidence_payload(self) -> dict[str, object]:
        return {
            "handler_key": self.handler_key,
            "ontology_subject_kind": self.ontology_subject_kind,
            "operation_families": self.operation_families,
        }


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration:
    handler_key: str
    ontology_subject_kind: str
    operation_families: tuple[str, ...]
    planner: MetaProviderDeltaTypedOperationDirtyEntryPlanner

    def registration_keys(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            (self.ontology_subject_kind, operation_family)
            for operation_family in self.operation_families
        )

    def evidence_payload(self) -> dict[str, object]:
        return {
            "handler_key": self.handler_key,
            "ontology_subject_kind": self.ontology_subject_kind,
            "operation_families": self.operation_families,
        }


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaFeatureProvider:
    feature_key: str
    ontology_subject_kinds: tuple[str, ...]
    typed_operation_dirty_entry_planner_registrations: tuple[
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration,
        ...,
    ] = ()
    ontology_operation_registrations: tuple[
        MetaProviderDeltaOntologyOperationRegistration,
        ...,
    ] = ()
    semantic_operation_resolver_registrations: tuple[
        MetaProviderDeltaSemanticOperationResolverRegistration,
        ...,
    ] = ()
    source_projection_builder: MetaProviderDeltaSourceProjectionBuilder | None = None
    generated_materialization_builder: (
        MetaProviderDeltaGeneratedMaterializationBuilder | None
    ) = None

    def handles_subject_kind(self, ontology_subject_kind: str) -> bool:
        return ontology_subject_kind in self.ontology_subject_kinds


__all__ = [
    "GENERATED_MATERIALIZATION_EXPECTATION_DEFERRED",
    "GENERATED_MATERIALIZATION_EXPECTATION_NOT_REQUIRED",
    "GENERATED_MATERIALIZATION_EXPECTATION_REQUIRED",
    "GENERATED_MATERIALIZATION_EXPECTATION_UNSUPPORTED",
    "GENERATED_MATERIALIZATION_FULFILLMENT_FULFILLED",
    "GENERATED_MATERIALIZATION_FULFILLMENT_MISSING",
    "GENERATED_MATERIALIZATION_FULFILLMENT_NOT_APPLICABLE",
    "META_PROVIDER_DELTA_GENERATED_MATERIALIZATION_EXPECTATION_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_GENERATED_MATERIALIZATION_FEATURE_RESULT_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_SOURCE_PROJECTION_FEATURE_RESULT_CONTRACT_VERSION",
    "MetaProviderDeltaFeatureProvider",
    "MetaProviderDeltaGeneratedMaterializationBuilder",
    "MetaProviderDeltaGeneratedMaterializationContext",
    "MetaProviderDeltaGeneratedMaterializationExpectation",
    "MetaProviderDeltaGeneratedMaterializationFeatureResult",
    "MetaProviderDeltaOntologyOperationPlanner",
    "MetaProviderDeltaOntologyOperationRegistration",
    "MetaProviderDeltaSemanticOperationResolver",
    "MetaProviderDeltaSemanticOperationResolverRegistration",
    "MetaProviderDeltaSourceProjectionBuilder",
    "MetaProviderDeltaSourceProjectionContext",
    "MetaProviderDeltaSourceProjectionFeatureResult",
    "MetaProviderDeltaTypedOperationDirtyEntryPlanner",
    "MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration",
    "meta_provider_delta_world_change_event_key",
]
