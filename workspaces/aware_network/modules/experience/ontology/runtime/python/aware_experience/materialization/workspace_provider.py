from __future__ import annotations

import ast
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import tomllib
from uuid import UUID

from aware_code.semantic_materialization import (
    SemanticPackageMaterializationEmittedPackageOutput,
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationObjectIdentity,
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationResult,
)
from aware_code.stable_ids import (
    code_package_generated_config_key,
    stable_code_package_config_id,
    stable_code_package_id,
)
from aware_types import JsonObject
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaAuthorityKind,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
    CodePackageDeltaProducerRef,
    CodePackageDeltaProduction,
    CodePackagePathRole,
)
from aware_environment_ontology_dto.stable_ids import (
    stable_environment_config_id,
    stable_environment_profile_config_id,
)
from aware_experience_ontology_dto.stable_ids import (
    stable_environment_experience_id,
    stable_environment_experience_profile_config_id,
)
from aware_experience.compiler.compile import compile_experience_workspace
from aware_experience.compiler.models import (
    ExperienceCompilePlan,
    ExperienceConnectorConfigOwnership,
    ExperienceConnectorInvocationActionConfigOwnership,
    ExperienceConnectorProviderOwnership,
    ExperienceSensorConfigOwnership,
    ExperienceActuatorConfigOwnership,
    ExperienceProjectionExperienceOwnership,
    ExperienceViewStateModelContract,
)
from aware_experience.connector.compiler import (
    load_connector_ownership_from_sources,
)
from aware_experience.connector.protocol_renderer import (
    build_connector_protocol_plan,
    render_python_connector_protocol_module,
)
from aware_experience.language_contracts import (
    ExperienceLanguageContractPackage,
    materialize_experience_language_contracts,
)
from aware_experience.materialization import (
    materialize_experience_package_from_manifest,
    resolve_experience_profile_publication_summary,
)
from aware_experience.materialization.branches import (
    derive_experience_reference_branch_id,
)
from aware_experience.materialization.service import (
    ConnectorConfigMaterializationSpec,
    resolve_connector_config_materialization_specs,
)
from aware_experience.projection.compiler import (
    load_projection_experience_ownership_from_sources,
)
from aware_experience.semantic_contract import (
    EXPERIENCE_PROVIDER_OWNER,
    EXPERIENCE_VIEW_API_COMPILE_PLAN_OUTPUT_KEY,
    EXPERIENCE_VIEW_API_PACKAGE_OUTPUT_KEY,
    EXPERIENCE_VIEW_API_PRODUCER_KEY,
    EXPERIENCE_VIEW_API_RUNTIME_CONTRACT_VERSION,
    EXPERIENCE_VIEW_API_TARGET_INPUT_KEY,
    EXPERIENCE_VIEW_API_TARGET_PROVIDER_KEY,
    EXPERIENCE_VIEW_API_TARGET_SEMANTIC_OWNER,
)
from aware_experience.view_contracts import (
    load_view_state_model_contracts_from_sources,
)
from aware_experience.view_api import (
    build_experience_view_api_ownership,
    emit_experience_view_api_compile_plan_artifact,
)

_FULL_REBUILD_FALLBACK_REASON = (
    "Experience provider has not implemented delta materialization yet; "
    "replayed the full Experience package manifest."
)
_LANGUAGE_CONTRACT_PRODUCER_KEY = "aware_experience.language_contract"
_LANGUAGE_CONTRACT_OUTPUT_KEY = "experience.language_contract.generated_code_packages"
_LANGUAGE_CONTRACT_ARTIFACT_FAMILY = "experience_language_contract"
_LANGUAGE_CONTRACT_MATERIALIZATION_SOURCE = "experience"
_LANGUAGE_CONTRACT_RENDERER_KIND = "language_contract"
_LANGUAGE_CONTRACT_SURFACE = "runtime"
_LANGUAGE_TARGET_PRODUCER_KEY = "aware_experience.language_target"
_LANGUAGE_TARGET_OUTPUT_KEY = "experience.language_target.code_package"
_LANGUAGE_TARGET_ARTIFACT_FAMILY = "experience_language_target"
_CONNECTOR_PROTOCOL_MODULE_RELATIVE_PATH = "connector_protocols.py"
_DIRECT_CODE_PACKAGE_EXCLUDED_DIR_NAMES = frozenset(
    {
        ".aware",
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".svn",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "venv",
    }
)
_DIRECT_CODE_PACKAGE_EXCLUDED_SUFFIXES = frozenset({".pyc", ".pyo"})


@dataclass(frozen=True, slots=True)
class _ExperienceRuntimeTargetPackage:
    language: str
    package_name: str
    import_root: str
    package_root: Path
    relpath: str
    manifest_relative_path: str
    sources_root_relpath: str


@dataclass(frozen=True, slots=True)
class _ServiceProtocolEndpointBindingMetadata:
    endpoint_ref: str
    api_name: str
    capability_name: str
    endpoint_name: str
    request_type_ref: str
    response_type_ref: str | None
    stream_event_type_refs: tuple[str, ...]
    fulfillment_bindings: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class _ConnectorProtocolPublication:
    package_name: str
    package_root_relpath: str
    relative_path: str
    action_keys: tuple[str, ...]
    endpoint_refs: tuple[str, ...]
    content_hash_sha256: str


def _experience_reference_branch_ids_from_context(
    *, context: Mapping[str, object] | None
) -> dict[str, UUID]:
    if context is None:
        return {}
    raw_branch_ids = context.get("experience_reference_branch_ids_by_experience_name")
    if raw_branch_ids is None:
        return {}
    if not isinstance(raw_branch_ids, Mapping):
        raise RuntimeError(
            "Experience Workspace materialization requires dependency reference branch ids to be a mapping"
        )
    branch_ids: dict[str, UUID] = {}
    for raw_name, raw_branch_id in raw_branch_ids.items():
        name = str(raw_name or "").strip()
        if not name:
            raise RuntimeError(
                "Experience Workspace materialization received an empty dependency Experience name"
            )
        try:
            branch_id = (
                raw_branch_id
                if isinstance(raw_branch_id, UUID)
                else UUID(str(raw_branch_id))
            )
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "Experience Workspace materialization received an invalid dependency reference branch id "
                + f"for experience {name!r}"
            ) from exc
        existing_branch_id = branch_ids.get(name.casefold())
        if existing_branch_id is not None and existing_branch_id != branch_id:
            raise RuntimeError(
                "Experience Workspace materialization received conflicting dependency reference branches "
                + f"for experience {name!r}"
            )
        branch_ids[name] = branch_id
        branch_ids[name.casefold()] = branch_id
    return branch_ids


