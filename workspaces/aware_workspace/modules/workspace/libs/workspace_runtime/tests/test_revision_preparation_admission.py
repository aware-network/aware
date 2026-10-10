from __future__ import annotations

import asyncio
import copy
import importlib
import os
import pickle

import pytest
import pytest_asyncio
from aware_code_semantic_contract_runtime import ContentDigest, canonical_json_bytes
from aware_workspace_runtime import WorkspaceSemanticMaterializationGraphCoordinator
from aware_workspace_runtime.revision_preparation_admission import (
    WorkspaceMaterializationGraphExecutionAdmissionCapability,
    WorkspaceRevisionPreparationAdmissionError,
    WorkspaceRevisionPreparationContextCapability,
    admit_completed_workspace_materialization_graph_execution,
    verify_workspace_materialization_graph_execution_admission,
    verify_workspace_revision_preparation_context,
)
from aware_workspace_runtime.revision_preparation_contracts import (
    WorkspaceMaterializationGraphExecutionAdmission,
)
from test_materialization_graph_coordinator import (
    _fixture,
    _issue_current_graph_admission,
)
from test_revision_preparation import (
    _prepared_fixture,
    _PreparedFixture,
    _verify_test_revision_preparation_context,
)


@pytest_asyncio.fixture(scope="module")
async def admitted_fixture() -> _PreparedFixture:
    return await _prepared_fixture(2)


def test_graph_and_context_capabilities_are_nominal_and_nonportable(
    admitted_fixture: _PreparedFixture,
) -> None:
    with pytest.raises(TypeError):
        WorkspaceMaterializationGraphExecutionAdmissionCapability()
    with pytest.raises(TypeError):
        WorkspaceRevisionPreparationContextCapability()
    for capability in (
        admitted_fixture.graph_capability,
        admitted_fixture.context_capability,
    ):
        with pytest.raises(TypeError):
            copy.copy(capability)
        with pytest.raises(TypeError):
            copy.deepcopy(capability)
        with pytest.raises(TypeError):
            pickle.dumps(capability)


def test_graph_verifier_requires_exact_plan_result_owner_and_admission(
    admitted_fixture: _PreparedFixture,
) -> None:
    verify_workspace_materialization_graph_execution_admission(
        capability=admitted_fixture.graph_capability,
        admission=admitted_fixture.graph_admission,
        execution=admitted_fixture.execution,
        owner=admitted_fixture.owner,
        plan=admitted_fixture.plan,
        result=admitted_fixture.graph_result,
    )
    structural_copy = (
        WorkspaceMaterializationGraphExecutionAdmission.from_canonical_bytes(
            admitted_fixture.graph_admission.canonical_bytes()
        )
    )
    with pytest.raises(WorkspaceRevisionPreparationAdmissionError):
        verify_workspace_materialization_graph_execution_admission(
            capability=admitted_fixture.graph_capability,
            admission=structural_copy,
            execution=admitted_fixture.execution,
            owner=admitted_fixture.owner,
            plan=admitted_fixture.plan,
            result=admitted_fixture.graph_result,
        )
    with pytest.raises(WorkspaceRevisionPreparationAdmissionError):
        verify_workspace_materialization_graph_execution_admission(
            capability=admitted_fixture.graph_capability,
            admission=admitted_fixture.graph_admission,
            execution=admitted_fixture.execution,
            owner=object(),
            plan=admitted_fixture.plan,
            result=admitted_fixture.graph_result,
        )


def test_context_verifier_reauthenticates_every_exact_authority(
    admitted_fixture: _PreparedFixture,
) -> None:
    _verify_test_revision_preparation_context(
        stage="selection",
        capability=admitted_fixture.context_capability,
        owner=admitted_fixture.owner,
        operation_authority_digest=admitted_fixture.operation_digest,
        workspace_ref="workspace:test",
        branch_ref="workspace-branch:test",
        predecessor=admitted_fixture.predecessor,
        predecessor_state=None,
        predecessor_source_closure=None,
        source_closure=admitted_fixture.source_closure,
        source_admission=admitted_fixture.source_admission,
        selection=admitted_fixture.selection,
        transitions=admitted_fixture.transitions,
    )
    copied_source = type(admitted_fixture.source_closure).from_canonical_bytes(
        admitted_fixture.source_closure.canonical_bytes()
    )
    with pytest.raises(WorkspaceRevisionPreparationAdmissionError):
        _verify_test_revision_preparation_context(
            stage="selection",
            capability=admitted_fixture.context_capability,
            owner=admitted_fixture.owner,
            operation_authority_digest=admitted_fixture.operation_digest,
            workspace_ref="workspace:test",
            branch_ref="workspace-branch:test",
            predecessor=admitted_fixture.predecessor,
            predecessor_state=None,
            predecessor_source_closure=None,
            source_closure=copied_source,
            source_admission=admitted_fixture.source_admission,
            selection=admitted_fixture.selection,
            transitions=admitted_fixture.transitions,
        )


