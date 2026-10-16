"""Original source-first C custody; no mock Issue or physical admission."""

from __future__ import annotations

import asyncio
import copy
import gc
import hashlib
import json
import os
import pickle
import sys
import threading
import weakref
from dataclasses import asdict, replace

import pytest
from aware_workspace_sdk.repository_tree_projection import (
    WorkspaceRepositoryTreeProjectionClient,
    WorkspaceTreeProjectionAdmission,
    WorkspaceTreeProjectionPlan,
    WorkspaceTreeProjectionRefusal,
    WorkspaceTreeProjectionResult,
    read_original_tree_projection_result,
)
from aware_workspace_sdk.repository_tree_projection_values import (
    DEFAULT_TREE_LIMITS,
    WorkspaceTreeAncestorIntent,
    WorkspaceTreeFileIntent,
    WorkspaceTreeProjectionRequest,
)
from aware_workspace_sdk.repository_workflow import (
    read_original_repository_workflow_source,
    verify_original_repository_workflow_source,
)
from aware_workspace_sdk.repository_workflow_values import (
    WorkspaceRepositoryWorkflowAttemptObserveRequest,
    WorkspaceRepositoryWorkflowEvidenceAppendRequest,
)

from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_workflow import (
    inputs as inputs,  # noqa: PLC0414 - original pytest fixture
)
from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_workflow import (
    workflow_source,
)


def setup(inputs):
    attempt, source, observed = workflow_source(inputs)
    target, state = inputs[1:3]
    client = WorkspaceRepositoryTreeProjectionClient.filesystem(
        repository_root=target,
        state_root=state / "tree",
        execution_id=observed.binding.execution_id,
    )
    request = WorkspaceTreeProjectionRequest(
        observed.binding.workflow_ref,
        "layout:explicit",
        "invocation:1",
        observed.binding,
        (
            WorkspaceTreeFileIntent(
                "out.py", "CREATE", observed.files[0].output_path, 0o644
            ),
        ),
        (),
        "descriptor_walk_v1",
        DEFAULT_TREE_LIMITS,
    )
    return attempt, source, observed, client, request


@pytest.mark.asyncio
async def test_genuine_source_and_physical_preparation_issue_plan_without_effect(
    inputs,
):
    _attempt, source, observed, client, request = setup(inputs)
    assert _attempt is not None
    target = inputs[1]
    head = (target / ".git/HEAD").read_bytes()
    plan = await client.prepare_tree_projection(request, source_delivery=source)
    observed_plan = client.observe_tree_projection_plan(plan)
    assert observed_plan.phase == "prepared"
    assert observed_plan.binding.source_binding == observed.binding
    assert observed_plan.binding.transition_count == 1
    assert len(observed_plan.binding.scratch_effects) == 4
    assert observed_plan.binding.scratch_effects[0].requested_mode == 0o600
    assert (
        client.verify_tree_projection_plan(plan, expected_binding=observed_plan.binding)
        == observed_plan
    )
    assert (
        not (target / "out.py").exists() and (target / ".git/HEAD").read_bytes() == head
    )
    verify_original_repository_workflow_source(
        source, expected_binding=observed.binding
    )
    cleanup = await client.release_tree_projection()
    assert cleanup.cleanup_state == "completed"
    assert any(row.kind == "body_retention" for row in cleanup.resources)
    assert any(row.kind == "descriptor" for row in cleanup.resources)
    assert any(row.kind == "observation_session" for row in cleanup.resources)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        client.observe_tree_projection_plan(plan)
    assert (await client.release_tree_projection()).cleanup_state == "completed"


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["delete", "create_directory", "preserve_directory"])
async def test_bodyless_preparation_preserves_borrowed_source_and_parent(inputs, kind):
    attempt, source, observed, client, request = setup(inputs)
    target = inputs[1]
    preserved = target / "out.py"
    preserved.write_bytes(b"original target preimage")
    preserved.chmod(0o640)
    if kind == "delete":
        request = replace(
            request, files=(WorkspaceTreeFileIntent("out.py", "DELETE", None, None),)
        )
    else:
        if kind == "preserve_directory":
            (target / "directory").mkdir(mode=0o750)
        request = replace(
            request,
            files=(),
            ancestors=(
                WorkspaceTreeAncestorIntent(
                    "directory",
                    "create" if kind == "create_directory" else "preserve",
                    0o755 if kind == "create_directory" else None,
                ),
            ),
        )
    before = {
        path.relative_to(target): (
            path.stat().st_mode,
            path.read_bytes() if path.is_file() else None,
        )
        for path in target.rglob("*")
    }
    plan = await client.prepare_tree_projection(request, source_delivery=source)
    assert client.observe_tree_projection_plan(plan).binding.transition_count == 1
    assert before == {
        path.relative_to(target): (
            path.stat().st_mode,
            path.read_bytes() if path.is_file() else None,
        )
        for path in target.rglob("*")
    }
    verify_original_repository_workflow_source(
        source, expected_binding=observed.binding
    )
    batch = read_original_repository_workflow_source(
        source,
        expected_binding=observed.binding,
        output_paths=(observed.files[0].output_path,),
    )
    assert (
        batch.bodies[0].body == (inputs[0] / observed.files[0].source_path).read_bytes()
    )
    # Journal append checks the original parent is active; readback alone does not.
    workflow = inputs[-2]
    snapshot = workflow.observe_repository_workflow_attempt(
        WorkspaceRepositoryWorkflowAttemptObserveRequest(
            observed.binding.source_repository_binding_ref,
            observed.binding.target_repository_binding_ref,
            observed.binding.attempt_ref,
            observed.binding.binding_ref,
        )
    )
    written = workflow.append_repository_workflow_evidence(
        attempt,
        WorkspaceRepositoryWorkflowEvidenceAppendRequest(
            observed.binding.binding_ref,
            snapshot.last_verified_cursor,
            snapshot.last_verified_digest,
            "qualification",
            request.invocation_ref,
            (),
            (),
            (),
            (),
            "caller_reported",
            "not_dispatched",
            "none",
            "not_attempted",
            False,
            (),
        ),
    )
    assert written.persistence_state == "persisted"
    assert written.cleanup_state == "completed"
    verify_original_repository_workflow_source(
        source, expected_binding=observed.binding
    )
    assert (await client.release_tree_projection()).cleanup_state == "completed"
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await client.prepare_tree_projection(request, source_delivery=source)


@pytest.mark.asyncio
async def test_bodyless_request_still_rejects_changed_original_source(inputs):
    _attempt, source, observed, client, request = setup(inputs)
    request = replace(
        request,
        files=(),
        ancestors=(WorkspaceTreeAncestorIntent("directory", "create", 0o755),),
    )
    path = inputs[0] / observed.files[0].source_path
    original = path.read_bytes()
    path.write_bytes(b"changed original source")
    with pytest.raises(WorkspaceTreeProjectionRefusal):
        await client.prepare_tree_projection(request, source_delivery=source)
    assert not (inputs[1] / "directory").exists()
    path.write_bytes(original)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await client.prepare_tree_projection(request, source_delivery=source)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field,value", [("maximum_combined_body_bytes", 1), ("maximum_file_bytes", 1)]
)
async def test_actual_bodies_must_fit_before_supplier_selection(inputs, field, value):
    _attempt, source, observed, client, request = setup(inputs)
    request = replace(request, limits=replace(request.limits, **{field: value}))
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="quota_exceeded"):
        await client.prepare_tree_projection(request, source_delivery=source)
    assert not (inputs[2] / "tree").exists() and not (inputs[1] / "out.py").exists()
    verify_original_repository_workflow_source(
        source, expected_binding=observed.binding
    )


@pytest.mark.asyncio
async def test_native_foreign_source_cannot_substitute_descriptive_binding(inputs):
    _attempt, _source, _observed, client, request = setup(inputs)
    with pytest.raises(WorkspaceTreeProjectionRefusal):
        await client.prepare_tree_projection(request, source_delivery=object())
    assert not (inputs[2] / "tree").exists()
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await client.prepare_tree_projection(request, source_delivery=object())


@pytest.mark.asyncio
async def test_unknown_output_mapping_refuses_before_any_retention(inputs):
    _attempt, source, _observed, client, request = setup(inputs)
    request = replace(
        request, files=(replace(request.files[0], source_output_path="not-selected"),)
    )
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="source_unavailable"):
        await client.prepare_tree_projection(request, source_delivery=source)
    assert not (inputs[2] / "tree").exists()


@pytest.mark.asyncio
async def test_original_source_mutation_refuses_and_restoration_cannot_resume(inputs):
    _attempt, source, observed, client, request = setup(inputs)
    path = inputs[0] / observed.files[0].source_path
    original = path.read_bytes()
    path.write_bytes(b"changed")
    with pytest.raises(WorkspaceTreeProjectionRefusal):
        await client.prepare_tree_projection(request, source_delivery=source)
    path.write_bytes(original)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await client.prepare_tree_projection(request, source_delivery=source)
    assert not (inputs[1] / "out.py").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["root", "binding", "execution"])
async def test_copied_target_binding_does_not_select_original_target(inputs, change):
    _attempt, source, _observed, client, request = setup(inputs)
    binding = request.expected_source_binding
    changes = {
        "root": {"target_root_identity": (9, 9)},
        "binding": {"target_repository_binding_ref": "sha256:" + "f" * 64},
        "execution": {"execution_id": "foreign"},
    }
    request = replace(
        request, expected_source_binding=replace(binding, **changes[change])
    )
    with pytest.raises(WorkspaceTreeProjectionRefusal):
        await client.prepare_tree_projection(request, source_delivery=source)
    assert not (inputs[2] / "tree").exists()


