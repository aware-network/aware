from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from aware_api_runtime.snapshots.commit import (
    ApiPackageLanguagePackageSnapshotRef,
    commit_api_package_manifest_snapshot,
    commit_api_reference_snapshot,
)
from aware_api_runtime.handlers._generated import (
    meta_handlers as api_meta_handlers,
)
from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
    stable_code_package_id,
)
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package import CodePackage
from aware_code.types import JsonArray, JsonObject
from aware_api_ontology.stable_ids import (
    stable_api_graph_projection_id,
    stable_api_id,
    stable_api_package_id,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.materialization.contracts import MaterializationLaneContext
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
    MetaGraphRuntimeIndex,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.testing import IsolatedMetaAwareRoot
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_ontology_ontology.stable_ids import stable_ontology_package_id
from aware_orm.session.session import Session
from aware_service_runtime.handlers._generated import (
    meta_handlers as service_meta_handlers,
)
from aware_service_ontology.service.service_api_provider_set import (
    ServiceApiProviderSet,
)
from aware_service_ontology.service.service_api_provider_set_service_package import (
    ServiceApiProviderSetServicePackage,
)
from aware_service_ontology.service.service_operation_config_api_endpoint import (
    ServiceOperationConfigApiEndpoint,
)
from aware_service_ontology.service.service_operation_config_api_endpoint_function import (
    ServiceOperationConfigApiEndpointFunction,
)
from aware_service_ontology.stable_ids import (
    stable_service_api_provider_set_id,
    stable_service_api_provider_set_service_package_id,
)
from _service_runtime_test_paths import REPO_ROOT

_API_META_HANDLERS_ANY: Any = api_meta_handlers
_API_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _API_META_HANDLERS_ANY,
)
_API_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _API_META_HANDLERS_ANY,
)
_SERVICE_META_HANDLERS_ANY: Any = service_meta_handlers
_SERVICE_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _SERVICE_META_HANDLERS_ANY,
)
_SERVICE_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _SERVICE_META_HANDLERS_ANY,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class _FailClosedSemanticRuntime:
    def __init__(self, *, manifest_path: Path) -> None:
        self._manifest_path = manifest_path

    @property
    def manifest_path(self) -> Path:
        return self._manifest_path

    @property
    def invoker(self):
        raise AssertionError(
            "Service package materialization must not route through legacy runtime"
        )


def _service_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/economy/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/service/ontology/structure/aware.toml",
    )


def _build_service_meta_runtime(
    repo_root: Path,
    *,
    workspace_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_service_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=workspace_root,
        handler_modules=(
            _API_META_HANDLER_MODULE,
            _SERVICE_META_HANDLER_MODULE,
        ),
        bootstrap_modules=(
            _API_META_BOOTSTRAP_MODULE,
            _SERVICE_META_BOOTSTRAP_MODULE,
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=(MetaGraphFunctionImplOwnership.authored),
        ),
    )
    assert runtime.context is not None
    return runtime


def _runtime_index(runtime: MetaGraphRuntime) -> MetaGraphRuntimeIndex:
    assert runtime.context is not None
    return runtime.context.index


def _find_projection_hash_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> str:
    target = (projection_name or "").strip()
    for opg in index.ocg.object_projection_graphs:
        name = (opg.name or "").strip()
        if name == target:
            return opg.projection_hash
    raise ValueError(
        f"Projection {projection_name!r} was not found in Service runtime OCG"
    )


def _resolve_class_config_id(
    *,
    index: MetaGraphRuntimeIndex,
    class_name_suffix: str,
) -> UUID:
    target = (class_name_suffix or "").strip()
    matches: list[UUID] = [
        class_config.id
        for class_config in index.class_configs_by_id.values()
        if class_config.class_fqn == target
        or (class_config.class_fqn or "").endswith(target)
        or class_config.name == target
    ]
    unique_matches: tuple[UUID, ...] = tuple(dict.fromkeys(matches))
    if not unique_matches:
        raise RuntimeError(f"Could not resolve class config {class_name_suffix!r}")
    if len(unique_matches) > 1:
        raise RuntimeError(f"Ambiguous class config {class_name_suffix!r}")
    return unique_matches[0]


def test_service_package_dependency_payload_derives_materialization_protocol_digest(
    tmp_path: Path,
) -> None:
    from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
    from aware_service_runtime.materialization.service import (  # noqa: WPS433
        _api_service_protocol_artifact_hash,
        _service_package_dependencies_payload,
    )

    service_toml_path = tmp_path / "services" / "meta" / "aware.service.toml"
    _write(
        service_toml_path,
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "aware-meta-service"',
                'fqn_prefix = "aware_meta_service"',
                "version_number = 1",
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "force_fresh_scan = true",
                'compilation_mode = "service_ontology"',
                "",
                "[host]",
                'service_surface = "service"',
                'activation_mode = "materialize_and_load_committed"',
                "materialize_on_start = true",
                "",
                "[implementation]",
                "",
                "[[dependencies]]",
                'package_name = "meta-service-api"',
                "version_number = 1",
                'kind = "api_service_protocol"',
                "",
            ]
        ),
    )
    artifact_path = (
        tmp_path
        / ".aware"
        / "api"
        / "runtime"
        / "meta-service-api"
        / "api.service_protocol_plan.json"
    )
    _write(artifact_path, '{"z": 2, "a": 1}\n')
    spec = load_aware_service_toml_spec(toml_path=service_toml_path)

    actual_hash = _api_service_protocol_artifact_hash(
        workspace_root=tmp_path,
        package_name="meta-service-api",
    )
    assert actual_hash is not None

    payload = _service_package_dependencies_payload(
        spec=spec,
        workspace_root=tmp_path,
    )

    first_dependency = cast(dict[str, object], payload[0])
    assert (
        first_dependency["service_protocol_plan_hash_sha256"] == actual_hash.hash_sha256
    )


