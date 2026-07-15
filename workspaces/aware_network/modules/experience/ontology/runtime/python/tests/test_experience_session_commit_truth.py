from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from aware_experience.handlers._generated import meta_handlers
from aware_experience.semantic_contract import (
    EXPERIENCE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES,
)
from aware_experience_ontology.stable_ids import (
    stable_experience_session_id,
    stable_experience_session_profile_id,
)
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import (
    MetaGraphCommitInvocationBackend,
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedInvocationHandlerRegistry,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphOigMaterializerPreStateProvider,
    MetaGraphRuntime,
    build_meta_graph_generated_constructor_bootstrap_registry,
    build_meta_graph_generated_handler_executor,
    build_meta_graph_generated_language_handler_registry,
    find_meta_graph_projection_hash_by_name,
    reify_meta_orm_root_from_oig_commit,
)
from aware_meta.runtime.graph_context import (
    build_meta_graph_runtime_context_for_workspace_required_projections,
)

REPO_ROOT = Path(__file__).resolve().parents[8]


@contextmanager
def _isolated_meta_root(root: Path) -> Iterator[Path]:
    root.mkdir(parents=True, exist_ok=True)
    (root / ".aware").mkdir(parents=True, exist_ok=True)
    previous = {
        "AWARE_ROOT": os.environ.get("AWARE_ROOT"),
        "AWARE_PERSISTENCE_BACKEND": os.environ.get("AWARE_PERSISTENCE_BACKEND"),
        "DATABASE_URL": os.environ.get("DATABASE_URL"),
    }
    os.environ["AWARE_ROOT"] = str(root)
    os.environ["AWARE_PERSISTENCE_BACKEND"] = "fs"
    os.environ.pop("DATABASE_URL", None)
    try:
        yield root
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _build_runtime(aware_root: Path) -> MetaGraphRuntime:
    handler_module = cast(MetaGraphGeneratedLanguageHandlerModule, meta_handlers)
    bootstrap_module = cast(MetaGraphGeneratedConstructorBootstrapModule, meta_handlers)
    context = build_meta_graph_runtime_context_for_workspace_required_projections(
        repo_root=REPO_ROOT,
        required_projection_names=(),
        required_package_names=(
            EXPERIENCE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
        aware_root=aware_root,
        composition_context_id=uuid5(
            NAMESPACE_URL,
            "aware://tests/experience/session-commit-meta-runtime",
        ),
        composite_name="Experience Session Commit Meta Runtime",
    )
    bootstrap_resolver = build_meta_graph_generated_constructor_bootstrap_registry(
        module=bootstrap_module,
    )
    handler_executor = build_meta_graph_generated_handler_executor(
        handler_resolver=build_meta_graph_generated_language_handler_registry(
            module=handler_module,
        ),
        invocation_handler_resolver=MetaGraphGeneratedInvocationHandlerRegistry(
            handlers_by_key=meta_handlers.AWARE_META_GRAPH_INVOCATION_HANDLERS,
        ),
        pre_state_provider=MetaGraphOigMaterializerPreStateProvider(
            materializer=OIGMaterializer(
                commits=FSCommitStore(root_dir=aware_root),
                snaps=FSSnapshotStore(root_dir=aware_root),
            ),
            empty_lane_bootstrap_resolver=bootstrap_resolver,
        ),
        empty_lane_bootstrap_resolver=bootstrap_resolver,
    )
    return MetaGraphRuntime(
        backend=MetaGraphCommitInvocationBackend(
            handler_executor=handler_executor,
            lane_committer=FSLaneCommitter(store=FSCommitStore(root_dir=aware_root)),
            implementation_policy=MetaGraphImplementationPolicy(
                default_function_impl_ownership=(
                    MetaGraphFunctionImplOwnership.authored
                ),
            ),
        ),
        context=context,
    )


def _projection_hash(
    runtime: MetaGraphRuntime,
    projection_name: str = "ExperienceSession",
) -> str:
    assert runtime.context is not None
    return find_meta_graph_projection_hash_by_name(
        index=runtime.context.index,
        projection_name=projection_name,
    )


@pytest.mark.asyncio
async def test_experience_session_handler_rejects_non_uuid_identity_key() -> None:
    from aware_experience.handlers.impl.session.experience_session import (
        build_via_environment_experience,
    )

    with pytest.raises(TypeError, match="requires identity_session_id"):
        await build_via_environment_experience(
            environment_experience_id=uuid4(),
            identity_session_id="not-a-uuid",  # type: ignore[arg-type]
            environment_session_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_environment_experience_public_start_session_attaches_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_experience.handlers.impl.environment import (
        environment_experience as environment_experience_handler,
    )
    from aware_experience_ontology.environment.environment_experience import (
        EnvironmentExperience,
    )
    from aware_experience_ontology.session.experience_session import (
        ExperienceSession,
    )
    from aware_experience_ontology.session.experience_session_enums import (
        ExperienceSessionState,
    )

    environment_experience_id = uuid4()
    identity_session_id = uuid4()
    environment_session_id = uuid4()
    child = ExperienceSession(
        id=stable_experience_session_id(
            environment_experience_id=environment_experience_id,
            identity_session_id=identity_session_id,
        ),
        environment_experience_id=environment_experience_id,
        identity_session_id=identity_session_id,
        environment_session_id=environment_session_id,
        profiles=[],
        state=ExperienceSessionState.active,
    )

    async def _build(**_kwargs: object) -> ExperienceSession:
        return child

    monkeypatch.setattr(
        ExperienceSession,
        "build_via_environment_experience",
        _build,
    )
    parent = EnvironmentExperience(
        id=environment_experience_id,
        fqn_prefix="aware.demo",
    )

    created = await environment_experience_handler.start_session(
        environment_experience=parent,
        identity_session_id=identity_session_id,
        environment_session_id=environment_session_id,
    )
    repeated = await environment_experience_handler.start_session(
        environment_experience=parent,
        identity_session_id=identity_session_id,
        environment_session_id=environment_session_id,
    )

    assert created is repeated is child
    assert parent.sessions == [child]


@pytest.mark.asyncio
async def test_experience_session_public_mount_supports_multiple_profiles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_experience.handlers.impl.session import (
        experience_session as experience_session_handler,
    )
    from aware_experience_ontology.session.experience_session import (
        ExperienceSession,
    )
    from aware_experience_ontology.session.experience_session_enums import (
        ExperienceSessionState,
    )
    from aware_experience_ontology.session.experience_session_profile import (
        ExperienceSessionProfile,
    )

    experience_session_id = uuid4()
    session = ExperienceSession(
        id=experience_session_id,
        environment_experience_id=uuid4(),
        identity_session_id=uuid4(),
        environment_session_id=uuid4(),
        profiles=[],
        state=ExperienceSessionState.active,
    )

    async def _build(
        *, profile_id: UUID, **_kwargs: object
    ) -> ExperienceSessionProfile:
        return ExperienceSessionProfile(
            id=stable_experience_session_profile_id(
                experience_session_id=experience_session_id,
                profile_id=profile_id,
            ),
            experience_session_id=experience_session_id,
            profile_id=profile_id,
            status="active",
        )

    monkeypatch.setattr(
        ExperienceSessionProfile,
        "build_via_experience_session",
        _build,
    )
    first_profile_id = uuid4()
    second_profile_id = uuid4()
    first = await experience_session_handler.mount_profile(
        experience_session=session,
        profile_id=first_profile_id,
    )
    repeated = await experience_session_handler.mount_profile(
        experience_session=session,
        profile_id=first_profile_id,
    )
    second = await experience_session_handler.mount_profile(
        experience_session=session,
        profile_id=second_profile_id,
    )

    assert first is repeated
    assert first.id != second.id
    assert [mount.profile_id for mount in session.profiles] == [
        first_profile_id,
        second_profile_id,
    ]


@pytest.mark.asyncio
async def test_experience_session_constructor_commits_and_rehydrates_truth(
    tmp_path: Path,
) -> None:
    with _isolated_meta_root(tmp_path / "aware_root") as aware_root:
        runtime = _build_runtime(aware_root)

        from aware_experience_ontology.session.experience_session import (
            ExperienceSession,
        )
        from aware_experience_ontology.session.experience_session_enums import (
            ExperienceSessionState,
        )
        from aware_experience_ontology.session.experience_session_profile import (
            ExperienceSessionProfile,
        )

        environment_experience_id = uuid4()
        identity_session_id = uuid4()
        environment_session_id = uuid4()
        first_profile_id = uuid4()
        second_profile_id = uuid4()
        actor_id = uuid4()
        experience_session_id = stable_experience_session_id(
            environment_experience_id=environment_experience_id,
            identity_session_id=identity_session_id,
        )

        lane = runtime.bind(
            branch_id=experience_session_id,
            projection="ExperienceSession",
            actor_id=actor_id,
        )
        with lane.activate(commit=True, publish=False):
            created = await ExperienceSession.build_via_environment_experience(
                environment_experience_id=environment_experience_id,
                identity_session_id=identity_session_id,
                environment_session_id=environment_session_id,
                state=ExperienceSessionState.active,
            )
            repeated = await ExperienceSession.build_via_environment_experience(
                environment_experience_id=environment_experience_id,
                identity_session_id=identity_session_id,
                environment_session_id=environment_session_id,
            )

        assert created.id == repeated.id == experience_session_id
        commit_store = FSCommitStore(root_dir=aware_root)
        head = await commit_store.head(
            branch_id=experience_session_id,
            projection_hash=_projection_hash(runtime),
        )
        assert head is not None

        assert runtime.context is not None
        committed = await reify_meta_orm_root_from_oig_commit(
            index=runtime.context.index,
            branch_id=experience_session_id,
            projection_hash=_projection_hash(runtime),
            projection_name="ExperienceSession",
            commit_id=UUID(str(head["commit_id"])),
            root_id=experience_session_id,
            root_type=ExperienceSession,
            commit_store=commit_store,
            snapshot_store=FSSnapshotStore(root_dir=aware_root),
        )
        assert committed is not None
        assert committed.environment_experience_id == environment_experience_id
        assert committed.identity_session_id == identity_session_id
        assert committed.environment_session_id == environment_session_id
        mounts = []
        for profile_id in (first_profile_id, second_profile_id):
            mount_id = stable_experience_session_profile_id(
                experience_session_id=experience_session_id,
                profile_id=profile_id,
            )
            mount_lane = runtime.bind(
                branch_id=mount_id,
                projection="ExperienceSessionProfile",
                actor_id=actor_id,
            )
            with mount_lane.activate(commit=True, publish=False):
                mount = await ExperienceSessionProfile.build_via_experience_session(
                    experience_session_id=experience_session_id,
                    profile_id=profile_id,
                )
                repeated_mount = (
                    await ExperienceSessionProfile.build_via_experience_session(
                        experience_session_id=experience_session_id,
                        profile_id=profile_id,
                    )
                )
            assert mount.id == repeated_mount.id == mount_id
            mounts.append(mount)

        committed_mounts = []
        for mount in mounts:
            mount_projection_hash = _projection_hash(
                runtime,
                "ExperienceSessionProfile",
            )
            mount_head = await commit_store.head(
                branch_id=mount.id,
                projection_hash=mount_projection_hash,
            )
            assert mount_head is not None
            committed_mount = await reify_meta_orm_root_from_oig_commit(
                index=runtime.context.index,
                branch_id=mount.id,
                projection_hash=mount_projection_hash,
                projection_name="ExperienceSessionProfile",
                commit_id=UUID(str(mount_head["commit_id"])),
                root_id=mount.id,
                root_type=ExperienceSessionProfile,
                commit_store=commit_store,
                snapshot_store=FSSnapshotStore(root_dir=aware_root),
            )
            assert committed_mount is not None
            committed_mounts.append(committed_mount)
        assert {mount.profile_id for mount in committed_mounts} == {
            first_profile_id,
            second_profile_id,
        }
        assert "profile_id" not in ExperienceSession.model_fields
        assert "active_projection_experience_id" not in ExperienceSession.model_fields
        assert committed.state == ExperienceSessionState.active


def test_experience_session_stable_identity_is_child_identity_scoped() -> None:
    environment_experience_id = uuid4()
    first = stable_experience_session_id(
        environment_experience_id=environment_experience_id,
        identity_session_id=uuid4(),
    )
    second = stable_experience_session_id(
        environment_experience_id=environment_experience_id,
        identity_session_id=uuid4(),
    )
    assert first != second
