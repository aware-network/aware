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
            "AWARE_PERSISTENCE_BACKEND": os.environ.get(
                "AWARE_PERSISTENCE_BACKEND",
            ),
            "DATABASE_URL": os.environ.get("DATABASE_URL"),
            "AWARE_META_SERVICE_EVENT_STORE_ROOT": os.environ.get(
                "AWARE_META_SERVICE_EVENT_STORE_ROOT",
            ),
        }
        object.__setattr__(self, "_env_overrides", env_overrides)
        os.environ["AWARE_ROOT"] = str(root)
        os.environ["AWARE_META_SERVICE_EVENT_STORE_ROOT"] = str(
            root / ".aware" / "meta-service-events",
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


def _environment_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return environment_package_manifest_paths(repo_root)


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


@pytest.mark.asyncio
async def test_environment_profile_topology_meta_runtime_commits(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    package_manifest_paths = _environment_package_manifest_paths(repo_root)

    from aware_environment.handlers._generated import (  # noqa: WPS433
        meta_handlers as environment_meta_handlers,
    )
    from aware_attention_ontology.stable_ids import (  # noqa: WPS433
        stable_layout_config_id,
        stable_layout_config_section_config_id,
    )
    from aware_environment_ontology.environment.environment import (  # noqa: WPS433
        Environment,
    )
    from aware_environment_ontology.environment.environment_profile import (  # noqa: WPS433
        EnvironmentProfile,
    )
    from aware_environment_ontology.environment.environment_profile_config import (  # noqa: WPS433
        EnvironmentProfileConfig,
    )
    from aware_environment_ontology.process.process_config import (  # noqa: WPS433
        ProcessConfig,
    )
    from aware_environment_ontology.process.process import (  # noqa: WPS433
        Process,
    )
    from aware_environment_ontology.stable_ids import (  # noqa: WPS433
        stable_environment_config_id,
        stable_environment_id,
        stable_environment_profile_id,
        stable_environment_profile_config_id,
        stable_process_config_id,
        stable_process_id,
        stable_thread_config_id,
        stable_thread_config_layout_config_id,
        stable_thread_config_layout_config_section_id,
        stable_thread_config_object_projection_graph_id,
        stable_thread_id,
    )
    from aware_environment_ontology.thread.thread_config import (  # noqa: WPS433
        ThreadConfig,
    )
    from aware_environment_ontology.thread.thread_config_layout_config import (  # noqa: WPS433
        ThreadConfigLayoutConfig,
    )

    environment_key = "pytest.environment"
    profile_key = "os.default"
    process_config_key = "workspace.process"
    process_key = "runtime.process"
    thread_config_key = "workspace.thread"
    thread_key = "runtime.thread"
    layout_key = "personal"
    layout_section_key = "identity_admission"

    actor_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/environment-profile/actor",
    )
    expected_environment_id = stable_environment_id(key=environment_key)
    environment_config_id = stable_environment_config_id(handle=environment_key)
    expected_profile_config_id = stable_environment_profile_config_id(
        environment_config_id=environment_config_id,
        key=profile_key,
    )
    expected_profile_id = stable_environment_profile_id(
        environment_id=expected_environment_id,
        profile_config_id=expected_profile_config_id,
    )
    expected_process_config_id = stable_process_config_id(
        environment_profile_config_id=expected_profile_config_id,
        key=process_config_key,
    )
    expected_process_id = stable_process_id(
        environment_profile_id=expected_profile_id,
        process_config_id=expected_process_config_id,
        key=process_key,
    )
    expected_thread_config_id = stable_thread_config_id(
        process_config_id=expected_process_config_id,
        key=thread_config_key,
    )
    expected_thread_id = stable_thread_id(
        thread_config_id=expected_thread_config_id,
        process_id=expected_process_id,
        key=thread_key,
    )
    expected_layout_config_id = stable_layout_config_id(key=layout_key)
    expected_thread_layout_config_id = stable_thread_config_layout_config_id(
        thread_config_id=expected_thread_config_id,
        layout_config_id=expected_layout_config_id,
    )
    expected_layout_config_section_config_id = stable_layout_config_section_config_id(
        layout_config_id=expected_layout_config_id,
        section_key=layout_section_key,
    )
    expected_thread_layout_config_section_id = (
        stable_thread_config_layout_config_section_id(
            thread_config_layout_config_id=expected_thread_layout_config_id,
            layout_config_section_config_id=expected_layout_config_section_config_id,
        )
    )

    environment_build_proof = FunctionCallProof(
        function_key="Environment.build",
        commit_expectation=OigCommitExpectation(
            label="Environment.build",
            expected_domain_branch_id=expected_environment_id,
            expected_root_object_id=expected_environment_id,
        ),
    )
    environment_apply_profile_proof = FunctionCallProof(
        function_key="Environment.apply_profile",
        commit_expectation=OigCommitExpectation(
            label="Environment.apply_profile",
            require_domain_commit_id=False,
            require_object_instance_graph_commit_id=False,
            require_graph_hash_post=False,
            expected_domain_branch_id=expected_environment_id,
            require_root_object_id=False,
        ),
    )
    profile_build_proof = FunctionCallProof(
        function_key="EnvironmentProfile.build_via_environment",
        commit_expectation=OigCommitExpectation(
            label="EnvironmentProfile.build_via_environment",
            require_domain_commit_id=False,
            require_object_instance_graph_commit_id=False,
            require_graph_hash_post=False,
            expected_domain_branch_id=expected_profile_id,
            expected_root_object_id=expected_profile_id,
        ),
    )
    profile_config_build_proof = FunctionCallProof(
        function_key="EnvironmentProfileConfig.build_via_environment_config",
        commit_expectation=OigCommitExpectation(
            label="EnvironmentProfileConfig.build_via_environment_config",
            expected_domain_branch_id=expected_profile_config_id,
            expected_root_object_id=expected_profile_config_id,
        ),
    )
    profile_config_create_process_config_proof = FunctionCallProof(
        function_key="EnvironmentProfileConfig.create_process_config",
        commit_expectation=OigCommitExpectation(
            label="EnvironmentProfileConfig.create_process_config",
            expected_domain_branch_id=expected_profile_config_id,
            expected_root_object_id=expected_profile_config_id,
        ),
    )
    profile_create_process_proof = FunctionCallProof(
        function_key="EnvironmentProfile.create_process",
        commit_expectation=OigCommitExpectation(
            label="EnvironmentProfile.create_process",
            require_domain_commit_id=False,
            require_object_instance_graph_commit_id=False,
            require_graph_hash_post=False,
            expected_domain_branch_id=expected_profile_id,
            expected_root_object_id=expected_profile_id,
        ),
    )
    process_build_proof = FunctionCallProof(
        function_key="Process.build_via_environment_profile",
        commit_expectation=OigCommitExpectation(
            label="Process.build_via_environment_profile",
            require_domain_commit_id=False,
            require_object_instance_graph_commit_id=False,
            require_graph_hash_post=False,
            expected_domain_branch_id=expected_process_id,
            expected_root_object_id=expected_process_id,
        ),
    )
    process_create_thread_config_proof = FunctionCallProof(
        function_key="ProcessConfig.create_thread_config",
        commit_expectation=OigCommitExpectation(
            label="ProcessConfig.create_thread_config",
            expected_domain_branch_id=expected_profile_config_id,
            expected_root_object_id=expected_profile_config_id,
        ),
    )
    process_create_thread_proof = FunctionCallProof(
        function_key="Process.create_thread",
        commit_expectation=OigCommitExpectation(
            label="Process.create_thread",
            require_domain_commit_id=False,
            require_object_instance_graph_commit_id=False,
            require_graph_hash_post=False,
            expected_domain_branch_id=expected_process_id,
            expected_root_object_id=expected_process_id,
        ),
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        meta_session = build_local_meta_sdk_session_for_aware_package_manifests(
            package_manifest_paths=package_manifest_paths,
            workspace_root=repo_root,
            aware_root=aware_root,
            composite_name="Aware Environment Environment Profile Meta SDK Proof",
            projection_name="Environment",
            actor_id=actor_id,
            branch_id=expected_environment_id,
            generated_language_handler_module=environment_meta_handlers,
        )
        environment_lane = meta_session.bind(
            projection="Environment",
            actor_id=actor_id,
            branch_id=expected_environment_id,
        )
        with environment_lane.activate(commit=True, publish=False):
            environment = await Environment.build(
                key=environment_key,
                title="Pytest Environment",
            )

        with environment_lane.activate(commit=True, publish=False):
            profile_from_environment = await environment.apply_profile(
                profile_config_id=expected_profile_config_id,
                title="Default OS",
            )

        assert environment.id == expected_environment_id
        assert environment.config_id == environment_config_id
        assert profile_from_environment.id == expected_profile_id

        profile_config_lane = meta_session.bind(
            projection="EnvironmentProfileConfig",
            actor_id=actor_id,
            branch_id=expected_profile_config_id,
        )
        with profile_config_lane.activate(commit=True, publish=False):
            profile_config = await EnvironmentProfileConfig.build_via_environment_config(
                environment_config_id=environment_config_id,
                key=profile_key,
                title="Default OS",
            )

        profile_lane = meta_session.bind(
            projection="EnvironmentProfile",
            actor_id=actor_id,
            branch_id=expected_profile_id,
        )
        profile_projection_hash = meta_session.projection_hash("EnvironmentProfile")
        profile_object_projection_graph_id = (
            meta_session.service_session.resolver.graph_context.index.opg_by_hash[
                profile_projection_hash
            ].id
        )
        with profile_lane.activate(commit=True, publish=False):
            profile = await EnvironmentProfile.build_via_environment(
                environment_id=expected_environment_id,
                profile_config_id=expected_profile_config_id,
                title="Default OS",
            )

        with profile_config_lane.activate(commit=True, publish=False):
            process_config = await profile_config.create_process_config(
                type="workspace",
                key=process_config_key,
                title="Workspace Process",
                is_default=True,
            )

        with profile_lane.activate(commit=True, publish=False):
            process = await profile.create_process(
                process_config_id=expected_process_config_id,
                key=process_key,
                title="Runtime Process",
            )

        with profile_config_lane.activate(commit=True, publish=False):
            thread_config = await process_config.create_thread_config(
                key=thread_config_key,
                title="Workspace Thread",
                is_default=True,
            )

        process_lane = meta_session.bind(
            projection="Process",
            actor_id=actor_id,
            branch_id=expected_process_id,
        )
        with process_lane.activate(commit=True, publish=False):
            process_root = await Process.build_via_environment_profile(
                environment_profile_id=expected_profile_id,
                process_config_id=expected_process_config_id,
                key=process_key,
                title="Runtime Process",
            )

        with process_lane.activate(commit=True, publish=False):
            thread = await process_root.create_thread(
                thread_config_id=expected_thread_config_id,
                key=thread_key,
                title="Runtime Thread",
                is_main=True,
            )
        with profile_config_lane.activate(commit=True, publish=False):
            thread_projection = await thread_config.add_object_projection_graph(
                object_projection_graph_id=profile_object_projection_graph_id,
                view_key="profile",
                is_default=True,
            )
        with profile_config_lane.activate(commit=True, publish=False):
            thread_layout_config = await thread_config.add_layout_config(
                layout_config_id=expected_layout_config_id,
                key=layout_key,
                position=0,
            )
        with profile_config_lane.activate(commit=True, publish=False):
            thread_layout_config_section = await thread_layout_config.add_section(
                layout_config_section_config_id=(
                    expected_layout_config_section_config_id
                ),
                object_projection_graph_id=profile_object_projection_graph_id,
                key=layout_section_key,
                position=0,
                is_default=True,
            )

        assert profile_config.id == expected_profile_config_id
        assert profile.id == expected_profile_id
        assert process_config.id == expected_process_config_id
        assert process_config.is_default is True
        assert process.id == expected_process_id
        assert thread_config.id == expected_thread_config_id
        assert thread_config.is_default is True
        assert thread.id == expected_thread_id
        assert thread.process_id == expected_process_id
        assert thread_projection.id == stable_thread_config_object_projection_graph_id(
            thread_config_id=expected_thread_config_id,
            object_projection_graph_id=profile_object_projection_graph_id,
        )
        assert thread_layout_config.id == expected_thread_layout_config_id
        assert (
            thread_layout_config_section.id == expected_thread_layout_config_section_id
        )

        environment_build_proof.assert_matches(
            _record_by_function(
                environment_lane.records, function_name="build"
            ).response,
        )
        environment_apply_profile_proof.assert_matches(
            _record_by_function(
                environment_lane.records,
                function_name="apply_profile",
            ).response,
        )
        profile_build_proof.assert_matches(
            _record_by_function(
                profile_lane.records,
                function_name="build_via_environment",
            ).response,
        )
        profile_config_build_proof.assert_matches(
            _record_by_function(
                profile_config_lane.records,
                function_name="build_via_environment_config",
            ).response,
        )
        profile_config_create_process_config_proof.assert_matches(
            _record_by_function(
                profile_config_lane.records,
                function_name="create_process_config",
            ).response,
        )
        profile_create_process_proof.assert_matches(
            _record_by_function(
                profile_lane.records,
                function_name="create_process",
            ).response,
        )
        process_build_proof.assert_matches(
            _record_by_function(
                process_lane.records,
                function_name="build_via_environment_profile",
            ).response,
        )
        process_create_thread_config_proof.assert_matches(
            _record_by_function(
                profile_config_lane.records,
                function_name="create_thread_config",
            ).response,
        )
        process_create_thread_proof.assert_matches(
            _record_by_function(
                process_lane.records,
                function_name="create_thread",
            ).response,
        )

        environment_head = await environment_lane.get_head()
        assert environment_head.status == "succeeded"
        assert environment_head.root_object_id == expected_environment_id
        profile_head = await profile_lane.get_head()
        assert profile_head.status == "succeeded"
        assert profile_head.root_object_id == expected_profile_id
        profile_config_head = await profile_config_lane.get_head()
        assert profile_config_head.status == "succeeded"
        assert profile_config_head.root_object_id == expected_profile_config_id
        process_head = await process_lane.get_head()
        assert process_head.status == "succeeded"
        assert process_head.root_object_id == expected_process_id

        committed_environment = await _rehydrate_lane_root_from_head(
            meta_session=meta_session,
            aware_root=aware_root,
            branch_id=expected_environment_id,
            projection_name="Environment",
            root_id=expected_environment_id,
            root_type=Environment,
        )
        assert committed_environment.id == expected_environment_id
        assert committed_environment.config_id == environment_config_id

        committed_profile = await _rehydrate_lane_root_from_head(
            meta_session=meta_session,
            aware_root=aware_root,
            branch_id=expected_profile_id,
            projection_name="EnvironmentProfile",
            root_id=expected_profile_id,
            root_type=EnvironmentProfile,
        )
        assert committed_profile.id == expected_profile_id
        committed_profile_config = await _rehydrate_lane_root_from_head(
            meta_session=meta_session,
            aware_root=aware_root,
            branch_id=expected_profile_config_id,
            projection_name="EnvironmentProfileConfig",
            root_id=expected_profile_config_id,
            root_type=EnvironmentProfileConfig,
        )
        assert committed_profile_config.id == expected_profile_config_id
        committed_process_config = next(
            item
            for item in committed_profile_config.process_configs
            if item.id == expected_process_config_id
        )
        assert isinstance(committed_process_config, ProcessConfig)
        assert committed_process_config.is_default is True
        committed_thread_config = next(
            item
            for item in committed_process_config.thread_configs
            if item.id == expected_thread_config_id
        )
        assert isinstance(committed_thread_config, ThreadConfig)
        assert committed_thread_config.is_default is True

        committed_process = await _rehydrate_lane_root_from_head(
            meta_session=meta_session,
            aware_root=aware_root,
            branch_id=expected_process_id,
            projection_name="Process",
            root_id=expected_process_id,
            root_type=Process,
        )
        assert committed_process.id == expected_process_id
        committed_thread_layout_config = next(
            item
            for item in committed_thread_config.layout_configs
            if item.id == expected_thread_layout_config_id
        )
        assert isinstance(committed_thread_layout_config, ThreadConfigLayoutConfig)
        assert [section.id for section in committed_thread_layout_config.sections] == [
            expected_thread_layout_config_section_id,
        ]

        thread_commit = await process_lane.assert_last_commit(
            process_create_thread_proof.commit_expectation,
        )

    assert thread_commit.status == "succeeded"
    assert thread_commit.root_object_id == expected_process_id
    assert thread_commit.commit is not None


@pytest.mark.asyncio
async def test_environment_navigation_context_meta_runtime_commits(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    package_manifest_paths = _environment_package_manifest_paths(repo_root)

    from aware_environment.handlers._generated import (  # noqa: WPS433
        meta_handlers as environment_meta_handlers,
    )
    from aware_environment_ontology.environment.environment_navigation_context import (  # noqa: WPS433
        EnvironmentNavigationContext,
    )
    from aware_environment_ontology.environment.environment_session import (  # noqa: WPS433
        EnvironmentSession,
    )
    from aware_environment_ontology.stable_ids import (  # noqa: WPS433
        stable_environment_navigation_context_id,
        stable_environment_session_id,
    )

    actor_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/navigation-context/actor",
    )
    environment_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/navigation-context/environment",
    )
    session_config_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/navigation-context/session-config",
    )
    identity_session_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/navigation-context/identity-session",
    )
    initial_session_thread_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/navigation-context/session-thread/initial",
    )
    next_session_thread_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/navigation-context/session-thread/next",
    )

    context_key = "main"
    expected_session_id = stable_environment_session_id(
        environment_id=environment_id,
        identity_session_id=identity_session_id,
    )
    expected_context_id = stable_environment_navigation_context_id(
        environment_session_id=expected_session_id,
        key=context_key,
    )

    session_build_proof = FunctionCallProof(
        function_key="EnvironmentSession.build_via_environment",
        commit_expectation=OigCommitExpectation(
            label="EnvironmentSession.build_via_environment",
            expected_domain_branch_id=expected_session_id,
            expected_root_object_id=expected_session_id,
        ),
    )
    session_create_context_proof = FunctionCallProof(
        function_key="EnvironmentSession.create_navigation_context",
        commit_expectation=OigCommitExpectation(
            label="EnvironmentSession.create_navigation_context",
            require_domain_commit_id=False,
            require_object_instance_graph_commit_id=False,
            require_graph_hash_post=False,
            expected_domain_branch_id=expected_session_id,
            expected_root_object_id=expected_session_id,
        ),
    )
    context_build_proof = FunctionCallProof(
        function_key="EnvironmentNavigationContext.build_via_environment_session",
        commit_expectation=OigCommitExpectation(
            label="EnvironmentNavigationContext.build_via_environment_session",
            expected_domain_branch_id=expected_context_id,
            expected_root_object_id=expected_context_id,
        ),
    )
    context_select_proof = FunctionCallProof(
        function_key="EnvironmentNavigationContext.select_target",
        commit_expectation=OigCommitExpectation(
            label="EnvironmentNavigationContext.select_target",
            expected_domain_branch_id=expected_context_id,
            expected_root_object_id=expected_context_id,
        ),
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        meta_session = build_local_meta_sdk_session_for_aware_package_manifests(
            package_manifest_paths=package_manifest_paths,
            workspace_root=repo_root,
            aware_root=aware_root,
            composite_name=(
                "Aware Environment Environment Navigation Context " "Meta SDK Proof"
            ),
            projection_name="EnvironmentSession",
            actor_id=actor_id,
            branch_id=expected_session_id,
            generated_language_handler_module=environment_meta_handlers,
        )
        session_lane = meta_session.bind(
            projection="EnvironmentSession",
            actor_id=actor_id,
            branch_id=expected_session_id,
        )
        with session_lane.activate(commit=True, publish=False):
            session = await EnvironmentSession.build_via_environment(
                environment_id=environment_id,
                identity_session_id=identity_session_id,
                session_config_id=session_config_id,
                key="daily-sync",
                title="Daily Sync",
                source_kind="pytest",
            )

        with session_lane.activate(commit=True, publish=False):
            context_from_session = await session.create_navigation_context(
                key=context_key,
                title="Main",
                session_thread_id=initial_session_thread_id,
            )

        assert isinstance(session, EnvironmentSession)
        assert session.id == expected_session_id
        assert session.environment_id == environment_id
        assert session.session_config_id == session_config_id
        assert isinstance(context_from_session, EnvironmentNavigationContext)
        assert context_from_session.id == expected_context_id
        assert context_from_session.environment_session_id == expected_session_id
        assert context_from_session.session_thread_id == initial_session_thread_id

        context_lane = meta_session.bind(
            projection="EnvironmentNavigationContext",
            actor_id=actor_id,
            branch_id=expected_context_id,
        )
        with context_lane.activate(commit=True, publish=False):
            context = await EnvironmentNavigationContext.build_via_environment_session(
                environment_session_id=expected_session_id,
                key=context_key,
                title="Main",
                session_thread_id=initial_session_thread_id,
            )

        with context_lane.activate(commit=True, publish=False):
            selected = await context.select_target(
                session_thread_id=next_session_thread_id,
            )

        assert context.id == expected_context_id
        assert selected.id == expected_context_id
        assert selected.environment_session_id == expected_session_id
        assert selected.session_thread_id == next_session_thread_id

        session_records = session_lane.records
        session_build_record = _record_by_function(
            session_records,
            function_name="build_via_environment",
        )
        session_create_record = _record_by_function(
            session_records,
            function_name="create_navigation_context",
        )
        session_build_proof.assert_matches(session_build_record.response)
        session_create_context_proof.assert_matches(session_create_record.response)

        context_records = context_lane.records
        context_build_record = _record_by_function(
            context_records,
            function_name="build_via_environment_session",
        )
        context_select_record = _record_by_function(
            context_records,
            function_name="select_target",
        )
        context_build_proof.assert_matches(context_build_record.response)
        context_select_proof.assert_matches(context_select_record.response)

        session_head = await session_lane.get_head()
        assert session_head.status == "succeeded"
        assert session_head.root_object_id == expected_session_id
        context_head = await context_lane.get_head()
        assert context_head.status == "succeeded"
        assert context_head.root_object_id == expected_context_id

        committed_session = await _rehydrate_lane_root_from_head(
            meta_session=meta_session,
            aware_root=aware_root,
            branch_id=expected_session_id,
            projection_name="EnvironmentSession",
            root_id=expected_session_id,
            root_type=EnvironmentSession,
        )
        assert committed_session.id == expected_session_id
        assert committed_session.environment_id == environment_id
        assert committed_session.session_config_id == session_config_id
        assert committed_session.identity_session_id == identity_session_id

        committed_context = await _rehydrate_lane_root_from_head(
            meta_session=meta_session,
            aware_root=aware_root,
            branch_id=expected_context_id,
            projection_name="EnvironmentNavigationContext",
            root_id=expected_context_id,
            root_type=EnvironmentNavigationContext,
        )
        assert committed_context.id == expected_context_id
        assert committed_context.session_thread_id == next_session_thread_id

        select_commit = await context_lane.assert_last_commit(
            context_select_proof.commit_expectation,
        )

    assert select_commit.status == "succeeded"
    assert select_commit.root_object_id == expected_context_id
    assert select_commit.commit is not None


def test_environment_navigation_context_meta_runtime_proof_uses_sdk_rail() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    forbidden_tokens = (
        "aware_" + "runtime.testing",
        "Runtime" + "Harness",
        "run_module_" + "proof",
    )
    for forbidden in forbidden_tokens:
        assert forbidden not in source