def test_service_package_dependency_payload_resolves_declared_workspace_protocol(
    tmp_path: Path,
) -> None:
    from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
    from aware_service_runtime.materialization.service import (  # noqa: WPS433
        _api_service_protocol_artifact_hash,
        _service_package_dependencies_payload,
    )

    workspaces_root = tmp_path / "workspaces"
    network_root = workspaces_root / "aware_network"
    kernel_root = workspaces_root / "aware_kernel"
    _write(
        network_root / "aware.workspace.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[workspace]",
                'handle = "aware_network"',
                "",
                "[[workspace.dependencies]]",
                'id = "aware_kernel"',
                'kind = "workspace"',
                'source = "workspace://aware_kernel"',
                "",
            ]
        ),
    )
    _write(
        kernel_root / "aware.workspace.toml",
        "\n".join(["aware = 1", "", "[workspace]", 'handle = "aware_kernel"', ""]),
    )
    service_toml_path = network_root / "services" / "reactivity" / "aware.service.toml"
    _write(
        service_toml_path,
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "aware-reactivity-service"',
                'fqn_prefix = "aware_reactivity_service"',
                "version_number = 1",
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "force_fresh_scan = true",
                'compilation_mode = "service_ontology"',
                "",
                "[host]",
                'service_surface = "service"',
                'activation_mode = "materialize_and_load_committed"',
                "materialize_on_start = true",
                "",
                "[implementation]",
                "",
                "[[dependencies]]",
                'package_name = "reactivity-service-api"',
                "version_number = 1",
                'kind = "api_service_protocol"',
                "",
            ]
        ),
    )
    protocol_path = (
        kernel_root
        / ".aware"
        / "api"
        / "runtime"
        / "reactivity-service-api"
        / "api.service_protocol_plan.json"
    )
    _write(protocol_path, '{"version": 1, "package_name": "reactivity-service-api"}\n')
    spec = load_aware_service_toml_spec(toml_path=service_toml_path)

    artifact = _api_service_protocol_artifact_hash(
        workspace_root=network_root,
        package_name="reactivity-service-api",
    )
    assert artifact is not None
    assert artifact.path == protocol_path

    payload = _service_package_dependencies_payload(
        spec=spec,
        workspace_root=network_root,
    )

    dependency = cast(dict[str, object], payload[0])
    assert dependency["service_protocol_plan_hash_sha256"] == artifact.hash_sha256


def test_service_package_dependency_payload_preserves_route_authority_selector(
    tmp_path: Path,
) -> None:
    from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
    from aware_service_runtime.materialization.service import (  # noqa: WPS433
        _service_package_dependencies_payload,
    )

    service_toml_path = tmp_path / "services" / "environment" / "aware.service.toml"
    _write(
        service_toml_path,
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "aware-environment-service"',
                'fqn_prefix = "aware_environment_service"',
                "version_number = 1",
                "",
                "[build]",
                'sources_dir = "bindings"',
                "",
                "[[dependencies]]",
                'package_name = "ontology-service-api"',
                'kind = "api_invocation"',
                'route_authority_selector = { provider_set_id = "kernel.ontology_authority.v1", workspace_deployment_channel = "stable" }',
                "",
            ]
        ),
    )
    spec = load_aware_service_toml_spec(toml_path=service_toml_path)

    payload = _service_package_dependencies_payload(
        spec=spec,
        workspace_root=tmp_path,
    )

    first_dependency = cast(dict[str, object], payload[0])
    assert first_dependency["route_authority_selector"] == {
        "provider_set_id": "kernel.ontology_authority.v1",
        "workspace_deployment_channel": "stable",
    }


def test_service_toml_ontology_package_rejects_non_replica_role(
    tmp_path: Path,
) -> None:
    from aware_service_runtime.manifest.loader import (  # noqa: WPS433
        AwareServiceTomlError,
        load_aware_service_toml_spec,
    )

    service_toml_path = tmp_path / "services" / "search" / "aware.service.toml"
    _write(
        service_toml_path,
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "aware-search-service"',
                'fqn_prefix = "aware_search_service"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                "",
                "[[ontology_packages]]",
                'package_name = "identity-ontology"',
                'fqn_prefix = "aware_identity"',
                'role = "writer"',
                "",
            ]
        ),
    )

    with pytest.raises(AwareServiceTomlError, match="only supports 'replica'"):
        load_aware_service_toml_spec(toml_path=service_toml_path)


