from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import TypeVar
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.runtime import reify_meta_orm_root_from_oig_commit
from aware_meta_sdk import FunctionCallProof, OigCommitExpectation
from aware_meta_service.local_sdk import (
    build_local_meta_sdk_session_for_aware_package_manifests,
)
from aware_orm.models.orm_model import ORMModel

from ._environment_runtime_test_paths import (
    REPO_ROOT,
    environment_package_manifest_paths,
)

_TRoot = TypeVar("_TRoot", bound=ORMModel)


@dataclass(frozen=True, slots=True)
class IsolatedMetaAwareRoot:
    root: Path
    persistence_backend: str = "fs"
    _env_overrides: dict[str, str | None] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    def __enter__(self) -> Path:
        root = self.root.expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        (root / ".aware").mkdir(parents=True, exist_ok=True)
        env_overrides = {
            "AWARE_ROOT": os.environ.get("AWARE_ROOT"),
            "AWARE_META_SERVICE_EVENT_STORE_ROOT": os.environ.get(
                "AWARE_META_SERVICE_EVENT_STORE_ROOT",
            ),
            "AWARE_PERSISTENCE_BACKEND": os.environ.get(
                "AWARE_PERSISTENCE_BACKEND",
            ),
            "DATABASE_URL": os.environ.get("DATABASE_URL"),
        }
        object.__setattr__(self, "_env_overrides", env_overrides)
        os.environ["AWARE_ROOT"] = str(root)
        os.environ["AWARE_META_SERVICE_EVENT_STORE_ROOT"] = str(
            root / ".aware" / "meta-events",
        )
        os.environ["AWARE_PERSISTENCE_BACKEND"] = self.persistence_backend
        os.environ.pop("DATABASE_URL", None)
        return root

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        for key, previous in self._env_overrides.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous


def _record_by_function(records, *, function_name: str):
    matches = [record for record in records if record.function_name == function_name]
    assert len(matches) == 1
    return matches[0]


async def _rehydrate_lane_root_from_head(
    *,
    meta_session,
    aware_root: Path,
    branch_id: UUID,
    projection_name: str,
    root_id: UUID,
    root_type: type[_TRoot],
) -> _TRoot:
    graph_context = meta_session.service_session.resolver.graph_context
    projection_hash = meta_session.projection_hash(projection_name)
    commit_store = FSCommitStore(root_dir=aware_root)
    head = await commit_store.head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head is not None
    commit_id = UUID(str(head["commit_id"]))
    root = await reify_meta_orm_root_from_oig_commit(
        index=graph_context.index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        projection_name=projection_name,
        commit_id=commit_id,
        root_id=root_id,
        root_type=root_type,
        commit_store=commit_store,
        snapshot_store=FSSnapshotStore(root_dir=aware_root),
    )
    assert root is not None
    return root


def _environment_environment_config_package_manifest_paths(
    repo_root: Path,
) -> tuple[Path, ...]:
    return environment_package_manifest_paths(repo_root)