@pytest.mark.asyncio
async def test_unknown_holder_rejection_does_not_retire_or_pin_another_family(inputs):
    _attempt, _source, _observed, client, _request = setup(inputs)
    reference = weakref.ref(client)
    held = None
    try:
        await WorkspaceRepositoryTreeProjectionClient.release_tree_projection(object())
    except WorkspaceTreeProjectionRefusal as error:
        held = error
    del client
    gc.collect()
    assert reference() is None and held is not None


@pytest.mark.asyncio
async def test_registered_client_restamping_is_behavior_free_and_terminal(inputs):
    _attempt, source, _observed, client, request = setup(inputs)
    calls = []

    class Foreign(WorkspaceRepositoryTreeProjectionClient):
        __slots__ = ()

        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign dispatch")

    client.__class__ = Foreign
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await WorkspaceRepositoryTreeProjectionClient.prepare_tree_projection(
            client, request, source_delivery=source
        )
    client.__class__ = WorkspaceRepositoryTreeProjectionClient
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await client.prepare_tree_projection(request, source_delivery=source)
    assert calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["prepare", "retire", "release"])
async def test_selected_runtime_method_substitution_rejects_without_dispatch(
    inputs, monkeypatch, name
):
    from aware_workspace_runtime.repository_tree_projection import (
        WorkspaceRepositoryTreeProjectionRuntime,
    )

    _attempt, source, _observed, client, request = setup(inputs)
    original = vars(WorkspaceRepositoryTreeProjectionRuntime)[name]
    calls = []

    def foreign(*args):
        calls.append(True)
        raise AssertionError("foreign runtime")

    monkeypatch.setattr(WorkspaceRepositoryTreeProjectionRuntime, name, foreign)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await client.prepare_tree_projection(request, source_delivery=source)
    monkeypatch.setattr(WorkspaceRepositoryTreeProjectionRuntime, name, original)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await client.prepare_tree_projection(request, source_delivery=source)
    assert calls == []


@pytest.mark.asyncio
async def test_rejected_prepare_does_not_pin_borrowed_source_in_c_frames(inputs):
    _attempt, source, _observed, client, request = setup(inputs)
    reference = weakref.ref(source)
    held = None
    request = replace(
        request, files=(replace(request.files[0], source_output_path="not-selected"),)
    )
    try:
        await client.prepare_tree_projection(request, source_delivery=source)
    except WorkspaceTreeProjectionRefusal as error:
        held = error
    del source
    gc.collect()
    assert reference() is None and held is not None
    await client.release_tree_projection()


@pytest.mark.asyncio
async def test_fork_refuses_before_inherited_lock_and_preserves_parent(inputs):
    _attempt, _source, _observed, client, _request = setup(inputs)
    if not hasattr(os, "fork"):
        pytest.skip("POSIX fork proof")
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            client.observe_tree_projection_plan(object())
        except WorkspaceTreeProjectionRefusal:
            os.write(write_fd, b"refused")
        finally:
            os._exit(0)
    os.close(write_fd)
    try:
        assert os.read(read_fd, 16) == b"refused"
        assert os.waitpid(pid, 0)[1] == 0  # noqa: ASYNC222 - bounded exited disposable child
    finally:
        os.close(read_fd)
    assert (await client.release_tree_projection()).cleanup_state == "completed"


@pytest.mark.asyncio
async def test_wrong_thread_cannot_cleanup_parent(inputs):
    _attempt, _source, _observed, client, _request = setup(inputs)
    outcomes = []

    def other():
        try:
            client.observe_tree_projection_plan(object())
        except WorkspaceTreeProjectionRefusal as error:
            outcomes.append(error.code)

    worker = threading.Thread(target=other)
    worker.start()
    worker.join(timeout=2)
    assert not worker.is_alive() and outcomes == ["original_owner_required"]
    assert (await client.release_tree_projection()).cleanup_state == "completed"


@pytest.mark.parametrize(
    "kind",
    [
        WorkspaceTreeProjectionPlan,
        WorkspaceTreeProjectionAdmission,
        WorkspaceTreeProjectionResult,
        WorkspaceRepositoryTreeProjectionClient,
    ],
)
def test_opaque_handles_cannot_be_constructed_or_copied(kind):
    with pytest.raises(TypeError):
        kind()
    forged = object.__new__(kind)
    for operation in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError):
            operation(forged)


@pytest.mark.asyncio
async def test_runtime_restamping_refuses_before_foreign_attributes(inputs):
    from aware_workspace_runtime.repository_tree_projection import (
        WorkspaceRepositoryTreeProjectionRuntime,
    )
    from aware_workspace_sdk import repository_tree_projection as api

    _attempt, source, _observed, client, request = setup(inputs)
    runtime = next(
        record[0] for original, record in api._CLIENTS.items() if original is client
    )
    calls = []

    class Foreign(WorkspaceRepositoryTreeProjectionRuntime):
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign receiver")

        def __setattr__(self, name, value):
            calls.append(name)
            raise AssertionError("foreign receiver")

    object.__setattr__(runtime, "__class__", Foreign)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await client.prepare_tree_projection(request, source_delivery=source)
    object.__setattr__(runtime, "__class__", WorkspaceRepositoryTreeProjectionRuntime)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await client.prepare_tree_projection(request, source_delivery=source)
    assert calls == []


@pytest.mark.asyncio
async def test_harness_refusal_is_terminal_before_lock_and_restoration(
    inputs, monkeypatch
):
    _attempt, source, _observed, client, request = setup(inputs)
    monkeypatch.setenv("CODEX_THREAD_ID", "changed-tree-execution")
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await client.prepare_tree_projection(request, source_delivery=source)
    monkeypatch.setenv("CODEX_THREAD_ID", "workflow-planning-test")
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await client.prepare_tree_projection(request, source_delivery=source)


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["CREATE", "UPDATE", "DELETE"])
async def test_native_file_plan_preserves_exact_physical_footprint(inputs, kind):
    _attempt, source, _observed, client, request = setup(inputs)
    target = inputs[1] / "out.py"
    if kind != "CREATE":
        target.write_bytes(b"original target")
        target.chmod(0o640)
    before = target.read_bytes() if target.exists() else None
    mode = target.stat().st_mode if target.exists() else None
    request = replace(
        request,
        files=(
            replace(
                request.files[0],
                kind=kind,
                source_output_path=None
                if kind == "DELETE"
                else request.files[0].source_output_path,
                requested_mode=None if kind == "DELETE" else 0o755,
            ),
        ),
    )
    plan = await client.prepare_tree_projection(request, source_delivery=source)
    observed = client.observe_tree_projection_plan(plan)
    payload = asdict(observed.binding)
    del payload["binding_ref"]
    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    assert observed.binding.binding_ref == "sha256:" + digest
    assert observed.binding.files[0].kind == kind
    assert len(observed.binding.scratch_effects) == (0 if kind == "DELETE" else 4)
    assert set(observed.binding.effect_paths) == {"out.py"} | {
        row.path for row in observed.binding.scratch_effects
    }
    assert all(
        not (inputs[1] / row.path).exists() for row in observed.binding.scratch_effects
    )
    assert (target.read_bytes() if target.exists() else None) == before
    assert (target.stat().st_mode if target.exists() else None) == mode
    assert (await client.release_tree_projection()).cleanup_state == "completed"


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["source", "target", "scratch"])
async def test_original_plan_currentness_loss_is_terminal(inputs, change):
    _attempt, source, observed, client, request = setup(inputs)
    plan = await client.prepare_tree_projection(request, source_delivery=source)
    bound = client.observe_tree_projection_plan(plan).binding
    if change == "source":
        path = inputs[0] / observed.files[0].source_path
        original = path.read_bytes()
    elif change == "target":
        path, original = inputs[1] / "out.py", None
    else:
        path, original = inputs[1] / bound.scratch_effects[0].path, None
    path.write_bytes(b"foreign change")
    with pytest.raises(WorkspaceTreeProjectionRefusal):
        client.verify_tree_projection_plan(plan, expected_binding=bound)
    if original is None:
        path.unlink()
    else:
        path.write_bytes(original)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        client.observe_tree_projection_plan(plan)
    released = await client.release_tree_projection()
    assert released.cleanup_state == "completed"
    assert any(row.kind == "descriptor" for row in released.resources)


@pytest.mark.asyncio
async def test_detached_binding_cannot_mutate_original_plan(inputs):
    _attempt, source, _observed, client, request = setup(inputs)
    plan = await client.prepare_tree_projection(request, source_delivery=source)
    observed = client.observe_tree_projection_plan(plan)
    original = observed.binding.binding_ref
    object.__setattr__(observed.binding, "physical_preparation_ref", "foreign")
    fresh = client.observe_tree_projection_plan(plan)
    assert fresh.binding.binding_ref == original
    assert fresh.binding.physical_preparation_ref != "foreign"
    with pytest.raises(WorkspaceTreeProjectionRefusal):
        client.verify_tree_projection_plan(plan, expected_binding=observed.binding)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        client.observe_tree_projection_plan(plan)
    await client.release_tree_projection()


