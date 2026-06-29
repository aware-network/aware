from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Protocol, runtime_checkable
from uuid import UUID

from aware_code.types import JsonArray, JsonObject, JsonValue
from aware_meta.graph.projection.portal_index import ObjectProjectionGraphPortalIndex
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.function.function_call import FunctionCall
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)

if TYPE_CHECKING:
    from aware_meta.runtime.invocation_engine import (
        MetaGraphInvokeFunctionCallable,
        MetaGraphInvokeFunctionInput,
    )


@runtime_checkable
class MetaGraphCommitIndex(Protocol):
    """Minimal indexed graph truth required before handler execution.

    This is intentionally not the legacy composed-runtime index. Meta should
    depend on the fields needed for graph execution, not on the heavy object
    that currently happens to provide them.
    """

    ocg: ObjectConfigGraph
    class_configs_by_id: Mapping[UUID, ClassConfig]
    opg_by_id: Mapping[UUID, ObjectProjectionGraph]
    opg_by_hash: Mapping[str, ObjectProjectionGraph]


@runtime_checkable
class MetaGraphRuntimeIndex(MetaGraphCommitIndex, Protocol):
    """Meta-owned runtime index contract for handler execution.

    Production can satisfy this protocol with a lightweight Meta index built
    from committed package/index artifacts. The legacy composed runtime index can
    remain an adapter during migration.
    """

    attribute_configs_by_id: Mapping[UUID, AttributeConfig]
    relationships_by_id: Mapping[UUID, ClassConfigRelationship]
    portal_index: ObjectProjectionGraphPortalIndex


class MetaGraphImplementationKind(Enum):
    """Implementation rails accepted behind the Meta executor boundary."""

    aware_function_impl = "aware_function_impl"
    language_handler = "language_handler"


@dataclass(frozen=True, slots=True)
class MetaGraphResolvedFunctionTarget:
    function_config: FunctionConfig
    operation_label: str


@dataclass(frozen=True, slots=True)
class MetaGraphFunctionImplementationDescriptor:
    kind: MetaGraphImplementationKind
    function_config: FunctionConfig
    owner_class_config: ClassConfig | None = None
    class_function_edge: ClassConfigFunctionConfig | None = None
    is_constructor: bool = False


@dataclass(frozen=True, slots=True)
class MetaGraphPreStateIndex:
    """OIG lookup maps supplied before the hot execution path."""

    class_instances_by_id: Mapping[UUID, ClassInstance]
    class_instances_by_source_object_id: Mapping[UUID, ClassInstance]
    class_instances_by_class_and_source_object_id: Mapping[
        tuple[UUID, UUID],
        ClassInstance,
    ]
    relationships_by_membership: Mapping[
        tuple[UUID, UUID, UUID],
        ClassInstanceRelationship,
    ]


@dataclass(frozen=True, slots=True)
class MetaGraphInvocationLaneScope:
    domain_branch_id: UUID
    domain_projection_hash: str
    object_projection_graph_id: UUID
    object_projection_graph_identity_id: UUID
    object_instance_graph_id: UUID
    object_instance_graph_identity_id: UUID
    object_instance_graph_branch_id: UUID
    lane_id: UUID
    object_instance_graph_lane_id: UUID


@dataclass(frozen=True, slots=True)
class MetaGraphStagedFunctionCall:
    resolved_target: MetaGraphResolvedFunctionTarget
    lane_scope: MetaGraphInvocationLaneScope
    function_call: FunctionCall


@dataclass(frozen=True, slots=True)
class MetaGraphExecutionPlan:
    index: MetaGraphRuntimeIndex
    staged_call: MetaGraphStagedFunctionCall
    implementation: MetaGraphFunctionImplementationDescriptor
    object_projection_graph: ObjectProjectionGraph
    target_object_id: UUID | None = None
    expected_graph_hash_pre: str | None = None
    expected_head_commit_id: UUID | None = None
    function_targets_by_id: Mapping[UUID, MetaGraphResolvedFunctionTarget] | None = None
    implementation_descriptors_by_id: (
        Mapping[UUID, MetaGraphFunctionImplementationDescriptor] | None
    ) = None
    function_input_edges_by_id: Mapping[UUID, FunctionConfigAttributeConfig] | None = (
        None
    )
    function_input_edges_by_function_id: (
        Mapping[UUID, tuple[FunctionConfigAttributeConfig, ...]] | None
    ) = None
    function_input_edges_by_attribute_config_id: (
        Mapping[UUID, Mapping[UUID, FunctionConfigAttributeConfig]] | None
    ) = None


@dataclass(frozen=True, slots=True)
class MetaGraphHandlerExecutionRequest:
    request: MetaGraphInvokeFunctionInput
    staged_call: MetaGraphStagedFunctionCall
    execution_plan: MetaGraphExecutionPlan
    invoke_function: MetaGraphInvokeFunctionCallable | None = None


@dataclass(frozen=True, slots=True)
class MetaGraphPreState:
    execution_plan: MetaGraphExecutionPlan
    before_oig: ObjectInstanceGraph
    graph_hash_pre: str
    head_commit_id: UUID | None = None
    target_object_id: UUID | None = None
    root_object_id: UUID | None = None
    root_class_instance_identity_id: UUID | None = None
    oig_index: MetaGraphPreStateIndex | None = None


@dataclass(frozen=True, slots=True)
class MetaGraphBoundArguments:
    execution_plan: MetaGraphExecutionPlan
    positional: JsonArray
    keyword: JsonObject