async def materialize(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    result = await materialize_experience_package_from_manifest(
        runtime=request.runtime,
        index=request.index,
        actor_id=request.actor_id,
        branch_id=request.branch_id,
        workspace_root=request.workspace_root,
        experience_toml_path=request.manifest_path,
        install_scope="dependency_reference",
        projection_reference_branch_ids_by_name=(
            _experience_reference_branch_ids_from_context(context=request.context)
        ),
        prefer_snapshot_environment_profiles=True,
        semantic_materialization_context=request.context,
    )
    profile_publication = resolve_experience_profile_publication_summary(
        experience_toml_path=request.manifest_path,
        workspace_root=request.workspace_root,
    )
    profiles = tuple(
        _encode_profile(profile) for profile in profile_publication.profiles
    )
    current_semantic_object_ids = _profile_semantic_object_ids(
        result=result,
        profile_publication=profile_publication,
    )
    current_semantic_object_identities = _profile_semantic_object_identities(
        result=result,
        current_semantic_object_ids=current_semantic_object_ids,
    )
    view_api_output = _emit_view_api_package_output(
        request=request,
        source_package_key=result.experience_package.name,
    )
    language_contract_packages = result.language_contract_packages
    runtime_target_packages = _declared_python_runtime_target_packages(
        workspace_root=result.workspace_root,
        experience_package_root=result.experience_toml_path.parent,
        manifest_spec=result.manifest_spec,
        language_contract_packages=language_contract_packages,
    )
    connector_protocol_publications = _materialize_connector_protocol_publications(
        workspace_root=result.workspace_root,
        experience_toml_path=result.experience_toml_path,
        runtime_target_packages=runtime_target_packages,
    )
    language_contract_code_package_deltas = (
        _language_contract_generated_code_package_deltas(
            language_contract_packages=language_contract_packages,
        )
    )
    runtime_target_code_package_deltas = _runtime_target_code_package_deltas(
        runtime_target_packages=runtime_target_packages,
    )
    generated_code_package_deltas = (
        *language_contract_code_package_deltas,
        *runtime_target_code_package_deltas,
    )
    runtime_code_package_refs = _dedupe_runtime_code_package_refs(
        (
            *_language_contract_runtime_code_package_refs(
                language_contract_packages=language_contract_packages,
            ),
            *_runtime_target_code_package_refs(
                runtime_target_packages=runtime_target_packages,
            ),
        )
    )
    return SemanticPackageMaterializationResult(
        details={
            "experience_toml_path": result.experience_toml_path.as_posix(),
            "experience_name": result.experience_name,
            "experience_names": list(result.experience_names),
            "environment_experience_id": str(result.environment_experience.id),
            "experience_handle": profile_publication.experience_handle,
            "experience_package_name": result.experience_package.name,
            "experience_package_id": str(result.experience_package.id),
            "semantic_branch_id": str(request.branch_id),
            "source_code_package_id": (
                str(result.source_code_package_id)
                if result.source_code_package_id is not None
                else None
            ),
            "experience_source_path": result.experience_source_path,
            "source_files": list(result.source_files),
            "profiles": list(profiles),
            "experience_phase_timings_s": dict(result.phase_timings_s),
            "environment_experience_commit_id": (
                str(result.environment_experience_commit_id)
                if result.environment_experience_commit_id is not None
                else None
            ),
            "projection_experience_commit_id": (
                str(result.projection_experience_commit_id)
                if result.projection_experience_commit_id is not None
                else None
            ),
            "projection_experience_head_commit_id": (
                str(result.projection_experience_head_commit_id)
                if result.projection_experience_head_commit_id is not None
                else None
            ),
            "projection_experience_graph_commit_id": (
                str(result.projection_experience_graph_commit_id)
                if result.projection_experience_graph_commit_id is not None
                else None
            ),
            "projection_experience_graph_head_commit_id": (
                str(result.projection_experience_graph_head_commit_id)
                if result.projection_experience_graph_head_commit_id is not None
                else None
            ),
            "projection_experience_section_surface_commit_id": (
                str(result.projection_experience_section_surface_commit_id)
                if result.projection_experience_section_surface_commit_id is not None
                else None
            ),
            "projection_experience_section_surface_head_commit_id": (
                str(result.projection_experience_section_surface_head_commit_id)
                if result.projection_experience_section_surface_head_commit_id
                is not None
                else None
            ),
            "activation_profile_config_commit_id": (
                str(getattr(result, "activation_profile_config_commit_id", None))
                if getattr(result, "activation_profile_config_commit_id", None)
                is not None
                else None
            ),
            "activation_profile_config_head_commit_id": (
                str(getattr(result, "activation_profile_config_head_commit_id", None))
                if getattr(result, "activation_profile_config_head_commit_id", None)
                is not None
                else None
            ),
            "activation_profile_config_branch_id": (
                str(result.activation_profile_config_branch_id)
                if result.activation_profile_config_branch_id is not None
                else None
            ),
            "activation_profile_config_projection_hash": (
                result.activation_profile_config_projection_hash
            ),
            "activation_profile_config_domain_object_instance_graph_id": (
                str(result.activation_profile_config_domain_object_instance_graph_id)
                if result.activation_profile_config_domain_object_instance_graph_id
                is not None
                else None
            ),
            "activation_profile_config_object_instance_graph_commit_id": (
                str(result.activation_profile_config_object_instance_graph_commit_id)
                if result.activation_profile_config_object_instance_graph_commit_id
                is not None
                else None
            ),
            "activation_action_experience_commit_id": (
                str(getattr(result, "activation_action_experience_commit_id", None))
                if getattr(result, "activation_action_experience_commit_id", None)
                is not None
                else None
            ),
            "activation_action_experience_head_commit_id": (
                str(
                    getattr(result, "activation_action_experience_head_commit_id", None)
                )
                if getattr(result, "activation_action_experience_head_commit_id", None)
                is not None
                else None
            ),
            "activation_invocation_config_commit_id": (
                str(getattr(result, "activation_invocation_config_commit_id", None))
                if getattr(result, "activation_invocation_config_commit_id", None)
                is not None
                else None
            ),
            "activation_invocation_config_head_commit_id": (
                str(
                    getattr(result, "activation_invocation_config_head_commit_id", None)
                )
                if getattr(result, "activation_invocation_config_head_commit_id", None)
                is not None
                else None
            ),
            "activation_reference_branch_ids_by_experience_name": {
                experience_name: str(branch_id)
                for experience_name, branch_id in sorted(
                    getattr(
                        result,
                        "activation_reference_branch_ids_by_experience_name",
                        {},
                    ).items()
                )
            },
            "experience_package_commit_id": (
                str(result.package_commit_id)
                if result.package_commit_id is not None
                else None
            ),
            "experience_package_head_commit_id": (
                str(result.package_head_commit_id)
                if result.package_head_commit_id is not None
                else None
            ),
            "emitted_view_api_package": (
                view_api_output.evidence_payload()
                if view_api_output is not None
                else None
            ),
            "language_contract_packages": list(
                _encode_language_contract_packages(
                    language_contract_packages=language_contract_packages,
                )
            ),
            "runtime_target_packages": list(
                _encode_runtime_target_packages(
                    runtime_target_packages=runtime_target_packages,
                )
            ),
            "connector_protocol_publications": [
                {
                    "package_name": publication.package_name,
                    "package_root_relpath": publication.package_root_relpath,
                    "relative_path": publication.relative_path,
                    "action_keys": list(publication.action_keys),
                    "endpoint_refs": list(publication.endpoint_refs),
                    "content_hash_sha256": publication.content_hash_sha256,
                }
                for publication in connector_protocol_publications
            ],
            "generated_code_package_deltas": [
                delta.model_dump(mode="json") for delta in generated_code_package_deltas
            ],
            "language_materialization_code_package_deltas": [
                delta.model_dump(mode="json") for delta in generated_code_package_deltas
            ],
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=result.experience_package.name,
                manifest_toml_path=result.experience_toml_path,
                semantic_package_id=result.experience_package.id,
                semantic_root_id=result.environment_experience.id,
                semantic_branch_id=request.branch_id,
                semantic_head_commit_id=result.package_head_commit_id,
                semantic_object_instance_graph_commit_id=(
                    result.package_object_instance_graph_commit_id
                ),
                semantic_root_object_instance_graph_commit_id=(
                    result.package_object_instance_graph_commit_id
                ),
                semantic_root_kind="experience_package",
                semantic_projection_name="ExperiencePackage",
                semantic_projection_hash=result.package_projection_hash,
                source_code_package_id=result.source_code_package_id,
                experience_handle=profile_publication.experience_handle,
                profiles=profiles,
                runtime_code_package_refs=runtime_code_package_refs,
            ),
        ),
        current_semantic_object_ids=current_semantic_object_ids,
        current_semantic_object_identities=current_semantic_object_identities,
        mode="full_rebuild",
        affected_semantic_keys=_semantic_keys_from_request(request),
        applied_semantic_keys=_semantic_keys_from_request(request),
        emitted_package_outputs=(
            (view_api_output,) if view_api_output is not None else ()
        ),
        fallback_reason=_FULL_REBUILD_FALLBACK_REASON,
        commit_id=result.package_commit_id,
        head_commit_id=result.package_head_commit_id,
        experience_reference_branch_ids_by_experience_name=(
            (
                {result.experience_package.name: request.branch_id}
                if result.experience_package.name.casefold()
                not in {name.casefold() for name in result.experience_names}
                else {}
            )
            | {
                experience_name: derive_experience_reference_branch_id(
                    base_branch_id=request.branch_id,
                    experience_name=experience_name,
                )
                for experience_name in result.experience_names
            }
        ),
    )


