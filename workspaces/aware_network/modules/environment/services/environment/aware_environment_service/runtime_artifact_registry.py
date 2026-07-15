from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from threading import RLock
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class EnvironmentRuntimeArtifactRegistration:
    artifact_ref: Mapping[str, object]
    artifact_set_id: str
    package_name: str
    fqn_prefix: str
    ontology_id: UUID | None
    membership_commit_id: UUID | None
    runtime_projection_descriptor_count: int
    capability_object_count: int
    capability_function_count: int
    registered_artifact_ref_count: int
    registry_artifact_ref_count: int


class EnvironmentRuntimeArtifactRegistry:
    """Environment-owned registry of Ontology runtime artifact-set descriptors."""

    def __init__(self, *, seed_artifact_refs: Sequence[object] = ()) -> None:
        self._seed_artifact_refs = tuple(seed_artifact_refs)
        self._dynamic_artifact_refs: dict[str, Mapping[str, object]] = {}
        self._lock = RLock()

    def artifact_refs(self) -> tuple[object, ...]:
        with self._lock:
            by_key: dict[str, object] = {}
            order: list[str] = []
            for artifact_ref in self._seed_artifact_refs:
                key = _artifact_ref_registry_key(artifact_ref)
                if key not in by_key:
                    order.append(key)
                by_key[key] = artifact_ref
            for key, artifact_ref in self._dynamic_artifact_refs.items():
                if key not in by_key:
                    order.append(key)
                by_key[key] = artifact_ref
            return tuple(by_key[key] for key in order)

    def register_artifact_set(
        self,
        *,
        artifact_set: object,
        ontology_id: UUID | None = None,
        membership_commit_id: UUID | None = None,
    ) -> EnvironmentRuntimeArtifactRegistration:
        payload = _model_mapping_payload(artifact_set)
        artifact_set_id = _required_text(
            payload.get("artifact_set_id"), "artifact_set_id"
        )
        package_name = _required_text(payload.get("package_name"), "package_name")
        fqn_prefix = _required_text(payload.get("fqn_prefix"), "fqn_prefix")
        artifact_ref = _artifact_ref_from_artifact_set_payload(payload)
        key = _artifact_ref_registry_key(artifact_ref)
        with self._lock:
            self._dynamic_artifact_refs[key] = artifact_ref
            registry_count = len(self.artifact_refs())
        capability_object_count, capability_function_count = _capability_counts(payload)
        return EnvironmentRuntimeArtifactRegistration(
            artifact_ref=artifact_ref,
            artifact_set_id=artifact_set_id,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            ontology_id=ontology_id,
            membership_commit_id=membership_commit_id,
            runtime_projection_descriptor_count=len(
                _mapping_sequence(payload.get("runtime_projection_descriptors"))
            ),
            capability_object_count=capability_object_count,
            capability_function_count=capability_function_count,
            registered_artifact_ref_count=1,
            registry_artifact_ref_count=registry_count,
        )


def _artifact_ref_from_artifact_set_payload(
    artifact_set: Mapping[str, object],
) -> Mapping[str, object]:
    artifact_set_id = _required_text(
        artifact_set.get("artifact_set_id"), "artifact_set_id"
    )
    package_name = _required_text(artifact_set.get("package_name"), "package_name")
    fqn_prefix = _required_text(artifact_set.get("fqn_prefix"), "fqn_prefix")
    artifacts = _mapping_sequence(artifact_set.get("artifacts"))
    descriptors = _mapping_sequence(artifact_set.get("runtime_projection_descriptors"))
    lifecycle_state = _optional_text(artifact_set.get("lifecycle_state")) or "produced"
    activation_policy = _optional_text(artifact_set.get("activation_policy"))
    runtime_contract_version = _optional_text(
        artifact_set.get("runtime_contract_version")
    )
    return {
        "artifact_family": "ontology_runtime_artifact_set",
        "artifact_key": artifact_set_id,
        "artifact_role": "runtime_artifact_set",
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "status": "available",
        "required_for": ["runtime_index", "service_boot"],
        "media_type": "application/json",
        "runtime_contract_version": runtime_contract_version,
        "provider_payload": {
            "package_name": package_name,
            "fqn_prefix": fqn_prefix,
            "artifact_set_id": artifact_set_id,
            "lifecycle_state": lifecycle_state,
            "activation_allowed": bool(artifact_set.get("activation_allowed") is True),
            "activation_policy": activation_policy,
            "artifact_count": len(artifacts),
            "runtime_projection_descriptor_count": len(descriptors),
        },
        "receipt": {"ontology_runtime_artifact_set": dict(artifact_set)},
    }


def _artifact_ref_registry_key(artifact_ref: object) -> str:
    payload = _artifact_ref_mapping(artifact_ref, "receipt")
    artifact_set = _model_mapping_payload(payload.get("ontology_runtime_artifact_set"))
    artifact_set_id = _optional_text(artifact_set.get("artifact_set_id"))
    if artifact_set_id is not None:
        return f"artifact_set:{artifact_set_id}"
    artifact_key = _optional_text(_artifact_ref_value(artifact_ref, "artifact_key"))
    if artifact_key is not None:
        return f"artifact_key:{artifact_key}"
    return f"object:{id(artifact_ref)}"


def _capability_counts(artifact_set: Mapping[str, object]) -> tuple[int, int]:
    object_count = 0
    function_count = 0
    for descriptor in _mapping_sequence(
        artifact_set.get("runtime_projection_descriptors")
    ):
        metadata = _model_mapping_payload(descriptor.get("metadata"))
        functions = _mapping_sequence(metadata.get("capability_functions"))
        if functions:
            object_count += 1
            function_count += len(functions)
    return object_count, function_count


def _artifact_ref_mapping(artifact_ref: object, key: str) -> Mapping[str, object]:
    return _model_mapping_payload(_artifact_ref_value(artifact_ref, key))


def _artifact_ref_value(artifact_ref: object, key: str) -> object | None:
    if isinstance(artifact_ref, Mapping):
        return artifact_ref.get(key)
    return getattr(artifact_ref, key, None)


def _model_mapping_payload(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return {str(key): _jsonish(item) for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return {str(key): _jsonish(item) for key, item in dumped.items()}
    return {}


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(
        _model_mapping_payload(item) for item in value if _model_mapping_payload(item)
    )


def _required_text(value: object, field_name: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise ValueError(f"Ontology runtime artifact set missing {field_name}.")
    return text


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _jsonish(value: object) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonish(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_jsonish(item) for item in value]
    if isinstance(value, list):
        return [_jsonish(item) for item in value]
    if isinstance(value, set):
        return [_jsonish(item) for item in sorted(value, key=str)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _jsonish(model_dump(mode="json"))
    return str(value)


__all__ = [
    "EnvironmentRuntimeArtifactRegistration",
    "EnvironmentRuntimeArtifactRegistry",
]