@dataclass(frozen=True, slots=True)
class MetaGraphExecutionSessionDelta:
    execution_plan: MetaGraphExecutionPlan
    before_oig: ObjectInstanceGraph
    changes: tuple[ObjectInstanceGraphChange, ...] = ()
    graph_hash_pre: str | None = None
    graph_hash_post: str | None = None
    root_object_id: UUID | None = None
    root_class_instance_identity_id: UUID | None = None
    target_class_instance_id: UUID | None = None
    constructed_class_instance_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class MetaGraphHandlerDispatchResult:
    execution_plan: MetaGraphExecutionPlan
    success: bool
    payload: JsonValue | None = None
    error_message: str | None = None
    execution_time_ms: int = 0
    session_delta: MetaGraphExecutionSessionDelta | None = None
    raw_result: object | None = None


@dataclass(frozen=True, slots=True)
class MetaGraphMutationSet:
    execution_plan: MetaGraphExecutionPlan
    before_oig: ObjectInstanceGraph
    changes: tuple[ObjectInstanceGraphChange, ...] = ()
    graph_hash_pre: str | None = None
    graph_hash_post: str | None = None
    root_object_id: UUID | None = None
    root_class_instance_identity_id: UUID | None = None
    target_class_instance_id: UUID | None = None
    constructed_class_instance_ids: tuple[UUID, ...] = ()


class MetaGraphMutationBoundaryStatus(Enum):
    """Boundary validation outcome before OIG append assembly."""

    accepted = "accepted"
    rejected = "rejected"


@dataclass(frozen=True, slots=True)
class MetaGraphMutationBoundaryValidation:
    execution_plan: MetaGraphExecutionPlan
    mutation_set: MetaGraphMutationSet
    status: MetaGraphMutationBoundaryStatus
    violation_message: str | None = None


@dataclass(frozen=True, slots=True)
class MetaGraphAppendReadyChanges:
    execution_plan: MetaGraphExecutionPlan
    before_oig: ObjectInstanceGraph
    changes: tuple[ObjectInstanceGraphChange, ...]
    graph_hash_pre: str
    graph_hash_post: str
    root_object_id: UUID | None = None
    root_class_instance_identity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class MetaGraphHandlerExecutionResult:
    success: bool
    payload: JsonValue | None = None
    error_message: str | None = None
    execution_time_ms: int = 0
    graph_hash_pre: str | None = None
    graph_hash_post: str | None = None
    root_object_id: UUID | None = None
    root_class_instance_identity_id: UUID | None = None
    before_oig: ObjectInstanceGraph | None = None
    changes: tuple[ObjectInstanceGraphChange, ...] = ()
    append_ready_changes: MetaGraphAppendReadyChanges | None = None


class MetaGraphPreStateMaterializer(Protocol):
    async def materialize_pre_state(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphPreState: ...


class MetaGraphArgumentBinder(Protocol):
    async def bind_arguments(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
    ) -> MetaGraphBoundArguments: ...


class MetaGraphImplementationDispatcher(Protocol):
    async def dispatch_implementation(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphHandlerDispatchResult: ...


class MetaGraphMutationRecorder(Protocol):
    async def record_mutations(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        dispatch_result: MetaGraphHandlerDispatchResult,
    ) -> MetaGraphMutationSet: ...


class MetaGraphMutationBoundaryValidator(Protocol):
    async def validate_mutations(
        self,
        request: MetaGraphHandlerExecutionRequest,
        mutation_set: MetaGraphMutationSet,
    ) -> MetaGraphMutationBoundaryValidation: ...


class MetaGraphAppendReadyChangeAssembler(Protocol):
    async def assemble_append_ready_changes(
        self,
        request: MetaGraphHandlerExecutionRequest,
        mutation_set: MetaGraphMutationSet,
        boundary_validation: MetaGraphMutationBoundaryValidation,
    ) -> MetaGraphAppendReadyChanges: ...


@dataclass(frozen=True, slots=True)
class MetaGraphHandlerExecutionPhases:
    pre_state_materializer: MetaGraphPreStateMaterializer
    argument_binder: MetaGraphArgumentBinder
    implementation_dispatcher: MetaGraphImplementationDispatcher
    mutation_recorder: MetaGraphMutationRecorder
    mutation_boundary_validator: MetaGraphMutationBoundaryValidator
    append_ready_change_assembler: MetaGraphAppendReadyChangeAssembler


class MetaGraphHandlerExecutor(Protocol):
    async def execute_function(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphHandlerExecutionResult: ...


__all__ = [
    "MetaGraphAppendReadyChangeAssembler",
    "MetaGraphAppendReadyChanges",
    "MetaGraphArgumentBinder",
    "MetaGraphBoundArguments",
    "MetaGraphCommitIndex",
    "MetaGraphExecutionPlan",
    "MetaGraphExecutionSessionDelta",
    "MetaGraphFunctionImplementationDescriptor",
    "MetaGraphHandlerDispatchResult",
    "MetaGraphHandlerExecutionRequest",
    "MetaGraphHandlerExecutionPhases",
    "MetaGraphHandlerExecutionResult",
    "MetaGraphHandlerExecutor",
    "MetaGraphImplementationKind",
    "MetaGraphImplementationDispatcher",
    "MetaGraphInvocationLaneScope",
    "MetaGraphMutationBoundaryStatus",
    "MetaGraphMutationBoundaryValidation",
    "MetaGraphMutationBoundaryValidator",
    "MetaGraphMutationRecorder",
    "MetaGraphMutationSet",
    "MetaGraphPreState",
    "MetaGraphPreStateIndex",
    "MetaGraphPreStateMaterializer",
    "MetaGraphResolvedFunctionTarget",
    "MetaGraphRuntimeIndex",
    "MetaGraphStagedFunctionCall",
]