@pytest.mark.skipif(not hasattr(os, "fork"), reason="POSIX fork is unavailable")
def test_process_loss_recovery_is_bound_to_one_exact_graph_execution(
    admitted_fixture: _PreparedFixture,
) -> None:
    read_fd, write_fd = os.pipe()
    process = os.fork()
    if process == 0:
        os.close(read_fd)
        try:
            accepted = True
            try:
                verify_workspace_materialization_graph_execution_admission(
                    capability=admitted_fixture.graph_capability,
                    admission=admitted_fixture.graph_admission,
                    execution=admitted_fixture.execution,
                    owner=admitted_fixture.owner,
                    plan=admitted_fixture.plan,
                    result=admitted_fixture.graph_result,
                )
            except WorkspaceRevisionPreparationAdmissionError:
                accepted = False

            async def completed_graph(
                node_count: int | None = None,
                *,
                exact_plan=None,  # type: ignore[no-untyped-def]
                exact_reader=None,  # type: ignore[no-untyped-def]
                operation_digest: ContentDigest | None = None,
                suffix: str = "graph",
            ):
                if exact_plan is None:
                    assert node_count is not None
                    plan, _reader, owner, execution = await _fixture(
                        node_count, operation_digest=operation_digest
                    )
                else:
                    plan = exact_plan
                    assert exact_reader is not None
                    owner, execution = _issue_current_graph_admission(
                        plan,
                        exact_reader,
                        suffix=suffix,
                        operation_digest=operation_digest,
                    )
                result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
                    execution, owner=owner
                )
                graph_admission, graph_capability = (
                    admit_completed_workspace_materialization_graph_execution(
                        execution=execution,
                        owner=owner,
                        result=result,
                    )
                )
                return (
                    plan,
                    owner,
                    execution,
                    result,
                    graph_admission,
                    graph_capability,
                )

            wrong_operation = asyncio.run(
                completed_graph(
                    exact_plan=admitted_fixture.plan,
                    exact_reader=admitted_fixture.graph_reader,
                    operation_digest=ContentDigest.of_bytes(b"foreign-operation"),
                )
            )
            unrelated = asyncio.run(completed_graph(3))
            wrong_context = asyncio.run(
                completed_graph(
                    exact_plan=admitted_fixture.plan,
                    exact_reader=admitted_fixture.graph_reader,
                    suffix="foreign-context",
                )
            )
            fresh = asyncio.run(
                completed_graph(
                    exact_plan=admitted_fixture.plan,
                    exact_reader=admitted_fixture.graph_reader,
                )
            )
            later = asyncio.run(
                completed_graph(
                    exact_plan=admitted_fixture.plan,
                    exact_reader=admitted_fixture.graph_reader,
                )
            )
            assert not accepted
            assert canonical_json_bytes(wrong_operation[0].to_wire()) == (
                canonical_json_bytes(admitted_fixture.plan.to_wire())
            )
            assert wrong_operation[4].operation_authority_digest != (
                admitted_fixture.operation_digest
            )
            assert (
                wrong_operation[4].execution_provenance_lifecycle
                == "same_process_execution"
            )
            assert (
                unrelated[0].graph.graph_digest
                != admitted_fixture.plan.graph.graph_digest
            )
            assert (
                unrelated[0].graph_execution_binding.binding_digest
                != admitted_fixture.plan.graph_execution_binding.binding_digest
            )
            assert (
                unrelated[4].execution_provenance_lifecycle
                == "same_process_execution"
            )
            assert (
                wrong_context[4].execution_provenance_lifecycle
                == "same_process_execution"
            )
            assert canonical_json_bytes(fresh[0].to_wire()) == canonical_json_bytes(
                admitted_fixture.plan.to_wire()
            )
            assert (
                fresh[4].operation_authority_digest
                == admitted_fixture.operation_digest
            )
            assert (
                fresh[4].execution_provenance_lifecycle
                == "reexecuted_after_process_loss"
            )
            assert (
                later[4].execution_provenance_lifecycle
                == "same_process_execution"
            )
            caller_selected_recovery = (
                WorkspaceMaterializationGraphExecutionAdmission.create(
                    disposition="admitted",
                    operation_authority_digest=(
                        unrelated[4].operation_authority_digest
                    ),
                    execution_provenance_lifecycle=(
                        "reexecuted_after_process_loss"
                    ),
                    plan_body_sha256=unrelated[4].plan_body_sha256,
                    plan_body_size_bytes=unrelated[4].plan_body_size_bytes,
                    graph_result_body_sha256=(
                        unrelated[4].graph_result_body_sha256
                    ),
                    graph_result_body_size_bytes=(
                        unrelated[4].graph_result_body_size_bytes
                    ),
                    graph_result_digest=unrelated[4].graph_result_digest,
                )
            )
            for restamped in (
                caller_selected_recovery,
                WorkspaceMaterializationGraphExecutionAdmission.from_canonical_bytes(
                    caller_selected_recovery.canonical_bytes()
                ),
            ):
                with pytest.raises(WorkspaceRevisionPreparationAdmissionError):
                    verify_workspace_materialization_graph_execution_admission(
                        capability=unrelated[5],
                        admission=restamped,
                        execution=unrelated[2],
                        owner=unrelated[1],
                        plan=unrelated[0],
                        result=unrelated[3],
                    )
            structural = (
                WorkspaceMaterializationGraphExecutionAdmission.from_canonical_bytes(
                    fresh[4].canonical_bytes()
                )
            )
            structural_accepted = True
            try:
                verify_workspace_materialization_graph_execution_admission(
                    capability=fresh[5],
                    admission=structural,
                    execution=fresh[2],
                    owner=fresh[1],
                    plan=fresh[0],
                    result=fresh[3],
                )
            except WorkspaceRevisionPreparationAdmissionError:
                structural_accepted = False
            assert not structural_accepted
            message = "exact-recovery-only"
            exit_code = 0
        except (AssertionError, RuntimeError, TypeError, ValueError) as error:
            message = f"child-error:{type(error).__name__}:{error}"
            exit_code = 1
        os.write(write_fd, message.encode())
        os.close(write_fd)
        os._exit(exit_code)
    os.close(write_fd)
    observed = os.read(read_fd, 256)
    os.close(read_fd)
    _, status = os.waitpid(process, 0)
    assert status == 0, observed
    assert observed == b"exact-recovery-only"
    verify_workspace_materialization_graph_execution_admission(
        capability=admitted_fixture.graph_capability,
        admission=admitted_fixture.graph_admission,
        execution=admitted_fixture.execution,
        owner=admitted_fixture.owner,
        plan=admitted_fixture.plan,
        result=admitted_fixture.graph_result,
    )


