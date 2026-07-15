from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from aware_code.types import JsonArray, JsonObject
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.environment.experience_package import (
    ExperiencePackage,
)
from aware_experience_ontology.projection.projection_experience_layout_graph_binding import (
    ProjectionExperienceLayoutGraphBinding,
)
from aware_experience.materialization.branches import (
    derive_experience_reference_branch_id,
)
from aware_interface.manifest.app_spec import (
    AwareAppSourceSpec,
    AwareAppTomlSpec,
)
from aware_interface.materialization.snapshot_commit import (
    AppConfigScreenSnapshotRef,
    AppConfigSnapshotCommitResult,
    AppPackageExperiencePackageSnapshotRef,
    AppPackageInterfacePackageSnapshotRef,
    AppPackageManifestSnapshotCommitResult,
    commit_app_config_snapshot,
    commit_app_package_manifest_snapshot,
)
from aware_interface_ontology.stable_ids import stable_interface_package_id
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_id,
    stable_object_instance_graph_identity_id,
)
from aware_meta.runtime import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.author import resolve_meta_author_id
from aware_meta.runtime.commit.identity_lane import (
    ensure_object_instance_graph_identity_lane_head,
)
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oigb_relationship_lane import attach_oigb_relationship
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.portal_lane_resolution import (
    MetaPortalResolvedLaneRef,
    resolve_portal_target_lane_refs,
)


@dataclass(frozen=True, slots=True)
class AppExperiencePackageReference:
    package_name: str
    experience_package_id: UUID
    semantic_branch_id: UUID
    semantic_head_commit_id: UUID
    aware_root: Path
    experience_package_object_instance_graph_commit_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class AppPackageMaterializationResult:
    app_config_snapshot: AppConfigSnapshotCommitResult
    app_package_snapshot: AppPackageManifestSnapshotCommitResult
    resolved_screens: tuple[AppConfigScreenSnapshotRef, ...]


@dataclass(frozen=True, slots=True)
class _ResolvedAppScreen:
    snapshot_ref: AppConfigScreenSnapshotRef
    projection_experience_branch_id: UUID
    projection_experience_layout_graph_binding_branch_id: UUID
    experience_aware_root: Path


class AppScreenResolutionError(RuntimeError):
    """Raised when an authored App screen cannot resolve committed Experience truth."""


