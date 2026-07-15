from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import UUID

from aware_meta.runtime.commit.required_reactions import (
    RuntimeCommitReactionContext,
    RuntimeCommitReactionReceipt,
    run_required_runtime_commit_reactions_batch,
    run_required_runtime_commit_reactions,
)
from aware_meta.graph.instance.commit.perf_trace import commit_perf_span
from aware_meta.runtime.invocation_commit_actions import MetaInvocationCommitAction
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.handler_executor.index import MetaGraphRuntimeIndexView
from aware_orm.session.execution_guard import (
    reset_mutation_owner,
    set_mutation_owner,
)


InvocationRequiredReactionRunner = Callable[
    [RuntimeCommitReactionContext],
    Awaitable[tuple[RuntimeCommitReactionReceipt, ...]],
]
InvocationRequiredReactionBatchRunner = Callable[
    [tuple[RuntimeCommitReactionContext, ...]],
    Awaitable[tuple[tuple[RuntimeCommitReactionReceipt, ...], ...]],
]


@dataclass(frozen=True, slots=True)
class InvocationRequiredReactionBatchItem:
    index: MetaGraphRuntimeIndex
    actor_id: UUID
    domain_branch_id: UUID
    domain_projection_hash: str
    domain_commit: ObjectInstanceGraphCommit
    index_view: MetaGraphRuntimeIndexView | None = None
    action: MetaInvocationCommitAction | None = None
    source_class_instance_identity_id: UUID | None = None
    perf_ms: dict[str, int] | None = None


async def run_invocation_required_commit_reactions(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    domain_commit: ObjectInstanceGraphCommit,
    index_view: MetaGraphRuntimeIndexView | None = None,
    action: MetaInvocationCommitAction | None = None,
    source_class_instance_identity_id: UUID | None = None,
    perf_ms: dict[str, int] | None = None,
    runner: InvocationRequiredReactionRunner = run_required_runtime_commit_reactions,
) -> tuple[RuntimeCommitReactionReceipt, ...]:
    metadata = {
        "domain_branch_id": str(domain_branch_id),
        "domain_projection_hash": domain_projection_hash,
        "domain_commit_id": str(domain_commit.id),
        "operation_label": action.operation_label if action is not None else None,
    }
    with commit_perf_span(
        phase="runtime.invoke_function.required_commit_reactions.resolve_source_identity",
        category="meta.runtime.invoke_function",
        metadata=metadata,
    ):
        source_identity_id = source_class_instance_identity_id
        if source_identity_id is None and action is not None:
            source_identity_id = action.class_instance_identity_id

    with commit_perf_span(
        phase="runtime.invoke_function.required_commit_reactions.set_mutation_owner",
        category="meta.runtime.invoke_function",
        metadata=metadata,
    ):
        token = set_mutation_owner(None)
    try:
        with commit_perf_span(
            phase="runtime.invoke_function.required_commit_reactions.runner",
            category="meta.runtime.invoke_function",
            metadata={
                **metadata,
                "source_class_instance_identity_id": (
                    str(source_identity_id) if source_identity_id is not None else None
                ),
            },
        ):
            return await runner(
                RuntimeCommitReactionContext(
                    index=index,
                    index_view=index_view,
                    actor_id=actor_id,
                    domain_branch_id=domain_branch_id,
                    domain_projection_hash=domain_projection_hash,
                    domain_commit=domain_commit,
                    source_class_instance_identity_id=source_identity_id,
                    perf_ms=perf_ms,
                )
            )
    finally:
        with commit_perf_span(
            phase="runtime.invoke_function.required_commit_reactions.reset_mutation_owner",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            reset_mutation_owner(token)


async def run_invocation_required_commit_reactions_batch(
    *,
    items: tuple[InvocationRequiredReactionBatchItem, ...],
    runner: InvocationRequiredReactionBatchRunner = (
        run_required_runtime_commit_reactions_batch
    ),
) -> tuple[tuple[RuntimeCommitReactionReceipt, ...], ...]:
    if not items:
        return ()
    metadata = {
        "batch_context_count": len(items),
        "domain_branch_id": str(items[0].domain_branch_id),
        "domain_projection_hash": items[0].domain_projection_hash,
        "domain_commit_id": str(items[0].domain_commit.id),
        "operation_label": (
            items[0].action.operation_label if items[0].action is not None else None
        ),
    }
    contexts: list[RuntimeCommitReactionContext] = []
    with commit_perf_span(
        phase=(
            "runtime.invoke_function.required_commit_reactions."
            "batch_resolve_source_identity"
        ),
        category="meta.runtime.invoke_function",
        metadata=metadata,
    ):
        for item in items:
            source_identity_id = item.source_class_instance_identity_id
            if source_identity_id is None and item.action is not None:
                source_identity_id = item.action.class_instance_identity_id
            contexts.append(
                RuntimeCommitReactionContext(
                    index=item.index,
                    index_view=item.index_view,
                    actor_id=item.actor_id,
                    domain_branch_id=item.domain_branch_id,
                    domain_projection_hash=item.domain_projection_hash,
                    domain_commit=item.domain_commit,
                    source_class_instance_identity_id=source_identity_id,
                    perf_ms=item.perf_ms,
                )
            )

    with commit_perf_span(
        phase="runtime.invoke_function.required_commit_reactions.batch_set_mutation_owner",
        category="meta.runtime.invoke_function",
        metadata=metadata,
    ):
        token = set_mutation_owner(None)
    try:
        with commit_perf_span(
            phase="runtime.invoke_function.required_commit_reactions.batch_runner",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            receipts = await runner(tuple(contexts))
    finally:
        with commit_perf_span(
            phase=(
                "runtime.invoke_function.required_commit_reactions."
                "batch_reset_mutation_owner"
            ),
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            reset_mutation_owner(token)
    if len(receipts) != len(items):
        raise RuntimeError(
            "Invocation required reaction batch returned an unexpected receipt count: "
            f"expected={len(items)} got={len(receipts)}"
        )
    return receipts


__all__ = [
    "InvocationRequiredReactionBatchItem",
    "InvocationRequiredReactionBatchRunner",
    "InvocationRequiredReactionRunner",
    "run_invocation_required_commit_reactions_batch",
    "run_invocation_required_commit_reactions",
]