def test_installed_modules_expose_no_detached_authority_minting_entrance() -> None:
    admission_module = importlib.import_module(
        "aware_workspace_runtime.revision_preparation_admission"
    )
    coordinator_module = importlib.import_module(
        "aware_workspace_runtime.materialization_graph_coordinator"
    )
    assert not hasattr(
        admission_module,
        "_register_workspace_materialization_graph_execution_completion",
    )
    assert not hasattr(
        admission_module,
        "_issue_workspace_revision_preparation_context_for_test",
    )
    for name in (
        "_GRAPH_EXECUTION_AFTER_PROCESS_LOSS",
        "_GRAPH_EXECUTION_RECOVERY_RECORDS",
        "_GRAPH_EXECUTION_RECOVERY_CLAIMS",
    ):
        assert not hasattr(coordinator_module, name)
    placeholder = object.__new__(WorkspaceRevisionPreparationContextCapability)
    with pytest.raises(WorkspaceRevisionPreparationAdmissionError):
        verify_workspace_revision_preparation_context(
            capability=placeholder,
            owner=object(),
            operation_authority_digest=("sha256:" + "0" * 64),
            workspace_ref="workspace:test",
            branch_ref="branch:test",
            predecessor=object(),  # type: ignore[arg-type]
            predecessor_state=None,
            predecessor_source_closure=None,
            source_closure=object(),  # type: ignore[arg-type]
            source_admission=object(),  # type: ignore[arg-type]
            selection=object(),  # type: ignore[arg-type]
            transitions=object(),  # type: ignore[arg-type]
        )
    assert type(placeholder) is WorkspaceRevisionPreparationContextCapability
