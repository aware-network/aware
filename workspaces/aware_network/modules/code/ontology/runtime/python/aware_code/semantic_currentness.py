"""Provider-owned semantic materialization currentness replay contract."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Literal, Protocol, cast
from uuid import UUID

from aware_code.semantic_materialization import SemanticPackageMaterializationBundle


SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_CONTRACT_VERSION = (
    "aware.code.semantic-materialization.currentness-replay.v1"
)
SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_METADATA_KEY = (
    "semantic_materialization_currentness_replay_adapter"
)
SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_ENTRYPOINT = (
    "resolve_currentness_replay"
)

SemanticMaterializationCurrentnessReplayStatus = Literal[
    "reused",
    "must_execute",
    "not_supported",
]
SemanticMaterializationCurrentnessReplaySemanticGraphs = Literal[
    "not_required",
    "required",
]


@dataclass(frozen=True, slots=True)
class SemanticMaterializationCurrentnessReplayContextRequirement:
    semantic_graphs: SemanticMaterializationCurrentnessReplaySemanticGraphs = (
        "not_required"
    )

    @property
    def requires_semantic_graphs(self) -> bool:
        return self.semantic_graphs == "required"


class SemanticMaterializationHeadReader(Protocol):
    async def __call__(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> Mapping[str, object] | None: ...


@dataclass(frozen=True, slots=True)
class SemanticMaterializationCurrentnessReplayRequest:
    provider_key: str
    semantic_owner: str
    workspace_root: Path
    workspace_manifest_kind: str
    semantic_package_family: str
    semantic_package_kind: str
    input_proof: Mapping[str, object]
    bundles: tuple[SemanticPackageMaterializationBundle, ...]
    read_head: SemanticMaterializationHeadReader
    replay_output_details: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SemanticMaterializationCurrentnessReplayResult:
    status: SemanticMaterializationCurrentnessReplayStatus
    reason: str
    replay_kind: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)
    context_requirement: SemanticMaterializationCurrentnessReplayContextRequirement = (
        field(
            default_factory=SemanticMaterializationCurrentnessReplayContextRequirement
        )
    )
    contract_version: str = SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_CONTRACT_VERSION

    @property
    def reused(self) -> bool:
        return self.status == "reused"


SemanticMaterializationCurrentnessReplayAdapter = Callable[
    [SemanticMaterializationCurrentnessReplayRequest],
    SemanticMaterializationCurrentnessReplayResult
    | Awaitable[SemanticMaterializationCurrentnessReplayResult],
]


def resolve_semantic_materialization_currentness_replay_adapter(
    *,
    capability_metadata: Mapping[str, object],
) -> SemanticMaterializationCurrentnessReplayAdapter | None:
    raw_adapter = capability_metadata.get(
        SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_METADATA_KEY
    )
    if not isinstance(raw_adapter, Mapping):
        return None
    callable_module = _optional_text(raw_adapter.get("callable_module"))
    callable_name = _optional_text(raw_adapter.get("callable_name"))
    contract_version = _optional_text(raw_adapter.get("contract_version"))
    if (
        callable_module is None
        or callable_name is None
        or contract_version
        != SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_CONTRACT_VERSION
    ):
        return None
    try:
        module = import_module(callable_module)
    except ModuleNotFoundError:
        return None
    adapter = getattr(module, callable_name, None)
    return (
        cast(SemanticMaterializationCurrentnessReplayAdapter, adapter)
        if callable(adapter)
        else None
    )


def semantic_materialization_declared_source_tree_input_is_complete(
    *,
    request: SemanticMaterializationCurrentnessReplayRequest,
) -> bool:
    return (
        request.input_proof.get("kind") == "declared_source_tree"
        and request.input_proof.get("complete") is True
    )


async def semantic_materialization_bundle_matches_live_head(
    *,
    bundle: SemanticPackageMaterializationBundle,
    read_head: SemanticMaterializationHeadReader,
) -> bool:
    branch_id = bundle.semantic_branch_id
    projection_hash = _optional_text(bundle.semantic_projection_hash)
    expected_oig_commit_id = bundle.semantic_object_instance_graph_commit_id
    if branch_id is None or projection_hash is None or expected_oig_commit_id is None:
        return False
    head = await read_head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if not isinstance(head, Mapping):
        return False
    return _uuid_or_none(head.get("object_instance_graph_commit_id")) == (
        expected_oig_commit_id
    )


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return UUID(value.strip())
    except ValueError:
        return None


__all__ = [
    "SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_ENTRYPOINT",
    "SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_METADATA_KEY",
    "SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_CONTRACT_VERSION",
    "SemanticMaterializationCurrentnessReplayAdapter",
    "SemanticMaterializationCurrentnessReplayContextRequirement",
    "SemanticMaterializationCurrentnessReplayRequest",
    "SemanticMaterializationCurrentnessReplayResult",
    "SemanticMaterializationCurrentnessReplayStatus",
    "SemanticMaterializationCurrentnessReplaySemanticGraphs",
    "SemanticMaterializationHeadReader",
    "resolve_semantic_materialization_currentness_replay_adapter",
    "semantic_materialization_bundle_matches_live_head",
    "semantic_materialization_declared_source_tree_input_is_complete",
]