@pytest.mark.asyncio
async def test_missing_issue_admission_cannot_execute_prepared_tree(inputs):
    _attempt, source, _observed, client, request = setup(inputs)
    plan = await client.prepare_tree_projection(request, source_delivery=source)
    bound = client.observe_tree_projection_plan(plan).binding
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="issue_refused"):
        await client.enroll_issue_tree_projection(plan, issue_admission=object())
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        client.verify_tree_projection_plan(plan, expected_binding=bound)
    assert not (inputs[1] / "out.py").exists()
    await client.release_tree_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method", ["observe_preparation", "validate_current", "release"]
)
async def test_selected_physical_method_substitution_never_dispatches(
    inputs, monkeypatch, method
):
    from aware_file_system.retained_tree_projection import (
        RetainedPhysicalTreeProjection,
    )

    _attempt, source, observed, client, request = setup(inputs)
    plan = await client.prepare_tree_projection(request, source_delivery=source)
    original = vars(RetainedPhysicalTreeProjection)[method]
    calls = []

    def foreign(*args):
        calls.append(True)
        raise AssertionError("substituted physical method")

    monkeypatch.setattr(RetainedPhysicalTreeProjection, method, foreign)
    with pytest.raises(WorkspaceTreeProjectionRefusal):
        client.observe_tree_projection_plan(plan)
    monkeypatch.setattr(RetainedPhysicalTreeProjection, method, original)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        client.observe_tree_projection_plan(plan)
    assert calls == []
    verify_original_repository_workflow_source(
        source, expected_binding=observed.binding
    )
    await client.release_tree_projection()


@pytest.mark.asyncio
async def test_foreign_plan_does_not_retire_original_preparation(inputs):
    _attempt, source, _observed, client, request = setup(inputs)
    plan = await client.prepare_tree_projection(request, source_delivery=source)
    original = client.observe_tree_projection_plan(plan)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="original_owner_required"):
        client.observe_tree_projection_plan(object())
    assert client.observe_tree_projection_plan(plan) == original
    await client.release_tree_projection()


@pytest.mark.asyncio
async def test_explicit_ancestors_and_read_guards_are_bound_before_admission(inputs):
    _attempt, source, _observed, client, request = setup(inputs)
    (inputs[1] / "existing").mkdir(mode=0o750)
    request = replace(
        request,
        files=(replace(request.files[0], path="existing/new/out.py"),),
        ancestors=(
            WorkspaceTreeAncestorIntent("existing", "preserve", None),
            WorkspaceTreeAncestorIntent("existing/new", "create", 0o755),
        ),
    )
    plan = await client.prepare_tree_projection(request, source_delivery=source)
    observed = client.observe_tree_projection_plan(plan)
    assert observed.binding.transition_count == 3
    assert observed.binding.read_guard_paths == ("existing",)
    assert "existing" not in observed.binding.effect_paths
    assert {"existing/new", "existing/new/out.py"} <= set(observed.binding.effect_paths)
    assert all(row.ordinal == 2 for row in observed.binding.scratch_effects)
    assert not (inputs[1] / "existing/new").exists()
    assert (await client.release_tree_projection()).cleanup_state == "completed"


@pytest.mark.asyncio
async def test_original_physical_failed_issuance_keeps_cleanup_evidence(inputs):
    _attempt, source, observed, client, request = setup(inputs)
    request = replace(
        request, limits=replace(request.limits, maximum_live_descriptors=1)
    )
    with pytest.raises(
        WorkspaceTreeProjectionRefusal, match="physical_refused"
    ) as caught:
        await client.prepare_tree_projection(request, source_delivery=source)
    cleanup = caught.value.evidence.cleanup
    assert cleanup.cleanup_state == "completed"
    assert any(row.kind == "descriptor" for row in cleanup.resources)
    assert any(row.kind == "body_retention" for row in cleanup.resources)
    assert all(row.cleanup_state == "completed" for row in cleanup.resources)
    assert caught.value.__cause__.code == "tree_descriptor_capacity_exceeded"
    verify_original_repository_workflow_source(
        source, expected_binding=observed.binding
    )
    assert not (inputs[1] / "out.py").exists()


async def genuine_issue_enrollment(inputs, kind="create"):
    from workspaces.aware_coordination.modules.workflow.sdks.issue.python.tests.test_repository_tree_projection_admission import (
        prepared,
    )

    (
        attempt,
        source,
        workspace,
        plan,
        binding,
        issuer,
        issue_plan,
        path,
    ) = await prepared(inputs, kind=kind)
    issue_admission = await issuer.admit_tree_projection(issue_plan)
    enrollment = await workspace.enroll_issue_tree_projection(
        plan, issue_admission=issue_admission
    )
    return (
        attempt,
        source,
        workspace,
        plan,
        binding,
        issuer,
        issue_admission,
        enrollment,
        path,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["create", "delete", "directory", "nested"])
async def test_genuine_issue_enrollment_spends_once_then_executes_original_tree(
    inputs, kind
):
    from aware_issue_sdk.source_projection import (
        IssueTreeProjectionRefusal,
        consume_tree_projection_admission,
    )

    (
        attempt,
        source,
        workspace,
        plan,
        binding,
        issuer,
        issue,
        enrollment,
        _path,
    ) = await genuine_issue_enrollment(inputs, kind)
    assert attempt is not None
    assert type(enrollment) is WorkspaceTreeProjectionAdmission
    assert workspace.observe_tree_projection_plan(plan).phase == "enrolled"
    result = await workspace.project_tree(plan, admission=enrollment)
    observed = read_original_tree_projection_result(result, expected_binding=binding)
    spent = issuer.observe_tree_projection_admission(issue)
    assert spent.phase == "spent" and spent.consumption_state == "spent"
    assert observed.consumption_ref == spent.consumption_ref
    assert (
        observed.phase == "complete"
        and observed.completed_prefix == binding.transition_count
    )
    assert observed.pending_ordinal is None and observed.ledger_complete
    assert (
        observed.index_state == "persisted"
        and observed.cleanup.cleanup_state == "completed"
    )
    assert len(observed.receipts) == binding.transition_count
    if kind == "delete":
        assert not (inputs[1] / "out.py").exists()
    elif kind == "directory":
        assert (inputs[1] / "public").is_dir()
        assert observed.receipts[0].mutation_receipt_ref is None
    else:
        file = binding.files[0]
        assert (inputs[1] / file.path).read_bytes() == (
            inputs[0] / file.source_path
        ).read_bytes()
        assert (inputs[1] / file.path).stat().st_mode & 0o777 == file.requested_mode
    for receipt in observed.receipts:
        if receipt.kind in ("CREATE", "DELETE"):
            assert (
                receipt.mutation_receipt_ref
                and receipt.capture_ref
                and receipt.delta_ref
            )
    resolution = await workspace.resolve_tree_projection_receipts(enrollment)
    assert resolution.resolution_state == "known" and not resolution.authorizes_retry
    assert resolution.observation == observed
    verify_original_repository_workflow_source(
        source, expected_binding=binding.source_binding
    )
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(plan, admission=enrollment)
    with pytest.raises(IssueTreeProjectionRefusal):
        consume_tree_projection_admission(issue, binding=binding)
    await issuer.release_tree_projection_admission(issue)
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_revoked_issue_during_spend_is_terminal_without_tree_effect(inputs):
    (
        attempt,
        source,
        workspace,
        plan,
        binding,
        issuer,
        issue,
        enrollment,
        path,
    ) = await genuine_issue_enrollment(inputs)
    original = path.read_bytes()
    path.write_bytes(original.replace(b"In Progress", b"Closed"))
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="issue_refused"):
        await workspace.project_tree(plan, admission=enrollment)
    observation = issuer.observe_tree_projection_admission(issue)
    assert observation.phase == "retired" and observation.consumption_state == "spent"
    path.write_bytes(original)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(plan, admission=enrollment)
    assert not (inputs[1] / "out.py").exists() and attempt is not None
    verify_original_repository_workflow_source(
        source, expected_binding=binding.source_binding
    )
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
async def test_changed_source_refuses_before_borrowed_issue_spend(inputs):
    (
        attempt,
        _source,
        workspace,
        plan,
        binding,
        issuer,
        issue,
        enrollment,
        path,
    ) = await genuine_issue_enrollment(inputs)
    changed = inputs[0] / binding.files[0].source_path
    original = changed.read_bytes()
    changed.write_bytes(b"changed original source")
    with pytest.raises(WorkspaceTreeProjectionRefusal):
        await workspace.project_tree(plan, admission=enrollment)
    assert (
        issuer.observe_tree_projection_admission(issue).consumption_state == "not_spent"
    )
    changed.write_bytes(original)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(plan, admission=enrollment)
    assert attempt is not None and path.exists()
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name",
    [
        "verify_tree_projection_admission",
        "consume_tree_projection_admission",
        "verify_tree_projection_consumption",
    ],
)
async def test_selected_issue_port_substitution_cannot_execute(
    inputs, monkeypatch, name
):
    from aware_issue_sdk import source_projection as ports

    (
        attempt,
        source,
        workspace,
        plan,
        binding,
        issuer,
        issue,
        enrollment,
        path,
    ) = await genuine_issue_enrollment(inputs)
    original = vars(ports)[name]
    calls = []

    def hostile(*args, **kwargs):
        calls.append(True)
        raise AssertionError("substituted Issue entrance")

    monkeypatch.setattr(ports, name, hostile)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="issue_refused"):
        await workspace.project_tree(plan, admission=enrollment)
    monkeypatch.setattr(ports, name, original)
    assert (
        calls == []
        and issuer.observe_tree_projection_admission(issue).consumption_state
        == "not_spent"
    )
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(plan, admission=enrollment)
    assert attempt is not None and path.exists()
    verify_original_repository_workflow_source(
        source, expected_binding=binding.source_binding
    )
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
async def test_controller_uses_original_issue_checks_on_owner_thread_without_callbacks(
    inputs,
):
    from aware_issue_sdk import source_projection as issue_ports
    from aware_workspace_runtime.repository_mutation import (
        WorkspaceRepositoryMutationCoordinator,
    )
    from aware_workspace_sdk.repository_tree_projection import (
        WorkspaceRepositoryTreeProjectionClient,
    )

    (
        attempt,
        source,
        workspace,
        plan,
        binding,
        issuer,
        issue,
        enrollment,
        path,
    ) = await genuine_issue_enrollment(inputs)
    code_events = {
        issue_ports.consume_tree_projection_admission.__code__: "consume",
        issue_ports.verify_tree_projection_consumption.__code__: "verify",
    }
    workspace_codes = {
        WorkspaceRepositoryTreeProjectionClient.observe_tree_projection_plan.__code__,
        WorkspaceRepositoryTreeProjectionClient.verify_tree_projection_plan.__code__,
    }
    transaction = WorkspaceRepositoryMutationCoordinator._run_tree_projection.__code__
    state = {"transaction": 0, "issue": 0}
    calls, callbacks = [], []

    def profile(frame, event, arg):
        if event not in ("call", "return"):
            return
        direction = 1 if event == "call" else -1
        if frame.f_code is transaction:
            state["transaction"] += direction
        if frame.f_code in code_events:
            state["issue"] += direction
            if event == "call":
                calls.append(
                    (
                        code_events[frame.f_code],
                        threading.get_ident(),
                        state["transaction"],
                    )
                )
        if frame.f_code in workspace_codes and state["issue"] and event == "call":
            callbacks.append(True)

    prior = sys.getprofile()
    sys.setprofile(profile)
    try:
        result = await workspace.project_tree(plan, admission=enrollment)
        assert type(result) is WorkspaceTreeProjectionResult
    finally:
        sys.setprofile(prior)
    assert [name for name, _, _ in calls] == ["consume"] + ["verify"] * 5
    assert all(thread == threading.get_ident() for _, thread, _ in calls)
    assert [depth for _, _, depth in calls] == [1, 1, 1, 1, 1, 0]
    assert callbacks == [] and state == {"transaction": 0, "issue": 0}
    assert attempt is not None and path.exists()
    verify_original_repository_workflow_source(
        source, expected_binding=binding.source_binding
    )
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
async def test_lost_original_consumption_return_never_authorizes_dispatch(inputs):
    from aware_issue_sdk import source_projection as issue_ports

    (
        attempt,
        source,
        workspace,
        plan,
        binding,
        issuer,
        issue,
        enrollment,
        path,
    ) = await genuine_issue_enrollment(inputs)
    selected = issue_ports.consume_tree_projection_admission.__code__

    def lost_return(frame, event, arg):
        if event == "return" and frame.f_code is selected:
            # Fault injection at the genuine return boundary; no supplying port,
            # authority, record, source reader or writer is substituted.
            del frame, arg
            raise RuntimeError("original consumption return lost")

    previous = sys.getprofile()
    sys.setprofile(lost_return)
    try:
        with pytest.raises(
            WorkspaceTreeProjectionRefusal, match="issue_refused"
        ) as caught:
            await workspace.project_tree(plan, admission=enrollment)
    finally:
        sys.setprofile(previous)
    assert str(caught.value.__cause__) == "original consumption return lost"
    assert issuer.observe_tree_projection_admission(issue).consumption_state == "spent"
    assert (
        caught.value.result is None
        and caught.value.evidence.cleanup.cleanup_state == "completed"
    )
    assert not (inputs[1] / "out.py").exists() and attempt is not None and path.exists()
    verify_original_repository_workflow_source(
        source, expected_binding=binding.source_binding
    )
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(plan, admission=enrollment)
    await issuer.release_tree_projection_admission(issue)


