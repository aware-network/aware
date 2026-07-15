from __future__ import annotations

import shutil
from typing import Protocol, TypeVar
from uuid import UUID

from aware_code_ontology.package.code_package import CodePackage
from aware_experience_ontology.environment.environment_experience import (
    EnvironmentExperience,
)
from aware_experience_ontology.environment.experience_package import ExperiencePackage
from aware_experience_ontology.environment.experience_package_attention_package import (
    ExperiencePackageAttentionPackage,
)
from aware_experience_ontology.environment.experience_package_dependency import (
    ExperiencePackageDependency,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    get_shared_materialization_cache,
)
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.validator_opg import (
    validate_object_instance_graph_against_opg,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_orm.session.session import Session
from aware_utils.logging import logger

_TRoot = TypeVar("_TRoot", EnvironmentExperience, ExperiencePackage, CodePackage)


class ProjectionViewKeyResolver(Protocol):
    def __call__(self, *, projection_session: Session) -> object: ...


def reset_generated_projection_lane(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
) -> None:
    branch_dir = store.aware_root / ".aware" / "oig" / str(branch_id)
    lane_dir = branch_dir / projection_hash
    if lane_dir.exists():
        shutil.rmtree(lane_dir)
    get_shared_materialization_cache().invalidate_lane(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if branch_dir.exists() and not any(branch_dir.iterdir()):
        shutil.rmtree(branch_dir)


async def reset_stale_generated_projection_lane_if_needed(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    error_context: str,
) -> bool:
    store = FSCommitStore()
    head = await store.head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return False

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"{error_context} missing projection hash: {projection_hash}"
        )

    try:
        oig, _ = await OIGMaterializer(commits=store).get(
            branch_id=branch_id,
            ocg=index.ocg,
            opg=opg,
            commit_id=None,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
        validate_object_instance_graph_against_opg(
            graph=oig,
            object_config_graph=index.ocg,
            object_projection_graph=opg,
        )
    except Exception as exc:
        reset_generated_projection_lane(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        logger.warning(
            "%s reset stale generated projection lane: branch_id=%s projection_hash=%s error=%s",
            error_context,
            branch_id,
            projection_hash,
            exc,
        )
        return True
    return False


async def reset_projection_lane_with_duplicate_view_keys_if_needed(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    error_context: str,
    view_ids_by_projection_key_resolver: ProjectionViewKeyResolver,
) -> bool:
    store = FSCommitStore()
    head = await store.head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return False

    if not callable(view_ids_by_projection_key_resolver):
        raise RuntimeError(
            "Experience lane-state reset requires a callable view key resolver"
        )

    try:
        projection_session = await hydrate_lane_session(
            index=index,
            branch_id=branch_id,
            projection_hash=projection_hash,
            error_context=error_context,
        )
        view_ids_by_projection_key_resolver(projection_session=projection_session)
    except RuntimeError as exc:
        if "duplicate committed ProjectionExperienceView keys" not in str(exc):
            raise
        reset_generated_projection_lane(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        logger.warning(
            "%s reset generated ProjectionExperience lane with duplicate view keys: "
            "branch_id=%s projection_hash=%s error=%s",
            error_context,
            branch_id,
            projection_hash,
            exc,
        )
        return True
    return False


async def hydrate_lane_session(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    error_context: str,
) -> Session:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        raise RuntimeError(f"{error_context} requires a committed lane head")

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"{error_context} missing projection hash: {projection_hash}"
        )

    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=None,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    session = reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )
    return session


async def hydrate_lane_root_from_head(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    root_id: UUID | None,
    root_type: type[_TRoot],
) -> _TRoot | None:
    if root_id is None:
        return None

    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"Experience package materialization missing projection hash: {projection_hash}"
        )

    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=None,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    session = reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )
    resolved_root = session.imap_get(root_type, root_id)
    if resolved_root is not None:
        if isinstance(resolved_root, ExperiencePackage):
            hydrate_experience_package_dependency_lists(
                session=session,
                experience_package=resolved_root,
            )
        return resolved_root

    return None


def hydrate_experience_package_dependency_lists(
    *,
    session: Session,
    experience_package: ExperiencePackage,
) -> None:
    package_id = experience_package.id
    if package_id is None:
        return
    existing_attention_ids = {
        dependency.id
        for dependency in experience_package.attention_packages
        if dependency.id is not None
    }
    for obj in session.imap_all_objects():
        if not isinstance(obj, ExperiencePackageAttentionPackage):
            continue
        if obj.experience_package_id != package_id or obj.id in existing_attention_ids:
            continue
        experience_package.attention_packages.append(obj)
        if obj.id is not None:
            existing_attention_ids.add(obj.id)
    existing_ids = {
        dependency.id
        for dependency in experience_package.experience_package_dependencies
        if dependency.id is not None
    }
    for obj in session.imap_all_objects():
        if not isinstance(obj, ExperiencePackageDependency):
            continue
        if obj.experience_package_id != package_id or obj.id in existing_ids:
            continue
        experience_package.experience_package_dependencies.append(obj)
        if obj.id is not None:
            existing_ids.add(obj.id)


async def lane_head_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
) -> UUID | None:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None:
        return None
    raw_commit_id = head.get("commit_id")
    if raw_commit_id is None:
        return None
    if isinstance(raw_commit_id, UUID):
        return raw_commit_id
    return UUID(str(raw_commit_id))


__all__ = [
    "hydrate_experience_package_dependency_lists",
    "hydrate_lane_root_from_head",
    "hydrate_lane_session",
    "lane_head_commit_id",
    "ProjectionViewKeyResolver",
    "reset_generated_projection_lane",
    "reset_projection_lane_with_duplicate_view_keys_if_needed",
    "reset_stale_generated_projection_lane_if_needed",
]