async def materialize_app_package_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    manifest_path: Path,
    spec: AwareAppTomlSpec,
    app_source: AwareAppSourceSpec,
    source_code_package_id: UUID | None,
    experience_package_references: tuple[AppExperiencePackageReference, ...],
) -> AppPackageMaterializationResult:
    declared_experience_packages = {
        dependency.package_name.casefold(): dependency
        for dependency in spec.dependencies
        if dependency.kind == "experience_package"
    }
    if not declared_experience_packages:
        raise AppScreenResolutionError(
            "App package materialization requires at least one declared "
            "ExperiencePackage dependency."
        )
    references_by_package_name = _references_by_package_name(
        experience_package_references=experience_package_references,
        declared_experience_packages=frozenset(declared_experience_packages),
    )
    for reference in references_by_package_name.values():
        await _validate_experience_package_reference(
            index=index,
            reference=reference,
        )
    resolved_screen_entries = tuple(
        [
            await _resolve_screen(
                index=index,
                screen_key=screen.screen_key,
                projection_experience_name=screen.projection_experience,
                layout_binding_key=screen.projection_experience_layout,
                experience_package_references=tuple(
                    references_by_package_name.values()
                ),
            )
            for screen in app_source.screens
        ]
    )
    resolved_screens = tuple(entry.snapshot_ref for entry in resolved_screen_entries)

    app_config_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="AppConfig",
    )
    app_config_snapshot = await commit_app_config_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=app_config_projection_hash,
        name=app_source.name,
        title=app_source.title,
        description=app_source.description,
        screen_refs=resolved_screens,
    )

    app_package_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="AppPackage",
    )
    manifest_relative_path = _relative_to_workspace(
        path=manifest_path,
        workspace_root=workspace_root,
    )
    package_root = _relative_to_workspace(
        path=manifest_path.parent,
        workspace_root=workspace_root,
    )
    experience_package_refs = tuple(
        AppPackageExperiencePackageSnapshotRef(
            experience_package_id=reference.experience_package_id,
            experience_package_object_instance_graph_commit_id=(
                _experience_package_object_instance_graph_commit_id(
                    index=index,
                    reference=reference,
                )
            ),
            role=declared_experience_packages[reference.package_name.casefold()].role,
        )
        for reference in references_by_package_name.values()
    )
    interface_package_refs = tuple(
        AppPackageInterfacePackageSnapshotRef(
            interface_package_id=stable_interface_package_id(
                name=interface.package_name
            ),
            role=interface.role,
        )
        for interface in spec.interfaces
    )
    app_package_snapshot = await commit_app_package_manifest_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=app_package_projection_hash,
        name=spec.app.package_name,
        app_config_id=app_config_snapshot.app_config.id,
        app_config_object_instance_graph_commit_id=(
            app_config_snapshot.object_instance_graph_commit_id
        ),
        source_code_package_id=source_code_package_id,
        version_number=spec.app.version_number,
        title=spec.app.title,
        description=spec.app.description,
        aware_app_version=spec.aware_app,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        dependencies=JsonArray(
            [
                {
                    "package_name": dependency.package_name,
                    "kind": dependency.kind,
                    "role": dependency.role,
                }
                for dependency in spec.dependencies
            ]
        ),
        dart=JsonObject(
            {
                "package_name": spec.dart.package_name,
                "package_path": spec.dart.package_path,
                "entrypoint": spec.dart.entrypoint,
                "factory_package_name": spec.factory.package_name,
            }
        ),
        metadata_json=JsonObject(
            {
                "app_name": spec.app.app_name,
                "source_path": app_source.source_path,
            }
        ),
        experience_package_refs=experience_package_refs,
        interface_package_refs=interface_package_refs,
    )
    await _attach_committed_app_portals(
        index=index,
        actor_id=actor_id,
        app_branch_id=branch_id,
        app_config_projection_hash=app_config_projection_hash,
        app_package_projection_hash=app_package_projection_hash,
        resolved_screen_entries=resolved_screen_entries,
        experience_package_references=tuple(references_by_package_name.values()),
    )
    return AppPackageMaterializationResult(
        app_config_snapshot=app_config_snapshot,
        app_package_snapshot=app_package_snapshot,
        resolved_screens=resolved_screens,
    )


def _references_by_package_name(
    *,
    experience_package_references: tuple[AppExperiencePackageReference, ...],
    declared_experience_packages: frozenset[str],
) -> dict[str, AppExperiencePackageReference]:
    resolved: dict[str, AppExperiencePackageReference] = {}
    for reference in experience_package_references:
        package_name = reference.package_name.strip().casefold()
        if package_name not in declared_experience_packages:
            continue
        existing = resolved.get(package_name)
        if existing is not None and existing != reference:
            raise AppScreenResolutionError(
                "Conflicting committed ExperiencePackage references for app: "
                f"package_name={reference.package_name!r}"
            )
        resolved[package_name] = reference
    missing = sorted(declared_experience_packages - set(resolved))
    if missing:
        raise AppScreenResolutionError(
            "App package is missing committed ExperiencePackage dependencies: "
            f"package_names={missing!r}"
        )
    return resolved


async def _resolve_screen(
    *,
    index: MetaGraphRuntimeIndex,
    screen_key: str,
    projection_experience_name: str,
    layout_binding_key: str,
    experience_package_references: tuple[AppExperiencePackageReference, ...],
) -> _ResolvedAppScreen:
    normalized_experience_name = projection_experience_name.strip().casefold()
    matches = tuple(
        match
        for match in [
            await _resolve_screen_in_experience_package(
                index=index,
                screen_key=screen_key,
                projection_experience_name=projection_experience_name,
                layout_binding_key=layout_binding_key,
                reference=reference,
            )
            for reference in experience_package_references
        ]
        if match is not None
    )
    if len(matches) != 1:
        raise AppScreenResolutionError(
            "App screen must resolve through exactly one declared committed "
            "ExperiencePackage dependency: "
            f"screen_key={screen_key!r} "
            f"projection_experience={projection_experience_name!r} "
            f"layout={layout_binding_key!r} matches={len(matches)}"
        )
    return matches[0]


