from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_layout_graph_binding import (
    ProjectionExperienceLayoutGraphBinding,
)
from aware_interface_ontology.interface.app_config import AppConfig
from aware_interface_ontology.interface.app_config_screen_config import (
    AppConfigScreenConfig,
)
from aware_interface_ontology.interface.app_package import AppPackage
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.portal_lane_resolution import (
    MetaPortalResolvedLaneRef,
    resolve_portal_target_lane_ref_for_object,
)


@dataclass(frozen=True, slots=True)
class CommittedAppScreenEntryRequest:
    app_package_id: UUID
    app_package_branch_id: UUID
    app_package_object_instance_graph_commit_id: UUID
    app_config_screen_config_id: UUID


@dataclass(frozen=True, slots=True)
class CommittedAppScreenEntryResolution:
    app_package_id: UUID
    app_package_branch_id: UUID
    app_package_object_instance_graph_commit_id: UUID
    app_config_id: UUID
    app_config_object_instance_graph_commit_id: UUID
    app_config_screen_config_id: UUID
    screen_key: str
    projection_experience_id: UUID
    projection_experience_branch_id: UUID
    projection_experience_head_commit_id: UUID
    projection_experience_layout_graph_binding_id: UUID
    experience_name: str
    layout_binding_key: str


class AppScreenEntryResolutionError(RuntimeError):
    """Raised when committed App screen evidence does not resolve exactly."""


async def resolve_committed_app_screen_entry(
    *,
    index: MetaGraphRuntimeIndex,
    request: CommittedAppScreenEntryRequest,
) -> CommittedAppScreenEntryResolution:
    app_package_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="AppPackage",
    )
    app_package_session = await _replay_projection(
        index=index,
        branch_id=request.app_package_branch_id,
        projection_hash=app_package_projection_hash,
        commit_id=request.app_package_object_instance_graph_commit_id,
    )
    app_package = _require_unique_object(
        session=app_package_session,
        model_type=AppPackage,
        object_id=request.app_package_id,
        label="AppPackage",
    )
    app_config_id = _required_uuid(
        app_package.app_config_id,
        label="AppPackage.app_config_id",
    )
    app_config_commit_id = _required_uuid(
        app_package.app_config_object_instance_graph_commit_id,
        label="AppPackage.app_config_object_instance_graph_commit_id",
    )

    app_config_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="AppConfig",
    )
    app_config_lane = await resolve_portal_target_lane_ref_for_object(
        index=index,
        source_domain_branch_id=request.app_package_branch_id,
        source_projection_hash=app_package_projection_hash,
        target_projection_hash=app_config_projection_hash,
        target_class_config_id=_class_config_id(
            index=index,
            class_name="AppConfig",
        ),
        target_object_id=app_config_id,
    )
    app_config_session = await _replay_projection(
        index=index,
        branch_id=app_config_lane.target_branch_id,
        projection_hash=app_config_projection_hash,
        commit_id=app_config_commit_id,
    )
    app_config = _require_unique_object(
        session=app_config_session,
        model_type=AppConfig,
        object_id=app_config_id,
        label="AppConfig",
    )
    screen = _require_screen(
        app_config=app_config,
        screen_id=request.app_config_screen_config_id,
    )

    projection_experience_id = _required_uuid(
        screen.projection_experience_id,
        label="AppConfigScreenConfig.projection_experience_id",
    )
    layout_binding_id = _required_uuid(
        screen.projection_experience_layout_graph_binding_id,
        label=(
            "AppConfigScreenConfig." "projection_experience_layout_graph_binding_id"
        ),
    )
    projection_experience_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperience",
    )
    projection_experience_lane = await resolve_portal_target_lane_ref_for_object(
        index=index,
        source_domain_branch_id=app_config_lane.target_branch_id,
        source_projection_hash=app_config_projection_hash,
        target_projection_hash=projection_experience_hash,
        target_class_config_id=_class_config_id(
            index=index,
            class_name="ProjectionExperience",
        ),
        target_object_id=projection_experience_id,
    )
    projection_experience_session = await _replay_portal_target(
        index=index,
        lane_ref=projection_experience_lane,
    )
    projection_experience = _require_unique_object(
        session=projection_experience_session,
        model_type=ProjectionExperience,
        object_id=projection_experience_id,
        label="ProjectionExperience",
    )
    layout_binding_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperienceLayoutGraphBinding",
    )
    layout_binding_lane = await resolve_portal_target_lane_ref_for_object(
        index=index,
        source_domain_branch_id=app_config_lane.target_branch_id,
        source_projection_hash=app_config_projection_hash,
        target_projection_hash=layout_binding_hash,
        target_class_config_id=_class_config_id(
            index=index,
            class_name="ProjectionExperienceLayoutGraphBinding",
        ),
        target_object_id=layout_binding_id,
    )
    layout_binding_session = await _replay_portal_target(
        index=index,
        lane_ref=layout_binding_lane,
    )
    layout_binding = _require_unique_object(
        session=layout_binding_session,
        model_type=ProjectionExperienceLayoutGraphBinding,
        object_id=layout_binding_id,
        label="ProjectionExperienceLayoutGraphBinding",
    )
    if layout_binding.projection_experience_id != projection_experience.id:
        raise AppScreenEntryResolutionError(
            "App screen layout binding does not belong to its committed "
            "ProjectionExperience: "
            f"layout_binding_id={layout_binding.id} "
            f"have={layout_binding.projection_experience_id} "
            f"expected={projection_experience.id}"
        )

    return CommittedAppScreenEntryResolution(
        app_package_id=app_package.id,
        app_package_branch_id=request.app_package_branch_id,
        app_package_object_instance_graph_commit_id=(
            request.app_package_object_instance_graph_commit_id
        ),
        app_config_id=app_config.id,
        app_config_object_instance_graph_commit_id=app_config_commit_id,
        app_config_screen_config_id=screen.id,
        screen_key=_required_text(screen.screen_key, label="screen_key"),
        projection_experience_id=projection_experience.id,
        projection_experience_branch_id=(projection_experience_lane.target_branch_id),
        projection_experience_head_commit_id=(
            projection_experience_lane.target_head_commit_id
        ),
        projection_experience_layout_graph_binding_id=layout_binding.id,
        experience_name=_required_text(
            projection_experience.name,
            label="ProjectionExperience.name",
        ),
        layout_binding_key=_required_text(
            layout_binding.binding_key,
            label="ProjectionExperienceLayoutGraphBinding.binding_key",
        ),
    )


