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
from aware_meta.graph.instance.commit.builder import (
    extract_object_instance_graph_commit_root_metadata,
)
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.contract import CommitActionDescriptor
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.state_index import build_commit_state_index
from aware_meta.graph.instance.commit.materialization_cache import (
    get_shared_materialization_cache,
)
from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    commit_perf_span,
    current_commit_perf_trace,
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


_OIGI_ENSURE_TRACE_PREFIX = "runtime.invoke_function.ensure_identity_lane_head"
_OIGI_REQUEST_TRACE_PREFIX = f"{_OIGI_ENSURE_TRACE_PREFIX}.build_handler_request"
_HANDLER_EXECUTION_TRACE_PREFIX = "handler_execution."
_EXECUTION_PLAN_TRACE_PREFIX = "handler_execution.execution_plan."


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


def _project_oigi_generated_execution_trace_events(
    *,
    recorder: CommitPerfTraceRecorder | None,
    event_start: int,
) -> None:
    if recorder is None:
        return
    events = recorder.snapshot()[event_start:]
    for event in events:
        if (
            event.category != "meta.runtime.handler_execution"
            or not event.phase.startswith(_HANDLER_EXECUTION_TRACE_PREFIX)
        ):
            continue
        detail_phase = event.phase.removeprefix(_HANDLER_EXECUTION_TRACE_PREFIX)
        recorder.record(
            phase=(
                f"{_OIGI_ENSURE_TRACE_PREFIX}.execute_generated_handler."
                f"detail.{detail_phase}"
            ),
            duration_ms=event.duration_ms,
            category="meta.runtime.invoke_function",
            metadata={
                **event.metadata,
                "source_phase": event.phase,
            },
        )


