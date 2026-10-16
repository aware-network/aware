"""Genuine C supplier admission; Workspace enrollment/execution remains separate."""

from __future__ import annotations

import ast
import copy
import gc
import hashlib
import os
import pickle
import weakref
from dataclasses import replace
from pathlib import Path

import pytest
from aware_issue_sdk.repository_tree_projection_values import IssueTreeProjectionRequest
from aware_issue_sdk.source_projection import (
    IssueRepositoryTreeProjectionClient,
    IssueTreeProjectionAdmission,
    IssueTreeProjectionAdmissionPlan,
    IssueTreeProjectionConsumption,
    IssueTreeProjectionRefusal,
    consume_tree_projection_admission,
    verify_tree_projection_admission,
    verify_tree_projection_consumption,
)
from aware_workspace_sdk.repository_tree_projection import (
    WorkspaceRepositoryTreeProjectionClient,
)
from aware_workspace_sdk.repository_tree_projection_values import (
    WorkspaceTreeAncestorIntent,
    WorkspaceTreeFileIntent,
)

from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_tree_projection import (
    setup,
)
from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_workflow import (
    inputs as inputs,  # noqa: PLC0414
)

REF = "fb/2026-10-12/tree"
ISSUE_PATH = "docs/issues/2026/10/12/fb-2026-10-12-tree.md"
EXECUTION = "codex-workflow-planning-test"
MANIFEST = """aware = 1
[protocol]
name = "aware.collaboration"
profile = "aware.collaboration.fs_v1"
semantic_version = 1
[target]
kind = "repository"
authority_mode = "filesystem"
[bootstrap]
agent_contract = "AGENTS.md"
[records.issue]
profile = "aware.issue.markdown.v1"
root = "docs/issues"
role = "authority"
path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"
[records.goal]
profile = "aware.goal.markdown.v1"
role = "unavailable"
[records.feed]
profile = "aware.feed.projection.v1"
role = "unavailable"
[records.specification]
profile = "specification_fs_v1"
role = "unavailable"
[records.evidence]
profile = "aware.protocol.evidence.v1"
role = "unavailable"
"""


def digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def install_issue(root, *, scope=("out.py",), owner=EXECUTION, status="In Progress"):
    (root / "aware.protocol.toml").write_text(MANIFEST)
    (root / "AGENTS.md").write_text("# Disposable consumer\n")
    path = root / ISSUE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# Issue: Tree
- Slug: tree
- Tag: {REF}
- Status: {status}
- Owner: {owner}
- Priority: P1
- Captured: 2026-10-12
- Recorder: {owner}
- Source: Genuine supplier qualification