def _profile_semantic_object_ids(
    *,
    result: object,
    profile_publication: object,
) -> dict[str, str]:
    manifest_spec = getattr(result, "manifest_spec", None)
    build_spec = getattr(manifest_spec, "build", None)
    environment_handle = str(
        getattr(build_spec, "environment_handle", "") or ""
    ).strip()
    fqn_prefix = str(
        getattr(profile_publication, "experience_handle", "") or ""
    ).strip()
    if not environment_handle or not fqn_prefix:
        return {}
    environment_config_id = stable_environment_config_id(handle=environment_handle)
    environment_experience_id = stable_environment_experience_id(fqn_prefix=fqn_prefix)
    identities: dict[str, str] = {}
    for profile in getattr(profile_publication, "profiles", ()):
        experience_name = str(getattr(profile, "experience_name", "") or "").strip()
        profile_key = str(getattr(profile, "key", "") or "").strip()
        if not experience_name or not profile_key:
            continue
        environment_profile_config_id = stable_environment_profile_config_id(
            environment_config_id=environment_config_id,
            key=profile_key,
        )
        profile_config_id = stable_environment_experience_profile_config_id(
            environment_experience_id=environment_experience_id,
            environment_profile_config_id=environment_profile_config_id,
            key=profile_key,
        )
        identities[f"experience.profile:{experience_name}:{profile_key}"] = str(
            profile_config_id
        )
    return dict(sorted(identities.items()))


def _profile_semantic_object_identities(
    *,
    result: object,
    current_semantic_object_ids: dict[str, str],
) -> tuple[SemanticPackageMaterializationObjectIdentity, ...]:
    branch_id = getattr(result, "activation_profile_config_branch_id", None)
    projection_hash = getattr(
        result,
        "activation_profile_config_projection_hash",
        None,
    )
    object_instance_graph_id = getattr(
        result,
        "activation_profile_config_domain_object_instance_graph_id",
        None,
    )
    object_instance_graph_commit_id = getattr(
        result,
        "activation_profile_config_object_instance_graph_commit_id",
        None,
    )
    semantic_head_commit_id = getattr(
        result,
        "activation_profile_config_head_commit_id",
        None,
    )
    if (
        branch_id is None
        or not projection_hash
        or object_instance_graph_id is None
        or object_instance_graph_commit_id is None
        or semantic_head_commit_id is None
    ):
        return ()
    return tuple(
        SemanticPackageMaterializationObjectIdentity(
            semantic_key=semantic_key,
            object_id=object_id,
            domain_branch_id=str(branch_id),
            projection_hash=str(projection_hash),
            domain_object_instance_graph_id=str(object_instance_graph_id),
            object_instance_graph_commit_id=str(object_instance_graph_commit_id),
            semantic_head_commit_id=str(semantic_head_commit_id),
            source="aware_experience.activation_profile_config",
        )
        for semantic_key, object_id in sorted(current_semantic_object_ids.items())
    )


def _materialize_language_contract_packages(
    *,
    request: SemanticPackageMaterializationRequest,
) -> tuple[ExperienceLanguageContractPackage, ...]:
    if not request.manifest_path.exists():
        return ()
    compile_result = compile_experience_workspace(
        toml_path=request.manifest_path,
        repo_root=request.workspace_root,
    )
    snapshot = compile_result.snapshot
    if not snapshot.spec.targets:
        return ()
    language_contract_result = materialize_experience_language_contracts(
        snapshot=snapshot,
        languages=tuple(sorted(snapshot.spec.targets)),
    )
    return language_contract_result.packages


def _encode_language_contract_packages(
    *,
    language_contract_packages: tuple[ExperienceLanguageContractPackage, ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "language": package.language,
            "package_name": package.package_name,
            "package_root_relpath": package.relpath,
            "manifest_relative_path": package.manifest_relative_path,
            "sources_root_relpath": package.sources_root_relpath,
            "file_count": package.file_count,
            "contract_count": package.contract_count,
        }
        for package in language_contract_packages
    )


def _declared_python_runtime_target_packages(
    *,
    workspace_root: Path,
    experience_package_root: Path,
    manifest_spec: object,
    language_contract_packages: tuple[ExperienceLanguageContractPackage, ...],
) -> tuple[_ExperienceRuntimeTargetPackage, ...]:
    targets = getattr(manifest_spec, "targets", None)
    if not isinstance(targets, dict):
        return ()
    generated_manifest_paths = {
        package.manifest_relative_path for package in language_contract_packages
    }
    packages: list[_ExperienceRuntimeTargetPackage] = []
    resolved_workspace_root = workspace_root.resolve()
    resolved_experience_package_root = experience_package_root.resolve()
    for language, target in sorted(targets.items()):
        if str(language).strip().casefold() != "python":
            continue
        package_root = (
            resolved_experience_package_root
            / str(getattr(target, "root_dir", "")).strip()
            / str(getattr(target, "package_dir", "")).strip()
        ).resolve()
        _assert_path_within(
            root=resolved_experience_package_root,
            path=package_root,
            label="[targets.python]",
        )
        manifest_path = package_root / "pyproject.toml"
        if not manifest_path.is_file() or manifest_path.is_symlink():
            continue
        manifest_relative_path = manifest_path.relative_to(
            resolved_workspace_root
        ).as_posix()
        if manifest_relative_path in generated_manifest_paths:
            continue
        package_name = _python_project_name_from_pyproject(manifest_path)
        if package_name is None:
            package_name = str(
                getattr(getattr(manifest_spec, "experience", None), "package_name", "")
            ).strip()
        if not package_name:
            continue
        import_root = _target_import_root(target=target)
        sources_root = package_root / import_root
        if not sources_root.is_dir() or sources_root.is_symlink():
            sources_root = package_root
        packages.append(
            _ExperienceRuntimeTargetPackage(
                language="python",
                package_name=package_name,
                import_root=import_root,
                package_root=package_root,
                relpath=package_root.relative_to(resolved_workspace_root).as_posix(),
                manifest_relative_path=manifest_relative_path,
                sources_root_relpath=sources_root.relative_to(
                    resolved_workspace_root
                ).as_posix(),
            )
        )
    return tuple(packages)


def _encode_runtime_target_packages(
    *,
    runtime_target_packages: tuple[_ExperienceRuntimeTargetPackage, ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "language": package.language,
            "package_name": package.package_name,
            "import_root": package.import_root,
            "package_root_relpath": package.relpath,
            "manifest_relative_path": package.manifest_relative_path,
            "sources_root_relpath": package.sources_root_relpath,
        }
        for package in runtime_target_packages
    )


def _materialize_connector_protocol_publications(
    *,
    workspace_root: Path,
    experience_toml_path: Path,
    runtime_target_packages: tuple[_ExperienceRuntimeTargetPackage, ...],
) -> tuple[_ConnectorProtocolPublication, ...]:
    python_targets = tuple(
        package for package in runtime_target_packages if package.language == "python"
    )
    if not python_targets or not experience_toml_path.exists():
        return ()

    compile_result = compile_experience_workspace(
        toml_path=experience_toml_path,
        repo_root=workspace_root,
    )
    snapshot = compile_result.snapshot
    package_name = (snapshot.spec.experience.package_name or "").strip()
    fqn_prefix = (snapshot.spec.experience.fqn_prefix or "").strip()
    if not package_name or not fqn_prefix:
        return ()

    specs = _resolve_connector_protocol_materialization_specs(snapshot=snapshot)
    if not specs:
        return ()

    endpoint_refs = _api_connector_endpoint_refs(specs=specs)
    endpoint_bindings = _load_service_protocol_endpoint_bindings(
        workspace_root=workspace_root,
        required_endpoint_refs=endpoint_refs,
    )
    plan = build_connector_protocol_plan(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        specs=specs,
        endpoint_bindings=endpoint_bindings,
    )
    module_text = render_python_connector_protocol_module(plan=plan)
    action_keys = tuple(
        sorted(
            invocation.materialized_action_key
            for connector in plan.connectors
            for invocation in connector.all_invocation_actions
        )
    )
    content_hash_sha256 = sha256(module_text.encode("utf-8")).hexdigest()
    publications: list[_ConnectorProtocolPublication] = []
    for package in python_targets:
        relative_path = (
            PurePosixPath(package.import_root)
            / _CONNECTOR_PROTOCOL_MODULE_RELATIVE_PATH
        ).as_posix()
        target_path = package.package_root / Path(*PurePosixPath(relative_path).parts)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if (
            not target_path.exists()
            or target_path.read_text(encoding="utf-8") != module_text
        ):
            target_path.write_text(module_text, encoding="utf-8")
        publications.append(
            _ConnectorProtocolPublication(
                package_name=package.package_name,
                package_root_relpath=package.relpath,
                relative_path=relative_path,
                action_keys=action_keys,
                endpoint_refs=endpoint_refs,
                content_hash_sha256=content_hash_sha256,
            )
        )
    return tuple(publications)


