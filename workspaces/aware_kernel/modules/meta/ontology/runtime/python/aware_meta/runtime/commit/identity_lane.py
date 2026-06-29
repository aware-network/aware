"""Meta-owned OIG Identity (OIGI) lane helpers.

Canonical v0:
- Every domain projection lane has a stable `object_instance_graph_id` (OIGI id).
- The OIGI must be commit-backed in the `object_instance_graph_identity` projection.
- On **OPG constructor** calls, Meta must ensure the OIGI lane exists *before*
  appending the domain constructor commit. (Identity → Domain → OIGB → Env)
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import shutil
import time
from pathlib import Path
from uuid import UUID

from aware_code.types import JsonArray, JsonObject
from aware_history_ontology.stable_ids import stable_lane_id

# Meta Ontology
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)

# Meta Runtime
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.fs_store import (
    CommitActionDescriptor,
    FSCommitStore,
)
from aware_meta.graph.instance.commit.materialization_cache import (
    get_shared_materialization_cache,
)
from aware_meta.runtime import oigi_generated_handlers
from aware_meta.runtime.handler_executor import (
    build_meta_graph_execution_plan,
    build_meta_graph_generated_handler_executor,
    build_meta_graph_generated_language_handler_registry,
    MetaGraphHandlerExecutionRequest,
    MetaGraphInvocationLaneScope,
    MetaGraphPreStateProviderResult,
    MetaGraphRuntimeIndex,
    MetaGraphRuntimeIndexView,
    MetaGraphStagedFunctionCall,
)
from aware_meta.runtime.function_call_builder import build_meta_function_call
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphInvokeFunctionInput,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_lane import (
    ObjectInstanceGraphLane,
)
from aware_meta_ontology.graph.projection.object_projection_graph_identity import (
    ObjectProjectionGraphIdentity,
)
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_branch_id,
    stable_object_instance_graph_identity_id,
    stable_object_instance_graph_lane_id,
)


def _record_perf(
    perf_ms: dict[str, int] | None,
    metric: str,
    *,
    started: float,
) -> None:
    if perf_ms is None:
        return
    perf_ms[metric] = max(int((time.monotonic() - started) * 1000), 0)


def _record_commit_perf(
    perf_ms: dict[str, int] | None,
    *,
    prefix: str,
    committer: FSLaneCommitter,
) -> None:
    if perf_ms is None:
        return
    for (
        metric_name,
        metric_value,
    ) in committer.last_commit_perf_profile_snapshot().items():
        perf_ms[f"{prefix}_{metric_name}"] = max(metric_value, 0)


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphIdentityLaneContext:
    opg: ObjectProjectionGraph
    projection_hash: str


@dataclass(frozen=True, slots=True)
class _StaticObjectInstanceGraphIdentityPreStateProvider:
    before_oig: ObjectInstanceGraph
    root_object_id: UUID

    async def read_pre_state(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphPreStateProviderResult:
        return MetaGraphPreStateProviderResult(
            before_oig=self.before_oig,
            graph_hash_pre=self.before_oig.hash,
            root_object_id=self.root_object_id,
        )


def _optional_uuid_from_mapping(
    mapping: Mapping[str, object] | None,
    key: str,
) -> UUID | None:
    if mapping is None:
        return None
    raw = mapping.get(key)
    if isinstance(raw, UUID):
        return raw
    if isinstance(raw, str) and raw.strip():
        return UUID(raw)
    return None


def resolve_object_instance_graph_identity_lane_context(
    *, index: MetaGraphRuntimeIndex
) -> ObjectInstanceGraphIdentityLaneContext | None:
    opg = next(
        (
            o
            for o in index.ocg.object_projection_graphs
            if (o.name or "").strip() == "ObjectInstanceGraphIdentity"
        ),
        None,
    )
    if opg is None:
        return None
    return ObjectInstanceGraphIdentityLaneContext(
        opg=opg,
        projection_hash=opg.projection_hash,
    )


def _resolve_root_class_config_id(*, opg: ObjectProjectionGraph) -> UUID:
    for node in opg.object_projection_graph_nodes:
        if node.is_root:
            return node.class_config_id
    nodes = list(opg.object_projection_graph_nodes or [])
    if not nodes:
        raise RuntimeError("ObjectInstanceGraphIdentity OPG has no nodes")
    return nodes[0].class_config_id


def _resolve_constructor_function_id(
    *,
    index: MetaGraphRuntimeIndex,
    class_config_id: UUID,
    function_name: str,
) -> UUID:
    for node in index.ocg.object_config_graph_nodes:
        cc = node.class_config
        if cc is None or cc.id != class_config_id:
            continue
        for link in cc.class_config_function_configs:
            if link.function_config.name == function_name:
                return link.function_config.id
    raise RuntimeError(
        "Constructor FunctionConfig not found in OCG: "
        + f"class_config_id={class_config_id} function_name={function_name}"
    )


def _build_object_instance_graph_identity_lane_scope(
    *,
    ctx: ObjectInstanceGraphIdentityLaneContext,
    domain_oig_id: UUID,
    object_projection_graph_identity_id: UUID,
    oigi_id: UUID,
) -> MetaGraphInvocationLaneScope:
    oigb_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=oigi_id,
        branch_id=domain_oig_id,
    )
    lane_id = stable_lane_id(
        branch_id=domain_oig_id,
        lane_hash=ctx.projection_hash,
    )
    oigl_id = stable_object_instance_graph_lane_id(
        object_instance_graph_branch_id=oigb_id,
        lane_id=lane_id,
    )
    return MetaGraphInvocationLaneScope(
        domain_branch_id=domain_oig_id,
        domain_projection_hash=ctx.projection_hash,
        object_projection_graph_id=ctx.opg.id,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_id=oigi_id,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_branch_id=oigb_id,
        lane_id=lane_id,
        object_instance_graph_lane_id=oigl_id,
    )


def _build_object_instance_graph_identity_handler_request(
    *,
    index: MetaGraphRuntimeIndex,
    ctx: ObjectInstanceGraphIdentityLaneContext,
    before_oig: ObjectInstanceGraph,
    root_cc_id: UUID,
    opgi: ObjectProjectionGraphIdentity,
    domain_oig_id: UUID,
    oigi_id: UUID,
    author_id: UUID,
    label: str,
) -> MetaGraphHandlerExecutionRequest:
    function_name = oigi_generated_handlers.OIGI_CREATE_VIA_OPGI
    function_id = _resolve_constructor_function_id(
        index=index,
        class_config_id=root_cc_id,
        function_name=function_name,
    )
    _ocgi, identity_lane_opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=ctx.projection_hash,
    )
    if identity_lane_opgi is None:
        raise RuntimeError(
            "Missing required OPGI on runtime bundle: "
            f"projection_hash={ctx.projection_hash}"
        )
    lane_scope = _build_object_instance_graph_identity_lane_scope(
        ctx=ctx,
        domain_oig_id=domain_oig_id,
        object_projection_graph_identity_id=identity_lane_opgi.id,
        oigi_id=oigi_id,
    )
    target_object_id = before_oig.root_class_instance_id
    if target_object_id is None:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity lane pre-state is missing "
            "root_class_instance_id."
        )

    function_call = build_meta_function_call(
        index=index,
        object_id=target_object_id,
        function_id=function_id,
        args=[],
        kwargs={
            "object_projection_graph_identity_id": opgi.id,
            "object_instance_graph_id": domain_oig_id,
            "label": label,
        },
        domain_oig_lane=ObjectInstanceGraphLane.model_construct(
            id=lane_scope.object_instance_graph_lane_id,
        ),
        object_instance_graph_identity_id=oigi_id,
        call_key=oigi_id,
        expected_graph_hash_pre=before_oig.hash,
    )
    invoke_input = MetaGraphInvokeFunctionInput(
        index=index,
        actor_id=author_id,
        function_id=function_id,
        domain_branch_id=domain_oig_id,
        domain_projection_hash=ctx.projection_hash,
        call_key=oigi_id,
        call_target=MetaGraphCallTarget.opg_constructor,
        target_object_id=target_object_id,
        object_projection_graph_id=ctx.opg.id,
        args=JsonArray(),
        kwargs=JsonObject(
            {
                "object_projection_graph_identity_id": str(opgi.id),
                "object_instance_graph_id": str(domain_oig_id),
                "label": label,
            }
        ),
        expected_graph_hash_pre=before_oig.hash,
        commit=False,
    )
    index_view = MetaGraphRuntimeIndexView(index=index)
    resolved_target = index_view.resolve_function_target(function_id)
    staged_call = MetaGraphStagedFunctionCall(
        resolved_target=resolved_target,
        lane_scope=lane_scope,
        function_call=function_call,
    )
    execution_plan = build_meta_graph_execution_plan(
        index=index,
        request=invoke_input,
        staged_call=staged_call,
        index_view=index_view,
    )
    return MetaGraphHandlerExecutionRequest(
        request=invoke_input,
        staged_call=staged_call,
        execution_plan=execution_plan,
    )


def resolve_domain_object_instance_graph_identity_id(
    *,
    index: MetaGraphRuntimeIndex,
    object_instance_graph_id: UUID,
    domain_projection_hash: str,
) -> UUID:
    """Resolve the canonical OIGI id for a domain OIG/projection pair."""
    _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=domain_projection_hash,
    )
    if opgi is None:
        raise RuntimeError(
            f"Missing required OPGI on runtime bundle: projection_hash={domain_projection_hash}"
        )
    return stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi.id,
        object_instance_graph_id=object_instance_graph_id,
    )


def _reset_invalid_object_instance_graph_identity_lane(
    *,
    aware_root: Path,
    branch_id: UUID,
    projection_hash: str,
) -> None:
    branch_dir = aware_root / ".aware" / "oig" / str(branch_id)
    lane_dir = branch_dir / projection_hash
    if lane_dir.exists():
        shutil.rmtree(lane_dir)
    get_shared_materialization_cache().invalidate_lane(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if branch_dir.exists() and not any(branch_dir.iterdir()):
        shutil.rmtree(branch_dir)


async def ensure_object_instance_graph_identity_lane_head(
    *,
    index: MetaGraphRuntimeIndex,
    object_instance_graph_id: UUID,
    domain_projection_hash: str,
    author_id: UUID,
    label: str | None = None,
    perf_ms: dict[str, int] | None = None,
    perf_metric_prefix: str = "ensure_oigi_lane",
) -> None:
    """Ensure the OIGI lane exists for `object_instance_graph_id`.

    This is a durability helper: it appends the first commit to the
    `object_instance_graph_identity` lane when missing.

    Notes:
    - Idempotent: no-op when the lane already has a HEAD commit.
    - Never creates/updates OIGB or environment topology (those are separate rails).
    """
    total_started = time.monotonic()
    ctx = resolve_object_instance_graph_identity_lane_context(index=index)
    if ctx is None:
        raise RuntimeError("Missing required OPG: object_instance_graph_identity")

    if not (ctx.projection_hash or "").strip():
        raise RuntimeError(
            "object_instance_graph_identity OPG has empty projection_hash"
        )

    store = FSCommitStore()
    head_started = time.monotonic()
    head_raw = await store.head(
        branch_id=object_instance_graph_id, projection_hash=ctx.projection_hash
    )
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_head_read_ms",
        started=head_started,
    )
    head = head_raw if isinstance(head_raw, Mapping) else None

    # Canonical v1: the OIGI lane is routed by the boundary OIG id, but the
    # payload graph/root object is the canonical OIGI identity object.
    domain_oig_id = object_instance_graph_id

    root_cc_id = _resolve_root_class_config_id(opg=ctx.opg)

    # Canonical: OIGI must point at a compiler-owned OPGI (no synthesis).
    domain_opg = index.opg_by_hash.get(domain_projection_hash)
    if domain_opg is None:
        raise RuntimeError(
            f"Missing required domain OPG for OIGI creation: projection_hash={domain_projection_hash}"
        )

    _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=domain_projection_hash,
    )
    if opgi is None:
        raise RuntimeError(
            f"Missing required OPGI on runtime bundle: projection_hash={domain_projection_hash}"
        )

    oigi_id = resolve_domain_object_instance_graph_identity_id(
        index=index,
        object_instance_graph_id=domain_oig_id,
        domain_projection_hash=domain_projection_hash,
    )
    if head and head.get("commit_id"):
        head_oig_id = _optional_uuid_from_mapping(head, "object_instance_graph_id")
        if head_oig_id is not None and head_oig_id != oigi_id:
            # This lane is deterministic and derived. If the persisted head payload
            # no longer matches the canonical OIGI id, recover by dropping the
            # stale lane so the current contract can reseed it immediately.
            _reset_invalid_object_instance_graph_identity_lane(
                aware_root=store.aware_root,
                branch_id=object_instance_graph_id,
                projection_hash=ctx.projection_hash,
            )
            head = None
        if head is not None:
            if perf_ms is not None:
                perf_ms[f"{perf_metric_prefix}_head_hit"] = 1
            _record_perf(
                perf_ms,
                f"{perf_metric_prefix}_total_ms",
                started=total_started,
            )
            return

    if label is None:
        label = f"oigi:{domain_oig_id.hex[:8]}"

    build_base_started = time.monotonic()
    before_oig = build_rooted_object_instance_graph_base(
        key=str(oigi_id),
        name=f"OIGI_{domain_oig_id.hex[:8]}",
        description="ROOTED_BASE",
        object_config_graph=index.ocg,
        object_projection_graph=ctx.opg,
        root_source_object_id=oigi_id,
        root_class_config_id=root_cc_id,
        oig_id=oigi_id,
    )
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_build_base_oig_ms",
        started=build_base_started,
    )

    handler_request = _build_object_instance_graph_identity_handler_request(
        index=index,
        ctx=ctx,
        before_oig=before_oig,
        root_cc_id=root_cc_id,
        opgi=opgi,
        domain_oig_id=domain_oig_id,
        oigi_id=oigi_id,
        author_id=author_id,
        label=label,
    )
    executor = build_meta_graph_generated_handler_executor(
        handler_resolver=build_meta_graph_generated_language_handler_registry(
            module=oigi_generated_handlers,
        ),
        pre_state_provider=_StaticObjectInstanceGraphIdentityPreStateProvider(
            before_oig=before_oig,
            root_object_id=oigi_id,
        ),
    )
    execute_started = time.monotonic()
    execution_result = await executor.execute_function(handler_request)
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_execute_generated_handler_ms",
        started=execute_started,
    )
    if not execution_result.success:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity generated handler failed: "
            + (execution_result.error_message or "unknown error")
        )
    append_ready = execution_result.append_ready_changes
    if append_ready is None:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity generated handler did not return "
            "append-ready change evidence."
        )
    changes = append_ready.changes
    if not changes:
        _record_perf(
            perf_ms,
            f"{perf_metric_prefix}_total_ms",
            started=total_started,
        )
        return

    commit_action = CommitActionDescriptor(
        operation_label="ObjectInstanceGraphIdentity.create",
        call_target="opg_constructor",
        function_id=handler_request.request.function_id,
        object_id=oigi_id,
    )
    committer = FSLaneCommitter()
    fs_commit_started = time.monotonic()
    _ = await committer.commit(
        branch_id=domain_oig_id,
        projection_hash=ctx.projection_hash,
        object_projection_graph_identity_id=(
            handler_request.staged_call.lane_scope.object_projection_graph_identity_id
        ),
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=before_oig.id,
        before_oig=before_oig,
        root_object_id=oigi_id,
        changes=changes,
        graph_hash_pre=append_ready.graph_hash_pre,
        graph_hash_post=append_ready.graph_hash_post,
        author_id=author_id,
        commit_action=commit_action,
    )
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_fs_commit_ms",
        started=fs_commit_started,
    )
    _record_commit_perf(
        perf_ms,
        prefix=f"{perf_metric_prefix}_fs_commit",
        committer=committer,
    )
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_total_ms",
        started=total_started,
    )