## Ownership Scope
"""
        + "".join(f"- `{p}`\n" for p in scope)
        + "\n## Updates (append-only)\n"
    )
    return path


async def prepared(inputs, *, kind="create", scope=None, defer=False):
    attempt, source, _observed, workspace, request = setup(inputs)
    target = inputs[1]
    if kind == "delete":
        (target / "out.py").write_bytes(b"old")
        request = replace(
            request, files=(WorkspaceTreeFileIntent("out.py", "DELETE", None, None),)
        )
    elif kind == "directory":
        request = replace(
            request,
            files=(),
            ancestors=(WorkspaceTreeAncestorIntent("public", "create", 0o755),),
        )
    elif kind == "nested":
        (target / "public").mkdir(mode=0o750)
        request = replace(
            request,
            files=(replace(request.files[0], path="public/out.py"),),
            ancestors=(WorkspaceTreeAncestorIntent("public", "preserve", None),),
        )
    path = install_issue(
        target,
        scope=scope
        or (
            (ISSUE_PATH,)
            if kind == "authority_issue"
            else ("aware.protocol.toml",)
            if kind == "authority_manifest"
            else ("public",)
            if kind in ("nested", "directory")
            else ("out.py",)
        ),
    )
    if kind in ("authority_issue", "authority_manifest"):
        protected = ISSUE_PATH if kind == "authority_issue" else "aware.protocol.toml"
        request = replace(
            request,
            files=(WorkspaceTreeFileIntent(protected, "DELETE", None, None),),
            ancestors=tuple(
                WorkspaceTreeAncestorIntent(str(parent), "preserve", None)
                for parent in sorted(
                    path.relative_to(target).parents,
                    key=lambda p: (len(p.parts), str(p)),
                )
                if str(parent) != "."
            )
            if kind == "authority_issue"
            else (),
        )
    tree = await workspace.prepare_tree_projection(request, source_delivery=source)
    binding = workspace.observe_tree_projection_plan(tree).binding
    # CREATE needs the explicitly reserved scratch paths, not just the target.
    if scope is None and kind == "create":
        path = install_issue(target, scope=binding.effect_paths)
    client = IssueRepositoryTreeProjectionClient.filesystem(
        repository_root=target, execution_id=EXECUTION
    )
    admission_request = IssueTreeProjectionRequest(
        REF, digest(path.read_bytes()), EXECUTION, "harness:declared", "intent:tree"
    )
    if defer:
        return (
            attempt,
            source,
            workspace,
            tree,
            binding,
            client,
            admission_request,
            path,
        )
    plan = await client.prepare_tree_projection_admission(
        admission_request,
        workspace_client=workspace,
        workspace_plan=tree,
        expected_binding=binding,
    )
    return attempt, source, workspace, tree, binding, client, plan, path


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ("create", "delete", "directory", "nested"))
async def test_original_plan_admission_single_spend_and_cleanup_without_tree_writes(
    inputs, kind
):
    attempt, source, workspace, tree, binding, client, plan, path = await prepared(
        inputs, kind=kind
    )
    before = path.read_bytes()
    assert type(plan) is IssueTreeProjectionAdmissionPlan
    observed = client.observe_tree_projection_admission(plan)
    assert observed.phase == "prepared" and not observed.authorizes_retry
    assert observed.binding.workspace_binding_ref == binding.binding_ref
    admission = await client.admit_tree_projection(plan)
    assert type(admission) is IssueTreeProjectionAdmission
    assert (
        verify_tree_projection_admission(admission, expected_binding=binding).phase
        == "admitted"
    )
    consumption = consume_tree_projection_admission(admission, binding=binding)
    assert type(consumption) is IssueTreeProjectionConsumption
    for _ in range(3):
        assert (
            verify_tree_projection_consumption(
                consumption, expected_binding=binding
            ).consumption_state
            == "spent"
        )
    with pytest.raises(IssueTreeProjectionRefusal, match="spent"):
        consume_tree_projection_admission(admission, binding=binding)
    cleanup = await client.release_tree_projection_admission(consumption)
    assert cleanup.cleanup_state == "completed"
    assert all(
        row.ownership == "borrowed" and not row.cleanup_attempted
        for row in cleanup.resources
    )
    assert await client.release_tree_projection_admission(consumption) == cleanup
    # Issue never disposes the borrowed Workspace plan/body/preparation or parent.
    assert (
        workspace.verify_tree_projection_plan(tree, expected_binding=binding).phase
        == "prepared"
    )
    assert attempt is not None and source is not None and path.read_bytes() == before
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_consumption_and_ordinal_verification_make_no_workspace_callbacks(
    inputs, monkeypatch
):
    _attempt, _source, workspace, _tree, binding, client, plan, _path = await prepared(
        inputs
    )
    admission = await client.admit_tree_projection(plan)

    def forbidden(*args, **kwargs):
        pytest.fail("reciprocal Workspace call under transaction")

    for name in ("observe_tree_projection_plan", "verify_tree_projection_plan"):
        monkeypatch.setattr(WorkspaceRepositoryTreeProjectionClient, name, forbidden)
    consumption = consume_tree_projection_admission(admission, binding=binding)
    verify_tree_projection_consumption(consumption, expected_binding=binding)
    await client.release_tree_projection_admission(consumption)
    await workspace.release_tree_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ("admit", "verify", "consume", "ordinal"))
@pytest.mark.parametrize("drift", ("source", "manifest"))
async def test_drift_refuses_terminally_and_restoration_cannot_revive(
    inputs, boundary, drift
):
    _attempt, _source, workspace, _tree, binding, client, plan, path = await prepared(
        inputs
    )
    admission = (
        None if boundary == "admit" else await client.admit_tree_projection(plan)
    )
    consumption = (
        consume_tree_projection_admission(admission, binding=binding)
        if boundary == "ordinal"
        else None
    )
    changed = path if drift == "source" else inputs[1] / "aware.protocol.toml"
    original = changed.read_bytes()
    changed.write_bytes(original + b"\n")
    with pytest.raises(IssueTreeProjectionRefusal) as failure:
        if boundary == "admit":
            await client.admit_tree_projection(plan)
        elif boundary == "verify":
            verify_tree_projection_admission(admission, expected_binding=binding)
        elif boundary == "consume":
            consume_tree_projection_admission(admission, binding=binding)
        else:
            verify_tree_projection_consumption(consumption, expected_binding=binding)
    assert failure.value.observation.phase == "retired"
    if boundary in ("consume", "ordinal"):
        assert failure.value.observation.consumption_state == "spent"
    changed.write_bytes(original)
    with pytest.raises(IssueTreeProjectionRefusal):
        await client.admit_tree_projection(plan)
    assert not (inputs[1] / "out.py").exists()
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_foreign_client_and_forged_handles_do_not_retire_original(inputs):
    _attempt, _source, workspace, _tree, binding, client, plan, _path = await prepared(
        inputs
    )
    other = IssueRepositoryTreeProjectionClient.filesystem(
        repository_root=inputs[1], execution_id=EXECUTION
    )
    with pytest.raises(IssueTreeProjectionRefusal):
        await other.admit_tree_projection(plan)
    admission = await client.admit_tree_projection(plan)
    forged = object.__new__(IssueTreeProjectionAdmission)
    with pytest.raises(IssueTreeProjectionRefusal):
        consume_tree_projection_admission(forged, binding=binding)
    assert (
        verify_tree_projection_admission(admission, expected_binding=binding).phase
        == "admitted"
    )
    await client.release_tree_projection_admission(admission)
    await workspace.release_tree_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", (copy.copy, copy.deepcopy, pickle.dumps))
async def test_original_handles_never_serialize_or_copy(inputs, operation):
    _attempt, _source, workspace, _tree, _binding, client, plan, _path = await prepared(
        inputs
    )
    admission = await client.admit_tree_projection(plan)
    for handle in (client, plan, admission):
        with pytest.raises(TypeError):
            operation(handle)
    await client.release_tree_projection_admission(admission)
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_detached_binding_mutation_cannot_change_original_authority(inputs):
    _attempt, _source, workspace, _tree, binding, client, plan, _path = await prepared(
        inputs
    )
    observed = client.observe_tree_projection_admission(plan)
    object.__setattr__(observed.binding, "effect_paths", ("foreign",))
    assert (
        client.observe_tree_projection_admission(plan).binding.effect_paths
        == binding.effect_paths
    )
    admission = await client.admit_tree_projection(plan)
    with pytest.raises(IssueTreeProjectionRefusal):
        consume_tree_projection_admission(
            admission, binding=replace(binding, effect_paths=("foreign",))
        )
    assert (
        client.observe_tree_projection_admission(admission).consumption_state == "spent"
    )
    await workspace.release_tree_projection()


def test_legacy_source_projection_bodies_remain_ast_identical():
    import subprocess

    import aware_issue_operational_runtime.source_projection as runtime

    root = next(p for p in Path(__file__).parents if (p / "aware.repo.toml").exists())
    path = Path(runtime.__file__).relative_to(root)
    old = ast.parse(
        subprocess.check_output(
            ["git", "show", "6b1e8d9598bef135a94335b661f13dba1cef0fd4:" + str(path)],
            text=True,
        )
    )
    new = ast.parse(Path(runtime.__file__).read_text())
    for name in ("_PlanRecord", "IssueSourceProjectionRuntime"):
        assert ast.dump(
            next(n for n in old.body if getattr(n, "name", None) == name)
        ) == ast.dump(next(n for n in new.body if getattr(n, "name", None) == name))


def _custody_descriptors():
    """Stable descriptor targets; never open or close an owner's descriptor."""
    snapshot = {}
    for leaf in Path("/proc/self/fd").iterdir():
        try:
            snapshot[int(leaf.name)] = os.readlink(leaf)
        except FileNotFoundError:
            pass  # The directory enumeration's own temporary descriptor.
    return snapshot