def _resolve_connector_protocol_materialization_specs(
    *,
    snapshot: object,
) -> tuple[ConnectorConfigMaterializationSpec, ...]:
    projection_ownership = load_projection_experience_ownership_from_sources(
        package_root=getattr(snapshot, "package_root"),
        source_files=getattr(snapshot, "source_files"),
    )
    connector_ownership = load_connector_ownership_from_sources(
        package_root=getattr(snapshot, "package_root"),
        source_files=getattr(snapshot, "source_files"),
    )
    if not connector_ownership:
        return ()
    payload = {
        "projection_experience_ownership": [
            {
                "name": projection.name,
                "projection": projection.projection,
                "source_path": projection.source_path,
            }
            for projection in projection_ownership
        ],
        "connector_ownership": [
            _connector_ownership_payload(connector=connector)
            for connector in connector_ownership
        ],
    }
    return resolve_connector_config_materialization_specs(
        compile_plan_payloads=(payload,),
    )


def _connector_ownership_payload(
    *,
    connector: ExperienceConnectorConfigOwnership,
) -> dict[str, object]:
    return {
        "connector_key": connector.connector_key,
        "connector_kind": connector.connector_kind,
        "source_path": connector.source_path,
        "label": connector.label,
        "description": connector.description,
        "providers": [
            _connector_provider_payload(provider=provider)
            for provider in connector.providers
        ],
        "sensor_configs": [
            _connector_sensor_payload(sensor=sensor)
            for sensor in connector.sensor_configs
        ],
        "actuator_configs": [
            _connector_actuator_payload(actuator=actuator)
            for actuator in connector.actuator_configs
        ],
    }


def _connector_provider_payload(
    *,
    provider: ExperienceConnectorProviderOwnership,
) -> dict[str, object]:
    return {
        "provider_key": provider.provider_key,
        "provider_kind": provider.provider_kind,
        "source_path": provider.source_path,
        "provider_ref": provider.provider_ref,
        "label": provider.label,
        "description": provider.description,
    }


def _connector_sensor_payload(
    *,
    sensor: ExperienceSensorConfigOwnership,
) -> dict[str, object]:
    return {
        "sensor_key": sensor.sensor_key,
        "sensor_kind": sensor.sensor_kind,
        "source_path": sensor.source_path,
        "source_ref": sensor.source_ref,
        "observed_state_node_refs": list(sensor.observed_state_node_refs),
        "label": sensor.label,
        "description": sensor.description,
        "invocation_action_configs": [
            _connector_invocation_payload(invocation=invocation)
            for invocation in sensor.invocation_action_configs
        ],
    }


def _connector_actuator_payload(
    *,
    actuator: ExperienceActuatorConfigOwnership,
) -> dict[str, object]:
    return {
        "actuator_key": actuator.actuator_key,
        "actuator_kind": actuator.actuator_kind,
        "source_path": actuator.source_path,
        "target_ref": actuator.target_ref,
        "affected_state_node_refs": list(actuator.affected_state_node_refs),
        "label": actuator.label,
        "description": actuator.description,
        "invocation_action_configs": [
            _connector_invocation_payload(invocation=invocation)
            for invocation in actuator.invocation_action_configs
        ],
    }


def _connector_invocation_payload(
    *,
    invocation: ExperienceConnectorInvocationActionConfigOwnership,
) -> dict[str, object]:
    return {
        "action_key": invocation.action_key,
        "action_kind": invocation.action_kind,
        "target_ref": invocation.target_ref,
        "source_path": invocation.source_path,
        "label": invocation.label,
        "receipt_policy": invocation.receipt_policy,
        "confirmation_policy": invocation.confirmation_policy,
        "optimistic_policy": invocation.optimistic_policy,
        "request_fields": [
            {
                "attribute": field.attribute,
                "source_ref": field.source_ref,
                "required": field.required,
            }
            for field in invocation.request_fields
        ],
    }


def _api_connector_endpoint_refs(
    *,
    specs: tuple[ConnectorConfigMaterializationSpec, ...],
) -> tuple[str, ...]:
    endpoint_refs: set[str] = set()
    for spec in specs:
        for sensor in spec.sensor_configs:
            for invocation in sensor.invocation_action_configs:
                if invocation.action_kind == "api":
                    endpoint_refs.add(invocation.target_ref)
        for actuator in spec.actuator_configs:
            for invocation in actuator.invocation_action_configs:
                if invocation.action_kind == "api":
                    endpoint_refs.add(invocation.target_ref)
    return tuple(sorted(endpoint_refs))


def _load_service_protocol_endpoint_bindings(
    *,
    workspace_root: Path,
    required_endpoint_refs: tuple[str, ...],
) -> dict[str, _ServiceProtocolEndpointBindingMetadata]:
    if not required_endpoint_refs:
        return {}
    required = set(required_endpoint_refs)
    bindings: dict[str, _ServiceProtocolEndpointBindingMetadata] = {}
    api_runtime_root = workspace_root / ".aware" / "api" / "runtime"
    if api_runtime_root.is_dir():
        for plan_path in sorted(
            api_runtime_root.glob("*/api.service_protocol_plan.json"),
            key=lambda item: item.as_posix(),
        ):
            for binding in _load_service_protocol_plan_endpoint_bindings(
                plan_path=plan_path
            ):
                if binding.endpoint_ref in required:
                    bindings[binding.endpoint_ref] = binding
    missing = required - set(bindings)
    if missing:
        for binding in _load_source_service_protocol_endpoint_bindings(
            workspace_root=workspace_root,
            required_endpoint_refs=tuple(sorted(missing)),
        ):
            if binding.endpoint_ref in missing:
                bindings[binding.endpoint_ref] = binding
    missing = tuple(sorted(required - set(bindings)))
    if missing:
        raise RuntimeError(
            "Experience connector protocol publication requires generated API "
            "service-protocol metadata for endpoint refs: "
            + ", ".join(repr(item) for item in missing)
        )
    return bindings


def _load_source_service_protocol_endpoint_bindings(
    *,
    workspace_root: Path,
    required_endpoint_refs: tuple[str, ...],
) -> tuple[_ServiceProtocolEndpointBindingMetadata, ...]:
    if not required_endpoint_refs:
        return ()
    required = set(required_endpoint_refs)
    bindings: list[_ServiceProtocolEndpointBindingMetadata] = []
    for protocol_path in sorted(
        workspace_root.glob(
            "modules/**/apis/**/python/*_protocol/*_protocol/protocols.py"
        ),
        key=lambda item: item.as_posix(),
    ):
        for binding in _load_service_protocol_module_endpoint_bindings(
            protocol_path=protocol_path
        ):
            if binding.endpoint_ref in required:
                bindings.append(binding)
    return tuple(bindings)


