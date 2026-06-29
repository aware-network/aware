from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphHandlerExecutionRequest,
    MetaGraphPreState,
    MetaGraphPreStateIndex,
)
from aware_meta.runtime.handler_executor.language_handler import (
    MetaGraphGeneratedLanguageHandlerKey,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.stable_ids import stable_class_instance_identity_id


class MetaGraphPreStateNotReadyError(RuntimeError):
    """Raised when Meta cannot materialize validated pre-state for execution."""


@dataclass(frozen=True, slots=True)
class MetaGraphEmptyLaneBootstrap:
    root_object_id: UUID
    root_class_config_id: UUID | None = None
    key: str | None = None
    name: str | None = None
    description: str | None = None


MetaGraphEmptyLaneBootstrapCallable = Callable[
    [MetaGraphHandlerExecutionRequest],
    MetaGraphEmptyLaneBootstrap | None,
]


class MetaGraphEmptyLaneBootstrapResolver(Protocol):
    def resolve_empty_lane_bootstrap(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphEmptyLaneBootstrap | None: ...


@dataclass(frozen=True, slots=True)
class MetaGraphGeneratedConstructorBootstrapRegistry:
    bootstraps_by_key: Mapping[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphEmptyLaneBootstrapCallable,
    ]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "bootstraps_by_key",
            _expand_empty_lane_bootstrap_key_map(self.bootstraps_by_key),
        )

    def resolve_empty_lane_bootstrap(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphEmptyLaneBootstrap | None:
        descriptor = request.execution_plan.implementation
        if not descriptor.is_constructor:
            return None
        key = MetaGraphGeneratedLanguageHandlerKey.from_descriptor(
            descriptor,
            include_function_id=True,
        )
        bootstrap = self.bootstraps_by_key.get(key)
        if bootstrap is None:
            symbolic_key = MetaGraphGeneratedLanguageHandlerKey.from_descriptor(
                descriptor,
                include_function_id=False,
            )
            bootstrap = self.bootstraps_by_key.get(symbolic_key)
        if bootstrap is None:
            semantic_key = key.without_owner_class()
            bootstrap = self.bootstraps_by_key.get(semantic_key)
        if bootstrap is None:
            semantic_symbolic_key = (
                MetaGraphGeneratedLanguageHandlerKey.from_descriptor(
                    descriptor,
                    include_function_id=False,
                ).without_owner_class()
            )
            bootstrap = self.bootstraps_by_key.get(semantic_symbolic_key)
        if bootstrap is None:
            return None
        return bootstrap(request)


def _expand_empty_lane_bootstrap_key_map(
    source: Mapping[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphEmptyLaneBootstrapCallable,
    ],
) -> dict[
    MetaGraphGeneratedLanguageHandlerKey,
    MetaGraphEmptyLaneBootstrapCallable,
]:
    expanded: dict[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphEmptyLaneBootstrapCallable,
    ] = {}
    for key, value in source.items():
        _insert_empty_lane_bootstrap_key(
            expanded=expanded,
            key=key,
            value=value,
        )
        semantic_key = key.without_owner_class()
        if semantic_key != key:
            _insert_empty_lane_bootstrap_key(
                expanded=expanded,
                key=semantic_key,
                value=value,
            )
    return expanded


def _insert_empty_lane_bootstrap_key(
    *,
    expanded: dict[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphEmptyLaneBootstrapCallable,
    ],
    key: MetaGraphGeneratedLanguageHandlerKey,
    value: MetaGraphEmptyLaneBootstrapCallable,
) -> None:
    existing = expanded.get(key)
    if existing is not None and existing is not value:
        raise ValueError(
            "Duplicate generated Meta constructor bootstrap semantic key: "
            f"{key.describe()}"
        )
    expanded[key] = value


@dataclass(frozen=True, slots=True)
class MetaGraphPreStateProviderResult:
    before_oig: ObjectInstanceGraph
    graph_hash_pre: str | None = None
    head_commit_id: UUID | None = None
    root_object_id: UUID | None = None
    root_class_instance_identity_id: UUID | None = None
    oig_index: MetaGraphPreStateIndex | None = None


class MetaGraphPreStateProvider(Protocol):
    async def read_pre_state(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphPreStateProviderResult: ...


@dataclass(slots=True)
class MetaGraphPreStateMaterializerPhase:
    provider: MetaGraphPreStateProvider

    async def materialize_pre_state(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphPreState:
        snapshot = await self.provider.read_pre_state(request)
        return build_meta_graph_pre_state(
            request=request,
            snapshot=snapshot,
        )


@dataclass(slots=True)
class MetaGraphOigMaterializerPreStateProvider:
    """Pre-state provider backed by Meta's OIG materializer."""

    materializer: OIGMaterializer
    empty_lane_bootstrap_resolver: MetaGraphEmptyLaneBootstrapResolver | None

    def __init__(
        self,
        *,
        materializer: OIGMaterializer | None = None,
        empty_lane_bootstrap_resolver: (
            MetaGraphEmptyLaneBootstrapResolver | None
        ) = None,
    ) -> None:
        self.materializer = materializer or OIGMaterializer()
        self.empty_lane_bootstrap_resolver = empty_lane_bootstrap_resolver

    async def read_pre_state(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphPreStateProviderResult:
        plan = request.execution_plan
        lane_scope = plan.staged_call.lane_scope
        if plan.expected_head_commit_id is None:
            head = await self.materializer.commits.head(
                branch_id=lane_scope.domain_branch_id,
                projection_hash=lane_scope.domain_projection_hash,
            )
            if head is None:
                return self._read_empty_lane_pre_state(request)

        before_oig, _indexes = await self.materializer.get(
            branch_id=lane_scope.domain_branch_id,
            ocg=plan.index.ocg,
            opg=plan.object_projection_graph,
            commit_id=plan.expected_head_commit_id,
            oig_id=lane_scope.object_instance_graph_id,
            attribute_configs_by_id=plan.index.attribute_configs_by_id,
            class_configs_by_id=plan.index.class_configs_by_id,
        )
        return MetaGraphPreStateProviderResult(
            before_oig=before_oig,
            graph_hash_pre=before_oig.hash,
            head_commit_id=plan.expected_head_commit_id,
            oig_index=build_meta_graph_pre_state_index(before_oig),
        )

    def _read_empty_lane_pre_state(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphPreStateProviderResult:
        resolver = self.empty_lane_bootstrap_resolver
        if resolver is None:
            raise MetaGraphPreStateNotReadyError(
                "Meta pre-state cannot bootstrap an empty lane without a "
                "constructor bootstrap resolver. "
                f"function_call_id={request.staged_call.function_call.id}"
            )

        bootstrap = resolver.resolve_empty_lane_bootstrap(request)
        if bootstrap is None:
            raise MetaGraphPreStateNotReadyError(
                "Meta pre-state cannot bootstrap an empty lane for unresolved "
                "constructor root identity. "
                f"function_call_id={request.staged_call.function_call.id}"
            )

        plan = request.execution_plan
        lane_scope = plan.staged_call.lane_scope
        opg = plan.object_projection_graph
        root_class_config_id = bootstrap.root_class_config_id
        owner_class_config = plan.implementation.owner_class_config
        if root_class_config_id is None and owner_class_config is not None:
            root_class_config_id = owner_class_config.id
        if root_class_config_id is None:
            root_class_config_id = _root_class_config_id_from_opg(request)

        before_oig = build_rooted_object_instance_graph_base(
            key=bootstrap.key or str(lane_scope.domain_branch_id),
            name=bootstrap.name or opg.name,
            description=bootstrap.description or opg.description or "",
            object_config_graph=plan.index.ocg,
            object_projection_graph=opg,
            root_source_object_id=bootstrap.root_object_id,
            root_class_config_id=root_class_config_id,
            oig_id=lane_scope.object_instance_graph_id,
        )
        root_class_instance_identity_id = stable_class_instance_identity_id(
            object_instance_graph_identity_id=(
                lane_scope.object_instance_graph_identity_id
            ),
            class_instance_id=before_oig.root_class_instance.id,
        )
        return MetaGraphPreStateProviderResult(
            before_oig=before_oig,
            graph_hash_pre=before_oig.hash,
            head_commit_id=None,
            root_object_id=bootstrap.root_object_id,
            root_class_instance_identity_id=root_class_instance_identity_id,
            oig_index=build_meta_graph_pre_state_index(before_oig),
        )


def build_meta_graph_pre_state(
    *,
    request: MetaGraphHandlerExecutionRequest,
    snapshot: MetaGraphPreStateProviderResult,
) -> MetaGraphPreState:
    plan = request.execution_plan
    lane_scope = plan.staged_call.lane_scope
    before_oig = snapshot.before_oig
    oig_index = snapshot.oig_index or build_meta_graph_pre_state_index(before_oig)
    if before_oig.id != lane_scope.object_instance_graph_id:
        raise MetaGraphPreStateNotReadyError(
            "Meta pre-state OIG id mismatch: "
            f"have={before_oig.id} expected={lane_scope.object_instance_graph_id}"
        )

    graph_hash_pre = _resolve_graph_hash_pre(
        request=request,
        snapshot=snapshot,
    )
    expected_graph_hash_pre = plan.expected_graph_hash_pre
    if (
        expected_graph_hash_pre is not None
        and graph_hash_pre != expected_graph_hash_pre
    ):
        raise MetaGraphPreStateNotReadyError(
            "Meta pre-state graph hash mismatch: "
            f"have={graph_hash_pre} expected={expected_graph_hash_pre}"
        )

    expected_head_commit_id = plan.expected_head_commit_id
    if (
        expected_head_commit_id is not None
        and snapshot.head_commit_id is not None
        and snapshot.head_commit_id != expected_head_commit_id
    ):
        raise MetaGraphPreStateNotReadyError(
            "Meta pre-state head commit mismatch: "
            f"have={snapshot.head_commit_id} expected={expected_head_commit_id}"
        )

    return MetaGraphPreState(
        execution_plan=plan,
        before_oig=before_oig,
        graph_hash_pre=graph_hash_pre,
        head_commit_id=snapshot.head_commit_id,
        target_object_id=_resolve_target_class_instance_id(
            oig_index=oig_index,
            target_object_id=plan.target_object_id,
        ),
        root_object_id=snapshot.root_object_id,
        root_class_instance_identity_id=snapshot.root_class_instance_identity_id,
        oig_index=oig_index,
    )


def _resolve_graph_hash_pre(
    *,
    request: MetaGraphHandlerExecutionRequest,
    snapshot: MetaGraphPreStateProviderResult,
) -> str:
    before_hash = snapshot.before_oig.hash
    snapshot_hash = snapshot.graph_hash_pre
    if before_hash and snapshot_hash and before_hash != snapshot_hash:
        raise MetaGraphPreStateNotReadyError(
            "Meta pre-state provider returned inconsistent graph hashes: "
            f"before_oig.hash={before_hash} graph_hash_pre={snapshot_hash}"
        )

    graph_hash_pre = snapshot_hash or before_hash or request.execution_plan.expected_graph_hash_pre
    if not graph_hash_pre:
        raise MetaGraphPreStateNotReadyError(
            "Meta pre-state requires graph_hash_pre before handler execution."
        )
    return graph_hash_pre


def _resolve_target_class_instance_id(
    *,
    oig_index: MetaGraphPreStateIndex,
    target_object_id: UUID | None,
) -> UUID | None:
    if target_object_id is None:
        return None
    if target_object_id in oig_index.class_instances_by_id:
        return target_object_id
    class_instance = oig_index.class_instances_by_source_object_id.get(
        target_object_id,
    )
    if class_instance is not None:
        return class_instance.id
    return target_object_id


def build_meta_graph_pre_state_index(
    before_oig: ObjectInstanceGraph,
) -> MetaGraphPreStateIndex:
    class_instances_by_id = {}
    class_instances_by_source_object_id = {}
    class_instances_by_class_and_source_object_id = {}
    duplicate_source_object_ids = set()

    for class_instance in before_oig.class_instances:
        class_instances_by_id[class_instance.id] = class_instance
        class_source_key = (
            class_instance.class_config_id,
            class_instance.source_object_id,
        )
        class_instances_by_class_and_source_object_id[class_source_key] = (
            class_instance
        )

        source_object_id = class_instance.source_object_id
        existing = class_instances_by_source_object_id.get(source_object_id)
        if existing is None and source_object_id not in duplicate_source_object_ids:
            class_instances_by_source_object_id[source_object_id] = class_instance
        elif existing is not None and existing.id != class_instance.id:
            class_instances_by_source_object_id.pop(source_object_id, None)
            duplicate_source_object_ids.add(source_object_id)

    relationships_by_membership = {
        (
            relationship.class_config_relationship_id,
            relationship.source_class_instance_id,
            relationship.target_class_instance_id,
        ): relationship
        for relationship in before_oig.class_instance_relationships
    }

    return MetaGraphPreStateIndex(
        class_instances_by_id=class_instances_by_id,
        class_instances_by_source_object_id=class_instances_by_source_object_id,
        class_instances_by_class_and_source_object_id=(
            class_instances_by_class_and_source_object_id
        ),
        relationships_by_membership=relationships_by_membership,
    )


def _root_class_config_id_from_opg(
    request: MetaGraphHandlerExecutionRequest,
) -> UUID:
    opg = request.execution_plan.object_projection_graph
    root_nodes = tuple(
        node for node in opg.object_projection_graph_nodes if node.is_root
    )
    if len(root_nodes) != 1:
        raise MetaGraphPreStateNotReadyError(
            "Meta empty-lane bootstrap requires exactly one root OPG node. "
            f"have={len(root_nodes)} object_projection_graph_id={opg.id}"
        )
    return root_nodes[0].class_config_id


__all__ = [
    "build_meta_graph_pre_state",
    "build_meta_graph_pre_state_index",
    "MetaGraphEmptyLaneBootstrap",
    "MetaGraphEmptyLaneBootstrapCallable",
    "MetaGraphEmptyLaneBootstrapResolver",
    "MetaGraphGeneratedConstructorBootstrapRegistry",
    "MetaGraphOigMaterializerPreStateProvider",
    "MetaGraphPreStateMaterializerPhase",
    "MetaGraphPreStateNotReadyError",
    "MetaGraphPreStateProvider",
    "MetaGraphPreStateProviderResult",
]