async def _resolve_screen_in_experience_package(
    *,
    index: MetaGraphRuntimeIndex,
    screen_key: str,
    projection_experience_name: str,
    layout_binding_key: str,
    reference: AppExperiencePackageReference,
) -> _ResolvedAppScreen | None:
    normalized_experience_name = projection_experience_name.strip().casefold()
    projection_branch_id = derive_experience_reference_branch_id(
        base_branch_id=reference.semantic_branch_id,
        experience_name=normalized_experience_name,
    )
    session = await _hydrate_projection_experience_session(
        index=index,
        reference=reference,
        projection_branch_id=projection_branch_id,
    )
    if session is None:
        return None
    experiences = tuple(
        obj
        for obj in session.imap_all_objects()
        if isinstance(obj, ProjectionExperience)
        and (obj.name or "").strip().casefold() == normalized_experience_name
    )
    if not experiences:
        return None
    if len(experiences) != 1:
        raise AppScreenResolutionError(
            "App screen requires exactly one committed ProjectionExperience: "
            f"screen_key={screen_key!r} "
            f"projection_experience={projection_experience_name!r} "
            f"package_name={reference.package_name!r} matches={len(experiences)}"
        )
    experience = experiences[0]
    normalized_layout_binding_key = layout_binding_key.strip().casefold()
    projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperience",
    )
    layout_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperienceLayoutGraphBinding",
    )
    portal_refs = await resolve_portal_target_lane_refs(
        index=index,
        source_domain_branch_id=projection_branch_id,
        source_projection_hash=projection_hash,
        target_projection_hash=layout_projection_hash,
        source_store=FSCommitStore(root_dir=reference.aware_root),
        target_store=FSCommitStore(root_dir=reference.aware_root),
    )
    layout_binding_entries: list[
        tuple[ProjectionExperienceLayoutGraphBinding, MetaPortalResolvedLaneRef]
    ] = []
    for portal_ref in portal_refs:
        layout_bindings = await _hydrate_layout_graph_bindings_from_portal(
            index=index,
            reference=reference,
            portal_ref=portal_ref,
        )
        layout_binding_entries.extend(
            (layout_binding, portal_ref)
            for layout_binding in layout_bindings
            if layout_binding.projection_experience_id == experience.id
            and (layout_binding.binding_key or "").strip().casefold()
            == normalized_layout_binding_key
        )
    if len(layout_binding_entries) != 1:
        raise AppScreenResolutionError(
            "App screen requires exactly one committed "
            "ProjectionExperienceLayoutGraphBinding: "
            f"screen_key={screen_key!r} "
            f"projection_experience={projection_experience_name!r} "
            f"layout={layout_binding_key!r} "
            f"package_name={reference.package_name!r} "
            f"matches={len(layout_binding_entries)}"
        )
    layout_binding, layout_portal_ref = layout_binding_entries[0]
    return _ResolvedAppScreen(
        snapshot_ref=AppConfigScreenSnapshotRef(
            screen_key=screen_key,
            projection_experience_id=experience.id,
            projection_experience_layout_graph_binding_id=layout_binding.id,
        ),
        projection_experience_branch_id=projection_branch_id,
        projection_experience_layout_graph_binding_branch_id=(
            layout_portal_ref.target_branch_id
        ),
        experience_aware_root=reference.aware_root,
    )


