"""Meta-owned required commit reactions.

The receipt bus is intentionally best-effort observation. This module is the
fail-closed reaction rail for commit side effects that must exist before a
commit can be treated as replayable runtime truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Literal
from uuid import UUID

from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

from aware_meta.graph.instance.commit.fs_store import ObjectInstanceGraphCommitEnvelope
from aware_meta.runtime.commit.identity_history import (
    upsert_object_instance_graph_identity_history_from_domain_commit,
)
from aware_meta.runtime.commit.identity_lane import (
    resolve_object_instance_graph_identity_lane_context,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex


@dataclass(frozen=True, slots=True)
class RuntimeCommitReactionContext:
    index: MetaGraphRuntimeIndex
    actor_id: UUID
    domain_branch_id: UUID
    domain_projection_hash: str
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

        oigi_id = await upsert_object_instance_graph_identity_history_from_domain_commit(
            index=context.index,
            actor_id=context.actor_id,
            domain_branch_id=context.domain_branch_id,
            domain_projection_hash=context.domain_projection_hash,
            domain_commit=context.domain_commit,
            domain_commit_envelope=context.domain_commit_envelope,
            source_class_instance_identity_id=context.source_class_instance_identity_id,
            perf_ms=context.perf_ms,
            projector_mode=context.oigi_history_projector_mode,
        )
        return RuntimeCommitReactionReceipt(
            provider_key=self.provider_key,
            reaction_key=self.reaction_key,
            status="succeeded",
            details={"object_instance_graph_identity_id": str(oigi_id)},
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


MetaCommitReactionContext = RuntimeCommitReactionContext
MetaCommitReactionError = RuntimeCommitReactionError
MetaCommitReactionReceipt = RuntimeCommitReactionReceipt
run_required_meta_commit_reactions = run_required_runtime_commit_reactions


__all__ = [
    "MetaCommitReactionContext",
    "MetaCommitReactionError",
    "MetaCommitReactionReceipt",
    "RuntimeCommitReactionContext",
    "RuntimeCommitReactionError",
    "RuntimeCommitReactionReceipt",
    "run_required_meta_commit_reactions",
    "run_required_runtime_commit_reactions",
]
