"""Real source resources and explicit borrowed-parent lifetime proofs."""

import asyncio
import copy
import os
import pickle
from contextlib import contextmanager
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    DirectInvocationExpectation,
)
from aware_workspace_runtime import (
    SourceObservationUnavailable,
    WorkspaceSemanticMaterializationGraphCoordinator,
    direct_command_composition as composition,
    materialization_operation,
)
from aware_workspace_runtime.command_lifetime import (
    WorkspaceCommandLifetimeRuntime,
    WorkspaceCommandLifetimeUnavailable,
)
from aware_workspace_runtime.materialization_graph_coordinator import _execution_state
from aware_workspace_runtime.source_exclusion import WorkspaceSourceExclusion
from test_materialization_graph_coordinator import _executed_fixture
from test_observed_semantic_issuers import setup


@contextmanager
def fenced_direct_sources(*, session, store, workspace_manifest_path):
    lifetime = WorkspaceCommandLifetimeRuntime()
    parent = lifetime._retain_direct_invocation_parent()
    expected = DirectInvocationExpectation(
        lifetime.invocation_identity, lifetime.epoch_identity, os.getpid()
    )
    exclusion = WorkspaceSourceExclusion(
        runtime=lifetime, parent=parent, expected=expected
    )
    try:
        with composition._compose_direct_workspace_sources(
            session=session,
            store=store,
            workspace_manifest_path=workspace_manifest_path,
            exclusion=exclusion,
        ) as resources:
            yield resources
    finally:
        lifetime.close()


async def test_fixed_assembly_rejects_missing_or_reconstructed_exclusion(tmp_path):
    async with setup(tmp_path) as (_, session, observer, _, _, _, _):
        with pytest.raises(TypeError, match="original WorkspaceSourceExclusion"):
            with composition._compose_direct_workspace_sources(
                session=session,
                store=observer._store,
                workspace_manifest_path="aware.workspace.toml",
                exclusion=object(),
            ):
                pytest.fail("foreign exclusion admitted")


async def test_fixed_assembly_preserves_original_resources_and_closes_only_owned(
    tmp_path,
):
    async with setup(tmp_path) as (_, session, observer, membership, retained, _, _):
        with fenced_direct_sources(
            session=session,
            store=observer._store,
            workspace_manifest_path="aware.workspace.toml",
        ) as resources:
            assert type(resources.exclusion) is WorkspaceSourceExclusion
            assert resources.observation_runtime._exclusion is resources.exclusion
            assert resources.membership_runtime._exclusion is resources.exclusion
            assert resources.scope_runtime._exclusion is resources.exclusion
            assert resources.observation_runtime is not observer
            assert resources.membership_runtime is not membership
            issuer = resources.semantic_issuer
            assert issuer._observation_runtime is resources.observation_runtime
            assert issuer._membership_runtime is resources.membership_runtime
            assert issuer._observation is resources.observation
            assert not hasattr(issuer, "issue_isolated_pair")
            with pytest.raises(SourceObservationUnavailable):
                issuer.issue_source_planning_pair(None, context=None, expected=None)
            projection = resources.scope_adapter.read_complete_scope_projection(
                resources.scope_snapshot
            )
            assert [p.package_id for p in projection.packages] == [
                "demo",
                "provider",
                "target",
            ]
            resources.scope_adapter.validate_complete_scope_projection(
                resources.scope_snapshot, projection_digest=projection.projection_digest
            )
        with pytest.raises(
            (SourceObservationUnavailable, WorkspaceCommandLifetimeUnavailable)
        ):
            resources.scope_adapter.validate_complete_scope_projection(
                resources.scope_snapshot
            )
        assert session.authority_admitted
        assert issuer._closed
        observer.revalidate(retained)  # Borrowed session and shared store still work.


@pytest.mark.parametrize("failure", [RuntimeError, asyncio.CancelledError])
async def test_body_failure_and_cancellation_unwind(tmp_path, failure):
    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        with pytest.raises(failure), fenced_direct_sources(
            session=session,
            store=observer._store,
            workspace_manifest_path="aware.workspace.toml",
        ) as resources:
            raise failure("body failed")
        with pytest.raises(
            (SourceObservationUnavailable, WorkspaceCommandLifetimeUnavailable)
        ):
            resources.observation_runtime.revalidate(resources.observation)
        assert resources.semantic_issuer._closed
        observer.revalidate(retained)


async def test_all_cleanups_attempted_and_primary_error_preserved(
    tmp_path, monkeypatch
):
    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        calls = []
        original = composition.WorkspaceCompleteScopeObservationRuntime.close

        def failing_close(owner):
            calls.append("scope")
            original(owner)
            raise RuntimeError("cleanup failed")

        monkeypatch.setattr(
            composition.WorkspaceCompleteScopeObservationRuntime, "close", failing_close
        )
        with pytest.raises(BaseExceptionGroup) as caught, fenced_direct_sources(
            session=session,
            store=observer._store,
            workspace_manifest_path="aware.workspace.toml",
        ) as resources:
            raise asyncio.CancelledError("cancelled")
        assert calls == ["scope"]
        assert isinstance(caught.value.exceptions[0], asyncio.CancelledError)
        assert str(caught.value.exceptions[1]) == "cleanup failed"
        with pytest.raises(
            (SourceObservationUnavailable, WorkspaceCommandLifetimeUnavailable)
        ):
            resources.observation_runtime.revalidate(resources.observation)
        observer.revalidate(retained)


