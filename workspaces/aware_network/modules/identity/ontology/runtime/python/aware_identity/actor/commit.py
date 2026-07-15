from __future__ import annotations

from typing import TypeAlias, TypeVar
from uuid import UUID

from aware_identity_service_dto.actor.commit import (
    ActorCommitEnsureReceipt,
)
from aware_identity_service_dto.actor.commit import (
    ActorCommitEnsureRequest,
)
from aware_identity_service_dto.actor.commit import (
    ActorCommitRecord,
)
from aware_identity_service_dto.actor.commit import (
    ActorCommitResolveRequest,
)
from aware_identity_service_dto.actor.commit import (
    ActorCommitResolveResult,
)
from aware_identity_ontology.actor.actor_commit import ActorCommit
from aware_identity_ontology.identity.identity import Identity
from aware_identity_ontology.stable_ids import stable_actor_commit_id
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph as ObjectProjectionGraphModel,
)
from aware_meta.materialization.context import MaterializationRuntimeContext
from aware_identity.materialization.bootstrap import (
    resolve_actor_identity_binding,
)

_TRoot = TypeVar("_TRoot", bound=ActorCommit)

ActorCommitMaterializationContext: TypeAlias = MaterializationRuntimeContext


async def ensure_actor_commit(
    *,
    request: ActorCommitEnsureRequest,
    context: ActorCommitMaterializationContext | None = None,
) -> ActorCommitEnsureReceipt:
    projection_hash = _normalize_projection_hash(request.domain_projection_hash)
    actor_commit_id = stable_actor_commit_id(
        actor_id=request.actor_id,
        domain_branch_id=request.domain_branch_id,
        domain_projection_hash=projection_hash,
        domain_commit_id=request.domain_commit_id,
    )
    resolved_context = _require_actor_commit_context(context)

    actor_commit = await _resolve_actor_commit_by_id(
        context=resolved_context,
        actor_commit_id=actor_commit_id,
    )
    actor_commit_created = actor_commit is None
    if actor_commit is None:
        await _ensure_actor_commit_on_identity_lane(
            context=resolved_context,
            request=request,
            projection_hash=projection_hash,
        )
        actor_commit = await _resolve_actor_commit_by_id(
            context=resolved_context,
            actor_commit_id=actor_commit_id,
        )

    if actor_commit is None:
        raise RuntimeError(
            "ActorCommit materialization did not hydrate ActorCommit lane root: "
            + f"actor_commit_id={actor_commit_id}"
        )
    return ActorCommitEnsureReceipt(
        request_id=request.request_id,
        actor_commit=_record_from_actor_commit(actor_commit),
        actor_commit_created=actor_commit_created,
        info="identity actor-commit ensured",
    )


async def resolve_actor_commits(
    *,
    request: ActorCommitResolveRequest,
    context: ActorCommitMaterializationContext | None = None,
) -> ActorCommitResolveResult:
    resolved_context = _require_actor_commit_context(context)
    actor_commits = await _list_actor_commits(context=resolved_context)
    records = [
        _record_from_actor_commit(actor_commit)
        for actor_commit in actor_commits
        if _actor_commit_matches(actor_commit=actor_commit, request=request)
    ]
    records.sort(
        key=lambda record: (
            record.created_at_unix_ms if record.created_at_unix_ms is not None else -1,
            record.head_version if record.head_version is not None else -1,
            str(record.domain_commit_id),
        ),
        reverse=True,
    )
    return ActorCommitResolveResult(
        request_id=request.request_id,
        actor_commits=records[: _bounded_limit(request.limit)],
        info="identity actor-commits resolved",
    )


async def _resolve_actor_commit_by_id(
    *,
    context: ActorCommitMaterializationContext,
    actor_commit_id: UUID,
) -> ActorCommit | None:
    for actor_commit in await _list_actor_commits(context=context):
        if actor_commit.id == actor_commit_id:
            return actor_commit
    return None


async def _list_actor_commits(
    *,
    context: ActorCommitMaterializationContext,
) -> list[ActorCommit]:
    commit_store = FSCommitStore()
    identity_opg = _resolve_opg_by_name(context.index, name="Identity")
    actor_commits: list[ActorCommit] = []
    async for identity_branch_id, _ in commit_store.iter_lane_heads_by_projection(
        projection_hash=identity_opg.projection_hash,
    ):
        actor_commits.extend(
            await _materialize_identity_actor_commits(
                context=context,
                branch_id=identity_branch_id,
            )
        )
    return actor_commits