async def enroll_original_request(inputs, request, source, workspace):
    from aware_issue_sdk.repository_tree_projection_values import (
        IssueTreeProjectionRequest,
    )
    from aware_issue_sdk.source_projection import IssueRepositoryTreeProjectionClient

    from workspaces.aware_coordination.modules.workflow.sdks.issue.python.tests.test_repository_tree_projection_admission import (
        EXECUTION,
        REF,
        digest,
        install_issue,
    )

    install_issue(
        inputs[1],
        scope=tuple(row.path for row in request.files)
        + tuple(row.path for row in request.ancestors),
    )
    tree = await workspace.prepare_tree_projection(request, source_delivery=source)
    binding = workspace.observe_tree_projection_plan(tree).binding
    path = install_issue(inputs[1], scope=binding.effect_paths)
    issuer = IssueRepositoryTreeProjectionClient.filesystem(
        repository_root=inputs[1], execution_id=EXECUTION
    )
    issue_plan = await issuer.prepare_tree_projection_admission(
        IssueTreeProjectionRequest(
            REF, digest(path.read_bytes()), EXECUTION, "harness:declared", "intent:tree"
        ),
        workspace_client=workspace,
        workspace_plan=tree,
        expected_binding=binding,
    )
    issue = await issuer.admit_tree_projection(issue_plan)
    enrollment = await workspace.enroll_issue_tree_projection(
        tree, issue_admission=issue
    )
    return tree, binding, issuer, issue, enrollment, path


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", [0o644, 0o755])
@pytest.mark.parametrize("content", ["changed", "same"])
async def test_real_update_retains_byte_evidence_only_for_byte_changes(
    inputs, mode, content
):
    from aware_workspace_fs_adapter.repository_mutation_store import (
        WorkspaceRepositoryMutationStore,
    )

    parent, source, observed, workspace, request = setup(inputs)
    body = (inputs[0] / observed.files[0].source_path).read_bytes()
    (inputs[1] / "out.py").write_bytes(b"previous" if content == "changed" else body)
    (inputs[1] / "out.py").chmod(0o644)
    request = replace(
        request, files=(replace(request.files[0], kind="UPDATE", requested_mode=mode),)
    )
    tree, binding, issuer, issue, enrollment, _path = await enroll_original_request(
        inputs, request, source, workspace
    )
    result = await workspace.project_tree(tree, admission=enrollment)
    result_observation = read_original_tree_projection_result(
        result, expected_binding=binding
    )
    receipt = result_observation.receipts[0]
    assert (inputs[1] / "out.py").read_bytes() == body
    assert (inputs[1] / "out.py").stat().st_mode & 0o777 == mode
    assert (
        result_observation.completed_prefix == 1
        and result_observation.phase == "complete"
    )
    assert result_observation.index_state == "persisted"
    index = WorkspaceRepositoryMutationStore(
        repository_binding_ref=binding.target_repository_binding_ref,
        state_root=inputs[2] / "tree" / "receipts",
    )
    if content == "changed":
        assert (
            receipt.mutation_receipt_ref and receipt.capture_ref and receipt.delta_ref
        )
        fingerprint, canonical = index.resolve(receipt.mutation_receipt_ref)
        assert fingerprint == binding.binding_ref + ":0"
        assert (
            canonical.receipt.operation_ref == "workspace_sdk.project_repository_tree"
        )
        assert (
            canonical.receipt.expected_content_digest
            == binding.files[0].before.content_digest
        )
        assert (
            canonical.receipt.result_content_digest == binding.files[0].successor_digest
        )
        assert canonical.receipt.context_refs == (
            binding.binding_ref,
            receipt.consumption_ref,
        )
    else:
        assert (
            receipt.mutation_receipt_ref
            is receipt.capture_ref
            is receipt.delta_ref
            is None
        )
        assert index.retained_count == 0
    assert parent is not None
    await workspace.release_tree_projection()
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        read_original_tree_projection_result(result, expected_binding=binding)
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
async def test_subsequent_ordinal_refuses_after_original_issue_revocation(
    inputs, monkeypatch
):
    parent, source, _observed, workspace, request = setup(inputs)
    request = replace(
        request, files=(request.files[0], replace(request.files[0], path="second.py"))
    )
    (
        tree,
        _binding,
        issuer,
        issue,
        enrollment,
        issue_path,
    ) = await enroll_original_request(inputs, request, source, workspace)
    original = os.link
    executed = []

    def revoke_after_first(*args, **kwargs):
        returned = original(*args, **kwargs)
        if args[1] == "out.py":
            executed.append(True)
            issue_path.write_bytes(
                issue_path.read_bytes().replace(b"In Progress", b"Closed")
            )
        return returned

    monkeypatch.setattr(os, "link", revoke_after_first)
    with pytest.raises(WorkspaceTreeProjectionRefusal) as caught:
        await workspace.project_tree(tree, admission=enrollment)
    observation = caught.value.evidence.observation
    assert executed == [True] and parent is not None
    assert observation.completed_prefix == 1 and observation.phase == "held"
    assert (
        len(observation.receipts) == 1 and observation.receipts[0].mutation_receipt_ref
    )
    assert (inputs[1] / "out.py").exists() and not (inputs[1] / "second.py").exists()
    assert caught.value.evidence.cleanup.cleanup_state == "completed"
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(tree, admission=enrollment)
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
async def test_cancellation_settles_actual_writer_before_cleanup(inputs, monkeypatch):
    (
        parent,
        _source,
        workspace,
        tree,
        _binding,
        issuer,
        issue,
        enrollment,
        _path,
    ) = await genuine_issue_enrollment(inputs)
    entered, finish = threading.Event(), threading.Event()
    original = os.link

    def blocked(*args, **kwargs):
        if args[1] == "out.py":
            entered.set()
            if not finish.wait(5):
                raise RuntimeError("test writer settlement timed out")
        return original(*args, **kwargs)

    monkeypatch.setattr(os, "link", blocked)
    task = asyncio.create_task(workspace.project_tree(tree, admission=enrollment))
    assert await asyncio.to_thread(entered.wait, 3)
    task.cancel()
    release = asyncio.create_task(workspace.release_tree_projection())
    await asyncio.sleep(0.02)
    assert not task.done() and not release.done()
    finish.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert (await release).cleanup_state == "completed"
    resolution = await workspace.resolve_tree_projection_receipts(enrollment)
    assert resolution.observation.phase == "held"
    assert resolution.observation.completed_prefix == 1
    assert resolution.observation.receipts[0].mutation_receipt_ref
    assert (inputs[1] / "out.py").exists() and parent is not None
    assert not resolution.authorizes_retry
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
async def test_lost_link_return_preserves_unknown_effect_without_success(
    inputs, monkeypatch
):
    (
        parent,
        _source,
        workspace,
        tree,
        _binding,
        issuer,
        issue,
        enrollment,
        _path,
    ) = await genuine_issue_enrollment(inputs)
    original = os.link

    def lose(*args, **kwargs):
        result = original(*args, **kwargs)
        if args[1] == "out.py":
            raise KeyboardInterrupt("actual link return lost")
        return result

    monkeypatch.setattr(os, "link", lose)
    with pytest.raises(WorkspaceTreeProjectionRefusal) as caught:
        await workspace.project_tree(tree, admission=enrollment)
    observation = caught.value.evidence.observation
    assert (inputs[1] / "out.py").exists() and parent is not None
    assert observation.effect_state == "unknown" and not observation.ledger_complete
    assert observation.completed_prefix == 0 and len(observation.receipts) == 1
    assert observation.receipts[0].completion_state != "complete"
    assert observation.receipts[0].mutation_receipt_ref is None
    assert any(
        row.state == "unknown" for row in observation.receipts[0].physical_effects
    )
    assert caught.value.result is None
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(tree, admission=enrollment)
    await workspace.release_tree_projection()
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
async def test_known_write_survives_index_persistence_failure(inputs, monkeypatch):
    from aware_workspace_fs_adapter.repository_mutation_store import (
        WorkspaceRepositoryMutationStore,
    )

    (
        parent,
        _source,
        workspace,
        tree,
        binding,
        issuer,
        issue,
        enrollment,
        _path,
    ) = await genuine_issue_enrollment(inputs)

    def failed_index(self):
        raise OSError("disposable receipt-index write unavailable")

    monkeypatch.setattr(WorkspaceRepositoryMutationStore, "_persist", failed_index)
    result = await workspace.project_tree(tree, admission=enrollment)
    observation = read_original_tree_projection_result(result, expected_binding=binding)
    assert observation.phase == "complete" and observation.effect_state == "applied"
    assert (
        observation.completed_prefix == 1
        and observation.receipts[0].mutation_receipt_ref
    )
    assert (
        observation.index_state == "unavailable"
        and observation.cleanup.cleanup_state == "completed"
    )
    resolution = await workspace.resolve_tree_projection_receipts(enrollment)
    assert (
        resolution.resolution_state == "incomplete" and not resolution.authorizes_retry
    )
    assert parent is not None and (inputs[1] / "out.py").exists()
    await workspace.release_tree_projection()
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method", ["apply_next_transition", "finish", "validate_consumed_current"]
)
async def test_execution_method_substitution_never_dispatches(
    inputs, monkeypatch, method
):
    from aware_file_system.retained_tree_projection import (
        RetainedPhysicalTreeProjection,
    )

    (
        parent,
        _source,
        workspace,
        tree,
        _binding,
        issuer,
        issue,
        enrollment,
        _path,
    ) = await genuine_issue_enrollment(inputs)
    original = vars(RetainedPhysicalTreeProjection)[method]
    calls = []

    def hostile(*args):
        calls.append(True)

    monkeypatch.setattr(RetainedPhysicalTreeProjection, method, hostile)
    with pytest.raises(WorkspaceTreeProjectionRefusal):
        await workspace.project_tree(tree, admission=enrollment)
    monkeypatch.setattr(RetainedPhysicalTreeProjection, method, original)
    assert calls == [] and not (inputs[1] / "out.py").exists() and parent is not None
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(tree, admission=enrollment)
    await workspace.release_tree_projection()
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
async def test_explicit_directory_creation_then_original_file_ordinal(inputs):
    parent, source, observed, workspace, request = setup(inputs)
    request = replace(
        request,
        files=(
            replace(request.files[0], path="public/deep/out.py", requested_mode=0o755),
        ),
        ancestors=(
            WorkspaceTreeAncestorIntent("public", "create", 0o755),
            WorkspaceTreeAncestorIntent("public/deep", "create", 0o755),
        ),
    )
    tree, binding, issuer, issue, enrollment, _path = await enroll_original_request(
        inputs, request, source, workspace
    )
    result = await workspace.project_tree(tree, admission=enrollment)
    evidence = read_original_tree_projection_result(result, expected_binding=binding)
    assert [row.kind for row in evidence.receipts] == [
        "directory_create",
        "directory_create",
        "CREATE",
    ]
    assert evidence.completed_prefix == 3 and evidence.ledger_complete
    assert len(evidence.final_entries) == 4
    assert sum(pin.content_digest is not None for pin in evidence.final_entries) == 1
    assert all(row.mutation_receipt_ref is None for row in evidence.receipts[:2])
    assert evidence.receipts[2].mutation_receipt_ref and evidence.receipts[2].delta_ref
    assert (inputs[1] / "public/deep/out.py").read_bytes() == (
        inputs[0] / observed.files[0].source_path
    ).read_bytes()
    assert (inputs[1] / "public/deep/out.py").stat().st_mode & 0o777 == 0o755
    assert parent is not None
    await workspace.release_tree_projection()
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
async def test_postimage_failure_preserves_actual_effect_without_final_result(
    inputs, monkeypatch
):
    (
        parent,
        _source,
        workspace,
        tree,
        _binding,
        issuer,
        issue,
        enrollment,
        _path,
    ) = await genuine_issue_enrollment(inputs)
    original = os.link

    def changed_postimage(*args, **kwargs):
        returned = original(*args, **kwargs)
        if args[1] == "out.py":
            (inputs[1] / "out.py").chmod(0o777)
        return returned

    monkeypatch.setattr(os, "link", changed_postimage)
    with pytest.raises(WorkspaceTreeProjectionRefusal) as caught:
        await workspace.project_tree(tree, admission=enrollment)
    observation = caught.value.evidence.observation
    assert (inputs[1] / "out.py").exists() and parent is not None
    assert observation.phase == "held" and observation.completed_prefix == 0
    assert observation.effect_state in ("applied", "unknown")
    assert len(observation.receipts) == 1
    assert observation.receipts[0].completion_state != "complete"
    assert observation.receipts[0].mutation_receipt_ref is None
    assert caught.value.result is None
    assert caught.value.evidence.cleanup.cleanup_state == "completed"
    await workspace.release_tree_projection()
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure", ["none", "close_return", "close_interrupt", "port_return"]
)
async def test_physical_release_uncertainty_preserves_known_write_and_receipt(
    inputs, failure
):
    from aware_file_system import retained_tree_projection as physical
    from aware_file_system.confined_mutation import _ReadLedger

    (
        parent,
        source,
        workspace,
        tree,
        binding,
        issuer,
        issue,
        enrollment,
        _path,
    ) = await genuine_issue_enrollment(inputs)
    state = next(
        value
        for value in physical._HANDLES.values()
        if value.root == inputs[1] and value.root_fd is not None
    )
    root_fd = state.root_fd
    original_close = os.close
    close_code = _ReadLedger.close.__code__
    release_code = physical.RetainedPhysicalTreeProjection.release.__code__
    closes, releases = [], []

    def release_profile(frame, event, returned):
        if frame.f_code is release_code and event == "call":
            releases.append(True)
        if (
            event == "c_return"
            and returned is original_close
            and frame.f_code is close_code
            and frame.f_locals.get("descriptor") == root_fd
            and (inputs[1] / "out.py").exists()
        ):
            closes.append(root_fd)
            if failure == "close_return":
                raise OSError("original target root close return unavailable")
            if failure == "close_interrupt":
                raise KeyboardInterrupt("original target root close interrupted")
        if (
            failure == "port_return"
            and event == "return"
            and frame.f_code is release_code
        ):
            raise RuntimeError("original release port return unavailable")

    previous = sys.getprofile()
    sys.setprofile(release_profile)
    try:
        if failure == "none":
            result = await workspace.project_tree(tree, admission=enrollment)
        else:
            with pytest.raises(WorkspaceTreeProjectionRefusal) as caught:
                await workspace.project_tree(tree, admission=enrollment)
    finally:
        sys.setprofile(previous)
    assert closes == [root_fd] and releases == [True]
    assert parent is not None and (inputs[1] / "out.py").exists()
    if failure == "none":
        observation = read_original_tree_projection_result(
            result, expected_binding=binding
        )
        assert observation.cleanup.cleanup_state == "completed"
        assert observation.cleanup.ledger_complete and observation.ledger_complete
    else:
        observation = caught.value.evidence.observation
        assert caught.value.result is None
        cleanup = caught.value.evidence.cleanup
        assert cleanup.cleanup_state == "unknown" and not cleanup.ledger_complete
        assert not observation.ledger_complete and observation.cleanup == cleanup
        assert any(
            row.ownership == "unknown" and row.cleanup_state == "unknown"
            for row in cleanup.resources
        )
        if failure in ("close_return", "close_interrupt"):
            original = physical._cleanup(state)
            assert original.cleanup_state == "unknown" and not original.ledger_complete
            assert {row.resource_ref for row in original.resources} <= {
                row.resource_ref for row in cleanup.resources
            }
            assert any(
                row.kind == "descriptor" and row.ownership == "unknown"
                for row in cleanup.resources
            )
            assert observation.diagnostics == original.diagnostics
            assert str(caught.value.__cause__) == "tree_cleanup_unknown"
        else:
            assert (
                str(caught.value.__cause__)
                == "original release port return unavailable"
            )
        resolved = await workspace.resolve_tree_projection_receipts(enrollment)
        assert resolved.observation == observation and not resolved.authorizes_retry
    assert observation.completed_prefix == 1
    assert observation.receipts[0].mutation_receipt_ref
    assert observation.receipts[0].capture_ref and observation.receipts[0].delta_ref
    verify_original_repository_workflow_source(
        source, expected_binding=binding.source_binding
    )
    # Explicit release may settle other Workspace resources, but must never
    # restore or redispatch the spent physical disposal right.
    sys.setprofile(release_profile)
    try:
        first = await workspace.release_tree_projection()
        second = await workspace.release_tree_projection()
    finally:
        sys.setprofile(previous)
    assert closes == [root_fd] and releases == [True]
    if failure != "none":
        assert first.cleanup_state == second.cleanup_state == "unknown"
        assert not first.ledger_complete and not second.ledger_complete
        resolved = await workspace.resolve_tree_projection_receipts(enrollment)
        assert resolved.observation.cleanup.cleanup_state == "unknown"
        assert not resolved.observation.cleanup.ledger_complete
        assert (
            resolved.observation.receipts[0].mutation_receipt_ref
            == observation.receipts[0].mutation_receipt_ref
        )
        assert not resolved.authorizes_retry
    await issuer.release_tree_projection_admission(issue)