def _project_oigi_execution_plan_trace_events(
    *,
    recorder: CommitPerfTraceRecorder | None,
    event_start: int,
) -> None:
    if recorder is None:
        return
    events = recorder.snapshot()[event_start:]
    for event in events:
        if (
            event.category != "meta.runtime.handler_execution"
            or not event.phase.startswith(_EXECUTION_PLAN_TRACE_PREFIX)
        ):
            continue
        detail_phase = event.phase.removeprefix(_EXECUTION_PLAN_TRACE_PREFIX)
        recorder.record(
            phase=(
                f"{_OIGI_REQUEST_TRACE_PREFIX}.build_execution_plan."
                f"detail.{detail_phase}"
            ),
            duration_ms=event.duration_ms,
            category="meta.runtime.invoke_function",
            metadata={
                **event.metadata,
                "source_phase": event.phase,
            },
        )


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphIdentityLaneContext:
    opg: ObjectProjectionGraph
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphIdentityLaneHeadEnsureResult:
    status: str
    branch_id: UUID
    projection_hash: str
    object_instance_graph_identity_id: UUID
    object_instance_graph_id: UUID
    commit_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None


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
    index_view: MetaGraphRuntimeIndexView | None = None,
    ctx: ObjectInstanceGraphIdentityLaneContext,
    before_oig: ObjectInstanceGraph,
    root_cc_id: UUID,
    opgi: ObjectProjectionGraphIdentity,
    domain_oig_id: UUID,
    oigi_id: UUID,
    author_id: UUID,
    label: str,
) -> MetaGraphHandlerExecutionRequest:
    trace_metadata = {
        "domain_object_instance_graph_id": str(domain_oig_id),
        "object_instance_graph_identity_id": str(oigi_id),
        "projection_hash": ctx.projection_hash,
    }
    function_name = oigi_generated_handlers.OIGI_CREATE_VIA_OPGI
    with commit_perf_span(
        phase=f"{_OIGI_REQUEST_TRACE_PREFIX}.resolve_constructor_function",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
        function_id = _resolve_constructor_function_id(
            index=index,
            class_config_id=root_cc_id,
            function_name=function_name,
        )
    with commit_perf_span(
        phase=f"{_OIGI_REQUEST_TRACE_PREFIX}.resolve_identity_opgi",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
        _ocgi, identity_lane_opgi = resolve_meta_graph_ocgi_opgi(
            index=index,
            projection_hash=ctx.projection_hash,
        )
    if identity_lane_opgi is None:
        raise RuntimeError(
            "Missing required OPGI on runtime bundle: "
            f"projection_hash={ctx.projection_hash}"
        )
    with commit_perf_span(
        phase=f"{_OIGI_REQUEST_TRACE_PREFIX}.build_lane_scope",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
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

    with commit_perf_span(
        phase=f"{_OIGI_REQUEST_TRACE_PREFIX}.build_function_call",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
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
    with commit_perf_span(
        phase=f"{_OIGI_REQUEST_TRACE_PREFIX}.build_invoke_input",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
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
    with commit_perf_span(
        phase=f"{_OIGI_REQUEST_TRACE_PREFIX}.build_index_view",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
        if index_view is not None and index_view.index is not index:
            raise ValueError(
                "MetaGraphRuntimeIndexView belongs to a different runtime index object"
            )
        request_index_view = index_view or MetaGraphRuntimeIndexView(index=index)
    with commit_perf_span(
        phase=f"{_OIGI_REQUEST_TRACE_PREFIX}.resolve_function_target",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
        resolved_target = request_index_view.resolve_function_target(function_id)
    with commit_perf_span(
        phase=f"{_OIGI_REQUEST_TRACE_PREFIX}.build_staged_call",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
        staged_call = MetaGraphStagedFunctionCall(
            resolved_target=resolved_target,
            lane_scope=lane_scope,
            function_call=function_call,
        )
    with commit_perf_span(
        phase=f"{_OIGI_REQUEST_TRACE_PREFIX}.build_execution_plan",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
        plan_trace_recorder = current_commit_perf_trace()
        plan_trace_event_start = (
            len(plan_trace_recorder.snapshot()) if plan_trace_recorder else 0
        )
        execution_plan = build_meta_graph_execution_plan(
            index=index,
            request=invoke_input,
            staged_call=staged_call,
            index_view=request_index_view,
        )
    _project_oigi_execution_plan_trace_events(
        recorder=plan_trace_recorder,
        event_start=plan_trace_event_start,
    )
    with commit_perf_span(
        phase=f"{_OIGI_REQUEST_TRACE_PREFIX}.build_handler_execution_request",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
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


def reset_invalid_object_instance_graph_identity_lane(
    *,
    aware_root: Path,
    branch_id: UUID,
    projection_hash: str,
) -> None:
    """Drop the rebuildable OIGI derived lane for one domain OIG/projection."""
    branch_dir = aware_root / ".aware" / "oig" / str(branch_id)
    lane_dir = branch_dir / projection_hash
    if lane_dir.exists():
        shutil.rmtree(lane_dir)
    get_shared_materialization_cache().invalidate_lane(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )


def _reset_invalid_object_instance_graph_identity_lane(
    *,
    aware_root: Path,
    branch_id: UUID,
    projection_hash: str,
) -> None:
    branch_dir = aware_root / ".aware" / "oig" / str(branch_id)
    reset_invalid_object_instance_graph_identity_lane(
        aware_root=aware_root,
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if branch_dir.exists() and not any(branch_dir.iterdir()):
        shutil.rmtree(branch_dir)


async def ensure_object_instance_graph_identity_lane_head(
    *,
    index: MetaGraphRuntimeIndex,
    index_view: MetaGraphRuntimeIndexView | None = None,
    object_instance_graph_id: UUID,
    domain_projection_hash: str,
    author_id: UUID,
    label: str | None = None,
    perf_ms: dict[str, int] | None = None,
    perf_metric_prefix: str = "ensure_oigi_lane",
) -> ObjectInstanceGraphIdentityLaneHeadEnsureResult:
    """Ensure the OIGI lane exists for `object_instance_graph_id`.

    This is a durability helper: it appends the first commit to the
    `object_instance_graph_identity` lane when missing.

    Notes:
    - Idempotent: no-op when the lane already has a HEAD commit.
    - Never creates/updates OIGB or environment topology (those are separate rails).
    """
    total_started = time.monotonic()
    trace_metadata = {
        "object_instance_graph_id": str(object_instance_graph_id),
        "domain_projection_hash": domain_projection_hash,
    }
    context_started = time.monotonic()
    with commit_perf_span(
        phase="runtime.invoke_function.ensure_identity_lane_head.resolve_context",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
        ctx = resolve_object_instance_graph_identity_lane_context(index=index)
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_resolve_context_ms",
        started=context_started,
    )
    if ctx is None:
        raise RuntimeError("Missing required OPG: object_instance_graph_identity")

    if not (ctx.projection_hash or "").strip():
        raise RuntimeError(
            "object_instance_graph_identity OPG has empty projection_hash"
        )

    # Canonical v1: the OIGI lane is routed by the boundary OIG id, but the
    # payload graph/root object is the canonical OIGI identity object.
    domain_oig_id = object_instance_graph_id

    identity_started = time.monotonic()
    with commit_perf_span(
        phase=(
            "runtime.invoke_function.ensure_identity_lane_head."
            "resolve_canonical_identity"
        ),
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
        root_cc_id = _resolve_root_class_config_id(opg=ctx.opg)

        # Canonical: OIGI must point at a compiler-owned OPGI (no synthesis).
        domain_opg = index.opg_by_hash.get(domain_projection_hash)
        if domain_opg is None:
            raise RuntimeError(
                "Missing required domain OPG for OIGI creation: "
                f"projection_hash={domain_projection_hash}"
            )

        _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
            index=index,
            projection_hash=domain_projection_hash,
        )
        if opgi is None:
            raise RuntimeError(
                "Missing required OPGI on runtime bundle: "
                f"projection_hash={domain_projection_hash}"
            )

        oigi_id = resolve_domain_object_instance_graph_identity_id(
            index=index,
            object_instance_graph_id=domain_oig_id,
            domain_projection_hash=domain_projection_hash,
        )
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_resolve_canonical_identity_ms",
        started=identity_started,
    )

    store_setup_started = time.monotonic()
    with commit_perf_span(
        phase="runtime.invoke_function.ensure_identity_lane_head.store_setup",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
        store = FSCommitStore()
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_store_setup_ms",
        started=store_setup_started,
    )

    head_started = time.monotonic()
    with commit_perf_span(
        phase="runtime.invoke_function.ensure_identity_lane_head.head_store_read",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
        head_raw = await store.head(
            branch_id=domain_oig_id,
            projection_hash=ctx.projection_hash,
        )
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_head_read_ms",
        started=head_started,
    )
    if perf_ms is not None:
        perf_ms[f"{perf_metric_prefix}_head_store_read_count"] = 1
    head = head_raw if isinstance(head_raw, Mapping) else None

    if head and head.get("commit_id"):
        validate_started = time.monotonic()
        with commit_perf_span(
            phase="runtime.invoke_function.ensure_identity_lane_head.validate_head",
            category="meta.runtime.invoke_function",
            metadata=trace_metadata,
        ):
            head_oig_id = _optional_uuid_from_mapping(head, "object_instance_graph_id")
            if head_oig_id is not None and head_oig_id != oigi_id:
                # This lane is deterministic and derived. If the persisted head
                # payload no longer matches the canonical OIGI id, recover by
                # dropping the stale lane so the current contract can reseed it.
                _reset_invalid_object_instance_graph_identity_lane(
                    aware_root=store.aware_root,
                    branch_id=object_instance_graph_id,
                    projection_hash=ctx.projection_hash,
                )
                head = None
        _record_perf(
            perf_ms,
            f"{perf_metric_prefix}_validate_head_ms",
            started=validate_started,
        )
        if head is not None:
            head_commit_id = _optional_uuid_from_mapping(head, "commit_id")
            head_oig_commit_id = _optional_uuid_from_mapping(
                head,
                "object_instance_graph_commit_id",
            )
            if perf_ms is not None:
                perf_ms[f"{perf_metric_prefix}_head_hit"] = 1
            _record_perf(
                perf_ms,
                f"{perf_metric_prefix}_total_ms",
                started=total_started,
            )
            return ObjectInstanceGraphIdentityLaneHeadEnsureResult(
                status="head_hit",
                branch_id=domain_oig_id,
                projection_hash=ctx.projection_hash,
                object_instance_graph_identity_id=oigi_id,
                object_instance_graph_id=head_oig_id or oigi_id,
                commit_id=head_commit_id,
                object_instance_graph_commit_id=head_oig_commit_id,
            )

    if label is None:
        label = f"oigi:{domain_oig_id.hex[:8]}"

    build_base_started = time.monotonic()
    with commit_perf_span(
        phase="runtime.invoke_function.ensure_identity_lane_head.build_base_oig",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
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

    with commit_perf_span(
        phase="runtime.invoke_function.ensure_identity_lane_head.build_handler_request",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
        handler_request = _build_object_instance_graph_identity_handler_request(
            index=index,
            index_view=index_view,
            ctx=ctx,
            before_oig=before_oig,
            root_cc_id=root_cc_id,
            opgi=opgi,
            domain_oig_id=domain_oig_id,
            oigi_id=oigi_id,
            author_id=author_id,
            label=label,
        )
    with commit_perf_span(
        phase="runtime.invoke_function.ensure_identity_lane_head.build_executor",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
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
    trace_recorder = current_commit_perf_trace()
    trace_event_start = len(trace_recorder.snapshot()) if trace_recorder else 0
    with commit_perf_span(
        phase=(
            "runtime.invoke_function.ensure_identity_lane_head."
            "execute_generated_handler"
        ),
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
        execution_result = await executor.execute_function(handler_request)
    _project_oigi_generated_execution_trace_events(
        recorder=trace_recorder,
        event_start=trace_event_start,
    )
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
        return ObjectInstanceGraphIdentityLaneHeadEnsureResult(
            status="no_changes",
            branch_id=domain_oig_id,
            projection_hash=ctx.projection_hash,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=before_oig.id,
        )

    commit_action = CommitActionDescriptor(
        operation_label="ObjectInstanceGraphIdentity.create",
        call_target="opg_constructor",
        function_id=handler_request.request.function_id,
        object_id=oigi_id,
    )
    committer = FSLaneCommitter(store=store)
    fs_commit_started = time.monotonic()
    with commit_perf_span(
        phase="runtime.invoke_function.ensure_identity_lane_head.fs_commit",
        category="meta.runtime.invoke_function",
        metadata=trace_metadata,
    ):
        oigi_lane_commit_record = await committer.commit_record_shallow(
            branch_id=domain_oig_id,
            projection_hash=ctx.projection_hash,
            object_projection_graph_identity_id=(
                handler_request.staged_call.lane_scope.object_projection_graph_identity_id
            ),
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=before_oig.id,
            pre_state_index=build_commit_state_index(before_oig),
            root_metadata=extract_object_instance_graph_commit_root_metadata(
                graph=before_oig,
            ),
            root_object_id=oigi_id,
            changes=list(changes),
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
    return ObjectInstanceGraphIdentityLaneHeadEnsureResult(
        status="created",
        branch_id=domain_oig_id,
        projection_hash=ctx.projection_hash,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=before_oig.id,
        commit_id=oigi_lane_commit_record.commit_id,
        object_instance_graph_commit_id=(
            oigi_lane_commit_record.object_instance_graph_commit_id
        ),
    )
