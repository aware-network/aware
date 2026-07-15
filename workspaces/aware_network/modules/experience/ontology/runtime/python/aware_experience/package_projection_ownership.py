from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from aware_experience.compiler.models import ExperienceProjectionExperienceOwnership

from aware_experience.compiler.workspace import ExperienceWorkspace
from aware_experience.environment_profile.compiler import (
    load_environment_profile_ownership_from_sources,
)
from aware_experience.program.compiler import (
    load_program_ownership_from_sources,
    select_program_source_files,
)
from aware_experience.projection.compiler import (
    load_projection_experience_ownership_from_sources,
)
from aware_experience_service_dto.experience.package_materialization.models import (
    ExperiencePackageProjectionConsumerRef,
    ExperiencePackageProjectionNodeContract,
    ExperiencePackageProjectionOwnershipCatalog,
    ExperiencePackageProjectionOwnershipEntry,
)


def resolve_experience_package_projection_ownership_catalog(
    *,
    workspace_root: Path,
    experience_toml_path: Path,
) -> ExperiencePackageProjectionOwnershipCatalog:
    snapshot = ExperienceWorkspace.from_toml(
        toml_path=experience_toml_path,
        repo_root=workspace_root,
    ).build_snapshot()
    projection_ownerships = load_projection_experience_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
    )
    consumers_by_projection_name = _projection_consumers_by_name(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
        fqn_prefix=snapshot.spec.experience.fqn_prefix,
        projection_ownerships=projection_ownerships,
    )
    known_projection_names = {
        ownership.name.casefold(): ownership.name for ownership in projection_ownerships
    }
    missing_required_refs = tuple(
        sorted(
            {
                consumer.ref
                for ref, consumers in consumers_by_projection_name.items()
                if ref.casefold() not in known_projection_names
                for consumer in consumers
                if consumer.required
            },
            key=str.casefold,
        )
    )
    entries = tuple(
        ExperiencePackageProjectionOwnershipEntry(
            experience_name=ownership.name,
            target_projection=ownership.projection,
            source_path=ownership.source_path,
            status="declared",
            nodes=[
                ExperiencePackageProjectionNodeContract(
                    name=node.name,
                    node_ref=node.node_ref,
                    identity_keys=[
                        identity.key
                        for identity in node.identities
                        if identity.key.strip()
                    ],
                )
                for node in ownership.nodes
            ],
            consumers=consumers_by_projection_name.get(
                ownership.name.casefold(),
                [],
            ),
            evidence={
                "observable_count": len(ownership.observables),
                "branch_count": len(ownership.branches),
                "section_surface_count": len(ownership.section_surfaces),
            },
        )
        for ownership in sorted(
            projection_ownerships,
            key=lambda item: item.name.casefold(),
        )
    )
    return ExperiencePackageProjectionOwnershipCatalog(
        package_name=snapshot.spec.experience.package_name,
        fqn_prefix=snapshot.spec.experience.fqn_prefix,
        experience_name=entries[0].experience_name if entries else None,
        workspace_root=workspace_root.expanduser().resolve().as_posix(),
        experience_toml_path=experience_toml_path.expanduser().resolve().as_posix(),
        status="resolved" if not missing_required_refs else "missing_required",
        entries=list(entries),
        missing_required_projection_refs=list(missing_required_refs),
        evidence={
            "source_file_count": len(snapshot.source_files),
            "projection_experience_count": len(projection_ownerships),
        },
    )


def _projection_consumers_by_name(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    fqn_prefix: str,
    projection_ownerships: tuple[ExperienceProjectionExperienceOwnership, ...],
) -> dict[str, list[ExperiencePackageProjectionConsumerRef]]:
    consumers_by_name: dict[str, list[ExperiencePackageProjectionConsumerRef]] = {}
    _add_program_port_consumers(
        consumers_by_name=consumers_by_name,
        package_root=package_root,
        source_files=source_files,
        fqn_prefix=fqn_prefix,
        projection_ownerships=projection_ownerships,
    )
    _add_environment_profile_consumers(
        consumers_by_name=consumers_by_name,
        package_root=package_root,
        source_files=source_files,
        projection_ownerships=projection_ownerships,
    )
    return consumers_by_name