async def test_partial_capture_failure_closes_observation(tmp_path, monkeypatch):
    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        closed = []
        original = composition.WorkspaceSourceObservationRuntime.close

        def track(owner):
            closed.append(owner)
            original(owner)

        monkeypatch.setattr(
            composition.WorkspaceSourceObservationRuntime, "close", track
        )
        with pytest.raises(SourceObservationUnavailable), fenced_direct_sources(
            session=session,
            store=observer._store,
            workspace_manifest_path="absent.workspace.toml",
        ):
            pytest.fail("missing Workspace scope admitted")
        assert len(closed) == 1 and closed[0] is not observer
        observer.revalidate(retained)


async def test_cleanup_uses_retained_method_not_late_replacement(tmp_path, monkeypatch):
    async with setup(tmp_path) as (_, session, observer, _, _, _, _):
        with fenced_direct_sources(
            session=session,
            store=observer._store,
            workspace_manifest_path="aware.workspace.toml",
        ) as resources:
            monkeypatch.setattr(resources.observation_runtime, "close", lambda: None)
            monkeypatch.setattr(resources.semantic_issuer, "close", lambda: None)
        assert resources.semantic_issuer._closed
        with pytest.raises(
            (SourceObservationUnavailable, WorkspaceCommandLifetimeUnavailable)
        ):
            resources.observation_runtime.revalidate(resources.observation)


async def test_issuer_cleanup_precedes_sources_and_failure_keeps_unwinding(
    tmp_path, monkeypatch
):
    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        calls = []
        original = composition.WorkspaceSourcePlanningSemanticIssuerRuntime.close

        def failing_close(issuer):
            # The original source resources must still be live during issuer close.
            issuer._observation_runtime.revalidate(issuer._observation)
            calls.append("issuer")
            original(issuer)
            raise RuntimeError("issuer cleanup failed")

        monkeypatch.setattr(
            composition.WorkspaceSourcePlanningSemanticIssuerRuntime,
            "close",
            failing_close,
        )
        with pytest.raises(
            RuntimeError, match="issuer cleanup failed"
        ), fenced_direct_sources(
            session=session,
            store=observer._store,
            workspace_manifest_path="aware.workspace.toml",
        ) as resources:
            pass
        assert calls == ["issuer"]
        assert resources.semantic_issuer._closed
        with pytest.raises(
            (SourceObservationUnavailable, WorkspaceCommandLifetimeUnavailable)
        ):
            resources.scope_adapter.validate_complete_scope_projection(
                resources.scope_snapshot
            )
        observer.revalidate(retained)


@pytest.mark.asyncio
async def test_command_graph_check_requires_original_live_assembly(
    tmp_path, monkeypatch
) -> None:
    async with setup(tmp_path) as (_, session, observer, _, _, _, _):
        with composition._compose_direct_workspace_command_resources(
            session=session,
            store=observer._store,
            workspace_manifest_path="aware.workspace.toml",
        ) as command:
            _, _, owner, execution, _ = await _executed_fixture(
                owner_override=command.lifetime_runtime
            )
            graph = _execution_state(execution)
            original_prepare = graph.ports.operation_preparer
            expected_source_admission = object()
            checked_nodes = []

            def check_source(node, *, source_runtime, source_admission: object):
                assert source_runtime is command.sources.source_admission_runtime
                assert source_admission is expected_source_admission
                checked_nodes.append(node)

            monkeypatch.setattr(
                materialization_operation,
                "_validate_graph_node_owner_source",
                check_source,
            )

            async def prepare(preparation):
                operation, admission = await original_prepare(preparation)
                original_execute = operation._execute_graph_v2

                async def checked_execute(node):
                    composition._validate_command_owned_graph_node_source(
                        command, node, expected_source_admission
                    )
                    with composition._command_owned_graph_node_source_session(
                        command, node, expected_source_admission
                    ) as retained:
                        retained.validate()
                        with pytest.raises(TypeError):
                            copy.copy(retained)
                        with pytest.raises(TypeError):
                            pickle.dumps(retained)
                        await asyncio.sleep(0)
                        retained.validate()
                    with pytest.raises(RuntimeError, match="closed"):
                        retained.validate()
                    with pytest.raises(asyncio.CancelledError):
                        with composition._command_owned_graph_node_source_session(
                            command, node, expected_source_admission
                        ) as cancelled:
                            raise asyncio.CancelledError()
                    with pytest.raises(RuntimeError, match="closed"):
                        cancelled.validate()
                    with composition._command_owned_graph_node_source_session(
                        command, node, expected_source_admission
                    ) as foreign_thread:
                        with pytest.raises(RuntimeError, match="context changed"):
                            await asyncio.to_thread(foreign_thread.validate)
                        with pytest.raises(RuntimeError, match="closed"):
                            foreign_thread.validate()
                    node_state = materialization_operation._graph_node_admission_state(
                        node
                    )
                    node_state.owner = object()
                    try:
                        with pytest.raises(RuntimeError, match="not owned"):
                            composition._validate_command_owned_graph_node_source(
                                command, node, expected_source_admission
                            )
                    finally:
                        node_state.owner = command.lifetime_runtime
                    foreign = replace(
                        command, lifetime_runtime=WorkspaceCommandLifetimeRuntime()
                    )
                    with pytest.raises(RuntimeError, match="foreign or retired"):
                        composition._validate_command_owned_graph_node_source(
                            foreign, node, expected_source_admission
                        )
                    return await original_execute(node)

                operation._execute_graph_v2 = checked_execute
                return operation, admission

            graph.ports = replace(graph.ports, operation_preparer=prepare)
            result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
                execution, owner=owner
            )
            assert result.status == "succeeded"
            assert len(checked_nodes) == 6
        with pytest.raises(RuntimeError, match="foreign or retired"):
            composition._validate_command_owned_graph_node_source(
                command, checked_nodes[0], expected_source_admission
            )