async def _unknown_tree_lookup(entrance, client, binding):
    if entrance == "verify":
        verify_tree_projection_admission(object(), expected_binding=binding)
    elif entrance == "consume":
        consume_tree_projection_admission(object(), binding=binding)
    elif entrance == "ordinal":
        verify_tree_projection_consumption(object(), expected_binding=binding)
    elif entrance == "admit":
        await client.admit_tree_projection(object())
    elif entrance == "observe":
        client.observe_tree_projection_admission(object())
    else:
        await client.release_tree_projection_admission(object())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "entrance", ("verify", "consume", "ordinal", "admit", "observe", "release")
)
@pytest.mark.parametrize("hold_refusal", (False, True))
async def test_unknown_rejection_traceback_never_holds_unrelated_custody(
    inputs, entrance, hold_refusal
):
    before = _custody_descriptors()
    attempt, source, workspace, tree, binding, client, plan, path = await prepared(
        inputs
    )
    admission = await client.admit_tree_projection(plan)
    source_ref, plan_ref = weakref.ref(source), weakref.ref(tree)
    acquired = {
        fd: target
        for fd, target in _custody_descriptors().items()
        if before.get(fd) != target
    }
    assert str(inputs[0]) in acquired.values()
    assert str(inputs[1]) in acquired.values()
    held = None
    try:
        await _unknown_tree_lookup(entrance, client, binding)
    except IssueTreeProjectionRefusal as error:
        if hold_refusal:
            held = error
    else:
        pytest.fail("unknown lookup must refuse")
    assert client.observe_tree_projection_admission(admission).phase == "admitted"
    assert (
        workspace.verify_tree_projection_plan(tree, expected_binding=binding).phase
        == "prepared"
    )
    del source, workspace, tree, client, plan, admission
    gc.collect()
    assert plan_ref() is None and source_ref() is None
    after = _custody_descriptors()
    assert not any(after.get(fd) == target for fd, target in acquired.items())
    assert (held is not None) == hold_refusal
    if held is not None:
        assert held.code == (
            "issue_tree_not_issued"
            if entrance in ("verify", "consume", "ordinal")
            else "issue_tree_foreign_handle"
        )
        assert held.__traceback__ is not None
    assert attempt is not None and path.exists()