async def run_complete_tree_resource_probe(count, total, outfile):
    """Fresh-process genuine C qualification; never a substitute provider rail."""
    import resource
    import tempfile
    import time
    from dataclasses import replace
    from pathlib import Path

    import pytest
    from aware_issue_sdk.repository_tree_projection_values import (
        IssueTreeProjectionRequest,
    )
    from aware_issue_sdk.source_projection import IssueRepositoryTreeProjectionClient
    from aware_workspace_sdk.repository_tree_projection import (
        WorkspaceRepositoryTreeProjectionClient,
        read_original_tree_projection_result,
    )
    from aware_workspace_sdk.repository_tree_projection_values import (
        DEFAULT_TREE_LIMITS,
        WorkspaceTreeFileIntent,
        WorkspaceTreeProjectionRequest,
    )
    from aware_workspace_sdk.repository_workflow import (
        release_original_repository_workflow_source,
    )

    from workspaces.aware_coordination.modules.workflow.sdks.issue.python.tests.test_repository_tree_projection_admission import (
        EXECUTION,
        REF,
        digest,
        install_issue,
    )
    from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_workflow import (
        commit,
        inputs,
        workflow_source,
    )

    def peak_rss_mib():
        status = Path("/proc/self/status").read_text()
        return (
            int(
                next(
                    line.split()[1]
                    for line in status.splitlines()
                    if line.startswith("VmHWM:")
                )
            )
            / 1024
        )

    def emit(stage, **values):
        print(json.dumps({"stage": stage, **values}), flush=True)

    async def _run(count, total, outfile):
        monkey = pytest.MonkeyPatch()
        with tempfile.TemporaryDirectory(prefix="workspace-tree-resource-") as tmp:
            args = inputs.__wrapped__(Path(tmp), monkey)
            src, target, state, package, workflow, request = args
            base, remainder = divmod(total, count)
            for i in range(count):
                prefix = (f"# body {i:06d}\n").encode()
                size = base + (i < remainder)
                (package / f"file_{i:04d}.py").write_bytes(
                    prefix + b"x" * (size - len(prefix))
                )
            request = replace(request, source_commit=commit(src))
            args = (*args[:-1], request)
            try:
                parent, source, observed = workflow_source(args)
            except BaseException as setup_error:  # noqa: BLE001 - record supplier setup refusal separately
                value = {
                    "status": "source_setup_refused",
                    "count": count,
                    "combined_body_bytes": total,
                    "error_type": type(setup_error).__name__,
                    "error": str(setup_error),
                    "gate_pass": False,
                    "target_file_count": 0,
                    "peak_rss_mib": peak_rss_mib(),
                }
                Path(outfile).write_text(json.dumps(value, indent=2) + "\n")
                emit("setup_refusal", **value)
                monkey.undo()
                return
            selected = tuple(
                row
                for row in observed.files
                if Path(row.source_path).name.startswith("file_")
            )
            assert (
                len(selected) == count
                and sum(row.size_bytes for row in selected) == total
            )
            workspace = WorkspaceRepositoryTreeProjectionClient.filesystem(
                repository_root=target,
                state_root=state / "tree",
                execution_id=observed.binding.execution_id,
            )
            tree_request = WorkspaceTreeProjectionRequest(
                observed.binding.workflow_ref,
                "layout:explicit",
                "invocation:resource",
                observed.binding,
                tuple(
                    WorkspaceTreeFileIntent(
                        Path(row.source_path).name, "CREATE", row.output_path, 0o644
                    )
                    for row in selected
                ),
                (),
                "descriptor_walk_v1",
                DEFAULT_TREE_LIMITS,
            )
            install_issue(target, scope=tuple(row.path for row in tree_request.files))
            timings = {}
            started = time.perf_counter()
            issuer = issue = None
            try:
                t = time.perf_counter()
                plan = await workspace.prepare_tree_projection(
                    tree_request, source_delivery=source
                )
                binding = workspace.observe_tree_projection_plan(plan).binding
                timings["prepare"] = time.perf_counter() - t
                emit("prepared", seconds=timings["prepare"], count=count, bytes=total)
                path = install_issue(target, scope=binding.effect_paths)
                issuer = IssueRepositoryTreeProjectionClient.filesystem(
                    repository_root=target, execution_id=EXECUTION
                )
                t = time.perf_counter()
                ip = await issuer.prepare_tree_projection_admission(
                    IssueTreeProjectionRequest(
                        REF,
                        digest(path.read_bytes()),
                        EXECUTION,
                        "harness:declared",
                        "intent:tree",
                    ),
                    workspace_client=workspace,
                    workspace_plan=plan,
                    expected_binding=binding,
                )
                issue = await issuer.admit_tree_projection(ip)
                admitted = await workspace.enroll_issue_tree_projection(
                    plan, issue_admission=issue
                )
                timings["issue_enrollment"] = time.perf_counter() - t
                emit("enrolled", seconds=timings["issue_enrollment"])
                t = time.perf_counter()
                result = await workspace.project_tree(plan, admission=admitted)
                timings["project"] = time.perf_counter() - t
                emit("projected", seconds=timings["project"])
                t = time.perf_counter()
                final = read_original_tree_projection_result(
                    result, expected_binding=binding
                )
                resolved = await workspace.resolve_tree_projection_receipts(admitted)
                assert (
                    final.completed_prefix == count
                    and final.phase == "complete"
                    and final.index_state == "persisted"
                )
                assert (
                    len(final.receipts) == count
                    and resolved.resolution_state == "known"
                )
                assert all(
                    row.mutation_receipt_ref and row.capture_ref and row.delta_ref
                    for row in final.receipts
                )
                for row in selected:
                    assert hashlib.sha256(
                        (target / Path(row.source_path).name).read_bytes()
                    ).hexdigest() == row.content_digest.removeprefix("sha256:")
                timings["readback_resolution"] = time.perf_counter() - t
                t = time.perf_counter()
                cleanup = await workspace.release_tree_projection()
                assert cleanup.cleanup_state == "completed"
                await issuer.release_tree_projection_admission(issue)
                issue = None
                release_original_repository_workflow_source(source)
                timings["cleanup"] = time.perf_counter() - t
                elapsed = time.perf_counter() - started
                value = {
                    "status": "complete",
                    "count": count,
                    "combined_body_bytes": total,
                    "seconds": elapsed,
                    "peak_rss_mib": peak_rss_mib(),
                    "raw_ru_maxrss_mib": resource.getrusage(
                        resource.RUSAGE_SELF
                    ).ru_maxrss
                    / 1024,
                    "rss_source": "/proc/self/status:VmHWM",
                    "phases": timings,
                    "time_gate_seconds": 5,
                    "rss_gate_mib": 256,
                    "required_sample": count == 1000 and total == 8 * 1024 * 1024,
                    "latency_memory_pass": elapsed <= 5 and peak_rss_mib() <= 256,
                    "gate_pass": count == 1000
                    and total == 8 * 1024 * 1024
                    and elapsed <= 5
                    and peak_rss_mib() <= 256,
                }
                Path(outfile).write_text(json.dumps(value, indent=2) + "\n")
                emit("result", **value)
            except BaseException as error:  # noqa: BLE001 - retain complete benchmark refusal
                value = {
                    "status": "refused",
                    "count": count,
                    "combined_body_bytes": total,
                    "seconds": time.perf_counter() - started,
                    "peak_rss_mib": peak_rss_mib(),
                    "raw_ru_maxrss_mib": resource.getrusage(
                        resource.RUSAGE_SELF
                    ).ru_maxrss
                    / 1024,
                    "rss_source": "/proc/self/status:VmHWM",
                    "phases": timings,
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "cause": repr(error.__cause__),
                    "completed_prefix": getattr(
                        getattr(error, "evidence", None), "observation", None
                    ).completed_prefix
                    if getattr(getattr(error, "evidence", None), "observation", None)
                    is not None
                    else None,
                    "target_file_count": sum(
                        (target / Path(row.source_path).name).exists()
                        for row in selected
                    ),
                }
                Path(outfile).write_text(json.dumps(value, indent=2) + "\n")
                emit("refusal", **value)
            finally:
                cleanup_errors = []
                for name, close in (("workspace", workspace.release_tree_projection),):
                    try:
                        await close()
                    except BaseException as cleanup_error:  # noqa: BLE001 - drain independent original resources
                        cleanup_errors.append(
                            {
                                "owner": name,
                                "type": type(cleanup_error).__name__,
                                "message": str(cleanup_error),
                            }
                        )
                if issuer is not None and issue is not None:
                    try:
                        await issuer.release_tree_projection_admission(issue)
                    except BaseException as cleanup_error:  # noqa: BLE001 - drain independent original resources
                        cleanup_errors.append(
                            {
                                "owner": "issue",
                                "type": type(cleanup_error).__name__,
                                "message": str(cleanup_error),
                            }
                        )
                try:
                    release_original_repository_workflow_source(source)
                except BaseException as cleanup_error:  # noqa: BLE001 - drain independent original resources
                    cleanup_errors.append(
                        {
                            "owner": "source",
                            "type": type(cleanup_error).__name__,
                            "message": str(cleanup_error),
                        }
                    )
                try:
                    workflow.release_repository_workflow(parent)
                except BaseException as cleanup_error:  # noqa: BLE001 - drain independent original resources
                    cleanup_errors.append(
                        {
                            "owner": "workflow",
                            "type": type(cleanup_error).__name__,
                            "message": str(cleanup_error),
                        }
                    )
                value["cleanup_errors"] = cleanup_errors
                value["seconds_through_owner_cleanup"] = time.perf_counter() - started
                value["peak_rss_mib"] = peak_rss_mib()
                value["required_sample"] = count == 1000 and total == 8 * 1024 * 1024
                value["gate_pass"] = (
                    value["status"] == "complete"
                    and value["required_sample"]
                    and not cleanup_errors
                    and value["seconds_through_owner_cleanup"] <= 5
                    and value["peak_rss_mib"] <= 256
                )
                Path(outfile).write_text(json.dumps(value, indent=2) + "\n")
                monkey.undo()
            assert parent is not None

    return await _run(count, total, outfile)