def _add_program_port_consumers(
    *,
    consumers_by_name: dict[str, list[ExperiencePackageProjectionConsumerRef]],
    package_root: Path,
    source_files: tuple[Path, ...],
    fqn_prefix: str,
    projection_ownerships: tuple[ExperienceProjectionExperienceOwnership, ...],
) -> None:
    program_ownerships = load_program_ownership_from_sources(
        package_root=package_root,
        source_files=select_program_source_files(source_files),
        fqn_prefix=fqn_prefix,
        projection_experience_ownership=projection_ownerships,
    )
    for program in program_ownerships:
        artifact = program.program_config_plan_artifact
        if artifact is None:
            continue
        plan = _mapping_or_empty(artifact.get("plan"))
        for port in _list_or_empty(plan.get("ports")):
            port_data = _mapping_or_empty(port)
            projection_ref = str(port_data.get("projection") or "").strip()
            port_key = str(port_data.get("key") or "").strip()
            if not projection_ref:
                continue
            _append_consumer(
                consumers_by_name=consumers_by_name,
                projection_ref=projection_ref,
                consumer=ExperiencePackageProjectionConsumerRef(
                    kind="program_port",
                    ref=projection_ref,
                    source_path=program.path,
                    required=True,
                    program_ref=program.ref,
                    program_name=program.name,
                    port_key=port_key or None,
                ),
            )


def _add_environment_profile_consumers(
    *,
    consumers_by_name: dict[str, list[ExperiencePackageProjectionConsumerRef]],
    package_root: Path,
    source_files: tuple[Path, ...],
    projection_ownerships: tuple[ExperienceProjectionExperienceOwnership, ...],
) -> None:
    profile_ownerships = load_environment_profile_ownership_from_sources(
        package_root=package_root,
        source_files=source_files,
        projection_experience_ownership=projection_ownerships,
    )
    for profile in profile_ownerships:
        for process in profile.process_configs:
            for thread in process.thread_configs:
                for projection in thread.projection_experiences:
                    projection_ref = projection.projection_experience_name
                    _append_consumer(
                        consumers_by_name=consumers_by_name,
                        projection_ref=projection_ref,
                        consumer=ExperiencePackageProjectionConsumerRef(
                            kind="profile_projection",
                            ref=projection_ref,
                            source_path=projection.source_path,
                            required=True,
                            profile_key=profile.key,
                            thread_key=thread.key,
                        ),
                    )
                for layout in thread.layout_configs:
                    for section in layout.sections:
                        projection_ref = section.projection_experience_name
                        _append_consumer(
                            consumers_by_name=consumers_by_name,
                            projection_ref=projection_ref,
                            consumer=ExperiencePackageProjectionConsumerRef(
                                kind="profile_layout_section",
                                ref=projection_ref,
                                source_path=section.source_path,
                                required=True,
                                profile_key=profile.key,
                                thread_key=thread.key,
                                layout_key=layout.layout_key,
                                section_key=section.section_key,
                            ),
                        )
        for transition in profile.view_event_transitions:
            for projection_ref in (
                transition.source_projection_experience_name,
                transition.target_projection_experience_name,
            ):
                _append_consumer(
                    consumers_by_name=consumers_by_name,
                    projection_ref=projection_ref,
                    consumer=ExperiencePackageProjectionConsumerRef(
                        kind="profile_view_event_transition",
                        ref=projection_ref,
                        source_path=transition.source_path,
                        required=True,
                        profile_key=profile.key,
                    ),
                )


def _append_consumer(
    *,
    consumers_by_name: dict[str, list[ExperiencePackageProjectionConsumerRef]],
    projection_ref: str,
    consumer: ExperiencePackageProjectionConsumerRef,
) -> None:
    normalized_ref = projection_ref.strip().casefold()
    if not normalized_ref:
        return
    consumers_by_name.setdefault(normalized_ref, []).append(consumer)


def _mapping_or_empty(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _list_or_empty(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    return []
