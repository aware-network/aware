from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from aware_code_ontology.code.code_plan import CodePackageDelta


SEMANTIC_ANALYSIS_CAPABILITY = "semantic_analysis"
SemanticCapabilityEventVerb = Literal[
    "noop",
    "create",
    "update",
    "upsert",
    "delete",
    "rename",
]
SemanticCapabilityActionKind = Literal[
    "function_call",
    "source_projection",
    "notification",
    "test",
    "custom",
]
SemanticDependencyRequiredState = Literal[
    "available",
    "materialized",
    "committed",
]


@dataclass(frozen=True, slots=True)
class SemanticCapabilityDiagnostic:
    severity: str
    code: str
    message: str
    source_path: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SemanticCapabilityDelta:
    delta_key: str
    semantic_key: str
    verb: SemanticCapabilityEventVerb
    subject_type: str
    source: str
    source_refs: tuple[str, ...] = ()
    before_payload: Mapping[str, object] | None = None
    after_payload: Mapping[str, object] | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "delta_key": self.delta_key,
            "semantic_key": self.semantic_key,
            "verb": self.verb,
            "subject_type": self.subject_type,
            "source": self.source,
            "source_refs": self.source_refs,
            "metadata": dict(self.metadata),
        }
        if self.before_payload is not None:
            payload["before_payload"] = dict(self.before_payload)
        if self.after_payload is not None:
            payload["after_payload"] = dict(self.after_payload)
        return payload


@dataclass(frozen=True, slots=True)
class SemanticCapabilityFunctionCallBinding:
    binding_key: str
    event_key: str
    function_ref: str
    receiver_semantic_key_template: str | None = None
    argument_bindings: Mapping[str, str] = field(default_factory=dict)
    argument_ref_bindings: Mapping[str, str] = field(default_factory=dict)
    constant_arguments: Mapping[str, object] = field(default_factory=dict)
    result_semantic_key_template: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "binding_key": self.binding_key,
            "event_key": self.event_key,
            "function_ref": self.function_ref,
            "argument_bindings": dict(self.argument_bindings),
            "argument_ref_bindings": dict(self.argument_ref_bindings),
            "constant_arguments": dict(self.constant_arguments),
            "metadata": dict(self.metadata),
        }
        if self.receiver_semantic_key_template is not None:
            payload["receiver_semantic_key_template"] = (
                self.receiver_semantic_key_template
            )
        if self.result_semantic_key_template is not None:
            payload["result_semantic_key_template"] = self.result_semantic_key_template
        return payload


@dataclass(frozen=True, slots=True)
class SemanticCapabilityEvent:
    event_key: str
    semantic_key: str
    verb: SemanticCapabilityEventVerb
    subject_type: str
    source: str
    event_type: str = "semantic_change"
    source_refs: tuple[str, ...] = ()
    delta_keys: tuple[str, ...] = ()
    condition_keys: tuple[str, ...] = ()
    payload: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "event_key": self.event_key,
            "event_type": self.event_type,
            "semantic_key": self.semantic_key,
            "verb": self.verb,
            "subject_type": self.subject_type,
            "source": self.source,
            "source_refs": self.source_refs,
            "delta_keys": self.delta_keys,
            "condition_keys": self.condition_keys,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
        }
        return payload


@dataclass(frozen=True, slots=True)
class SemanticCapabilityTypedOperation:
    operation_key: str
    operation_family: SemanticCapabilityEventVerb
    semantic_operation_type: str
    semantic_key: str
    semantic_subject_type: str
    field_path: str | None = None
    event_key: str | None = None
    source: str = "aware_code.semantic_capability"
    source_refs: tuple[str, ...] = ()
    before_payload: Mapping[str, object] | None = None
    after_payload: Mapping[str, object] | None = None
    requires_baseline_object_identity: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "operation_key": self.operation_key,
            "operation_family": self.operation_family,
            "semantic_operation_type": self.semantic_operation_type,
            "semantic_key": self.semantic_key,
            "semantic_subject_type": self.semantic_subject_type,
            "source": self.source,
            "source_refs": self.source_refs,
            "requires_baseline_object_identity": (
                self.requires_baseline_object_identity
            ),
            "metadata": dict(self.metadata),
        }
        if self.field_path is not None:
            payload["field_path"] = self.field_path
        if self.event_key is not None:
            payload["event_key"] = self.event_key
        if self.before_payload is not None:
            payload["before_payload"] = dict(self.before_payload)
        if self.after_payload is not None:
            payload["after_payload"] = dict(self.after_payload)
        return payload


@dataclass(frozen=True, slots=True)
class SemanticCapabilityActionBinding:
    action_key: str
    event_key: str
    action_type: SemanticCapabilityActionKind
    description: str | None = None
    function_call_binding: SemanticCapabilityFunctionCallBinding | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "action_key": self.action_key,
            "event_key": self.event_key,
            "action_type": self.action_type,
            "metadata": dict(self.metadata),
        }
        if self.description is not None:
            payload["description"] = self.description
        if self.function_call_binding is not None:
            payload["function_call_binding"] = (
                self.function_call_binding.evidence_payload()
            )
        return payload