@pytest.mark.asyncio
async def test_original_ordinal_validator_substitution_is_terminal_without_dispatch(
    inputs, monkeypatch
):
    from aware_file_system.retained_tree_projection import (
        RetainedPhysicalTreeProjection,
    )
    from aware_workspace_sdk.repository_workflow import (
        observe_original_repository_workflow_source,
    )

    (
        parent,
        source,
        workspace,
        tree,
        binding,
        issuer,
        issue,
        enrollment,
        _path,
    ) = await genuine_issue_enrollment(inputs)
    original = RetainedPhysicalTreeProjection.validate_next_current
    calls = []

    def foreign(_receiver):
        calls.append(True)
        raise AssertionError("foreign ordinal validator")

    monkeypatch.setattr(
        RetainedPhysicalTreeProjection, "validate_next_current", foreign
    )
    with pytest.raises(WorkspaceTreeProjectionRefusal):
        await workspace.project_tree(tree, admission=enrollment)
    monkeypatch.setattr(
        RetainedPhysicalTreeProjection, "validate_next_current", original
    )
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(tree, admission=enrollment)
    assert not calls and not (inputs[1] / "out.py").exists()
    assert parent is not None and binding is not None
    verify_original_repository_workflow_source(
        source,
        expected_binding=observe_original_repository_workflow_source(source).binding,
    )
    await workspace.release_tree_projection()
    await issuer.release_tree_projection_admission(issue)