def test_service_toml_ontology_package_materializes_replica_snapshot(
    tmp_path: Path,
) -> None:
    from aware_service_runtime.manifest.loader import (  # noqa: WPS433
        load_aware_service_toml_spec,
    )
    from aware_service_runtime.materialization.service import (  # noqa: WPS433
        _service_package_ontology_package_snapshots,
    )

    service_toml_path = tmp_path / "services" / "search" / "aware.service.toml"
    _write(
        service_toml_path,
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "aware-search-service"',
                'fqn_prefix = "aware_search_service"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                "",
                "[[ontology_packages]]",
                'package_name = "identity-ontology"',
                'fqn_prefix = "aware_identity"',
                'role = "replica"',
                'requirement_mode = "required"',
                'expected_hash_sha256 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"',
                'description = "Identity ontology replica required for reads."',
                "",
            ]
        ),
    )

    spec = load_aware_service_toml_spec(toml_path=service_toml_path)

    snapshots = _service_package_ontology_package_snapshots(spec)

    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.ontology_package_id == stable_ontology_package_id(
        name="identity-ontology",
        fqn_prefix="aware_identity",
    )
    assert snapshot.package_name == "identity-ontology"
    assert snapshot.fqn_prefix == "aware_identity"
    assert snapshot.role == "replica"
    assert snapshot.requirement_mode == "required"
    assert (
        snapshot.expected_hash_sha256
        == "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    )
    assert snapshot.description == "Identity ontology replica required for reads."


def _write_service_package_fixture(
    *,
    workspace_root: Path,
    extra_service: bool = False,
    include_experience: bool = False,
    include_api_provider_set: bool = False,
) -> Path:
    service_toml_path = workspace_root / "aware.service.toml"
    _write(
        service_toml_path,
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "home-story-service"',
                'fqn_prefix = "aware_home_story_service"',
                "version_number = 7",
                'title = "Home Story Service"',
                'description = "Home story service semantic package"',
                "",
                "[build]",
                'sources_dir = "services/bindings"',
                'include_paths = ["**/*.aware"]',
                'exclude_paths = ["**/*.draft.aware"]',
                "force_fresh_scan = false",
                'compilation_mode = "service_ontology"',
                "",
                "[host]",
                'service_surface = "service"',
                'activation_mode = "materialize_and_load_committed"',
                "materialize_on_start = false",
                "",
                "[implementation]",
                "",
                "[[implementation.packages]]",
                'language = "python"',
                'package_name = "home-story-service"',
                'import_root = "aware_home_story_service"',
                'package_root = "."',
                'manifest_path = "pyproject.toml"',
                'entrypoint = "aware_home_story_service.service_bindings:build_service_bindings"',
                'role = "service_bindings"',
                'include_paths = ["aware_home_story_service/**/*.py"]',
                'exclude_paths = ["aware_home_story_service/**/__pycache__/**"]',
                "",
                "[[ontology_packages]]",
                'package_name = "identity-ontology"',
                'fqn_prefix = "aware_identity"',
                'role = "replica"',
                'requirement_mode = "required"',
                'description = "Identity ontology replica required for service reads."',
                "",
                *(
                    [
                        "[[api_provider_sets]]",
                        'key = "kernel.global_services.v1"',
                        'title = "Kernel Global Services"',
                        'membership_key = "kernel-services-host"',
                        'description = "Kernel global service providers."',
                        "",
                    ]
                    if include_api_provider_set
                    else []
                ),
                "[[dependencies]]",
                'package_name = "home-devices-api"',
                "version_number = 3",
                'kind = "api_service_protocol"',
                "",
                "[[dependencies]]",
                'package_name = "meta-service-api"',
                "version_number = 1",
                'kind = "api_invocation"',
            ]
        )
        + "\n",
    )
    _write(
        workspace_root
        / ".aware/api/runtime/home-devices-api/api.service_protocol_plan.json",
        '{"apis": [], "package_name": "home-devices-api", "schema_version": 1}\n',
    )
    lines = [
        "service home_story {",
        "    api home_devices;",
        *(["    experience home_story;"] if include_experience else []),
        "",
        "    operation lock_door {",
        "        endpoint home_devices.lock_door.lock_door;",
        "    }",
        "}",
        "",
    ]
    if extra_service:
        lines.extend(
            [
                "service weather_station {",
                "    api home_devices;",
                "",
                "    operation lock_window {",
                "        endpoint home_devices.lock_door.lock_door;",
                "    }",
                "}",
                "",
            ]
        )
    _write(
        workspace_root / "services" / "bindings" / "home.services.aware",
        "\n".join(lines),
    )
    _write(
        workspace_root / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                'name = "home-story-service"',
                'version = "0.1.0"',
                'readme = "README.md"',
                'requires-python = ">=3.12"',
                "dependencies = []",
                "",
                "[build-system]",
                'requires = ["hatchling>=1.27.0"]',
                'build-backend = "hatchling.build"',
                "",
                "[tool.hatch.build.targets.wheel]",
                'packages = ["aware_home_story_service"]',
                'include = ["README.md", "aware_home_story_service/py.typed"]',
            ]
        )
        + "\n",
    )
    _write(workspace_root / "README.md", "# Home Story Service\n")
    _write(
        workspace_root / "aware_home_story_service" / "__init__.py",
        "\n",
    )
    _write(workspace_root / "aware_home_story_service" / "py.typed", "")
    _write(
        workspace_root / "aware_home_story_service" / "service_bindings.py",
        "def build_service_bindings():\n    return {}\n",
    )
    return service_toml_path


def test_implementation_code_package_snapshot_includes_pyproject_support_files(
    tmp_path: Path,
) -> None:
    from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
    from aware_service_runtime.materialization.service import (  # noqa: WPS433
        _implementation_code_package_unparsed_texts,
    )

    service_toml_path = _write_service_package_fixture(workspace_root=tmp_path)
    service_spec = load_aware_service_toml_spec(toml_path=service_toml_path)
    implementation_spec = service_spec.implementation.packages[0]

    texts = _implementation_code_package_unparsed_texts(
        implementation_package_root=tmp_path,
        implementation_manifest_path=tmp_path / "pyproject.toml",
        implementation_spec=implementation_spec,
    )

    assert set(texts) == {
        "pyproject.toml",
        "README.md",
        "aware_home_story_service/__init__.py",
        "aware_home_story_service/py.typed",
        "aware_home_story_service/service_bindings.py",
    }