@pytest.mark.asyncio
async def test_environment_config_meta_runtime_commits_without_structure(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    package_manifest_paths = _environment_environment_config_package_manifest_paths(
        repo_root,
    )

    from aware_code_ontology.code.code_enums import CodeLanguage  # noqa: WPS433
    from aware_environment.handlers._generated import (  # noqa: WPS433
        meta_handlers as environment_meta_handlers,
    )
    from aware_environment_ontology.environment.environment_config import (  # noqa: WPS433
        EnvironmentConfig,
    )
    from aware_environment_ontology.environment.environment_config_package import (  # noqa: WPS433
        EnvironmentConfigPackage,
    )
    from aware_environment_ontology.environment.environment_config_package_dependency import (  # noqa: WPS433
        EnvironmentConfigPackageDependency,
    )
    from aware_environment_ontology.environment.environment_config_package_ontology_package import (  # noqa: WPS433
        EnvironmentConfigPackageOntologyPackage,
    )
    from aware_environment_ontology.stable_ids import (  # noqa: WPS433
        stable_environment_config_id,
        stable_environment_config_ontology_config_id,
        stable_environment_config_package_dependency_id,
        stable_environment_config_package_id,
        stable_environment_config_package_ontology_package_id,
    )
    from aware_ontology_ontology.stable_ids import (  # noqa: WPS433
        stable_ontology_config_id,
        stable_ontology_package_id,
    )

    actor_id = uuid5(NAMESPACE_URL, "aware://tests/environment/env-config/actor")
    environment_handle = "pytest.kernel"
    base_environment_handle = "pytest.base"
    ontology_name = "pytest-ontology"
    ontology_fqn_prefix = "pytest"
    ontology_config_commit_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/env-config/ontology-config-commit",
    )
    ontology_package_commit_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/env-config/ontology-package-commit",
    )
    base_package_commit_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/env-config/base-package-commit",
    )

    expected_config_id = stable_environment_config_id(handle=environment_handle)
    expected_base_config_id = stable_environment_config_id(
        handle=base_environment_handle,
    )
    expected_package_id = stable_environment_config_package_id(
        handle=environment_handle,
    )
    expected_base_package_id = stable_environment_config_package_id(
        handle=base_environment_handle,
    )
    expected_ontology_config_id = stable_ontology_config_id(
        name=ontology_name,
        fqn_prefix=ontology_fqn_prefix,
    )
    expected_ontology_config_edge_id = stable_environment_config_ontology_config_id(
        environment_config_id=expected_config_id,
        name=ontology_name,
        fqn_prefix=ontology_fqn_prefix,
    )
    expected_ontology_package_id = stable_ontology_package_id(
        name=ontology_name,
        fqn_prefix=ontology_fqn_prefix,
    )
    expected_ontology_package_edge_id = (
        stable_environment_config_package_ontology_package_id(
            environment_config_package_id=expected_package_id,
            name=ontology_name,
            fqn_prefix=ontology_fqn_prefix,
        )
    )
    expected_dependency_id = stable_environment_config_package_dependency_id(
        environment_config_package_id=expected_package_id,
        dependency_role="base",
        dependency_index=0,
        target_handle=base_environment_handle,
        target_environment_config_package_id=expected_base_package_id,
        target_environment_config_package_object_instance_graph_commit_id=(
            base_package_commit_id
        ),
    )

    config_build_proof = FunctionCallProof(
        function_key="EnvironmentConfig.build",
        commit_expectation=OigCommitExpectation(
            label="EnvironmentConfig.build",
            expected_domain_branch_id=expected_config_id,
            expected_root_object_id=expected_config_id,
        ),
    )
    config_attach_proof = FunctionCallProof(
        function_key="EnvironmentConfig.attach_ontology_config",
        commit_expectation=OigCommitExpectation(
            label="EnvironmentConfig.attach_ontology_config",
            expected_domain_branch_id=expected_config_id,
            expected_root_object_id=expected_config_id,
        ),
    )
    package_build_proof = FunctionCallProof(
        function_key="EnvironmentConfigPackage.build",
        commit_expectation=OigCommitExpectation(
            label="EnvironmentConfigPackage.build",
            expected_domain_branch_id=expected_package_id,
            expected_root_object_id=expected_package_id,
        ),
    )
    package_attach_ontology_proof = FunctionCallProof(
        function_key="EnvironmentConfigPackage.attach_ontology_package",
        commit_expectation=OigCommitExpectation(
            label="EnvironmentConfigPackage.attach_ontology_package",
            expected_domain_branch_id=expected_package_id,
            expected_root_object_id=expected_package_id,
        ),
    )
    package_attach_dependency_proof = FunctionCallProof(
        function_key="EnvironmentConfigPackage.attach_dependency",
        commit_expectation=OigCommitExpectation(
            label="EnvironmentConfigPackage.attach_dependency",
            require_domain_commit_id=False,
            require_object_instance_graph_commit_id=False,
            require_graph_hash_post=False,
            expected_domain_branch_id=expected_package_id,
            expected_root_object_id=expected_package_id,
        ),
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        meta_session = build_local_meta_sdk_session_for_aware_package_manifests(
            package_manifest_paths=package_manifest_paths,
            workspace_root=repo_root,
            aware_root=aware_root,
            composite_name="Aware Environment EnvironmentConfig Meta SDK Proof",
            projection_name="EnvironmentConfig",
            actor_id=actor_id,
            branch_id=expected_config_id,
            generated_language_handler_module=environment_meta_handlers,
        )

        config_lane = meta_session.bind(
            projection="EnvironmentConfig",
            actor_id=actor_id,
            branch_id=expected_config_id,
        )
        with config_lane.activate(commit=True, publish=False):
            environment_config = await EnvironmentConfig.build(
                handle=environment_handle,
                title="Pytest Kernel Environment",
                canonical_language=CodeLanguage.aware,
                languages=[CodeLanguage.aware, CodeLanguage.python],
                description="EnvironmentConfig meta runtime proof",
                is_kernel=True,
            )
        with config_lane.activate(commit=True, publish=False):
            ontology_config_edge = await environment_config.attach_ontology_config(
                name=ontology_name,
                fqn_prefix=ontology_fqn_prefix,
                ontology_config_object_instance_graph_commit_id=(
                    ontology_config_commit_id
                ),
            )

        base_config_lane = meta_session.bind(
            projection="EnvironmentConfig",
            actor_id=actor_id,
            branch_id=expected_base_config_id,
        )
        with base_config_lane.activate(commit=True, publish=False):
            await EnvironmentConfig.build(
                handle=base_environment_handle,
                title="Pytest Base Environment",
                canonical_language=CodeLanguage.aware,
                languages=[CodeLanguage.aware],
            )

        package_lane = meta_session.bind(
            projection="EnvironmentConfigPackage",
            actor_id=actor_id,
            branch_id=expected_package_id,
        )
        with package_lane.activate(commit=True, publish=False):
            environment_package = await EnvironmentConfigPackage.build(
                handle=environment_handle,
                environment_config_id=expected_config_id,
            )
        with package_lane.activate(commit=True, publish=False):
            ontology_package_edge = await environment_package.attach_ontology_package(
                name=ontology_name,
                fqn_prefix=ontology_fqn_prefix,
                ontology_package_object_instance_graph_commit_id=(
                    ontology_package_commit_id
                ),
            )
        with package_lane.activate(commit=True, publish=False):
            dependency_edge = await environment_package.attach_dependency(
                dependency_role="base",
                dependency_index=0,
                target_handle=base_environment_handle,
                target_environment_config_package_id=expected_base_package_id,
                target_environment_config_package_object_instance_graph_commit_id=(
                    base_package_commit_id
                ),
            )

        assert environment_config.id == expected_config_id
        assert ontology_config_edge.id == expected_ontology_config_edge_id
        assert ontology_config_edge.ontology_config_id == expected_ontology_config_id
        assert (
            ontology_config_edge.ontology_config_object_instance_graph_commit_id
            == ontology_config_commit_id
        )
        assert environment_package.id == expected_package_id
        assert environment_package.environment_config_id == expected_config_id
        assert ontology_package_edge.id == expected_ontology_package_edge_id
        assert ontology_package_edge.ontology_package_id == expected_ontology_package_id
        assert (
            ontology_package_edge.ontology_package_object_instance_graph_commit_id
            == ontology_package_commit_id
        )
        assert dependency_edge.id == expected_dependency_id
        assert dependency_edge.target_environment_config_package_id == (
            expected_base_package_id
        )

        config_build_proof.assert_matches(
            _record_by_function(config_lane.records, function_name="build").response,
        )
        config_attach_proof.assert_matches(
            _record_by_function(
                config_lane.records,
                function_name="attach_ontology_config",
            ).response,
        )
        package_build_proof.assert_matches(
            _record_by_function(package_lane.records, function_name="build").response,
        )
        package_attach_ontology_proof.assert_matches(
            _record_by_function(
                package_lane.records,
                function_name="attach_ontology_package",
            ).response,
        )
        package_attach_dependency_proof.assert_matches(
            _record_by_function(
                package_lane.records,
                function_name="attach_dependency",
            ).response,
        )

        config_head = await config_lane.get_head()
        assert config_head.status == "succeeded"
        assert config_head.root_object_id == expected_config_id
        package_head = await package_lane.get_head()
        assert package_head.status == "succeeded"
        assert package_head.root_object_id == expected_package_id

        committed_config = await _rehydrate_lane_root_from_head(
            meta_session=meta_session,
            aware_root=aware_root,
            branch_id=expected_config_id,
            projection_name="EnvironmentConfig",
            root_id=expected_config_id,
            root_type=EnvironmentConfig,
        )
        assert committed_config.id == expected_config_id
        assert [edge.id for edge in committed_config.ontology_configs] == [
            expected_ontology_config_edge_id,
        ]
        committed_package = await _rehydrate_lane_root_from_head(
            meta_session=meta_session,
            aware_root=aware_root,
            branch_id=expected_package_id,
            projection_name="EnvironmentConfigPackage",
            root_id=expected_package_id,
            root_type=EnvironmentConfigPackage,
        )
        assert committed_package.id == expected_package_id
        assert [
            edge.id
            for edge in committed_package.ontology_packages
            if isinstance(edge, EnvironmentConfigPackageOntologyPackage)
        ] == [expected_ontology_package_edge_id]
        assert [
            edge.id
            for edge in committed_package.dependencies
            if isinstance(edge, EnvironmentConfigPackageDependency)
        ] == [expected_dependency_id]
