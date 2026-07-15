from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any


ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY = "ontology_runtime_artifact_set"
ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY = "ontology_runtime_artifact_set"
ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE = "runtime_artifact_set"
ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION = (
    "aware.ontology.runtime_artifact_set.v1"
)


@dataclass(frozen=True, slots=True)
class InterfaceRuntimeArtifactRef:
    artifact_family: str
    artifact_key: str
    artifact_role: str
    required_for: tuple[str, ...] = ()
    status: str = "available"
    package_name: str | None = None
    revision_code_package_id: str | None = None
    semantic_package_commit_id: str | None = None
    source_code_package_id: str | None = None
    source_object_instance_graph_commit_id: str | None = None
    input_object_instance_graph_commit_id: str | None = None
    workspace_relative_path: str | None = None
    digest: str | None = None
    digest_algorithm: str | None = None
    media_type: str | None = None
    runtime_contract_version: str | None = None
    provider_payload: dict[str, object] = field(default_factory=dict)
    receipt: dict[str, object] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        return {
            key: _jsonable(value)
            for key, value in asdict(self).items()
            if value not in (None, (), {})
        }


@dataclass(frozen=True, slots=True)
class InterfaceOntologyRuntimeArtifactSet:
    artifact_set_id: str
    package_name: str
    fqn_prefix: str
    runtime_contract_version: str
    runtime_projection_descriptors: tuple[Mapping[str, object], ...]
    payload: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class InterfaceOntologyRuntimeArtifactCatalog:
    artifact_sets: tuple[InterfaceOntologyRuntimeArtifactSet, ...]

    @property
    def artifact_set_count(self) -> int:
        return len(self.artifact_sets)

    @property
    def runtime_projection_descriptor_count(self) -> int:
        return sum(
            len(artifact_set.runtime_projection_descriptors)
            for artifact_set in self.artifact_sets
        )


def runtime_artifact_refs_from_payload(
    payload: object,
) -> tuple[InterfaceRuntimeArtifactRef, ...]:
    if payload is None:
        return ()
    if not _is_sequence_not_text(payload):
        raise RuntimeError("Interface runtime_artifact_refs must be a list.")
    refs: list[InterfaceRuntimeArtifactRef] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise RuntimeError(
                "Interface runtime_artifact_refs entries must be JSON/TOML tables."
            )
        refs.append(runtime_artifact_ref_from_payload(item))
    return tuple(refs)


def runtime_artifact_ref_from_payload(
    payload: Mapping[str, object],
) -> InterfaceRuntimeArtifactRef:
    return InterfaceRuntimeArtifactRef(
        artifact_family=_read_required_text(payload, "artifact_family"),
        artifact_key=_read_required_text(payload, "artifact_key"),
        artifact_role=_read_required_text(payload, "artifact_role"),
        required_for=_read_text_tuple(payload.get("required_for")),
        status=_read_optional_text(payload.get("status")) or "available",
        package_name=_read_optional_text(payload.get("package_name")),
        revision_code_package_id=_read_optional_text(
            payload.get("revision_code_package_id")
        ),
        semantic_package_commit_id=_read_optional_text(
            payload.get("semantic_package_commit_id")
        ),
        source_code_package_id=_read_optional_text(
            payload.get("source_code_package_id")
        ),
        source_object_instance_graph_commit_id=_read_optional_text(
            payload.get("source_object_instance_graph_commit_id")
        ),
        input_object_instance_graph_commit_id=_read_optional_text(
            payload.get("input_object_instance_graph_commit_id")
        ),
        workspace_relative_path=_read_optional_text(
            payload.get("workspace_relative_path")
        ),
        digest=_read_optional_text(payload.get("digest")),
        digest_algorithm=_read_optional_text(payload.get("digest_algorithm")),
        media_type=_read_optional_text(payload.get("media_type")),
        runtime_contract_version=_read_optional_text(
            payload.get("runtime_contract_version")
        ),
        provider_payload=dict(_mapping_payload(payload.get("provider_payload"))),
        receipt=dict(_mapping_payload(payload.get("receipt"))),
    )