async def _materialize_identity_actor_commits(
    *,
    context: ActorCommitMaterializationContext,
    branch_id: UUID,
) -> list[ActorCommit]:
    identity_opg = _resolve_opg_by_name(context.index, name="Identity")
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=identity_opg.projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return []

    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=context.index.ocg,
        opg=identity_opg,
        commit_id=None,
        attribute_configs_by_id=context.index.attribute_configs_by_id,
        class_configs_by_id=context.index.class_configs_by_id,
    )
    actor_commits: list[ActorCommit] = []
    for actor_commit_id in _source_ids_for_class_name(
        index=context.index,
        oig=oig,
        class_name="ActorCommit",
    ):
        actor_commit = reify_oig_root_model(
            index=context.index,
            opg=identity_opg,
            oig=oig,
            model_type=ActorCommit,
            root_id=actor_commit_id,
            branch_id=branch_id,
        )
        if actor_commit is not None:
            actor_commits.append(actor_commit)
    return actor_commits


def _source_ids_for_class_name(
    *,
    index: MetaGraphRuntimeIndex,
    oig: object,
    class_name: str,
) -> list[UUID]:
    ids: list[UUID] = []
    for class_instance in getattr(oig, "class_instances", ()) or ():
        class_config = index.class_configs_by_id.get(
            getattr(class_instance, "class_config_id", None)
        )
        if class_config is None or not _class_config_matches_name(
            class_config=class_config,
            class_name=class_name,
        ):
            continue
        source_id = _uuid_or_none(getattr(class_instance, "source_object_id", None))
        if source_id is not None:
            ids.append(source_id)
    return ids


def _class_config_matches_name(*, class_config: object, class_name: str) -> bool:
    norm = class_name.strip()
    name = str(getattr(class_config, "name", "") or "").strip()
    if name == norm:
        return True
    class_fqn = str(getattr(class_config, "class_fqn", "") or "").strip()
    return class_fqn.endswith(f".{norm}")


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


async def _ensure_actor_commit_on_identity_lane(
    *,
    context: ActorCommitMaterializationContext,
    request: ActorCommitEnsureRequest,
    projection_hash: str,
) -> None:
    identity_branch_id, identity = await _materialize_identity_for_actor(
        context=context,
        actor_id=request.actor_id,
    )
    lane = context.bind_lane(
        projection="Identity",
        branch_id=identity_branch_id,
    )
    with lane.activate(commit=True, publish=False):
        actor = await identity.ensure_actor()
        if actor.id != request.actor_id:
            raise ValueError(
                "ActorCommit ensure resolved a different actor from the identity lane: "
                f"expected_actor_id={request.actor_id} got_actor_id={actor.id} "
                f"identity_id={identity.id}"
            )
        await actor.ensure_commit(
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=projection_hash,
            domain_commit_id=request.domain_commit_id,
            object_instance_graph_commit_id=request.object_instance_graph_commit_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            receipt_actor_id=request.receipt_actor_id,
            created_at_unix_ms=request.created_at_unix_ms,
            operation_label=request.operation_label,
            call_target=request.call_target,
            function_id=request.function_id,
            object_id=request.object_id,
            class_instance_identity_id=request.class_instance_identity_id,
            graph_hash_post=request.graph_hash_post,
            object_instance_graph_id=request.object_instance_graph_id,
            root_object_id=request.root_object_id,
            head_version=request.head_version,
            source=request.source,
        )


async def _materialize_identity_for_actor(
    *,
    context: ActorCommitMaterializationContext,
    actor_id: UUID,
) -> tuple[UUID, Identity]:
    identity_opg = _resolve_opg_by_name(context.index, name="Identity")
    binding = await resolve_actor_identity_binding(
        index=context.index,
        actor_id=actor_id,
        identity_projection_hash=identity_opg.projection_hash,
    )
    if binding is None:
        raise ValueError(f"missing identity lane for actor_id: {actor_id}")

    identity = await _materialize_lane_root(
        context=context,
        root_id=binding.identity_branch_id,
        projection_name="Identity",
        root_type=Identity,
    )
    if identity is None:
        raise ValueError(
            "identity lane could not be materialized for actor write: "
            f"actor_id={actor_id} identity_branch_id={binding.identity_branch_id}"
        )
    if identity.id != binding.identity_id:
        raise ValueError(
            "identity binding mismatch for actor write: "
            f"actor_id={actor_id} binding_identity_id={binding.identity_id} "
            f"lane_identity_id={identity.id}"
        )
    return binding.identity_branch_id, identity