@pytest.mark.asyncio
async def test_literal_binding_helper_runs_at_every_boundary_without_tree_clone(
    inputs, monkeypatch
):
    import sys

    from aware_workspace_sdk import repository_tree_projection_codec as codec

    _attempt, _source, workspace, _tree, binding, client, plan, _path = await prepared(
        inputs
    )
    admission = await client.admit_tree_projection(plan)
    original = codec.repository_tree_projection_value_validate_equal
    calls = []
    old_profile = sys.getprofile()

    def profile(frame, event, _arg):
        if event == "call" and frame.f_code is original.__code__:
            calls.append(frame.f_locals["value"] is binding)

    def forbidden(*_args, **_kwargs):
        pytest.fail("tree clone or reciprocal Workspace callback during consumption")

    try:
        with monkeypatch.context() as patch:
            patch.setattr(codec, "repository_tree_projection_value_clone", forbidden)
            for name in ("observe_tree_projection_plan", "verify_tree_projection_plan"):
                patch.setattr(WorkspaceRepositoryTreeProjectionClient, name, forbidden)
            sys.setprofile(profile)
            observed = verify_tree_projection_admission(
                admission, expected_binding=binding
            )
            consumption = consume_tree_projection_admission(admission, binding=binding)
            ordinal = verify_tree_projection_consumption(
                consumption, expected_binding=binding
            )
            object.__setattr__(ordinal, "phase", "retired")
            assert (
                verify_tree_projection_consumption(
                    consumption, expected_binding=binding
                ).phase
                == "spent"
            )
        assert calls == [True] * 4
        assert observed.phase == "admitted"
        assert client.observe_tree_projection_admission(consumption).phase == "spent"
    finally:
        sys.setprofile(old_profile)
        await workspace.release_tree_projection()