async def _materialize_committed_api_definition(
    *,
    runtime: MetaGraphRuntime,
    environment_id: UUID,
    process_id: UUID,
    thread_id: UUID,
    branch_id: UUID,
) -> None:
    index = _runtime_index(runtime)
    api_projection_hash = _find_projection_hash_by_name(
        index=index, projection_name="Api"
    )
    request_class_config_id = _resolve_class_config_id(
        index=index,
        class_name_suffix="aware_api.api.Api",
    )
    endpoint_ref = "home_devices.lock_door.lock_door"
    result = await commit_api_reference_snapshot(
        index=index,
        actor_id=None,
        projection_hash=api_projection_hash,
        branch_id=branch_id,
        api_name="home_devices",
        endpoint_refs=(endpoint_ref,),
        endpoint_request_class_config_ids={endpoint_ref: request_class_config_id},
        endpoint_fulfillment_names={endpoint_ref: ("lock",)},
        api_graph_function_config_id=uuid5(
            NAMESPACE_URL,
            "service-package-materialization/home-devices/lock",
        ),
    )
    _ = environment_id, process_id, thread_id

    assert result.commit_id is not None
    assert result.object_instance_graph_commit_id is not None
    api_package_projection_hash = _find_projection_hash_by_name(
        index=index,
        projection_name="ApiPackage",
    )
    await commit_api_package_manifest_snapshot(
        index=index,
        actor_id=None,
        branch_id=branch_id,
        projection_hash=api_package_projection_hash,
        package_name="home-devices-api",
        api_id=stable_api_id(name="home_devices"),
        api_object_instance_graph_commit_id=result.object_instance_graph_commit_id,
        source_code_package_id=None,
        fqn_prefix="aware_home_devices_api",
        version_number=3,
        title=None,
        description=None,
        aware_api_version=1,
        manifest_relative_path="apis/home_devices/aware.api.toml",
        package_root=".",
        sources_root="apis/home_devices",
        include_paths=JsonArray(),
        exclude_paths=JsonArray(),
        force_fresh_scan=True,
        compilation_mode="raw_xor",
        dependencies=JsonArray(),
        targets=JsonObject(),
        language_package_refs=(
            ApiPackageLanguagePackageSnapshotRef(
                code_package_id=uuid5(
                    NAMESPACE_URL,
                    "service-package-materialization/home-devices/protocol-package",
                ),
                object_instance_graph_commit_id=uuid5(
                    NAMESPACE_URL,
                    "service-package-materialization/home-devices/protocol-commit",
                ),
                package_name="home-devices-api-service-protocol",
                language=CodeLanguage.python,
                import_root="aware_home_devices_api_service_protocol",
                manifest_relative_path=(
                    ".aware/api/runtime/home-devices-api/"
                    "api.service_protocol_plan.json"
                ),
                package_root=".",
                role="service_protocol",
                output_key="python.service_protocol_package",
            ),
        ),
    )


async def _seed_boot_environment(
    *,
    environment_id: UUID,
) -> tuple[UUID, UUID, UUID]:
    from aware_history.stable_ids import stable_branch_id

    process_id = uuid5(
        NAMESPACE_URL,
        f"service-package-materialization/{environment_id}/process",
    )
    thread_id = uuid5(
        NAMESPACE_URL,
        f"service-package-materialization/{environment_id}/thread",
    )
    boot_branch_id = stable_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
    )
    return process_id, thread_id, boot_branch_id


async def _hydrate_projection_session(
    *,
    runtime: MetaGraphRuntime,
    branch_id: UUID,
    projection_hash: str,
) -> Session:
    index = _runtime_index(runtime)
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head is not None
    assert head.get("commit_id") is not None
    opg = index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=None,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )


def test_resolve_service_package_materialization_spec_rejects_multiple_service_declarations(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "service_package_spec_multiple"
    workspace_root.mkdir(parents=True, exist_ok=True)
    service_toml_path = _write_service_package_fixture(
        workspace_root=workspace_root,
        extra_service=True,
    )

    from aware_service_runtime.materialization import (  # noqa: WPS433
        resolve_service_package_materialization_spec,
    )

    with pytest.raises(
        RuntimeError, match="exactly one canonical `service` declaration"
    ):
        _ = resolve_service_package_materialization_spec(
            service_toml_path=service_toml_path,
            workspace_root=workspace_root,
        )


def test_resolve_service_package_materialization_spec_includes_experience_refs(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "service_package_spec_experience_refs"
    workspace_root.mkdir(parents=True, exist_ok=True)
    service_toml_path = _write_service_package_fixture(
        workspace_root=workspace_root,
        include_experience=True,
    )

    from aware_service_runtime.materialization import (
        resolve_service_package_materialization_spec,
    )  # noqa: WPS433

    spec = resolve_service_package_materialization_spec(
        service_toml_path=service_toml_path,
        workspace_root=workspace_root,
    )

    service_configs = spec.compile_plan_payload["service_configs"]
    assert isinstance(service_configs, list)
    assert service_configs[0]["experiences"] == [
        {
            "experience_ref": "home_story",
            "source_path": "services/bindings/home.services.aware",
        }
    ]


def test_committed_api_endpoint_refs_index_missing_fk_from_parent() -> None:
    from aware_api_ontology.api.api_capability_endpoint import (  # noqa: WPS433
        ApiCapabilityEndpoint,
    )
    from aware_service_runtime.materialization.service import (  # noqa: WPS433
        _insert_committed_api_endpoint_refs,
    )

    endpoint = ApiCapabilityEndpoint.model_construct(id=uuid4(), name="Search")
    parent_capability_id = uuid4()
    endpoints_by_key: dict[tuple[UUID, str], ApiCapabilityEndpoint] = {}

    _insert_committed_api_endpoint_refs(
        endpoints_by_key=endpoints_by_key,
        endpoint=endpoint,
        parent_api_capability_id=parent_capability_id,
    )

    assert endpoints_by_key[(parent_capability_id, "search")] is endpoint


def test_committed_api_endpoint_refs_keep_fk_and_parent_aliases() -> None:
    from aware_api_ontology.api.api_capability_endpoint import (  # noqa: WPS433
        ApiCapabilityEndpoint,
    )
    from aware_service_runtime.materialization.service import (  # noqa: WPS433
        _insert_committed_api_endpoint_refs,
    )

    endpoint_capability_id = uuid4()
    parent_capability_id = uuid4()
    endpoint = ApiCapabilityEndpoint.model_construct(
        id=uuid4(),
        name="Resolve",
        api_capability_id=endpoint_capability_id,
    )
    endpoints_by_key: dict[tuple[UUID, str], ApiCapabilityEndpoint] = {}

    _insert_committed_api_endpoint_refs(
        endpoints_by_key=endpoints_by_key,
        endpoint=endpoint,
        parent_api_capability_id=parent_capability_id,
    )

    assert endpoints_by_key[(endpoint_capability_id, "resolve")] is endpoint
    assert endpoints_by_key[(parent_capability_id, "resolve")] is endpoint


@pytest.mark.asyncio
async def test_committed_api_reference_context_indexes_projection_from_runtime_opg(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_service_api_ref_projection_index",
    ) as aware_root:
        runtime = _build_service_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        index = _runtime_index(runtime)

        from aware_api_runtime.ontology_graph.materialization.service import (  # noqa: WPS433
            materialize_api_graph_ontology,
        )
        from aware_service_runtime.materialization.service import (  # noqa: WPS433
            _hydrate_committed_api_reference_context,
            _resolve_committed_api_graph_projection_id,
        )

        environment_id = uuid4()
        process_id, thread_id, branch_id = await _seed_boot_environment(
            environment_id=environment_id,
        )
        api_projection_hash = _find_projection_hash_by_name(
            index=index,
            projection_name="Api",
        )
        focus_scope_projection_hash = _find_projection_hash_by_name(
            index=index,
            projection_name="FocusScope",
        )
        focus_scope_opg = index.opg_by_hash[focus_scope_projection_hash]
        lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=api_projection_hash,
        )
        graph_target = (index.ocg.fqn_prefix or index.ocg.name or "").strip()
        receipt = await materialize_api_graph_ontology(
            index=index,
            actor_id=None,
            lane=lane,
            compile_plan_payloads=(
                {
                    "api_ontology": [
                        {
                            "api": {
                                "name": "attention",
                                "description": None,
                                "source_path": "tests/attention.api.aware",
                            },
                            "graphs": [
                                {
                                    "api_name": "attention",
                                    "target": graph_target,
                                    "description": None,
                                    "source_path": "tests/attention.api.aware",
                                },
                            ],
                            "graph_projections": [
                                {
                                    "api_name": "attention",
                                    "graph_target": graph_target,
                                    "target": focus_scope_opg.name,
                                    "description": None,
                                    "source_path": "tests/attention.api.aware",
                                },
                            ],
                        }
                    ],
                },
            ),
        )
        assert receipt is not None
        context = await _hydrate_committed_api_reference_context(
            index=index,
            lane=lane,
        )
        api_id = stable_api_id(name="attention")
        graphs = context.graphs_by_api_id.get(api_id, ())
        assert len(graphs) == 1
        api_graph_id = graphs[0].id
        assert api_graph_id is not None
        expected_projection_id = stable_api_graph_projection_id(
            api_graph_id=api_graph_id,
            object_projection_graph_id=focus_scope_opg.id,
        )

        assert (
            _resolve_committed_api_graph_projection_id(
                api_context=context,
                api_ref="attention",
                projection_ref="aware_attention.FocusScope",
            )
            == expected_projection_id
        )


@pytest.mark.asyncio
async def test_committed_api_reference_context_indexes_projection_from_accessible_graph(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_service_api_ref_accessible_projection_index",
    ) as aware_root:
        runtime = _build_service_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        index = _runtime_index(runtime)

        from aware_api_runtime.ontology_graph.materialization.service import (  # noqa: WPS433
            materialize_api_graph_ontology,
        )
        from aware_service_runtime.materialization.service import (  # noqa: WPS433
            _hydrate_committed_api_reference_context,
            _resolve_committed_api_graph_projection_id,
        )

        environment_id = uuid4()
        process_id, thread_id, branch_id = await _seed_boot_environment(
            environment_id=environment_id,
        )
        api_projection_hash = _find_projection_hash_by_name(
            index=index,
            projection_name="Api",
        )
        external_graph_id = uuid5(
            NAMESPACE_URL,
            "service-package-materialization/accessibility-aware-network-ocg",
        )
        external_opg = ObjectProjectionGraph(
            id=uuid5(
                NAMESPACE_URL,
                "service-package-materialization/accessibility-network-directory-opg",
            ),
            object_config_graph_id=external_graph_id,
            name="NetworkDirectory",
            description=None,
            language=CodeLanguage.aware,
            projection_hash="sha256:network-directory",
            supports_virtual_build=True,
        )
        external_graph = ObjectConfigGraph(
            id=external_graph_id,
            name="network-ontology",
            description=None,
            hash="sha256:aware-network",
            fqn_prefix="aware_network",
            language=CodeLanguage.aware,
            object_projection_graphs=[external_opg],
        )
        lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=api_projection_hash,
        )
        receipt = await materialize_api_graph_ontology(
            index=index,
            actor_id=None,
            lane=lane,
            compile_plan_payloads=(
                {
                    "api_ontology": [
                        {
                            "api": {
                                "name": "network",
                                "description": None,
                                "source_path": "tests/network.api.aware",
                            },
                            "graphs": [
                                {
                                    "api_name": "network",
                                    "target": "aware_network",
                                    "description": None,
                                    "source_path": "tests/network.api.aware",
                                },
                            ],
                            "graph_projections": [
                                {
                                    "api_name": "network",
                                    "graph_target": "aware_network",
                                    "target": "aware_network.NetworkDirectory",
                                    "description": None,
                                    "source_path": "tests/network.api.aware",
                                },
                            ],
                        }
                    ],
                },
            ),
            extra_accessible_graphs=(external_graph,),
        )
        assert receipt is not None
        context = await _hydrate_committed_api_reference_context(
            index=index,
            lane=lane,
            accessible_graphs=(external_graph,),
        )
        api_id = stable_api_id(name="network")
        graphs = context.graphs_by_api_id.get(api_id, ())
        assert len(graphs) == 1
        api_graph_id = graphs[0].id
        assert api_graph_id is not None
        expected_projection_id = stable_api_graph_projection_id(
            api_graph_id=api_graph_id,
            object_projection_graph_id=external_opg.id,
        )

        assert (
            _resolve_committed_api_graph_projection_id(
                api_context=context,
                api_ref="network",
                projection_ref="aware_network.NetworkDirectory",
            )
            == expected_projection_id
        )