async def _binding_join(inputs):
    parent, source, observed, workspace, request = setup(inputs)
    request = replace(
        request,
        files=tuple(
            replace(request.files[0], path=name) for name in ("a.py", "b.py", "c.py")
        ),
    )
    tree, binding, issuer, issue, enrollment, path = await enroll_original_request(
        inputs, request, source, workspace
    )
    return (
        parent,
        source,
        observed,
        workspace,
        tree,
        binding,
        issuer,
        issue,
        enrollment,
        path,
    )


@pytest.mark.asyncio
async def test_binding_join_preserves_original_execution_checkpoints(inputs):
    from aware_issue_sdk import source_projection as issue_ports
    from aware_workspace_runtime import repository_tree_projection as runtime
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    (
        parent,
        source,
        source_observation,
        workspace,
        tree,
        binding,
        issuer,
        issue,
        enrollment,
        _path,
    ) = await _binding_join(inputs)
    helper = codec.repository_tree_projection_value_validate_equal
    codes = {
        issue_ports.consume_tree_projection_admission.__code__: "spend",
        runtime._verify_issue_boundary.__code__: "issue",
        runtime._verify_source_and_bodies.__code__: "source_body",
        runtime._verify_ordinal_source_and_bodies.__code__: "source_paths",
        runtime._verify_preparation.__code__: "physical",
        helper.__code__: "helper",
    }
    events, ordinals, original_operands = [], [], []
    previous = sys.getprofile()

    def profile(frame, event, _arg):
        if event != "call" or frame.f_code not in codes:
            return
        name = codes[frame.f_code]
        if name == "physical":
            if frame.f_locals["next_ordinal"]:
                # Observe original settled history, never manufacture its ordinal.
                ordinals.append(len(frame.f_locals["runtime"].transitions))
                assert events[-3:] == ["issue", "helper", "source_paths"]
                name = "physical_next"
            else:
                name = "physical_full"
        if name == "helper":
            original_operands.append(
                frame.f_locals["value"].binding_ref == binding.binding_ref
                and frame.f_locals["expected_value"].binding_ref == binding.binding_ref
            )
        events.append(name)

    try:
        sys.setprofile(profile)
        result = await workspace.project_tree(tree, admission=enrollment)
        returned = read_original_tree_projection_result(
            result, expected_binding=binding
        )
    finally:
        sys.setprofile(previous)
    assert events.count("spend") == 1
    assert events.count("issue") == binding.transition_count + 4
    assert events.count("helper") == binding.transition_count + 5
    assert events.count("source_body") >= 5
    assert events.count("source_paths") == binding.transition_count
    assert events.count("physical_full") >= 2
    assert ordinals == list(range(binding.transition_count))
    assert all(original_operands)
    assert returned.phase == "complete" and returned.ledger_complete
    assert returned.completed_prefix == 3 and returned.index_state == "persisted"
    assert len(returned.receipts) == 3
    body = (inputs[0] / binding.files[0].source_path).read_bytes()
    assert all((inputs[1] / row.path).read_bytes() == body for row in binding.files)
    object.__setattr__(returned, "phase", "held")
    assert (
        read_original_tree_projection_result(result, expected_binding=binding).phase
        == "complete"
    )
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(tree, admission=enrollment)
    assert parent is not None
    verify_original_repository_workflow_source(
        source, expected_binding=source_observation.binding
    )
    await workspace.release_tree_projection()
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
@pytest.mark.parametrize("changed_owner", ["source", "issue"])
@pytest.mark.parametrize("prefix", [0, 1])
async def test_binding_join_detects_real_drift_after_validated_helper_return(
    inputs, changed_owner, prefix
):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    (
        parent,
        source,
        observed,
        workspace,
        tree,
        binding,
        issuer,
        issue,
        enrollment,
        issue_path,
    ) = await _binding_join(inputs)
    path = (
        inputs[0] / binding.files[0].source_path
        if changed_owner == "source"
        else issue_path
    )
    original_body = path.read_bytes()
    expected_successor = (inputs[0] / binding.files[0].source_path).read_bytes()
    helper_code = codec.repository_tree_projection_value_validate_equal.__code__
    changed = []
    previous = sys.getprofile()

    def profile(frame, event, _arg):
        if (
            event == "return"
            and frame.f_code is helper_code
            and not changed
            and sum((inputs[1] / row.path).exists() for row in binding.files) == prefix
        ):
            path.write_bytes(original_body + b"\n# drift after binding validation\n")
            changed.append(True)

    try:
        sys.setprofile(profile)
        with pytest.raises(WorkspaceTreeProjectionRefusal) as caught:
            await workspace.project_tree(tree, admission=enrollment)
    finally:
        sys.setprofile(previous)
        path.write_bytes(original_body)
    assert changed == [True]
    assert [row.path for row in caught.value.evidence.observation.receipts] == [
        row.path for row in binding.files[:prefix]
    ]
    assert caught.value.evidence.observation.completed_prefix == prefix
    assert all(not (inputs[1] / row.path).exists() for row in binding.files[prefix:])
    if prefix:
        assert (inputs[1] / binding.files[0].path).read_bytes() == expected_successor
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(tree, admission=enrollment)
    assert parent is not None
    if changed_owner == "issue":
        verify_original_repository_workflow_source(
            source, expected_binding=observed.binding
        )
    await workspace.release_tree_projection()
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
@pytest.mark.parametrize("replacement", ["foreign", "self_restoring", "code"])
@pytest.mark.parametrize("prefix", [0, 1])
async def test_binding_join_rejects_helper_substitution_without_foreign_execution(
    inputs, replacement, prefix
):
    from aware_issue_sdk import source_projection as issue_ports
    from aware_workspace_runtime import repository_tree_projection as runtime
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    (
        parent,
        source,
        observed,
        workspace,
        tree,
        binding,
        issuer,
        issue,
        enrollment,
        _path,
    ) = await _binding_join(inputs)
    original = codec.repository_tree_projection_value_validate_equal
    boundary_codes = {
        issue_ports.consume_tree_projection_admission.__code__,
        runtime._verify_issue_boundary.__code__,
    }
    calls, changed = [], []
    previous = sys.getprofile()
    patch = pytest.MonkeyPatch()

    def foreign(_value, *, expected_value):
        calls.append(expected_value)
        if replacement == "self_restoring":
            codec.repository_tree_projection_value_validate_equal = original

    def foreign_code(_value, *, expected_value):
        raise AssertionError("foreign helper code executed")

    def profile(frame, event, _arg):
        if (
            event == "call"
            and frame.f_code in boundary_codes
            and not changed
            and sum((inputs[1] / row.path).exists() for row in binding.files) == prefix
        ):
            changed.append(True)
            if replacement == "code":
                patch.setattr(original, "__code__", foreign_code.__code__)
            else:
                patch.setattr(
                    codec,
                    "repository_tree_projection_value_validate_equal",
                    foreign,
                )

    try:
        sys.setprofile(profile)
        with pytest.raises(WorkspaceTreeProjectionRefusal) as caught:
            await workspace.project_tree(tree, admission=enrollment)
    finally:
        sys.setprofile(previous)
        patch.undo()
    assert changed == [True] and calls == []
    assert caught.value.evidence.observation.completed_prefix == prefix
    assert all(not (inputs[1] / row.path).exists() for row in binding.files[prefix:])
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(tree, admission=enrollment)
    verify_original_repository_workflow_source(
        source, expected_binding=observed.binding
    )
    assert parent is not None
    await workspace.release_tree_projection()
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change,prefix",
    [
        ("future_source", 1),
        ("visited_source", 2),
        ("manifest", 2),
        ("retained_future", 1),
        ("retained_visited", 2),
    ],
)
async def test_ordinal_source_law_preserves_known_prefix_but_never_final_success(
    inputs, change, prefix
):
    from aware_workspace_runtime import repository_tree_projection as runtime

    from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_workflow import (
        commit,
    )

    package = inputs[3]
    (package / "a.py").write_bytes(b"FIRST = 1\n")
    (package / "b.py").write_bytes(b"SECOND = 2\n")
    inputs = (*inputs[:-1], replace(inputs[-1], source_commit=commit(inputs[0])))
    parent, source, observed, workspace, request = setup(inputs)
    originals = {
        row.source_path.rsplit("/", 1)[-1]: row
        for row in observed.files
        if row.source_path.endswith(("/a.py", "/b.py"))
    }
    request = replace(
        request,
        files=tuple(
            replace(
                request.files[0],
                path=name,
                source_output_path=originals[name].output_path,
            )
            for name in ("a.py", "b.py")
        ),
    )
    tree, binding, issuer, issue, enrollment, _path = await enroll_original_request(
        inputs, request, source, workspace
    )
    selected = "a.py" if change in ("visited_source", "retained_visited") else "b.py"
    expected = {name: (package / name).read_bytes() for name in ("a.py", "b.py")}
    paths = (
        (package / "pyproject.toml",) if change == "manifest" else (package / selected,)
    )
    if change.startswith("retained_"):
        paths = tuple(
            path
            for path in (inputs[2] / "tree").rglob("*")
            if path.is_file() and path.read_bytes() == expected[selected]
        )
        assert paths
    bodies = tuple(path.read_bytes() for path in paths)
    ordinal = 1 if change in ("visited_source", "retained_visited") else 0
    changed = []
    previous = sys.getprofile()

    def profile(frame, event, _arg):
        if (
            event == "call"
            and frame.f_code is runtime._verify_ordinal_source_and_bodies.__code__
            and frame.f_locals["ordinal"] == ordinal
            and not changed
        ):
            for path in paths:
                path.write_bytes(b"changed after complete pre-effect validation")
            changed.append(True)

    try:
        sys.setprofile(profile)
        with pytest.raises(WorkspaceTreeProjectionRefusal) as caught:
            await workspace.project_tree(tree, admission=enrollment)
    finally:
        sys.setprofile(previous)
        for path, body in zip(paths, bodies, strict=True):
            path.write_bytes(body)
    assert changed == [True]
    evidence = caught.value.evidence.observation
    assert evidence.phase == "held" and evidence.completed_prefix == prefix
    assert [row.path for row in evidence.receipts] == [
        row.path for row in binding.files[:prefix]
    ]
    assert all(
        (inputs[1] / row.path).read_bytes() == expected[row.path]
        for row in binding.files[:prefix]
    )
    assert all(not (inputs[1] / row.path).exists() for row in binding.files[prefix:])
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(tree, admission=enrollment)
    assert parent is not None
    await workspace.release_tree_projection()
    await issuer.release_tree_projection_admission(issue)