async def _attach_committed_app_portals(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    app_branch_id: UUID,
    app_config_projection_hash: str,
    app_package_projection_hash: str,
    resolved_screen_entries: tuple[_ResolvedAppScreen, ...],
    experience_package_references: tuple[AppExperiencePackageReference, ...],
) -> None:
    author_id = resolve_meta_author_id(actor_id)
    await _ensure_app_portal_source_identity(
        index=index,
        author_id=author_id,
        branch_id=app_branch_id,
        projection_hash=app_package_projection_hash,
        label="app_package_portal_source",
    )
    await _ensure_app_portal_source_identity(
        index=index,
        author_id=author_id,
        branch_id=app_branch_id,
        projection_hash=app_config_projection_hash,
        label="app_config_portal_source",
    )
    await attach_oigb_relationship(
        index=index,
        author_id=author_id,
        source_domain_branch_id=app_branch_id,
        source_projection_hash=app_package_projection_hash,
        target_domain_branch_id=app_branch_id,
        target_projection_hash=app_config_projection_hash,
    )
    app_store = FSCommitStore()

    projection_experience_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperience",
    )
    for target_branch_id, target_aware_root in sorted(
        {
            (
                entry.projection_experience_branch_id,
                entry.experience_aware_root,
            )
            for entry in resolved_screen_entries
        },
        key=lambda item: (str(item[0]), item[1].as_posix()),
    ):
        await attach_oigb_relationship(
            index=index,
            author_id=author_id,
            source_domain_branch_id=app_branch_id,
            source_projection_hash=app_config_projection_hash,
            target_domain_branch_id=target_branch_id,
            target_projection_hash=projection_experience_hash,
            source_store=app_store,
            target_store=FSCommitStore(root_dir=target_aware_root),
        )

    layout_graph_binding_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperienceLayoutGraphBinding",
    )
    for target_branch_id, target_aware_root in sorted(
        {
            (
                entry.projection_experience_layout_graph_binding_branch_id,
                entry.experience_aware_root,
            )
            for entry in resolved_screen_entries
        },
        key=lambda item: (str(item[0]), item[1].as_posix()),
    ):
        await attach_oigb_relationship(
            index=index,
            author_id=author_id,
            source_domain_branch_id=app_branch_id,
            source_projection_hash=app_config_projection_hash,
            target_domain_branch_id=target_branch_id,
            target_projection_hash=layout_graph_binding_hash,
            source_store=app_store,
            target_store=FSCommitStore(root_dir=target_aware_root),
        )

    experience_package_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ExperiencePackage",
    )
    for reference in sorted(
        experience_package_references,
        key=lambda item: (item.package_name.casefold(), str(item.semantic_branch_id)),
    ):
        await attach_oigb_relationship(
            index=index,
            author_id=author_id,
            source_domain_branch_id=app_branch_id,
            source_projection_hash=app_package_projection_hash,
            target_domain_branch_id=reference.semantic_branch_id,
            target_projection_hash=experience_package_hash,
            source_store=app_store,
            target_store=FSCommitStore(root_dir=reference.aware_root),
        )


async def _ensure_app_portal_source_identity(
    *,
    index: MetaGraphRuntimeIndex,
    author_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    label: str,
) -> None:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None or opg.id is None:
        raise AppScreenResolutionError(
            "App portal source projection is missing from runtime index: "
            f"projection_hash={projection_hash}"
        )
    object_instance_graph_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(branch_id),
    )
    await ensure_object_instance_graph_identity_lane_head(
        index=index,
        object_instance_graph_id=object_instance_graph_id,
        domain_projection_hash=projection_hash,
        author_id=author_id,
        label=label,
    )


async def _hydrate_projection_experience_session(
    *,
    index: MetaGraphRuntimeIndex,
    reference: AppExperiencePackageReference,
    projection_branch_id: UUID,
):
    projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperience",
    )
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise AppScreenResolutionError(
            "App screen resolution missing ProjectionExperience projection: "
            f"projection_hash={projection_hash}"
        )
    store = FSCommitStore(root_dir=reference.aware_root)
    head = await store.head(
        branch_id=projection_branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None
    oig, _ = await OIGMaterializer(commits=store).get(
        branch_id=projection_branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(head["commit_id"])),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=projection_branch_id,
    )