async def _replay_projection(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    expected_graph_hash: str | None = None,
):
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise AppScreenEntryResolutionError(
            "App screen replay projection is missing from runtime index: "
            f"projection_hash={projection_hash}"
        )
    try:
        oig, _ = await OIGMaterializer(commits=FSCommitStore()).get(
            branch_id=branch_id,
            ocg=index.ocg,
            opg=opg,
            commit_id=commit_id,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
    except Exception as exc:
        raise AppScreenEntryResolutionError(
            "Committed App screen projection replay failed: "
            f"branch_id={branch_id} projection_hash={projection_hash} "
            f"commit_id={commit_id}"
        ) from exc
    if expected_graph_hash is not None and oig.hash != expected_graph_hash:
        raise AppScreenEntryResolutionError(
            "Committed App screen projection graph hash does not match portal "
            "evidence: "
            f"branch_id={branch_id} projection_hash={projection_hash} "
            f"expected={expected_graph_hash} actual={oig.hash}"
        )
    return reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )


async def _replay_portal_target(
    *,
    index: MetaGraphRuntimeIndex,
    lane_ref: MetaPortalResolvedLaneRef,
):
    head = await FSCommitStore().head(
        branch_id=lane_ref.target_branch_id,
        projection_hash=lane_ref.target_projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        raise AppScreenEntryResolutionError(
            "Committed App screen portal target has no lane HEAD: "
            f"branch_id={lane_ref.target_branch_id} "
            f"projection_hash={lane_ref.target_projection_hash}"
        )
    head_commit_id = UUID(str(head["commit_id"]))
    if head_commit_id != lane_ref.target_head_commit_id:
        raise AppScreenEntryResolutionError(
            "Committed App screen portal target HEAD changed during resolution: "
            f"branch_id={lane_ref.target_branch_id} "
            f"portal_head={lane_ref.target_head_commit_id} "
            f"actual_head={head_commit_id}"
        )
    return await _replay_projection(
        index=index,
        branch_id=lane_ref.target_branch_id,
        projection_hash=lane_ref.target_projection_hash,
        commit_id=head_commit_id,
        expected_graph_hash=lane_ref.target_graph_hash_post,
    )


def _require_unique_object(
    *,
    session: object,
    model_type: type,
    object_id: UUID,
    label: str,
):
    matches = tuple(
        obj
        for obj in session.imap_all_objects()
        if isinstance(obj, model_type) and obj.id == object_id
    )
    if len(matches) != 1:
        raise AppScreenEntryResolutionError(
            f"Committed {label} evidence must resolve exactly once: "
            f"object_id={object_id} matches={len(matches)}"
        )
    return matches[0]


def _require_screen(
    *,
    app_config: AppConfig,
    screen_id: UUID,
) -> AppConfigScreenConfig:
    matches = tuple(
        screen
        for screen in app_config.screen_configs
        if screen.id == screen_id and screen.app_config_id == app_config.id
    )
    if len(matches) != 1:
        raise AppScreenEntryResolutionError(
            "Committed AppConfigScreenConfig must be contained by the pinned "
            f"AppConfig: app_config_id={app_config.id} "
            f"screen_id={screen_id} matches={len(matches)}"
        )
    return matches[0]


def _class_config_id(
    *,
    index: MetaGraphRuntimeIndex,
    class_name: str,
) -> UUID:
    matches = tuple(
        class_config
        for class_config in index.class_configs_by_id.values()
        if str(getattr(class_config, "name", "") or "") == class_name
        or str(getattr(class_config, "class_fqn", "") or "").endswith(f".{class_name}")
    )
    if len(matches) != 1 or matches[0].id is None:
        raise AppScreenEntryResolutionError(
            "Committed App screen target class config must resolve exactly "
            f"once: class_name={class_name!r} matches={len(matches)}"
        )
    return matches[0].id


def _required_uuid(value: object, *, label: str) -> UUID:
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise AppScreenEntryResolutionError(
            f"Committed App screen evidence is missing {label}"
        ) from exc


def _required_text(value: object, *, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise AppScreenEntryResolutionError(
            f"Committed App screen evidence is missing {label}"
        )
    return text


__all__ = [
    "AppScreenEntryResolutionError",
    "CommittedAppScreenEntryRequest",
    "CommittedAppScreenEntryResolution",
    "resolve_committed_app_screen_entry",
]