def _record_from_actor_commit(actor_commit: ActorCommit) -> ActorCommitRecord:
    object_instance_graph_identity_id = None
    object_instance_graph_commit = actor_commit.object_instance_graph_commit
    if object_instance_graph_commit is not None:
        object_instance_graph_identity_id = (
            object_instance_graph_commit.object_instance_graph_identity_id
        )
    return ActorCommitRecord(
        actor_commit_id=actor_commit.id,
        actor_id=actor_commit.actor_id,
        domain_branch_id=actor_commit.domain_branch_id,
        domain_projection_hash=actor_commit.domain_projection_hash,
        domain_commit_id=actor_commit.domain_commit_id,
        object_instance_graph_commit_id=actor_commit.object_instance_graph_commit_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        environment_id=actor_commit.environment_id,
        process_id=actor_commit.process_id,
        thread_id=actor_commit.thread_id,
        receipt_actor_id=actor_commit.receipt_actor_id,
        created_at_unix_ms=actor_commit.created_at_unix_ms,
        operation_label=actor_commit.operation_label,
        call_target=actor_commit.call_target,
        function_id=actor_commit.function_id,
        object_id=actor_commit.object_id,
        class_instance_identity_id=actor_commit.class_instance_identity_id,
        graph_hash_post=actor_commit.graph_hash_post,
        object_instance_graph_id=actor_commit.object_instance_graph_id,
        root_object_id=actor_commit.root_object_id,
        head_version=actor_commit.head_version,
        source=actor_commit.source,
    )


def _actor_commit_matches(
    *,
    actor_commit: ActorCommit,
    request: ActorCommitResolveRequest,
) -> bool:
    if actor_commit.actor_id != request.actor_id:
        return False
    if (
        request.domain_branch_id is not None
        and actor_commit.domain_branch_id != request.domain_branch_id
    ):
        return False
    if request.domain_projection_hash is not None and _normalize_projection_hash(
        actor_commit.domain_projection_hash
    ) != _normalize_projection_hash(request.domain_projection_hash):
        return False
    if (
        request.domain_commit_id is not None
        and actor_commit.domain_commit_id != request.domain_commit_id
    ):
        return False
    if (
        request.environment_id is not None
        and actor_commit.environment_id != request.environment_id
    ):
        return False
    if request.process_id is not None and actor_commit.process_id != request.process_id:
        return False
    if request.thread_id is not None and actor_commit.thread_id != request.thread_id:
        return False
    if (
        request.receipt_actor_id is not None
        and actor_commit.receipt_actor_id != request.receipt_actor_id
    ):
        return False
    if (
        request.function_id is not None
        and actor_commit.function_id != request.function_id
    ):
        return False
    if request.object_id is not None and actor_commit.object_id != request.object_id:
        return False
    if (
        request.class_instance_identity_id is not None
        and actor_commit.class_instance_identity_id
        != request.class_instance_identity_id
    ):
        return False
    if (
        request.object_instance_graph_id is not None
        and actor_commit.object_instance_graph_id != request.object_instance_graph_id
    ):
        return False
    if (
        request.root_object_id is not None
        and actor_commit.root_object_id != request.root_object_id
    ):
        return False
    if request.source is not None and actor_commit.source != request.source:
        return False
    return True


async def _materialize_lane_root(
    *,
    context: ActorCommitMaterializationContext,
    root_id: UUID,
    projection_name: str,
    root_type: type[_TRoot],
) -> _TRoot | None:
    opg = _resolve_opg_by_name(context.index, name=projection_name)
    head = await FSCommitStore().head(
        branch_id=root_id,
        projection_hash=opg.projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None

    oig, _ = await OIGMaterializer().get(
        branch_id=root_id,
        ocg=context.index.ocg,
        opg=opg,
        commit_id=None,
        attribute_configs_by_id=context.index.attribute_configs_by_id,
        class_configs_by_id=context.index.class_configs_by_id,
    )
    root = reify_oig_root_model(
        index=context.index,
        opg=opg,
        oig=oig,
        model_type=root_type,
        root_id=root_id,
        branch_id=root_id,
    )
    if root is None:
        return None
    return root


def _resolve_opg_by_name(
    index: MetaGraphRuntimeIndex,
    *,
    name: str,
) -> ObjectProjectionGraphModel:
    norm = name.strip().casefold()
    matches = [
        opg
        for opg in index.opg_by_hash.values()
        if str(opg.name or "").strip().casefold() == norm
    ]
    if not matches:
        available = sorted(
            {
                str(opg.name or "").strip()
                for opg in index.opg_by_hash.values()
                if str(opg.name or "").strip()
            }
        )
        raise RuntimeError(f"OPG not found: name={name!r} (available={available})")
    if len(matches) > 1:
        raise RuntimeError(f"Duplicate OPG name={name!r} (count={len(matches)})")
    return matches[0]


def _normalize_projection_hash(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        raise ValueError("ActorCommit requires domain_projection_hash")
    return value


def _bounded_limit(raw: int | None) -> int:
    if raw is None:
        return 100
    return max(1, min(int(raw), 1000))


def _require_actor_commit_context(
    context: ActorCommitMaterializationContext | None,
) -> ActorCommitMaterializationContext:
    if context is None:
        raise ValueError("ActorCommit materialization context is required.")
    return context


__all__ = [
    "ActorCommitMaterializationContext",
    "ensure_actor_commit",
    "resolve_actor_commits",
]