async def _hydrate_layout_graph_bindings_from_portal(
    *,
    index: MetaGraphRuntimeIndex,
    reference: AppExperiencePackageReference,
    portal_ref: MetaPortalResolvedLaneRef,
) -> tuple[ProjectionExperienceLayoutGraphBinding, ...]:
    projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperienceLayoutGraphBinding",
    )
    if portal_ref.target_projection_hash != projection_hash:
        raise AppScreenResolutionError(
            "App screen layout portal resolved an unexpected projection: "
            f"expected={projection_hash} actual={portal_ref.target_projection_hash}"
        )
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise AppScreenResolutionError(
            "App screen resolution missing ProjectionExperienceLayoutGraphBinding "
            f"projection: projection_hash={projection_hash}"
        )
    store = FSCommitStore(root_dir=reference.aware_root)
    head = await store.head(
        branch_id=portal_ref.target_branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        raise AppScreenResolutionError(
            "App screen layout portal target has no committed lane HEAD: "
            f"branch_id={portal_ref.target_branch_id} "
            f"projection_hash={projection_hash}"
        )
    head_commit_id = UUID(str(head["commit_id"]))
    if head_commit_id != portal_ref.target_head_commit_id:
        raise AppScreenResolutionError(
            "App screen layout portal target HEAD changed during resolution: "
            f"branch_id={portal_ref.target_branch_id} "
            f"portal_head={portal_ref.target_head_commit_id} actual_head={head_commit_id}"
        )
    oig, _ = await OIGMaterializer(commits=store).get(
        branch_id=portal_ref.target_branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=head_commit_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    if oig.hash != portal_ref.target_graph_hash_post:
        raise AppScreenResolutionError(
            "App screen layout portal target graph hash does not match committed "
            "portal evidence: "
            f"branch_id={portal_ref.target_branch_id} "
            f"portal_hash={portal_ref.target_graph_hash_post} actual_hash={oig.hash}"
        )
    session = reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=portal_ref.target_branch_id,
    )
    bindings = tuple(
        obj
        for obj in session.imap_all_objects()
        if isinstance(obj, ProjectionExperienceLayoutGraphBinding)
        and (
            portal_ref.target_root_object_id is None
            or obj.id == portal_ref.target_root_object_id
        )
    )
    if len(bindings) != 1:
        raise AppScreenResolutionError(
            "App screen layout portal target must contain exactly one committed "
            "ProjectionExperienceLayoutGraphBinding root: "
            f"branch_id={portal_ref.target_branch_id} matches={len(bindings)}"
        )
    return bindings


def _experience_package_object_instance_graph_commit_id(
    *,
    index: MetaGraphRuntimeIndex,
    reference: AppExperiencePackageReference,
) -> UUID:
    projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ExperiencePackage",
    )
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None or opg.id is None:
        raise AppScreenResolutionError(
            "App package resolution missing ExperiencePackage projection: "
            f"projection_hash={projection_hash}"
        )
    _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=projection_hash,
    )
    if opgi is None:
        raise AppScreenResolutionError(
            "App package resolution missing ExperiencePackage projection identity."
        )
    domain_oig_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(reference.semantic_branch_id),
    )
    oigi_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi.id,
        object_instance_graph_id=domain_oig_id,
    )
    resolved = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=oigi_id,
        commit_id=reference.semantic_head_commit_id,
    )
    supplied = reference.experience_package_object_instance_graph_commit_id
    if supplied is not None and supplied != resolved:
        raise AppScreenResolutionError(
            "ExperiencePackage ObjectInstanceGraphCommit evidence does not match "
            "its semantic branch/head: "
            f"package_name={reference.package_name!r} "
            f"supplied={supplied} resolved={resolved}"
        )
    return resolved


async def _validate_experience_package_reference(
    *,
    index: MetaGraphRuntimeIndex,
    reference: AppExperiencePackageReference,
) -> None:
    projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ExperiencePackage",
    )
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise AppScreenResolutionError(
            "App package resolution missing ExperiencePackage projection: "
            f"projection_hash={projection_hash}"
        )
    store = FSCommitStore(root_dir=reference.aware_root)
    commit = await store.get_commit(
        branch_id=reference.semantic_branch_id,
        projection_hash=projection_hash,
        commit_id=reference.semantic_head_commit_id,
    )
    if commit is None:
        raise AppScreenResolutionError(
            "App package dependency does not resolve its committed "
            "ExperiencePackage head: "
            f"package_name={reference.package_name!r} "
            f"branch_id={reference.semantic_branch_id} "
            f"commit_id={reference.semantic_head_commit_id}"
        )
    oig, _ = await OIGMaterializer(commits=store).get(
        branch_id=reference.semantic_branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=reference.semantic_head_commit_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    session = reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=reference.semantic_branch_id,
    )
    packages = tuple(
        obj
        for obj in session.imap_all_objects()
        if isinstance(obj, ExperiencePackage)
        and obj.id == reference.experience_package_id
        and (obj.name or "").strip().casefold()
        == reference.package_name.strip().casefold()
    )
    if len(packages) != 1:
        raise AppScreenResolutionError(
            "Committed ExperiencePackage reference does not match package identity: "
            f"package_name={reference.package_name!r} "
            f"experience_package_id={reference.experience_package_id} "
            f"matches={len(packages)}"
        )


def _relative_to_workspace(*, path: Path, workspace_root: Path) -> str:
    resolved_path = path.expanduser().resolve()
    resolved_root = workspace_root.expanduser().resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(
            "App package path resolved outside Workspace boundary: "
            f"workspace_root={resolved_root} path={resolved_path}"
        ) from exc
    return relative.as_posix() or "."


__all__ = [
    "AppExperiencePackageReference",
    "AppPackageMaterializationResult",
    "AppScreenResolutionError",
    "materialize_app_package_snapshot",
]