def _load_service_protocol_module_endpoint_bindings(
    *,
    protocol_path: Path,
) -> tuple[_ServiceProtocolEndpointBindingMetadata, ...]:
    try:
        tree = ast.parse(protocol_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        raise RuntimeError(
            "API service protocol module is not readable: " f"{protocol_path}: {exc}"
        ) from exc
    constants = _module_string_constants(tree=tree)
    bindings: list[_ServiceProtocolEndpointBindingMetadata] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node.func) != "ServiceProtocolEndpointBinding":
            continue
        keywords = {keyword.arg: keyword.value for keyword in node.keywords}
        endpoint_ref = _literal_text_node(keywords.get("endpoint_ref"), constants)
        api_name = _literal_text_node(keywords.get("api_name"), constants)
        capability_name = _literal_text_node(keywords.get("capability_name"), constants)
        endpoint_name = _literal_text_node(keywords.get("endpoint_name"), constants)
        request_type_ref = _literal_text_node(
            keywords.get("request_type_ref"), constants
        )
        if not (
            endpoint_ref
            and api_name
            and capability_name
            and endpoint_name
            and request_type_ref
        ):
            continue
        response_type_ref = _optional_literal_text_node(
            keywords.get("response_type_ref"), constants
        )
        stream_event_type_refs = _literal_text_tuple_node(
            keywords.get("stream_event_type_refs"), constants
        )
        fulfillment_bindings = _literal_fulfillment_bindings_node(
            keywords.get("fulfillment_bindings")
        )
        bindings.append(
            _ServiceProtocolEndpointBindingMetadata(
                endpoint_ref=endpoint_ref,
                api_name=api_name,
                capability_name=capability_name,
                endpoint_name=endpoint_name,
                request_type_ref=request_type_ref,
                response_type_ref=response_type_ref,
                stream_event_type_refs=stream_event_type_refs,
                fulfillment_bindings=fulfillment_bindings,
            )
        )
    return tuple(bindings)


def _module_string_constants(*, tree: ast.Module) -> dict[str, str]:
    constants: dict[str, str] = {}
    for node in tree.body:
        target: ast.expr | None = None
        value: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            value = node.value
        if not isinstance(target, ast.Name) or value is None:
            continue
        try:
            literal = ast.literal_eval(value)
        except (ValueError, TypeError):
            continue
        if isinstance(literal, str):
            constants[target.id] = literal
    return constants


def _literal_text_node(
    node: ast.AST | None,
    constants: dict[str, str],
) -> str:
    value = _optional_literal_text_node(node, constants)
    return value or ""


def _optional_literal_text_node(
    node: ast.AST | None,
    constants: dict[str, str],
) -> str | None:
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else None
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError):
        return None
    return value if isinstance(value, str) else None


def _literal_text_tuple_node(
    node: ast.AST | None,
    constants: dict[str, str],
) -> tuple[str, ...]:
    if node is None:
        return ()
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError):
        return ()
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _literal_fulfillment_bindings_node(node: ast.AST | None) -> tuple[object, ...]:
    if node is None:
        return ()
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError):
        if isinstance(node, (ast.List, ast.Tuple)) and not node.elts:
            return ()
        return ("<non-literal-fulfillment-binding>",)
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return ()


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _load_service_protocol_plan_endpoint_bindings(
    *,
    plan_path: Path,
) -> tuple[_ServiceProtocolEndpointBindingMetadata, ...]:
    try:
        payload = json.loads(plan_path.read_text(encoding="utf-8") or "{}")
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "API service protocol plan is not readable: " f"{plan_path}: {exc}"
        ) from exc
    bindings: list[_ServiceProtocolEndpointBindingMetadata] = []
    apis = payload.get("apis", [])
    if not isinstance(apis, list):
        return ()
    for api_obj in apis:
        if not isinstance(api_obj, dict):
            continue
        api_name = _non_empty_text(api_obj.get("name"))
        capabilities = api_obj.get("capabilities", [])
        if not isinstance(capabilities, list):
            continue
        for capability_obj in capabilities:
            if not isinstance(capability_obj, dict):
                continue
            capability_name = _non_empty_text(capability_obj.get("name"))
            endpoints = capability_obj.get("endpoints", [])
            if not isinstance(endpoints, list):
                continue
            for endpoint_obj in endpoints:
                if not isinstance(endpoint_obj, dict):
                    continue
                binding = _service_protocol_endpoint_binding_from_payload(
                    api_name=api_name,
                    capability_name=capability_name,
                    endpoint_obj=endpoint_obj,
                    plan_path=plan_path,
                )
                if binding is not None:
                    bindings.append(binding)
    return tuple(bindings)


def _service_protocol_endpoint_binding_from_payload(
    *,
    api_name: str,
    capability_name: str,
    endpoint_obj: dict[str, object],
    plan_path: Path,
) -> _ServiceProtocolEndpointBindingMetadata | None:
    endpoint_name = _non_empty_text(endpoint_obj.get("name"))
    endpoint_ref = _non_empty_text(
        endpoint_obj.get("endpoint_ref") or endpoint_obj.get("discriminant")
    )
    request = endpoint_obj.get("request")
    if not isinstance(request, dict):
        raise RuntimeError(
            "API service protocol endpoint is missing request metadata: "
            f"{plan_path}:{endpoint_ref or endpoint_name}"
        )
    request_type_ref = _non_empty_text(request.get("class_ref"))
    if not endpoint_ref:
        endpoint_ref = ".".join(
            token for token in (api_name, capability_name, endpoint_name) if token
        )
    if not endpoint_ref or not api_name or not capability_name or not endpoint_name:
        return None
    if not request_type_ref:
        raise RuntimeError(
            "API service protocol endpoint is missing request class_ref: "
            f"{plan_path}:{endpoint_ref}"
        )
    response = endpoint_obj.get("response")
    response_type_ref = (
        _non_empty_text(response.get("class_ref"))
        if isinstance(response, dict)
        else None
    )
    stream = endpoint_obj.get("stream")
    stream_event_type_refs = _stream_event_type_refs_from_payload(stream=stream)
    fulfillment_bindings = endpoint_obj.get("fulfillment_bindings", [])
    if not isinstance(fulfillment_bindings, list):
        fulfillment_bindings = []
    return _ServiceProtocolEndpointBindingMetadata(
        endpoint_ref=endpoint_ref,
        api_name=api_name,
        capability_name=capability_name,
        endpoint_name=endpoint_name,
        request_type_ref=request_type_ref,
        response_type_ref=response_type_ref,
        stream_event_type_refs=stream_event_type_refs,
        fulfillment_bindings=tuple(fulfillment_bindings),
    )


def _stream_event_type_refs_from_payload(*, stream: object) -> tuple[str, ...]:
    if not isinstance(stream, dict):
        return ()
    event_refs: list[str] = []
    event_configs = stream.get("event_configs")
    if isinstance(event_configs, list):
        for event_obj in event_configs:
            if not isinstance(event_obj, dict):
                continue
            class_ref = _non_empty_text(event_obj.get("class_ref"))
            if class_ref:
                event_refs.append(class_ref)
    class_ref = _non_empty_text(stream.get("class_ref"))
    if class_ref:
        event_refs.append(class_ref)
    return tuple(dict.fromkeys(event_refs))


def _non_empty_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _language_contract_runtime_code_package_refs(
    *,
    language_contract_packages: tuple[ExperienceLanguageContractPackage, ...],
) -> tuple[dict[str, object], ...]:
    refs: list[dict[str, object]] = []
    for package in language_contract_packages:
        manifest_kind = _language_contract_manifest_kind(language=package.language)
        code_package_config_key = _language_contract_code_package_config_key(
            package=package,
            manifest_kind=manifest_kind,
        )
        code_package_config_id = stable_code_package_config_id(
            config_key=code_package_config_key,
        )
        source_code_package_id = _language_contract_code_package_id(
            package=package,
            code_package_config_id=code_package_config_id,
        )
        refs.append(
            {
                "role": "runtime",
                "source_code_package_id": str(source_code_package_id),
                "code_package_id": str(source_code_package_id),
                "code_package_config_key": code_package_config_key,
                "code_package_config_id": str(code_package_config_id),
                "package_name": package.package_name,
                "manifest_relative_path": package.manifest_relative_path,
                "manifest_kind": manifest_kind,
                "package_root": package.relpath,
                "sources_root": package.sources_root_relpath,
                "code_package_surface": _LANGUAGE_CONTRACT_SURFACE,
                "language": package.language,
            }
        )
    return tuple(refs)