def build_ontology_runtime_artifact_catalog(
    *,
    artifact_refs: Sequence[object],
) -> InterfaceOntologyRuntimeArtifactCatalog:
    artifact_sets: list[InterfaceOntologyRuntimeArtifactSet] = []
    for artifact_ref in artifact_refs:
        payload = ontology_runtime_artifact_set_payload_from_ref(artifact_ref)
        if payload is None:
            continue
        artifact_sets.append(_artifact_set_from_payload(payload))
    if not artifact_sets:
        raise RuntimeError(
            "Interface runtime requires ontology runtime artifact-set refs. "
            "Provide artifact refs with artifact_family="
            f"{ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY!r}, artifact_role="
            f"{ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE!r}, and embedded "
            f"{ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY!r} payload in receipt "
            "or provider_payload."
        )
    return InterfaceOntologyRuntimeArtifactCatalog(artifact_sets=tuple(artifact_sets))


def ontology_runtime_artifact_set_payload_from_ref(
    artifact_ref: object,
) -> Mapping[str, object] | None:
    artifact_family = _read_optional_text(
        _artifact_ref_value(artifact_ref, "artifact_family")
    )
    artifact_role = _read_optional_text(
        _artifact_ref_value(artifact_ref, "artifact_role")
    )
    if (
        artifact_family != ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY
        or artifact_role != ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE
    ):
        return None
    direct = _mapping_payload(
        _artifact_ref_value(artifact_ref, ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY)
    )
    if direct:
        return direct
    receipt = _artifact_ref_mapping(artifact_ref, "receipt")
    receipt_payload = _mapping_payload(
        receipt.get(ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY)
    )
    if receipt_payload:
        return receipt_payload
    provider_payload = _artifact_ref_mapping(artifact_ref, "provider_payload")
    provider_artifact_set = _mapping_payload(
        provider_payload.get(ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY)
    )
    return provider_artifact_set or None


def _artifact_set_from_payload(
    payload: Mapping[str, object],
) -> InterfaceOntologyRuntimeArtifactSet:
    contract_version = (
        _read_optional_text(payload.get("runtime_contract_version"))
        or ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION
    )
    if contract_version != ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION:
        raise RuntimeError(
            "Unsupported ontology runtime artifact-set contract: "
            f"{contract_version!r}"
        )
    descriptors = tuple(_mapping_items(payload.get("runtime_projection_descriptors")))
    return InterfaceOntologyRuntimeArtifactSet(
        artifact_set_id=_read_required_text(payload, "artifact_set_id"),
        package_name=_read_required_text(payload, "package_name"),
        fqn_prefix=_read_required_text(payload, "fqn_prefix"),
        runtime_contract_version=contract_version,
        runtime_projection_descriptors=descriptors,
        payload=payload,
    )


def _artifact_ref_mapping(artifact_ref: object, key: str) -> Mapping[str, object]:
    return _mapping_payload(_artifact_ref_value(artifact_ref, key))


def _artifact_ref_value(artifact_ref: object, key: str) -> object | None:
    if isinstance(artifact_ref, Mapping):
        return artifact_ref.get(key)
    return getattr(artifact_ref, key, None)


def _mapping_payload(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return {}


def _mapping_items(value: object) -> tuple[Mapping[str, object], ...]:
    if not _is_sequence_not_text(value):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _read_required_text(payload: Mapping[str, object], key: str) -> str:
    value = _read_optional_text(payload.get(key))
    if value is None:
        raise RuntimeError(f"Interface runtime artifact ref missing {key!r}.")
    return value


def _read_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _read_text_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if not _is_sequence_not_text(value):
        return ()
    return tuple(
        dict.fromkeys(
            text for item in value for text in (_read_optional_text(item),) if text
        )
    )


def _is_sequence_not_text(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    )


def _jsonable(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


__all__ = [
    "InterfaceOntologyRuntimeArtifactCatalog",
    "InterfaceOntologyRuntimeArtifactSet",
    "InterfaceRuntimeArtifactRef",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY",
    "build_ontology_runtime_artifact_catalog",
    "ontology_runtime_artifact_set_payload_from_ref",
    "runtime_artifact_ref_from_payload",
    "runtime_artifact_refs_from_payload",
]