def _binding_boundary(boundary, admission, consumption, binding):
    if boundary == "verify":
        return verify_tree_projection_admission(admission, expected_binding=binding)
    if boundary == "consume":
        return consume_tree_projection_admission(admission, binding=binding)
    return verify_tree_projection_consumption(consumption, expected_binding=binding)


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ("verify", "consume", "ordinal"))
@pytest.mark.parametrize("replacement", ("foreign", "self_restoring", "code"))
async def test_binding_helper_substitution_refuses_before_foreign_behavior(
    inputs, monkeypatch, boundary, replacement
):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    _attempt, _source, workspace, tree, binding, client, plan, _path = await prepared(
        inputs
    )
    admission = await client.admit_tree_projection(plan)
    consumption = (
        consume_tree_projection_admission(admission, binding=binding)
        if boundary == "ordinal"
        else None
    )
    original = codec.repository_tree_projection_value_validate_equal
    calls = []

    def foreign(_value, *, expected_value):
        calls.append(expected_value)
        if replacement == "self_restoring":
            codec.repository_tree_projection_value_validate_equal = original

    def foreign_code(_value, *, expected_value):
        raise AssertionError("foreign helper code must not execute")

    try:
        with monkeypatch.context() as patch:
            if replacement == "code":
                patch.setattr(original, "__code__", foreign_code.__code__)
            else:
                patch.setattr(
                    codec, "repository_tree_projection_value_validate_equal", foreign
                )
            with pytest.raises(IssueTreeProjectionRefusal) as caught:
                _binding_boundary(boundary, admission, consumption, binding)
            assert caught.value.code == "issue_tree_workspace_binding_validator_changed"
            assert caught.value.observation.phase == "retired"
            assert caught.value.observation.consumption_state == (
                "not_spent" if boundary == "verify" else "spent"
            )
            assert calls == []
        with pytest.raises(IssueTreeProjectionRefusal):
            _binding_boundary(boundary, admission, consumption, binding)
        # Refusing Issue's attempt cannot dispose its borrowed Workspace original.
        assert (
            workspace.verify_tree_projection_plan(tree, expected_binding=binding).phase
            == "prepared"
        )
        assert not (inputs[1] / "out.py").exists()
    finally:
        await workspace.release_tree_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ("verify", "consume", "ordinal"))
async def test_binding_helper_is_reauthenticated_after_return(
    inputs, monkeypatch, boundary
):
    import sys

    from aware_workspace_sdk import repository_tree_projection_codec as codec

    _attempt, _source, workspace, _tree, binding, client, plan, _path = await prepared(
        inputs
    )
    admission = await client.admit_tree_projection(plan)
    consumption = (
        consume_tree_projection_admission(admission, binding=binding)
        if boundary == "ordinal"
        else None
    )
    original = codec.repository_tree_projection_value_validate_equal
    old_profile = sys.getprofile()
    returns = []

    def profile(frame, event, _arg):
        if event == "return" and frame.f_code is original.__code__:
            returns.append(True)
            monkeypatch.setattr(
                codec,
                "repository_tree_projection_value_validate_equal",
                lambda *_a, **_k: None,
            )

    try:
        sys.setprofile(profile)
        with pytest.raises(IssueTreeProjectionRefusal) as caught:
            _binding_boundary(boundary, admission, consumption, binding)
        assert returns == [True]
        assert caught.value.code == "issue_tree_workspace_binding_validator_changed"
        assert caught.value.observation.phase == "retired"
        assert not (inputs[1] / "out.py").exists()
    finally:
        sys.setprofile(old_profile)
        monkeypatch.setattr(
            codec, "repository_tree_projection_value_validate_equal", original
        )
        await workspace.release_tree_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ("verify", "consume", "ordinal"))
@pytest.mark.parametrize("malformed", (False, True))
async def test_binding_helper_refusal_preserves_original_supplier_cause_and_retirement(
    inputs, boundary, malformed
):
    from aware_workspace_sdk.repository_tree_projection_codec import (
        WorkspaceTreeProjectionValueError,
    )

    _attempt, _source, workspace, _tree, binding, client, plan, _path = await prepared(
        inputs
    )
    admission = await client.admit_tree_projection(plan)
    consumption = (
        consume_tree_projection_admission(admission, binding=binding)
        if boundary == "ordinal"
        else None
    )
    expected = replace(binding)
    object.__setattr__(
        expected, "invocation_ref", True if malformed else "invocation:foreign"
    )
    try:
        with pytest.raises(IssueTreeProjectionRefusal) as caught:
            _binding_boundary(boundary, admission, consumption, expected)
        assert caught.value.code == "issue_tree_binding_mismatch"
        assert (
            type(caught.value.__cause__.__cause__) is WorkspaceTreeProjectionValueError
        )
        assert caught.value.observation.phase == "retired"
        assert caught.value.observation.consumption_state == (
            "not_spent" if boundary == "verify" else "spent"
        )
        assert not (inputs[1] / "out.py").exists()
    finally:
        await workspace.release_tree_projection()