def _runtime_target_code_package_refs(
    *,
    runtime_target_packages: tuple[_ExperienceRuntimeTargetPackage, ...],
) -> tuple[dict[str, object], ...]:
    refs: list[dict[str, object]] = []
    for package in runtime_target_packages:
        manifest_kind = _language_contract_manifest_kind(language=package.language)
        code_package_config_key = _runtime_code_package_config_key(
            package=package,
            manifest_kind=manifest_kind,
        )
        code_package_config_id = stable_code_package_config_id(
            config_key=code_package_config_key,
        )
        source_code_package_id = _runtime_target_code_package_id(
            package=package,
            code_package_config_id=code_package_config_id,
        )
        refs.append(
            {
                "role": "experience_language_package",
                "source_code_package_id": str(source_code_package_id),
                "code_package_id": str(source_code_package_id),
                "code_package_config_key": code_package_config_key,
                "code_package_config_id": str(code_package_config_id),
                "package_name": package.package_name,
                "manifest_relative_path": package.manifest_relative_path,
                "manifest_kind": manifest_kind,
                "package_root": package.relpath,
                "sources_root": package.sources_root_relpath,
                "code_package_surface": _LANGUAGE_CONTRACT_SURFACE,
                "language": package.language,
            }
        )
    return tuple(refs)