# Capacity successors use the same source, Issue and physical owners as C.
@pytest.mark.asyncio
async def test_capacity_refusal_precedes_issue_spend_and_all_physical_effects(inputs):
    from aware_workspace_sdk import repository_tree_projection as sdk

    attempt, source, observed, workspace, request = setup(inputs)
    request = replace(
        request, limits=replace(request.limits, maximum_metadata_bytes=50000)
    )
    plan, _binding, issuer, issue, enrollment, _ = await enroll_original_request(
        inputs, request, source, workspace
    )
    runtime = sdk._CLIENTS[workspace][0]
    original_physical = runtime.preparation
    target = inputs[1]
    before = {
        str(p.relative_to(target)): p.read_bytes()
        for p in target.rglob("*")
        if p.is_file()
    }
    with pytest.raises(
        WorkspaceTreeProjectionRefusal, match="quota_exceeded"
    ) as caught:
        await workspace.project_tree(plan, admission=enrollment)
    assert runtime.phase == "held" and runtime.issue_consumption_ref is None
    assert (
        issuer.observe_tree_projection_admission(issue).consumption_state == "not_spent"
    )
    assert original_physical.observe_effects().effects == ()
    assert {
        str(p.relative_to(target)): p.read_bytes()
        for p in target.rglob("*")
        if p.is_file()
    } == before
    assert runtime.receipt_store.retained_count == 0
    assert caught.value.evidence.observation.completed_prefix == 0
    assert caught.value.evidence.observation.receipts == ()
    assert caught.value.evidence.cleanup.cleanup_state == "completed"
    assert attempt is not None
    verify_original_repository_workflow_source(
        source, expected_binding=observed.binding
    )
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(plan, admission=enrollment)
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
async def test_forecast_substitution_executes_zero_foreign_calls(
    inputs, monkeypatch, behavior
):
    from aware_file_system.retained_tree_projection import (
        RetainedPhysicalTreeProjection,
    )

    (
        attempt,
        source,
        workspace,
        plan,
        binding,
        issuer,
        issue,
        enrollment,
        _,
    ) = await genuine_issue_enrollment(inputs)
    original = RetainedPhysicalTreeProjection.observe_capacity_forecast
    calls = []

    def foreign(self):
        calls.append(self)
        if behavior == "restore":
            RetainedPhysicalTreeProjection.observe_capacity_forecast = original
        if behavior == "raise":
            raise RuntimeError("foreign")

    monkeypatch.setattr(
        RetainedPhysicalTreeProjection, "observe_capacity_forecast", foreign
    )
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="physical_refused"):
        await workspace.project_tree(plan, admission=enrollment)
    assert not calls
    assert (
        issuer.observe_tree_projection_admission(issue).consumption_state == "not_spent"
    )
    monkeypatch.setattr(
        RetainedPhysicalTreeProjection, "observe_capacity_forecast", original
    )
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(plan, admission=enrollment)
    assert attempt is not None and source is not None
    verify_original_repository_workflow_source(
        source, expected_binding=binding.source_binding
    )
    await issuer.release_tree_projection_admission(issue)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name", ["require_forecast_origin", "capacity_bound", "enforce_capacity"]
)
@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
async def test_capacity_entry_substitution_executes_no_foreign_behavior(
    inputs, monkeypatch, name, behavior
):
    from aware_workspace_runtime import repository_tree_projection as receiver

    (
        parent,
        source,
        workspace,
        plan,
        binding,
        issuer,
        issue,
        enrollment,
        _,
    ) = await genuine_issue_enrollment(inputs)
    original = getattr(receiver, name)
    calls = []

    def foreign(*args):
        calls.append(args)
        if behavior == "restore":
            setattr(receiver, name, original)
        if behavior == "raise":
            raise OSError("foreign")

    monkeypatch.setattr(receiver, name, foreign)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="physical_refused"):
        await workspace.project_tree(plan, admission=enrollment)
    assert not calls and not (inputs[1] / "out.py").exists()
    assert (
        issuer.observe_tree_projection_admission(issue).consumption_state == "not_spent"
    )
    monkeypatch.setattr(receiver, name, original)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(plan, admission=enrollment)
    assert parent is not None
    verify_original_repository_workflow_source(
        source, expected_binding=binding.source_binding
    )
    await issuer.release_tree_projection_admission(issue)