@dataclass(frozen=True, slots=True)
class SemanticCapabilityDependencyRequirement:
    dependency_key: str
    provider_key: str
    package_name: str
    required_state: SemanticDependencyRequiredState = "materialized"
    dependency_kind: str = "semantic_package"
    semantic_owner: str | None = None
    manifest_kind: str | None = None
    package_selector: Mapping[str, object] = field(default_factory=dict)
    reason: str | None = None
    source_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "dependency_key": self.dependency_key,
            "provider_key": self.provider_key,
            "package_name": self.package_name,
            "required_state": self.required_state,
            "dependency_kind": self.dependency_kind,
            "source_refs": self.source_refs,
            "package_selector": dict(self.package_selector),
            "metadata": dict(self.metadata),
        }
        if self.semantic_owner is not None:
            payload["semantic_owner"] = self.semantic_owner
        if self.manifest_kind is not None:
            payload["manifest_kind"] = self.manifest_kind
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


@dataclass(frozen=True, slots=True)
class SemanticCapabilityFunctionCallPlan:
    function_ref: str
    binding_key: str | None = None
    action_key: str | None = None
    event_key: str | None = None
    receiver_semantic_key: str | None = None
    arguments: Mapping[str, object] = field(default_factory=dict)
    argument_refs: Mapping[str, str] = field(default_factory=dict)
    result_semantic_key: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "function_ref": self.function_ref,
            "arguments": dict(self.arguments),
            "argument_refs": dict(self.argument_refs),
            "metadata": dict(self.metadata),
        }
        if self.binding_key is not None:
            payload["binding_key"] = self.binding_key
        if self.action_key is not None:
            payload["action_key"] = self.action_key
        if self.event_key is not None:
            payload["event_key"] = self.event_key
        if self.receiver_semantic_key is not None:
            payload["receiver_semantic_key"] = self.receiver_semantic_key
        if self.result_semantic_key is not None:
            payload["result_semantic_key"] = self.result_semantic_key
        return payload


@dataclass(frozen=True, slots=True)
class SemanticCapabilityChangePreview:
    changed_source_files: tuple[str, ...] = ()
    affected_semantic_keys: tuple[str, ...] = ()
    required_materializations: tuple[str, ...] = ()
    required_semantic_dependencies: tuple[
        SemanticCapabilityDependencyRequirement,
        ...,
    ] = ()
    semantic_deltas: tuple[SemanticCapabilityDelta, ...] = ()
    semantic_events: tuple[SemanticCapabilityEvent, ...] = ()
    typed_operations: tuple[SemanticCapabilityTypedOperation, ...] = ()
    action_bindings: tuple[SemanticCapabilityActionBinding, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        return {
            "changed_source_files": self.changed_source_files,
            "affected_semantic_keys": self.affected_semantic_keys,
            "required_materializations": self.required_materializations,
            "required_semantic_dependencies": tuple(
                dependency.evidence_payload()
                for dependency in self.required_semantic_dependencies
            ),
            "semantic_deltas": tuple(
                delta.evidence_payload() for delta in self.semantic_deltas
            ),
            "semantic_events": tuple(
                event.evidence_payload() for event in self.semantic_events
            ),
            "typed_operations": tuple(
                operation.evidence_payload()
                for operation in self.typed_operations
            ),
            "action_bindings": tuple(
                action_binding.evidence_payload()
                for action_binding in self.action_bindings
            ),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class SemanticAnalysisCapabilityRequest:
    package_root: Path
    source_files: tuple[Path, ...]
    manifest_path: Path | None = None
    workspace_root: Path | None = None
    code_package_delta: CodePackageDelta | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SemanticAnalysisCapabilityResult:
    provider_key: str
    semantic_owner: str
    package_root: str
    source_files: tuple[str, ...]
    diagnostics: tuple[SemanticCapabilityDiagnostic, ...]
    change_preview: SemanticCapabilityChangePreview
    payload: object | None = None
    code_package_delta: CodePackageDelta | None = None
    capability: str = SEMANTIC_ANALYSIS_CAPABILITY
    schema_version: int = 1


__all__ = [
    "SEMANTIC_ANALYSIS_CAPABILITY",
    "SemanticAnalysisCapabilityRequest",
    "SemanticAnalysisCapabilityResult",
    "SemanticCapabilityActionBinding",
    "SemanticCapabilityActionKind",
    "SemanticCapabilityChangePreview",
    "SemanticCapabilityDependencyRequirement",
    "SemanticCapabilityDelta",
    "SemanticCapabilityDiagnostic",
    "SemanticCapabilityEvent",
    "SemanticCapabilityEventVerb",
    "SemanticCapabilityFunctionCallBinding",
    "SemanticCapabilityFunctionCallPlan",
    "SemanticCapabilityTypedOperation",
    "SemanticDependencyRequiredState",
]