@pytest.mark.asyncio
async def test_materialize_service_package_from_manifest_commits_canonical_package_root(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "service_package_materialization"
    workspace_root.mkdir(parents=True, exist_ok=True)
    service_toml_path = _write_service_package_fixture(
        workspace_root=workspace_root,
        include_api_provider_set=True,
    )

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_service_package_materialization",
    ) as aware_root:
        runtime = _build_service_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        semantic_runtime = _FailClosedSemanticRuntime(
            manifest_path=_service_package_manifest_paths(repo_root)[-1],
        )
        index = _runtime_index(runtime)

        from aware_service_runtime.materialization import (  # noqa: WPS433
            materialize_service_package_from_manifest,
            resolve_service_package_materialization_spec,
        )
        from aware_service_runtime.materialization.service import (  # noqa: WPS433
            _api_service_protocol_artifact_hash,
        )

        spec = resolve_service_package_materialization_spec(
            service_toml_path=service_toml_path,
            workspace_root=workspace_root,
        )
        assert spec.package_name == "home-story-service"
        assert spec.service_name == "home_story"
        assert spec.service_source_path == "services/bindings/home.services.aware"
        assert spec.source_files == ("services/bindings/home.services.aware",)

        environment_id = uuid4()
        process_id, thread_id, branch_id = await _seed_boot_environment(
            environment_id=environment_id,
        )

        service_config_projection_hash = _find_projection_hash_by_name(
            index=index,
            projection_name="ServiceConfig",
        )
        service_package_projection_hash = _find_projection_hash_by_name(
            index=index,
            projection_name="ServicePackage",
        )
        code_package_projection_hash = _find_projection_hash_by_name(
            index=index,
            projection_name="CodePackage",
        )
        service_api_provider_set_projection_hash = _find_projection_hash_by_name(
            index=index,
            projection_name="ServiceApiProviderSet",
        )
        assert service_config_projection_hash
        assert service_package_projection_hash
        assert code_package_projection_hash
        assert service_api_provider_set_projection_hash

        await _materialize_committed_api_definition(
            runtime=runtime,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
        )

        result = await materialize_service_package_from_manifest(
            runtime=semantic_runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            service_toml_path=service_toml_path,
            api_reference_branch_ids_by_api_name={
                "home_devices": branch_id,
                "home-devices-api": branch_id,
            },
        )

        assert result.service_toml_path == service_toml_path.resolve()
        assert result.workspace_root == workspace_root.resolve()
        assert result.manifest_spec.service.package_name == "home-story-service"
        assert result.service_config.name == "home_story"
        assert result.service_package.name == "home-story-service"
        assert result.service_package.service_config_id == result.service_config.id
        assert result.service_config_object_instance_graph_commit_id is not None
        assert len(result.activation_lanes) == 1
        activation_lane = result.activation_lanes[0]
        assert activation_lane.service_name == "home_story"
        assert activation_lane.service_config_id == result.service_config.id
        assert activation_lane.service_config_head_commit_id is not None
        assert (
            activation_lane.service_config_object_instance_graph_commit_id is not None
        )
        assert activation_lane.service_head_commit_id is not None
        assert activation_lane.service_object_instance_graph_commit_id is not None
        assert (
            result.service_package.service_config_object_instance_graph_commit_id
            == result.service_config_object_instance_graph_commit_id
        )
        assert result.service_package.fqn_prefix == "aware_home_story_service"
        assert result.service_package.version_number == 7
        assert result.service_package.title == "Home Story Service"
        assert (
            result.service_package.description == "Home story service semantic package"
        )
        assert result.service_package.aware_service_version == 1
        assert result.service_package.manifest_relative_path == "aware.service.toml"
        assert result.service_package.package_root == "."
        assert result.service_package.sources_root == "services/bindings"
        assert list(result.service_package.include_paths) == ["**/*.aware"]
        assert list(result.service_package.exclude_paths) == ["**/*.draft.aware"]
        assert result.service_package.force_fresh_scan is False
        assert result.service_package.compilation_mode == "service_ontology"
        assert result.service_package.service_surface == "service"
        assert (
            result.service_package.activation_mode == "materialize_and_load_committed"
        )
        assert result.service_package.materialize_on_start is False
        assert list(result.service_package.dependencies) == [
            {
                "package_name": "meta-service-api",
                "version_number": 1,
                "kind": "api_invocation",
            },
        ]
        provided_api_packages = result.service_package.provided_api_packages
        assert len(provided_api_packages) == 1
        assert provided_api_packages[0].api_package_id == stable_api_package_id(
            name="home-devices-api"
        )
        provided_api_package = provided_api_packages[0]
        assert (
            provided_api_package.api_package_object_instance_graph_commit_id is not None
        )
        assert provided_api_package.service_protocol_package_id is not None
        protocol_artifact = _api_service_protocol_artifact_hash(
            workspace_root=workspace_root,
            package_name="home-devices-api",
        )
        assert protocol_artifact is not None
        assert (
            provided_api_package.service_protocol_plan_hash_sha256
            == protocol_artifact.hash_sha256
        )
        required_api_packages = result.service_package.required_api_packages
        assert len(required_api_packages) == 1
        assert required_api_packages[0].api_package_id == stable_api_package_id(
            name="meta-service-api"
        )
        assert result.service_source_path == "services/bindings/home.services.aware"
        assert result.source_files == ("services/bindings/home.services.aware",)
        source_code_package_config_id = stable_code_package_config_id(
            config_key=code_package_source_config_key(
                manifest_kind="aware_service_toml",
                surface="service",
            )
        )
        assert result.source_code_package_id == stable_code_package_id(
            code_package_config_id=source_code_package_config_id,
            package_name="home-story-service",
            language=CodeLanguage.aware.value,
        )
        implementation_code_package_config_id = stable_code_package_config_id(
            config_key=code_package_source_config_key(
                manifest_kind="pyproject_toml",
                surface="service",
            )
        )
        implementation_code_package_id = stable_code_package_id(
            code_package_config_id=implementation_code_package_config_id,
            package_name="home-story-service",
            language=CodeLanguage.python.value,
        )
        assert result.implementation_code_package_ids == (
            implementation_code_package_id,
        )
        assert len(result.implementation_code_package_refs) == 1
        implementation_code_package_ref = result.implementation_code_package_refs[0]
        assert (
            implementation_code_package_ref["code_package_id"]
            == implementation_code_package_id
        )
        implementation_code_package_branch_id = UUID(
            str(implementation_code_package_ref["branch_id"])
        )
        assert implementation_code_package_ref["domain_commit_id"] is not None
        assert (
            implementation_code_package_ref["object_instance_graph_commit_id"]
            is not None
        )
        implementation_packages = result.service_package.implementation_packages
        assert len(implementation_packages) == 1
        implementation_package = implementation_packages[0]
        assert implementation_package.code_package_id == implementation_code_package_id
        assert implementation_package.package_name == "home-story-service"
        assert implementation_package.language == CodeLanguage.python
        assert implementation_package.import_root == "aware_home_story_service"
        assert implementation_package.manifest_relative_path == "pyproject.toml"
        assert implementation_package.package_root == "."
        assert (
            implementation_package.entrypoint
            == "aware_home_story_service.service_bindings:build_service_bindings"
        )
        assert implementation_package.role == "service_bindings"
        assert result.definition_commit_id is not None
        assert result.definition_head_commit_id is not None
        assert result.service_config_object_instance_graph_commit_id is not None
        assert result.package_commit_id is not None
        assert result.package_head_commit_id is not None
        assert result.package_object_instance_graph_commit_id is not None
        expected_provider_set_id = stable_service_api_provider_set_id(
            key="kernel.global_services.v1",
        )
        expected_provider_set_membership_id = (
            stable_service_api_provider_set_service_package_id(
                service_api_provider_set_id=expected_provider_set_id,
                service_package_id=result.service_package.id,
            )
        )
        assert result.api_provider_set_commit_id is not None
        assert result.api_provider_set_head_commit_id is not None
        assert len(result.api_provider_set_refs) == 1
        provider_set_ref = result.api_provider_set_refs[0]
        provider_set_branch_id = UUID(str(provider_set_ref["provider_set_branch_id"]))
        assert provider_set_ref == {
            "provider_set_key": "kernel.global_services.v1",
            "provider_set_id": expected_provider_set_id,
            "provider_set_branch_id": provider_set_branch_id,
            "provider_set_commit_id": result.api_provider_set_commit_id,
            "provider_set_object_instance_graph_commit_id": (
                result.api_provider_set_head_commit_id
            ),
            "service_package_id": result.service_package.id,
            "service_package_name": "home-story-service",
            "membership_id": expected_provider_set_membership_id,
            "membership_key": "kernel-services-host",
            "title": "Kernel Global Services",
            "description": "Kernel global service providers.",
        }
        assert (
            await FSCommitStore().domain_commit_id_for_object_instance_graph_commit_id(
                branch_id=branch_id,
                projection_hash=service_package_projection_hash,
                object_instance_graph_commit_id=(
                    result.package_object_instance_graph_commit_id
                ),
            )
            == result.package_commit_id
        )
        assert (
            await FSCommitStore().domain_commit_id_for_object_instance_graph_commit_id(
                branch_id=provider_set_branch_id,
                projection_hash=service_api_provider_set_projection_hash,
                object_instance_graph_commit_id=result.api_provider_set_head_commit_id,
            )
            == result.api_provider_set_commit_id
        )

        service_config_session = await _hydrate_projection_session(
            runtime=runtime,
            branch_id=branch_id,
            projection_hash=service_config_projection_hash,
        )
        service_endpoint_bindings = [
            obj
            for obj in service_config_session.imap_all_objects()
            if isinstance(obj, ServiceOperationConfigApiEndpoint)
        ]
        service_endpoint_function_bindings = [
            obj
            for obj in service_config_session.imap_all_objects()
            if isinstance(obj, ServiceOperationConfigApiEndpointFunction)
        ]
        assert len(service_endpoint_bindings) == 1
        assert len(service_endpoint_function_bindings) == 1

        code_package_session = await _hydrate_projection_session(
            runtime=runtime,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
        )
        code_packages = [
            obj
            for obj in code_package_session.imap_all_objects()
            if isinstance(obj, CodePackage)
        ]
        assert len(code_packages) == 1
        code_package = code_packages[0]
        assert code_package.id == result.source_code_package_id
        assert code_package.code_package_config_id == source_code_package_config_id
        assert code_package.package_name == "home-story-service"
        assert code_package.language == CodeLanguage.aware
        assert code_package.surface == "service"
        assert code_package.manifest_relative_path == "aware.service.toml"
        assert code_package.package_root == "."
        assert code_package.sources_root == "services/bindings"
        codes = [
            obj
            for obj in code_package_session.imap_all_objects()
            if isinstance(obj, Code)
        ]
        assert {code.relative_path for code in codes} == {
            "aware.service.toml",
            "services/bindings/home.services.aware",
        }

        implementation_code_package_session = await _hydrate_projection_session(
            runtime=runtime,
            branch_id=implementation_code_package_branch_id,
            projection_hash=code_package_projection_hash,
        )
        implementation_code_packages = [
            obj
            for obj in implementation_code_package_session.imap_all_objects()
            if isinstance(obj, CodePackage)
        ]
        assert len(implementation_code_packages) == 1
        implementation_code_package = implementation_code_packages[0]
        assert implementation_code_package.id == implementation_code_package_id
        assert (
            implementation_code_package.code_package_config_id
            == implementation_code_package_config_id
        )
        assert implementation_code_package.package_name == "home-story-service"
        assert implementation_code_package.language == CodeLanguage.python
        assert implementation_code_package.surface == "service"
        assert implementation_code_package.manifest_relative_path == "pyproject.toml"
        assert implementation_code_package.package_root == "."
        assert implementation_code_package.sources_root == "aware_home_story_service"
        implementation_codes = [
            obj
            for obj in implementation_code_package_session.imap_all_objects()
            if isinstance(obj, Code)
        ]
        assert {code.relative_path for code in implementation_codes} == {
            "pyproject.toml",
            "README.md",
            "aware_home_story_service/__init__.py",
            "aware_home_story_service/py.typed",
            "aware_home_story_service/service_bindings.py",
        }
        provider_set_session = await _hydrate_projection_session(
            runtime=runtime,
            branch_id=provider_set_branch_id,
            projection_hash=service_api_provider_set_projection_hash,
        )
        provider_sets = [
            obj
            for obj in provider_set_session.imap_all_objects()
            if isinstance(obj, ServiceApiProviderSet)
        ]
        provider_set_memberships = [
            obj
            for obj in provider_set_session.imap_all_objects()
            if isinstance(obj, ServiceApiProviderSetServicePackage)
        ]
        assert len(provider_sets) == 1
        assert provider_sets[0].id == expected_provider_set_id
        assert provider_sets[0].key == "kernel.global_services.v1"
        assert provider_sets[0].title == "Kernel Global Services"
        assert len(provider_set_memberships) == 1
        assert provider_set_memberships[0].id == expected_provider_set_membership_id
        assert (
            provider_set_memberships[0].service_package_id == result.service_package.id
        )
        assert provider_set_memberships[0].membership_key == "kernel-services-host"

        rerun = await materialize_service_package_from_manifest(
            runtime=semantic_runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            service_toml_path=service_toml_path,
            api_reference_branch_ids_by_api_name={
                "home_devices": branch_id,
                "home-devices-api": branch_id,
            },
        )
        assert rerun.service_config.id == result.service_config.id
        assert rerun.service_package.id == result.service_package.id
        assert (
            rerun.service_config_object_instance_graph_commit_id
            == result.service_config_object_instance_graph_commit_id
        )
        assert len(rerun.api_provider_set_refs) == 1
        assert (
            rerun.api_provider_set_refs[0]["provider_set_id"]
            == expected_provider_set_id
        )
        assert (
            rerun.api_provider_set_refs[0]["membership_id"]
            == expected_provider_set_membership_id
        )
        rerun_provider_set_session = await _hydrate_projection_session(
            runtime=runtime,
            branch_id=provider_set_branch_id,
            projection_hash=service_api_provider_set_projection_hash,
        )
        assert (
            len(
                [
                    obj
                    for obj in rerun_provider_set_session.imap_all_objects()
                    if isinstance(obj, ServiceApiProviderSetServicePackage)
                ]
            )
            == 1
        )


