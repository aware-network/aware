"""Meta-owned required commit reactions.

The receipt bus is intentionally best-effort observation. This module is the
fail-closed reaction rail for commit side effects that must exist before a
commit can be treated as replayable runtime truth.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Literal, cast
from uuid import UUID

from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

from aware_meta.graph.instance.commit.contract import ObjectInstanceGraphCommitEnvelope
from aware_meta.graph.instance.commit.perf_trace import commit_perf_span
from aware_meta.runtime.commit_groups import MetaInvocationCommitGroupEntry
from aware_meta.runtime.commit.identity_history import (
    ObjectInstanceGraphIdentityHistoryDomainCommitBatchItem,
    ObjectInstanceGraphIdentityHistoryUpsertResult,
    upsert_object_instance_graph_identity_history_from_domain_commit_result,
    upsert_object_instance_graph_identity_history_from_domain_commit_results_batch,
)
from aware_meta.runtime.commit.identity_lane import (
    resolve_object_instance_graph_identity_lane_context,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.handler_executor.index import MetaGraphRuntimeIndexView


@dataclass(frozen=True, slots=True)
class RuntimeCommitReactionContext:
    index: MetaGraphRuntimeIndex
    actor_id: UUID
    domain_branch_id: UUID
    domain_projection_hash: str
    index_view: MetaGraphRuntimeIndexView | None = None
    domain_commit: ObjectInstanceGraphCommit | None = None
    domain_commit_envelope: ObjectInstanceGraphCommitEnvelope | None = None
    source_class_instance_identity_id: UUID | None = None
    perf_ms: dict[str, int] | None = None
    oigi_history_projector_mode: Literal["handler", "direct"] = "handler"


@dataclass(frozen=True, slots=True)
class RuntimeCommitReactionReceipt:
    provider_key: str
    reaction_key: str
    status: str
    details: dict[str, str] = field(default_factory=dict)
    commit_group_entries: tuple[MetaInvocationCommitGroupEntry, ...] = ()


class RuntimeCommitReactionError(RuntimeError):
    def __init__(
        self,
        *,
        provider_key: str,
        reaction_key: str,
        cause: Exception,
        receipts: tuple[RuntimeCommitReactionReceipt, ...],
    ) -> None:
        self.provider_key = provider_key
        self.reaction_key = reaction_key
        self.cause = cause
        self.receipts = receipts
        super().__init__(f"{provider_key}.{reaction_key} failed: {cause}")


class MetaObjectInstanceGraphIdentityHistoryReaction:
    provider_key = "aware_meta"
    reaction_key = "object_instance_graph_identity.history_upsert"

    async def run(
        self, context: RuntimeCommitReactionContext
    ) -> RuntimeCommitReactionReceipt:
        metadata = {
            "provider_key": self.provider_key,
            "reaction_key": self.reaction_key,
            "domain_branch_id": str(context.domain_branch_id),
            "domain_projection_hash": context.domain_projection_hash,
            "domain_commit_id": (
                str(context.domain_commit.id)
                if context.domain_commit is not None
                else None
            ),
        }
        with commit_perf_span(
            phase="runtime.invoke_function.required_commit_reactions.oigi_history.resolve_context",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            resolve_started_at = perf_counter()
            oigi_ctx = resolve_object_instance_graph_identity_lane_context(
                index=context.index
            )
        _record_elapsed_ms(
            context.perf_ms,
            "required_reaction_oigi_history_resolve_context_ms",
            resolve_started_at,
        )
        if oigi_ctx is None:
            return RuntimeCommitReactionReceipt(
                provider_key=self.provider_key,
                reaction_key=self.reaction_key,
                status="skipped",
                details={"reason": "missing_object_instance_graph_identity_projection"},
            )

        if context.domain_projection_hash == oigi_ctx.projection_hash:
            return RuntimeCommitReactionReceipt(
                provider_key=self.provider_key,
                reaction_key=self.reaction_key,
                status="skipped",
                details={"reason": "self_projection"},
            )

        with commit_perf_span(
            phase="runtime.invoke_function.required_commit_reactions.oigi_history.contract_check",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            contract_started_at = perf_counter()
            has_upsert_contract = _has_oigi_history_upsert_contract(
                context=context,
                root_class_config_id=_root_class_config_id(oigi_ctx.opg),
            )
        _record_elapsed_ms(
            context.perf_ms,
            "required_reaction_oigi_history_contract_check_ms",
            contract_started_at,
        )
        if not has_upsert_contract:
            return RuntimeCommitReactionReceipt(
                provider_key=self.provider_key,
                reaction_key=self.reaction_key,
                status="skipped",
                details={"reason": "history_upsert_contract_unavailable"},
            )

        with commit_perf_span(
            phase="runtime.invoke_function.required_commit_reactions.oigi_history.upsert_history",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            upsert_result = await (
                upsert_object_instance_graph_identity_history_from_domain_commit_result
            )(
                index=context.index,
                index_view=context.index_view,
                actor_id=context.actor_id,
                domain_branch_id=context.domain_branch_id,
                domain_projection_hash=context.domain_projection_hash,
                domain_commit=context.domain_commit,
                domain_commit_envelope=context.domain_commit_envelope,
                source_class_instance_identity_id=(
                    context.source_class_instance_identity_id
                ),
                perf_ms=context.perf_ms,
                projector_mode=context.oigi_history_projector_mode,
            )
        return _oigi_history_receipt_from_upsert_result(
            provider_key=self.provider_key,
            reaction_key=self.reaction_key,
            upsert_result=upsert_result,
        )

    async def run_batch(
        self,
        contexts: Sequence[RuntimeCommitReactionContext],
    ) -> tuple[RuntimeCommitReactionReceipt, ...]:
        context_tuple = tuple(contexts)
        if not context_tuple:
            return ()

        first_context = context_tuple[0]
        metadata = {
            "provider_key": self.provider_key,
            "reaction_key": self.reaction_key,
            "batch_context_count": len(context_tuple),
            "domain_branch_id": str(first_context.domain_branch_id),
            "domain_projection_hash": first_context.domain_projection_hash,
        }
        with commit_perf_span(
            phase=(
                "runtime.invoke_function.required_commit_reactions."
                "oigi_history.batch_resolve_context"
            ),
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            resolve_started_at = perf_counter()
            oigi_ctx = resolve_object_instance_graph_identity_lane_context(
                index=first_context.index
            )
        for context in context_tuple:
            _record_elapsed_ms(
                context.perf_ms,
                "required_reaction_oigi_history_resolve_context_ms",
                resolve_started_at,
            )
        if oigi_ctx is None:
            return tuple(
                RuntimeCommitReactionReceipt(
                    provider_key=self.provider_key,
                    reaction_key=self.reaction_key,
                    status="skipped",
                    details={
                        "reason": "missing_object_instance_graph_identity_projection"
                    },
                )
                for _ in context_tuple
            )

        if first_context.domain_projection_hash == oigi_ctx.projection_hash:
            return tuple(
                RuntimeCommitReactionReceipt(
                    provider_key=self.provider_key,
                    reaction_key=self.reaction_key,
                    status="skipped",
                    details={"reason": "self_projection"},
                )
                for _ in context_tuple
            )

        with commit_perf_span(
            phase=(
                "runtime.invoke_function.required_commit_reactions."
                "oigi_history.batch_contract_check"
            ),
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            contract_started_at = perf_counter()
            has_upsert_contract = _has_oigi_history_upsert_contract(
                context=first_context,
                root_class_config_id=_root_class_config_id(oigi_ctx.opg),
            )
        for context in context_tuple:
            _record_elapsed_ms(
                context.perf_ms,
                "required_reaction_oigi_history_contract_check_ms",
                contract_started_at,
            )
        if not has_upsert_contract:
            return tuple(
                RuntimeCommitReactionReceipt(
                    provider_key=self.provider_key,
                    reaction_key=self.reaction_key,
                    status="skipped",
                    details={"reason": "history_upsert_contract_unavailable"},
                )
                for _ in context_tuple
            )

        with commit_perf_span(
            phase="runtime.invoke_function.required_commit_reactions.oigi_history.upsert_history",
            category="meta.runtime.invoke_function",
            metadata={**metadata, "batch_context_count": len(context_tuple)},
        ):
            upsert_results = await upsert_object_instance_graph_identity_history_from_domain_commit_results_batch(
                index=first_context.index,
                index_view=first_context.index_view,
                actor_id=first_context.actor_id,
                domain_commits=tuple(
                    ObjectInstanceGraphIdentityHistoryDomainCommitBatchItem(
                        domain_branch_id=context.domain_branch_id,
                        domain_projection_hash=context.domain_projection_hash,
                        domain_commit=context.domain_commit,
                        domain_commit_envelope=context.domain_commit_envelope,
                        source_class_instance_identity_id=(
                            context.source_class_instance_identity_id
                        ),
                    )
                    for context in context_tuple
                ),
                perf_ms=first_context.perf_ms,
                projector_mode=first_context.oigi_history_projector_mode,
            )
        if len(upsert_results) != len(context_tuple):
            raise RuntimeError(
                "OIGI history batch returned an unexpected result count: "
                f"expected={len(context_tuple)} got={len(upsert_results)}"
            )
        return tuple(
            _oigi_history_receipt_from_upsert_result(
                provider_key=self.provider_key,
                reaction_key=self.reaction_key,
                upsert_result=upsert_result,
            )
            for upsert_result in upsert_results
        )


def _oigi_history_receipt_from_upsert_result(
    *,
    provider_key: str,
    reaction_key: str,
    upsert_result: ObjectInstanceGraphIdentityHistoryUpsertResult,
) -> RuntimeCommitReactionReceipt:
    details = {
        "object_instance_graph_identity_id": str(
            upsert_result.object_instance_graph_identity_id
        ),
        "upsert_status": upsert_result.status,
    }
    commit_group_entries: tuple[MetaInvocationCommitGroupEntry, ...] = ()
    if (
        upsert_result.status == "created"
        and upsert_result.branch_id is not None
        and upsert_result.projection_hash is not None
        and upsert_result.commit_id is not None
        and upsert_result.object_instance_graph_commit_id is not None
    ):
        details["commit_id"] = str(upsert_result.commit_id)
        details["object_instance_graph_commit_id"] = str(
            upsert_result.object_instance_graph_commit_id
        )
        commit_group_entries = (
            MetaInvocationCommitGroupEntry(
                role="oigi_history_commit",
                branch_id=upsert_result.branch_id,
                projection_hash=upsert_result.projection_hash,
                commit_id=upsert_result.commit_id,
                object_instance_graph_commit_id=(
                    upsert_result.object_instance_graph_commit_id
                ),
                object_instance_graph_identity_id=(
                    upsert_result.object_instance_graph_identity_id
                ),
                object_instance_graph_id=upsert_result.object_instance_graph_id,
                operation_label=(
                    "ObjectInstanceGraphIdentity.upsert_history_from_lane_head"
                ),
                provider_key=provider_key,
                reaction_key=reaction_key,
            ),
        )
    return RuntimeCommitReactionReceipt(
        provider_key=provider_key,
        reaction_key=reaction_key,
        status="succeeded",
        details=details,
        commit_group_entries=commit_group_entries,
    )


def _root_class_config_id(opg: object) -> UUID | None:
    nodes = getattr(opg, "object_projection_graph_nodes", None) or []
    for node in nodes:
        if bool(getattr(node, "is_root", False)):
            class_config_id = getattr(node, "class_config_id", None)
            return class_config_id if isinstance(class_config_id, UUID) else None
    if nodes:
        class_config_id = getattr(nodes[0], "class_config_id", None)
        return class_config_id if isinstance(class_config_id, UUID) else None
    return None


def _has_oigi_history_upsert_contract(
    *,
    context: RuntimeCommitReactionContext,
    root_class_config_id: UUID | None,
) -> bool:
    if root_class_config_id is None:
        return False
    for node in context.index.ocg.object_config_graph_nodes:
        cc = node.class_config
        if cc is None or cc.id != root_class_config_id:
            continue
        attr_names = {
            (link.attribute_config.name or "")
            for link in (cc.class_config_attribute_configs or [])
        }
        has_history_shape = {
            "object_instance_graph_branches",
            "object_instance_graph_commits",
        }.issubset(attr_names)
        has_upsert_function = any(
            link.function_config.name == "upsert_history_from_lane_head"
            for link in cc.class_config_function_configs
        )
        return has_history_shape and has_upsert_function
    return False


_REQUIRED_RUNTIME_COMMIT_REACTIONS = (MetaObjectInstanceGraphIdentityHistoryReaction(),)


def _metric_key(value: str) -> str:
    normalized = "".join(
        char if char.isalnum() else "_" for char in value.strip().lower()
    ).strip("_")
    return normalized or "unknown"


def _record_elapsed_ms(
    perf_ms: dict[str, int] | None,
    metric_name: str,
    started_at: float,
) -> None:
    if perf_ms is None:
        return
    perf_ms[metric_name] = int(round(max(perf_counter() - started_at, 0.0) * 1000.0))


async def run_required_runtime_commit_reactions(
    context: RuntimeCommitReactionContext,
) -> tuple[RuntimeCommitReactionReceipt, ...]:
    receipts: list[RuntimeCommitReactionReceipt] = []
    for reaction in _REQUIRED_RUNTIME_COMMIT_REACTIONS:
        reaction_started_at = perf_counter()
        metric_prefix = (
            "required_reaction_"
            f"{_metric_key(reaction.provider_key)}_"
            f"{_metric_key(reaction.reaction_key)}"
        )
        try:
            with commit_perf_span(
                phase=(
                    "runtime.invoke_function.required_commit_reactions."
                    f"{_metric_key(reaction.provider_key)}."
                    f"{_metric_key(reaction.reaction_key)}"
                ),
                category="meta.runtime.invoke_function",
                metadata={
                    "provider_key": reaction.provider_key,
                    "reaction_key": reaction.reaction_key,
                    "domain_branch_id": str(context.domain_branch_id),
                    "domain_projection_hash": context.domain_projection_hash,
                    "domain_commit_id": (
                        str(context.domain_commit.id)
                        if context.domain_commit is not None
                        else None
                    ),
                },
            ):
                receipt = await reaction.run(context)
        except Exception as exc:
            _record_elapsed_ms(
                context.perf_ms,
                f"{metric_prefix}_failed_ms",
                reaction_started_at,
            )
            raise RuntimeCommitReactionError(
                provider_key=reaction.provider_key,
                reaction_key=reaction.reaction_key,
                cause=exc,
                receipts=tuple(receipts),
            ) from exc
        _record_elapsed_ms(
            context.perf_ms,
            f"{metric_prefix}_total_ms",
            reaction_started_at,
        )
        receipts.append(receipt)
    return tuple(receipts)


async def run_required_runtime_commit_reactions_batch(
    contexts: Sequence[RuntimeCommitReactionContext],
) -> tuple[tuple[RuntimeCommitReactionReceipt, ...], ...]:
    context_tuple = tuple(contexts)
    if not context_tuple:
        return ()
    receipt_lists: list[list[RuntimeCommitReactionReceipt]] = [
        [] for _ in context_tuple
    ]
    for reaction in _REQUIRED_RUNTIME_COMMIT_REACTIONS:
        reaction_started_at = perf_counter()
        metric_prefix = (
            "required_reaction_"
            f"{_metric_key(reaction.provider_key)}_"
            f"{_metric_key(reaction.reaction_key)}"
        )
        try:
            with commit_perf_span(
                phase=(
                    "runtime.invoke_function.required_commit_reactions.batch."
                    f"{_metric_key(reaction.provider_key)}."
                    f"{_metric_key(reaction.reaction_key)}"
                ),
                category="meta.runtime.invoke_function",
                metadata={
                    "provider_key": reaction.provider_key,
                    "reaction_key": reaction.reaction_key,
                    "batch_context_count": len(context_tuple),
                    "domain_branch_id": str(context_tuple[0].domain_branch_id),
                    "domain_projection_hash": (context_tuple[0].domain_projection_hash),
                },
            ):
                batch_runner = getattr(reaction, "run_batch", None)
                if callable(batch_runner):
                    receipts = await cast(Any, batch_runner)(context_tuple)
                else:
                    receipt_batches: list[tuple[RuntimeCommitReactionReceipt, ...]] = []
                    for context in context_tuple:
                        receipt_batches.append((await reaction.run(context),))
                    receipts = tuple(receipt_batches)
        except Exception as exc:
            for context in context_tuple:
                _record_elapsed_ms(
                    context.perf_ms,
                    f"{metric_prefix}_batch_failed_ms",
                    reaction_started_at,
                )
            raise RuntimeCommitReactionError(
                provider_key=reaction.provider_key,
                reaction_key=reaction.reaction_key,
                cause=exc,
                receipts=tuple(receipt_lists[0]),
            ) from exc
        if len(receipts) != len(context_tuple):
            raise RuntimeCommitReactionError(
                provider_key=reaction.provider_key,
                reaction_key=reaction.reaction_key,
                cause=RuntimeError(
                    "Required commit reaction batch returned an unexpected "
                    f"receipt count: expected={len(context_tuple)} got={len(receipts)}"
                ),
                receipts=tuple(receipt_lists[0]),
            )
        for context, receipt_list, receipt in zip(
            context_tuple,
            receipt_lists,
            receipts,
            strict=True,
        ):
            _record_elapsed_ms(
                context.perf_ms,
                f"{metric_prefix}_batch_total_ms",
                reaction_started_at,
            )
            if isinstance(receipt, RuntimeCommitReactionReceipt):
                receipt_list.append(receipt)
            else:
                receipt_list.extend(receipt)
    return tuple(tuple(receipts) for receipts in receipt_lists)


MetaCommitReactionContext = RuntimeCommitReactionContext
MetaCommitReactionError = RuntimeCommitReactionError
MetaCommitReactionReceipt = RuntimeCommitReactionReceipt
run_required_meta_commit_reactions = run_required_runtime_commit_reactions
run_required_meta_commit_reactions_batch = run_required_runtime_commit_reactions_batch


__all__ = [
    "MetaCommitReactionContext",
    "MetaCommitReactionError",
    "MetaCommitReactionReceipt",
    "RuntimeCommitReactionContext",
    "RuntimeCommitReactionError",
    "RuntimeCommitReactionReceipt",
    "run_required_meta_commit_reactions",
    "run_required_meta_commit_reactions_batch",
    "run_required_runtime_commit_reactions",
    "run_required_runtime_commit_reactions_batch",
]