def test_adoption_preserves_every_other_original_runtime_and_prior_test_declaration():
    import subprocess

    import aware_issue_operational_runtime.source_projection as runtime

    root = next(p for p in Path(__file__).parents if (p / "aware.repo.toml").exists())
    for path, excluded in (
        # The separately admitted I cut changes only descriptive cloning;
        # all original authority and ordinal methods remain conserved.
        (Path(runtime.__file__), {"_tree_expected", "_tree_clone"}),
        (Path(__file__), set()),
    ):
        old = ast.parse(
            subprocess.check_output(
                [
                    "git",
                    "show",
                    "17800617b725660d3e109cf60933b869d00d708c:"
                    + str(path.relative_to(root)),
                ],
                text=True,
            )
        )
        current = {
            node.name: ast.dump(node)
            for node in ast.parse(path.read_text()).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        for node in old.body:
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and node.name not in excluded
            ):
                assert current[node.name] == ast.dump(node)


@pytest.mark.asyncio
async def test_optimized_observations_preserve_fresh_source_and_binding_checkpoints(
    inputs,
):
    import sys

    import aware_issue_operational_runtime.source_projection as runtime

    _attempt, _source, workspace, _tree, binding, client, plan, path = await prepared(
        inputs
    )
    admission = await client.admit_tree_projection(plan)
    checkpoints = []
    original_profile = sys.getprofile()
    codes = {
        runtime.IssueTreeProjectionRuntime._fresh.__code__: "fresh",
        runtime._tree_expected.__code__: "binding",
    }

    def profile(frame, event, _arg):
        if event == "call" and frame.f_code in codes:
            checkpoints.append(codes[frame.f_code])

    try:
        sys.setprofile(profile)
        initial = verify_tree_projection_admission(admission, expected_binding=binding)
        consumption = consume_tree_projection_admission(admission, binding=binding)
        first = verify_tree_projection_consumption(
            consumption, expected_binding=binding
        )
        object.__setattr__(first.binding, "effect_paths", ("foreign",))
        second = verify_tree_projection_consumption(
            consumption, expected_binding=binding
        )
        assert (
            second.binding.effect_paths
            == initial.binding.effect_paths
            == binding.effect_paths
        )
        assert checkpoints == ["binding", "fresh"] * 4
        # Every subsequent call must reread the original source; no prior
        # successful observation can stand in for current admission.
        body = path.read_bytes()
        path.write_bytes(body + b"\n# changed after ordinal\n")
        with pytest.raises(IssueTreeProjectionRefusal) as caught:
            verify_tree_projection_consumption(consumption, expected_binding=binding)
        assert caught.value.observation.phase == "retired"
        assert checkpoints == ["binding", "fresh"] * 5
        path.write_bytes(body)
        with pytest.raises(IssueTreeProjectionRefusal):
            verify_tree_projection_consumption(consumption, expected_binding=binding)
    finally:
        sys.setprofile(original_profile)
        await workspace.release_tree_projection()


def test_i_performance_preserves_original_authority_and_predecessor_declarations():
    import json

    root = next(p for p in Path(__file__).parents if (p / "aware.repo.toml").exists())
    packet = json.loads(
        (
            root
            / "docs/reports/issue-tree-path-observation-performance-inputs-20261013.json"
        ).read_text()
    )
    for pin in packet["preimages"]:
        if not pin["path"].endswith(
            ("/source_projection.py", "/test_repository_tree_projection_admission.py")
        ):
            continue
        current = {
            node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse((root / pin["path"]).read_text()).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        excluded = (
            {"_tree_clone"}
            if pin["path"].endswith("/source_projection.py")
            else {
                "test_adoption_preserves_every_other_original_runtime_and_prior_test_declaration"
            }
        )
        for name, expected in pin["declarations"].items():
            if name not in excluded:
                assert hashlib.sha256(current[name].encode()).hexdigest() == expected, (
                    name
                )