def _dedupe_runtime_code_package_refs(
    refs: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    refs_by_id: dict[str, dict[str, object]] = {}
    for ref in refs:
        code_package_id = str(
            ref.get("code_package_id") or ref.get("source_code_package_id") or ""
        ).strip()
        if not code_package_id:
            continue
        refs_by_id[code_package_id] = ref
    return tuple(refs_by_id[key] for key in sorted(refs_by_id))


def _language_contract_generated_code_package_deltas(
    *,
    language_contract_packages: tuple[ExperienceLanguageContractPackage, ...],
) -> tuple[CodePackageDelta, ...]:
    deltas: list[CodePackageDelta] = []
    for package in language_contract_packages:
        delta = _language_contract_generated_code_package_delta(package=package)
        if delta is not None:
            deltas.append(delta)
    return tuple(deltas)


def _runtime_target_code_package_deltas(
    *,
    runtime_target_packages: tuple[_ExperienceRuntimeTargetPackage, ...],
) -> tuple[CodePackageDelta, ...]:
    deltas: list[CodePackageDelta] = []
    for package in runtime_target_packages:
        delta = _runtime_target_code_package_delta(package=package)
        if delta is not None:
            deltas.append(delta)
    return tuple(deltas)


def _language_contract_generated_code_package_delta(
    *,
    package: ExperienceLanguageContractPackage,
) -> CodePackageDelta | None:
    manifest_kind = _language_contract_manifest_kind(language=package.language)
    paths: list[CodePackageDeltaPath] = []
    for relpath_text in package.materialized_package_paths:
        relpath = PurePosixPath(relpath_text)
        file_path = package.package_root / Path(*relpath.parts)
        if not file_path.is_file() or file_path.is_symlink():
            raise RuntimeError(
                "Experience language contract package declared a generated file "
                f"that is not readable: {file_path.as_posix()}"
            )
        try:
            content_text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise RuntimeError(
                "Experience language contract package emitted non-text output: "
                f"{file_path.as_posix()}"
            ) from exc
        paths.append(
            CodePackageDeltaPath(
                relative_path=relpath.as_posix(),
                kind=CodePackageDeltaKind.update,
                content_text=content_text,
                language=_language_contract_code_language(language=package.language),
                is_structural=False,
                path_role=_language_contract_code_package_path_role(
                    relative_path=relpath,
                    manifest_kind=manifest_kind,
                ),
            )
        )
    if not paths:
        return None
    code_package_config_key = _language_contract_code_package_config_key(
        package=package,
        manifest_kind=manifest_kind,
    )
    code_package_config_id = stable_code_package_config_id(
        config_key=code_package_config_key,
    )
    code_package_id = _language_contract_code_package_id(
        package=package,
        code_package_config_id=code_package_config_id,
    )
    production = _language_contract_code_package_delta_production(
        package=package,
        manifest_kind=manifest_kind,
        code_package_config_key=code_package_config_key,
        code_package_config_id=code_package_config_id,
        code_package_id=code_package_id,
        paths=paths,
    )
    paths = [
        path.model_copy(
            update={
                "production": production,
                "after_hash": sha256(
                    (path.content_text or "").encode("utf-8")
                ).hexdigest(),
                "size_bytes": len((path.content_text or "").encode("utf-8")),
            }
        )
        for path in paths
    ]
    return CodePackageDelta(
        package_name=package.package_name,
        package_root=package.relpath,
        sources_root=package.sources_root_relpath,
        manifest_relative_path=package.manifest_relative_path,
        authority=CodePackageDeltaAuthorityKind.semantic_materialization,
        authority_kind=CodePackageDeltaAuthorityKind.semantic_materialization.value,
        source_revision_id=(
            "semantic_materialization:"
            f"aware_experience:{_LANGUAGE_CONTRACT_PRODUCER_KEY}:"
            f"{package.package_name}"
        ),
        production=production,
        paths=paths,
    )


def _runtime_target_code_package_delta(
    *,
    package: _ExperienceRuntimeTargetPackage,
) -> CodePackageDelta | None:
    manifest_kind = _language_contract_manifest_kind(language=package.language)
    paths: list[CodePackageDeltaPath] = []
    for file_path in sorted(
        package.package_root.rglob("*"),
        key=lambda item: item.as_posix(),
    ):
        if not file_path.is_file() or file_path.is_symlink():
            continue
        try:
            relative_path = file_path.resolve().relative_to(package.package_root)
        except ValueError:
            continue
        relpath = PurePosixPath(relative_path.as_posix())
        if _direct_code_package_path_is_denied(
            package_relative_path=relpath.as_posix()
        ):
            continue
        try:
            content_text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        paths.append(
            CodePackageDeltaPath(
                relative_path=relpath.as_posix(),
                kind=CodePackageDeltaKind.update,
                content_text=content_text,
                language=_language_contract_code_language(language=package.language),
                is_structural=False,
                path_role=_language_contract_code_package_path_role(
                    relative_path=relpath,
                    manifest_kind=manifest_kind,
                ),
            )
        )
    if not paths:
        return None
    code_package_config_key = _runtime_code_package_config_key(
        package=package,
        manifest_kind=manifest_kind,
    )
    code_package_config_id = stable_code_package_config_id(
        config_key=code_package_config_key,
    )
    code_package_id = _runtime_target_code_package_id(
        package=package,
        code_package_config_id=code_package_config_id,
    )
    production = _runtime_target_code_package_delta_production(
        package=package,
        manifest_kind=manifest_kind,
        code_package_config_key=code_package_config_key,
        code_package_config_id=code_package_config_id,
        code_package_id=code_package_id,
        paths=paths,
    )
    paths = [
        path.model_copy(
            update={
                "production": production,
                "after_hash": sha256(
                    (path.content_text or "").encode("utf-8")
                ).hexdigest(),
                "size_bytes": len((path.content_text or "").encode("utf-8")),
            }
        )
        for path in paths
    ]
    return CodePackageDelta(
        package_name=package.package_name,
        package_root=package.relpath,
        sources_root=package.sources_root_relpath,
        manifest_relative_path=package.manifest_relative_path,
        authority=CodePackageDeltaAuthorityKind.semantic_materialization,
        authority_kind=CodePackageDeltaAuthorityKind.semantic_materialization.value,
        source_revision_id=(
            "semantic_materialization:"
            f"aware_experience:{_LANGUAGE_TARGET_PRODUCER_KEY}:"
            f"{package.package_name}"
        ),
        production=production,
        paths=paths,
    )


def _language_contract_code_package_config_key(
    *,
    package: ExperienceLanguageContractPackage,
    manifest_kind: str,
) -> str:
    return code_package_generated_config_key(
        materialization_source=_LANGUAGE_CONTRACT_MATERIALIZATION_SOURCE,
        renderer_kind=_LANGUAGE_CONTRACT_RENDERER_KIND,
        language=_language_contract_code_language(language=package.language),
        surface=_LANGUAGE_CONTRACT_SURFACE,
        manifest_kind=manifest_kind,
    )


def _runtime_code_package_config_key(
    *,
    package: _ExperienceRuntimeTargetPackage,
    manifest_kind: str,
) -> str:
    return code_package_generated_config_key(
        materialization_source=_LANGUAGE_CONTRACT_MATERIALIZATION_SOURCE,
        renderer_kind=_LANGUAGE_CONTRACT_RENDERER_KIND,
        language=_language_contract_code_language(language=package.language),
        surface=_LANGUAGE_CONTRACT_SURFACE,
        manifest_kind=manifest_kind,
    )


def _language_contract_code_package_id(
    *,
    package: ExperienceLanguageContractPackage,
    code_package_config_id: UUID,
) -> UUID:
    return stable_code_package_id(
        code_package_config_id=code_package_config_id,
        package_name=package.package_name,
        language=package.language,
    )


def _runtime_target_code_package_id(
    *,
    package: _ExperienceRuntimeTargetPackage,
    code_package_config_id: UUID,
) -> UUID:
    return stable_code_package_id(
        code_package_config_id=code_package_config_id,
        package_name=package.package_name,
        language=package.language,
    )


def _language_contract_code_package_delta_production(
    *,
    package: ExperienceLanguageContractPackage,
    manifest_kind: str,
    code_package_config_key: str,
    code_package_config_id: UUID,
    code_package_id: UUID,
    paths: list[CodePackageDeltaPath],
) -> CodePackageDeltaProduction:
    output_digest = _language_contract_code_package_delta_output_digest(paths=paths)
    payload = JsonObject(
        {
            "semantic_owner": EXPERIENCE_PROVIDER_OWNER,
            "output_key": _LANGUAGE_CONTRACT_OUTPUT_KEY,
            "artifact_family": _LANGUAGE_CONTRACT_ARTIFACT_FAMILY,
            "target_language_plugin_id": package.language,
            "materialization_source": _LANGUAGE_CONTRACT_MATERIALIZATION_SOURCE,
            "renderer_kind": _LANGUAGE_CONTRACT_RENDERER_KIND,
            "renderer_profile": "experience_language_contract",
            "code_package_surface": _LANGUAGE_CONTRACT_SURFACE,
            "code_package_config_key": code_package_config_key,
            "code_package_config_id": str(code_package_config_id),
            "manifest_kind": manifest_kind,
            "declared_code_package_id": str(code_package_id),
            "code_package_id": str(code_package_id),
            "package_name": package.package_name,
            "package_root": package.relpath,
            "sources_root": package.sources_root_relpath,
            "manifest_relative_path": package.manifest_relative_path,
        }
    )
    return CodePackageDeltaProduction(
        producer=CodePackageDeltaProducerRef(
            provider_key="aware_experience",
            producer_key=_LANGUAGE_CONTRACT_PRODUCER_KEY,
            producer_kind="semantic_materializer",
            provider_payload=payload,
        ),
        output_digest=output_digest,
        emission_payload=JsonObject(
            {
                "contract_version": "aware.experience.language_contract.code_package_delta.v1",
                "package_name": package.package_name,
                "package_root": package.relpath,
                "sources_root": package.sources_root_relpath,
                "code_package_surface": _LANGUAGE_CONTRACT_SURFACE,
                "code_package_config_key": code_package_config_key,
                "code_package_config_id": str(code_package_config_id),
                "manifest_kind": manifest_kind,
                "manifest_relative_path": package.manifest_relative_path,
                "path_count": len(paths),
            }
        ),
    )


def _runtime_target_code_package_delta_production(
    *,
    package: _ExperienceRuntimeTargetPackage,
    manifest_kind: str,
    code_package_config_key: str,
    code_package_config_id: UUID,
    code_package_id: UUID,
    paths: list[CodePackageDeltaPath],
) -> CodePackageDeltaProduction:
    output_digest = _language_contract_code_package_delta_output_digest(paths=paths)
    payload = JsonObject(
        {
            "semantic_owner": EXPERIENCE_PROVIDER_OWNER,
            "output_key": _LANGUAGE_TARGET_OUTPUT_KEY,
            "artifact_family": _LANGUAGE_TARGET_ARTIFACT_FAMILY,
            "target_language_plugin_id": package.language,
            "materialization_source": _LANGUAGE_CONTRACT_MATERIALIZATION_SOURCE,
            "renderer_kind": _LANGUAGE_CONTRACT_RENDERER_KIND,
            "renderer_profile": "experience_language_target",
            "code_package_surface": _LANGUAGE_CONTRACT_SURFACE,
            "code_package_config_key": code_package_config_key,
            "code_package_config_id": str(code_package_config_id),
            "manifest_kind": manifest_kind,
            "declared_code_package_id": str(code_package_id),
            "code_package_id": str(code_package_id),
            "package_name": package.package_name,
            "package_root": package.relpath,
            "sources_root": package.sources_root_relpath,
            "manifest_relative_path": package.manifest_relative_path,
        }
    )
    return CodePackageDeltaProduction(
        producer=CodePackageDeltaProducerRef(
            provider_key="aware_experience",
            producer_key=_LANGUAGE_TARGET_PRODUCER_KEY,
            producer_kind="semantic_materializer",
            provider_payload=payload,
        ),
        output_digest=output_digest,
        emission_payload=JsonObject(
            {
                "contract_version": "aware.experience.language_target.code_package_delta.v1",
                "package_name": package.package_name,
                "package_root": package.relpath,
                "sources_root": package.sources_root_relpath,
                "code_package_surface": _LANGUAGE_CONTRACT_SURFACE,
                "code_package_config_key": code_package_config_key,
                "code_package_config_id": str(code_package_config_id),
                "manifest_kind": manifest_kind,
                "manifest_relative_path": package.manifest_relative_path,
                "path_count": len(paths),
            }
        ),
    )


def _language_contract_code_package_delta_output_digest(
    *,
    paths: list[CodePackageDeltaPath],
) -> str:
    payload = [
        {
            "relative_path": path.relative_path,
            "kind": str(getattr(path.kind, "value", path.kind)),
            "content_text": path.content_text,
        }
        for path in sorted(paths, key=lambda item: item.relative_path)
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def _python_project_name_from_pyproject(path: Path) -> str | None:
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    project = payload.get("project")
    if not isinstance(project, dict):
        return None
    name = project.get("name")
    if not isinstance(name, str):
        return None
    normalized = name.strip()
    return normalized or None


def _target_import_root(*, target: object) -> str:
    package_dir = str(getattr(target, "package_dir", "")).strip()
    parts = Path(package_dir).parts
    return parts[-1] if parts else package_dir


def _assert_path_within(*, root: Path, path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(
            f"Experience language target path escapes package root: {label}={path}"
        ) from exc


def _direct_code_package_path_is_denied(*, package_relative_path: str) -> bool:
    path = PurePosixPath(package_relative_path)
    if any(part in _DIRECT_CODE_PACKAGE_EXCLUDED_DIR_NAMES for part in path.parts):
        return True
    if path.suffix.lower() in _DIRECT_CODE_PACKAGE_EXCLUDED_SUFFIXES:
        return True
    return any(part.endswith(".egg-info") for part in path.parts)


def _language_contract_code_language(*, language: str) -> CodeLanguage:
    if language == "python":
        return CodeLanguage.python
    if language == "dart":
        return CodeLanguage.dart
    raise ValueError(
        "Unsupported Experience language contract CodePackage language: "
        f"{language!r}"
    )


def _language_contract_code_package_path_role(
    *,
    relative_path: PurePosixPath,
    manifest_kind: str,
) -> CodePackagePathRole:
    if relative_path.as_posix() == _language_contract_manifest_filename(
        manifest_kind=manifest_kind
    ):
        return CodePackagePathRole.generated_manifest
    if relative_path.suffix in {".py", ".dart"}:
        return CodePackagePathRole.generated_code
    return CodePackagePathRole.generated_metadata


def _language_contract_manifest_filename(*, manifest_kind: str) -> str:
    if manifest_kind == "pyproject_toml":
        return "pyproject.toml"
    if manifest_kind == "pubspec_yaml":
        return "pubspec.yaml"
    raise ValueError(
        "Unsupported Experience language contract manifest kind: " f"{manifest_kind!r}"
    )


def _language_contract_manifest_kind(*, language: str) -> str:
    if language == "python":
        return "pyproject_toml"
    if language == "dart":
        return "pubspec_yaml"
    raise ValueError(
        "Unsupported Experience language contract CodePackage language: "
        f"{language!r}"
    )


def _emit_view_api_package_output(
    *,
    request: SemanticPackageMaterializationRequest,
    source_package_key: str,
) -> SemanticPackageMaterializationEmittedPackageOutput | None:
    if not request.manifest_path.exists():
        return None
    compile_result = compile_experience_workspace(
        toml_path=request.manifest_path,
        repo_root=request.workspace_root,
    )
    snapshot = compile_result.snapshot
    package_name = (snapshot.spec.experience.package_name or "").strip()
    fqn_prefix = (snapshot.spec.experience.fqn_prefix or "").strip()
    projection_experiences = load_projection_experience_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
    )
    view_state_model_contracts = tuple(
        ExperienceViewStateModelContract(
            state_model_ref=contract.state_model_ref,
            class_config_id=contract.class_config_id,
            source_path=contract.source_path,
        )
        for contract in load_view_state_model_contracts_from_sources(
            package_root=snapshot.package_root,
            source_files=snapshot.source_files,
            fqn_prefix=fqn_prefix,
            package_name=package_name,
        )
    )
    view_api = build_experience_view_api_ownership(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        projection_experience_ownership=projection_experiences,
        view_state_model_contracts=view_state_model_contracts,
    )
    if view_api is None:
        return None

    experience_plan = ExperienceCompilePlan(
        schema_version=1,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        environment_handle=(snapshot.spec.build.environment_handle or "").strip(),
        source_files=tuple(path.as_posix() for path in snapshot.source_files),
        view_state_model_contracts=view_state_model_contracts,
        view_api_ownership=view_api,
        actor_role_contract=None,
        role_ownership=(),
        actor_ownership=(),
        environment_actor_bindings=(),
        action_ownership=(),
        connector_ownership=(),
        action_target_ownership=(),
        environment_ownership=(),
        projection_experience_ownership=projection_experiences,
        environment_profile_ownership=(),
        projection_api_ownership=(),
        graph_ownership=(),
        program_ownership=(),
        event_ownership=(),
    )
    artifact = emit_experience_view_api_compile_plan_artifact(
        experience_plan=experience_plan,
        repo_root=request.workspace_root,
    )
    if artifact is None:
        return None
    artifact_payload = _compile_plan_payload(artifact.path)
    return SemanticPackageMaterializationEmittedPackageOutput(
        producer_provider_key="aware_experience",
        producer_semantic_owner=EXPERIENCE_PROVIDER_OWNER,
        producer_key=EXPERIENCE_VIEW_API_PRODUCER_KEY,
        output_key=EXPERIENCE_VIEW_API_PACKAGE_OUTPUT_KEY,
        target_provider_key=EXPERIENCE_VIEW_API_TARGET_PROVIDER_KEY,
        target_semantic_owner=EXPERIENCE_VIEW_API_TARGET_SEMANTIC_OWNER,
        target_input_key=EXPERIENCE_VIEW_API_TARGET_INPUT_KEY,
        target_package_family="api",
        target_semantic_kind="api_package",
        package_key=view_api.package_name,
        input_artifact_producer_key=EXPERIENCE_VIEW_API_PRODUCER_KEY,
        input_artifact_output_key=EXPERIENCE_VIEW_API_COMPILE_PLAN_OUTPUT_KEY,
        input_artifact_family="api_compile_plan",
        input_artifact_path=artifact.path,
        input_artifact_payload=artifact_payload,
        runtime_contract_version=EXPERIENCE_VIEW_API_RUNTIME_CONTRACT_VERSION,
        source_package_key=source_package_key,
        source_manifest_path=_relative_or_posix(
            path=request.manifest_path,
            root=request.workspace_root,
        ),
        provider_payload={
            "artifact_relpath": artifact.relpath,
            "artifact_hash_sha256": artifact.hash_sha256,
            "runtime_required_projection_names": (
                _view_api_runtime_required_projection_names(
                    projection_experiences=projection_experiences,
                )
            ),
            "schema_version": _artifact_schema_version(artifact.path),
        },
    )


def _compile_plan_payload(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8") or "{}")
    except Exception as exc:
        raise RuntimeError(
            f"Experience generated view API compile plan is not readable: {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError(
            "Experience generated view API compile plan must be a JSON object: "
            + path.as_posix()
        )
    return payload


def _view_api_runtime_required_projection_names(
    *,
    projection_experiences: tuple[ExperienceProjectionExperienceOwnership, ...],
) -> tuple[str, ...]:
    projection_names: list[str] = []
    for experience in projection_experiences:
        if experience.projection.strip():
            projection_names.append(experience.projection.strip())
    return tuple(dict.fromkeys(projection_names))


def _artifact_schema_version(path: Path) -> int | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8") or "{}")
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    schema_version = payload.get("schema_version")
    return schema_version if isinstance(schema_version, int) else None


def _relative_or_posix(*, path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _encode_profile(profile: object) -> dict[str, object]:
    return {
        "key": getattr(profile, "key", None),
        "title": getattr(profile, "title", None),
        "description": getattr(profile, "description", None),
        "narrative": getattr(profile, "narrative", None),
        "roles": [
            {
                "name": getattr(role, "name", None),
                "description": getattr(role, "description", None),
                "capabilities": list(getattr(role, "capabilities", ())),
            }
            for role in getattr(profile, "roles", ())
        ],
        "actors": [
            {
                "key": getattr(actor, "key", None),
                "title": getattr(actor, "title", None),
                "description": getattr(actor, "description", None),
                "type": getattr(actor, "actor_type", None),
                "role_names": list(getattr(actor, "role_names", ())),
            }
            for actor in getattr(profile, "actors", ())
        ],
        "process_configs": [
            _encode_process_config(process)
            for process in getattr(profile, "process_configs", ())
        ],
    }


def _semantic_keys_from_request(
    request: SemanticPackageMaterializationRequest,
) -> tuple[str, ...]:
    raw_keys = request.change_preview.get("affected_semantic_keys")
    if not isinstance(raw_keys, (list, tuple, set)):
        return ()
    return tuple(sorted({str(key).strip() for key in raw_keys if str(key).strip()}))


def _encode_process_config(process: object) -> dict[str, object]:
    return {
        "type": getattr(process, "type", None),
        "key": getattr(process, "key", None),
        "process_key": getattr(process, "process_key", None),
        "title": getattr(process, "title", None),
        "description": getattr(process, "description", None),
        "shape": getattr(process, "shape", None),
        "position": getattr(process, "position", None),
        "is_bootstrap_default": bool(getattr(process, "is_bootstrap_default", False)),
        "narrative": getattr(process, "narrative", None),
        "intent": getattr(process, "intent", None),
        "thread_configs": [
            {
                "key": getattr(thread, "key", None),
                "thread_key": getattr(thread, "thread_key", None),
                "title": getattr(thread, "title", None),
                "description": getattr(thread, "description", None),
                "workspace_view_key": getattr(thread, "workspace_view_key", None),
                "position": getattr(thread, "position", None),
                "is_default": bool(getattr(thread, "is_default", False)),
                "narrative": getattr(thread, "narrative", None),
                "intent": getattr(thread, "intent", None),
                "state_prompt_template": getattr(thread, "state_prompt_template", None),
                "projection_experiences": [
                    {
                        "projection_experience_name": getattr(
                            projection, "projection_experience_name", None
                        ),
                        "view_key": getattr(projection, "view_key", None),
                        "is_default": bool(getattr(projection, "is_default", False)),
                    }
                    for projection in getattr(thread, "projection_experiences", ())
                ],
            }
            for thread in getattr(process, "thread_configs", ())
        ],
    }


__all__ = ["materialize"]