@pytest.mark.asyncio
async def test_materialize_service_package_from_manifest_accepts_committed_api_refs_from_other_branch(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "service_package_materialization_api_ref_branch"
    workspace_root.mkdir(parents=True, exist_ok=True)
    service_toml_path = _write_service_package_fixture(workspace_root=workspace_root)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_service_package_materialization_api_ref_branch",
    ) as aware_root:
        runtime = _build_service_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        semantic_runtime = _FailClosedSemanticRuntime(
            manifest_path=_service_package_manifest_paths(repo_root)[-1],
        )
        index = _runtime_index(runtime)

        from aware_service_runtime.materialization import (
            materialize_service_package_from_manifest,
        )  # noqa: WPS433

        environment_id = uuid4()
        process_id, thread_id, api_branch_id = await _seed_boot_environment(
            environment_id=environment_id,
        )
        service_branch_id = uuid4()

        await _materialize_committed_api_definition(
            runtime=runtime,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=api_branch_id,
        )

        result = await materialize_service_package_from_manifest(
            runtime=semantic_runtime,
            index=index,
            actor_id=None,
            branch_id=service_branch_id,
            workspace_root=workspace_root,
            service_toml_path=service_toml_path,
            api_reference_branch_ids_by_api_name={
                "home_devices": api_branch_id,
                "home-devices-api": api_branch_id,
            },
            api_reference_commit_store_roots_by_api_name={
                "home-devices-api": aware_root,
            },
        )

        assert result.service_config.name == "home_story"
        assert result.service_package.name == "home-story-service"
        assert result.service_package.service_config_id == result.service_config.id
        assert result.service_config_object_instance_graph_commit_id is not None
