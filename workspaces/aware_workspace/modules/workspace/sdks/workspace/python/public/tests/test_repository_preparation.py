"""Real source preparation, original-owner failures and authored value parity.

Temporary Git repositories are customer fixtures, not governance bypasses.
Controlled identity changes are in-process tests, not agent identity admission.
"""

from __future__ import annotations

import ast
import copy
import os
import pickle
import subprocess
import sys
from dataclasses import fields, replace
from pathlib import Path

import pytest
from aware_workspace_sdk.repository_preparation import (
    RepositoryPreparationAdmission,
    RepositoryPreparationError,
    RepositoryPreparationPlan,
    RepositoryPreparationValueError,
    RepositoryPrepareRequest,
    WorkspaceRepositoryPreparationClient,
    authority,
    repository_preparation_value_from_json,
    repository_preparation_value_from_payload,
    repository_preparation_value_to_json,
    repository_preparation_value_to_payload,
    values,
)

ROOT = next(
    parent for parent in Path(__file__).parents if (parent / "AGENTS.md").is_file()
)
WORKSPACE = ROOT / "workspaces/aware_workspace/modules/workspace"


@pytest.fixture(autouse=True)
def execution(monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "preparation-controlled-test")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    return "codex-preparation-controlled-test"


@pytest.fixture
def selected(tmp_path, execution):
    target = tmp_path / "customer"
    client = WorkspaceRepositoryPreparationClient.filesystem(
        repository_root=str(target), execution_id=execution
    )
    return target, client


def _apply(client, request):
    with client.plan_repository_preparation(request) as plan:
        admission = client.admit_repository_preparation(plan)
        return client.prepare_repository(request, admission=admission)


def _git(root, *arguments):
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def _fds():
    return len(os.listdir("/proc/self/fd"))


@pytest.mark.parametrize("exists", [False, True])
def test_real_preview_apply_existing_no_publication(selected, exists):
    target, client = selected
    if exists:
        target.mkdir(mode=0o750)
    original_mode = target.stat().st_mode if exists else None
    parent_mode = target.parent.stat().st_mode
    baseline = _fds()
    preview = client.prepare_repository(
        RepositoryPrepareRequest(str(target), True, True)
    )
    assert preview.outcome == "planned" and not preview.effects
    assert not (target / ".git").exists()
    request = RepositoryPrepareRequest(str(target), True)
    result = _apply(client, request)
    assert result.outcome == "created" and result.head is None
    assert result.cleanup_state == "completed" and result.ledger_complete
    assert result.authorizes_retry is False
    assert all(
        item.state == "applied" and not item.durability_confirmed
        for item in result.effects
    )
    assert _git(target, "symbolic-ref", "HEAD").stdout.strip() == "refs/heads/main"
    assert _git(target, "rev-parse", "--verify", "HEAD").returncode != 0
    assert not _git(target, "ls-files").stdout
    assert not _git(target, "remote").stdout
    assert _git(target, "config", "--local", "user.name").returncode != 0
    assert not (target / "aware.protocol.toml").exists()
    assert target.parent.stat().st_mode == parent_mode
    if exists:
        assert target.stat().st_mode == original_mode
    else:
        assert target.stat().st_mode & 0o777 == 0o700
    again = _apply(client, RepositoryPrepareRequest(str(target)))
    assert again.outcome == "existing" and not again.effects
    assert _fds() == baseline


def test_existing_committed_repository_preserves_head_index_and_files(selected):
    target, client = selected
    _apply(client, RepositoryPrepareRequest(str(target), True))
    (target / "foreign.txt").write_text("preserve\n")
    assert _git(target, "add", "foreign.txt").returncode == 0  # Fixture only.
    assert (
        _git(
            target,
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-m",
            "fixture",
        ).returncode
        == 0
    )
    (target / "untracked.txt").write_text("unrelated\n")
    before = (target / ".git/index").read_bytes()
    head = _git(target, "rev-parse", "HEAD").stdout.strip()
    result = _apply(client, RepositoryPrepareRequest(str(target)))
    assert result.outcome == "existing" and result.head == head
    assert (target / ".git/index").read_bytes() == before
    assert (target / "untracked.txt").read_text() == "unrelated\n"


@pytest.mark.parametrize("creation", [False, True])
def test_apply_without_admission_has_no_effect(selected, creation):
    target, client = selected
    baseline = _fds()
    with pytest.raises(RepositoryPreparationError) as raised:
        client.prepare_repository(RepositoryPrepareRequest(str(target), creation))
    assert not raised.value.evidence.effects
    assert not raised.value.evidence.provider_invoked
    assert not target.exists() and _fds() == baseline


@pytest.mark.parametrize("kind", ["no_intent", "nonempty", "nested", "bare"])
def test_real_target_refusals_preserve_state(tmp_path, execution, kind):
    target = tmp_path / "customer"
    create = kind != "no_intent"
    if kind == "nonempty":
        target.mkdir()
        (target / "foreign").write_bytes(b"preserve")
    elif kind == "nested":
        target.mkdir()
        assert _git(target, "init", "--initial-branch=main").returncode == 0
        target /= "nested"
    elif kind == "bare":
        target.mkdir()
        assert _git(target, "init", "--bare").returncode == 0
    client = WorkspaceRepositoryPreparationClient.filesystem(
        repository_root=str(target), execution_id=execution
    )
    result = _apply(client, RepositoryPrepareRequest(str(target), create))
    assert result.outcome == "refused" and result.diagnostics and not result.effects
    if kind == "nonempty":
        assert (target / "foreign").read_bytes() == b"preserve"
    if kind == "nested":
        assert not target.exists()


@pytest.mark.parametrize("kind", ["symlink", "missing_parent", "file"])
def test_unreadable_topology_has_typed_error_and_restores_descriptors(
    tmp_path, execution, kind
):
    target = tmp_path / "customer"
    if kind == "symlink":
        outside = tmp_path / "outside"
        outside.mkdir()
        target.symlink_to(outside, target_is_directory=True)
    elif kind == "file":
        target.write_bytes(b"preserve")
    else:
        target = tmp_path / "missing" / "customer"
    client = WorkspaceRepositoryPreparationClient.filesystem(
        repository_root=str(target), execution_id=execution
    )
    baseline = _fds()
    with pytest.raises(RepositoryPreparationError):
        client.plan_repository_preparation(RepositoryPrepareRequest(str(target), True))
    assert _fds() == baseline and not (target / ".git").exists()


@pytest.mark.parametrize(
    "root", ["relative", "/", "/tmp/../customer", "/tmp/customer/"]
)
def test_noncanonical_selection_refuses(execution, root):
    with pytest.raises(ValueError):
        WorkspaceRepositoryPreparationClient.filesystem(
            repository_root=root, execution_id=execution
        )


@pytest.mark.parametrize("kind", ["plan", "admission"])
@pytest.mark.parametrize("action", ["construct", "copy", "deepcopy", "pickle"])
def test_handles_cannot_be_constructed_or_copied(selected, kind, action):
    target, client = selected
    with client.plan_repository_preparation(
        RepositoryPrepareRequest(str(target), True)
    ) as plan:
        handle = plan if kind == "plan" else client.admit_repository_preparation(plan)
        with pytest.raises(TypeError):
            if action == "construct":
                type(handle)()
            elif action == "copy":
                copy.copy(handle)
            elif action == "deepcopy":
                copy.deepcopy(handle)
            else:
                pickle.dumps(handle)
        handle.release()


@pytest.mark.parametrize(
    "kind", ["wrong_request", "changed_root", "execution", "interrupted_freshness"]
)
def test_invocation_failure_spends_admission_and_restores_descriptors(
    selected, monkeypatch, kind
):
    target, client = selected
    request = RepositoryPrepareRequest(str(target), True)
    baseline = _fds()
    plan = client.plan_repository_preparation(request)
    admission = client.admit_repository_preparation(plan)
    if kind == "wrong_request":
        request = replace(request, create_if_missing=False)
    elif kind == "changed_root":
        target.mkdir()
        (target / "foreign").write_bytes(b"preserve")
    elif kind == "execution":
        monkeypatch.setenv("CODEX_THREAD_ID", "other-controlled-execution")
    else:
        runtime = authority._CLIENTS[client]
        physical = runtime.plans[plan].physical

        def interrupted():
            raise KeyboardInterrupt("controlled freshness interruption")

        monkeypatch.setattr(physical, "validate_current", interrupted)
    with pytest.raises(RepositoryPreparationError):
        client.prepare_repository(request, admission=admission)
    with pytest.raises(RepositoryPreparationError):
        client.prepare_repository(request, admission=admission)
    assert not (target / ".git").exists() and _fds() == baseline
    assert plan.observe().phase == "retired"


def test_foreign_admission_does_not_disturb_its_original_owner(tmp_path, execution):
    first = tmp_path / "first"
    second = tmp_path / "second"
    one = WorkspaceRepositoryPreparationClient.filesystem(
        repository_root=str(first), execution_id=execution
    )
    two = WorkspaceRepositoryPreparationClient.filesystem(
        repository_root=str(second), execution_id=execution
    )
    request = RepositoryPrepareRequest(str(first), True)
    with one.plan_repository_preparation(request) as plan:
        admission = one.admit_repository_preparation(plan)
        with pytest.raises(RepositoryPreparationError):
            two.prepare_repository(
                RepositoryPrepareRequest(str(second), True), admission=admission
            )
        assert one.prepare_repository(request, admission=admission).outcome == "created"
    assert not second.exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("repository_root", "/foreign"),
        ("authority_mode", "service"),
        ("head", "not-a-head"),
        ("diagnostics", (17,)),
        ("execution_id", "foreign-execution"),
        ("request", RepositoryPrepareRequest("/foreign", True)),
        ("authorizes_retry", True),
        ("cleanup_state", "unknown"),
        ("attempt_ref", None),
        ("attempt_ref", "repository-attempt:" + "f" * 32),
        ("diagnostics", ("foreign but well-typed diagnostic",)),
    ],
)
def test_malformed_result_after_real_creation_preserves_original_ledger(
    selected, monkeypatch, field, value
):
    target, client = selected
    runtime = authority._CLIENTS[client]
    original = runtime.prepare_repository

    def corrupt(request, *, admission=None):
        return replace(original(request, admission=admission), **{field: value})

    monkeypatch.setattr(runtime, "prepare_repository", corrupt)
    request = RepositoryPrepareRequest(str(target), True)
    with client.plan_repository_preparation(request) as plan:
        admission = client.admit_repository_preparation(plan)
        with pytest.raises(RepositoryPreparationError) as raised:
            client.prepare_repository(request, admission=admission)
        evidence = raised.value.evidence
        assert evidence.request == request and evidence.provider_invoked
        assert evidence.effects and all(
            item.state == "applied" for item in evidence.effects
        )
        assert evidence.reported_result[field] == (
            list(value)
            if field == "diagnostics"
            else repository_preparation_value_to_payload(value)
            if field == "request"
            else value
        )
        assert evidence.evidence_grade == "unvalidated_provider_report"
        assert not evidence.ledger_complete and not evidence.authorizes_retry
        assert evidence.cleanup_state == "completed"
        assert (target / ".git/HEAD").read_text() == "ref: refs/heads/main\n"
        with pytest.raises(RepositoryPreparationError):
            client.prepare_repository(request, admission=admission)


@pytest.mark.parametrize("mutation", ["caller", "reported_request", "reported_effect"])
def test_dispatch_mutation_after_creation_preserves_detached_owner_ledger(
    selected, monkeypatch, mutation
):
    target, client = selected
    runtime = authority._CLIENTS[client]
    original = runtime.prepare_repository
    request = RepositoryPrepareRequest(str(target), True)
    original_payload = None
    isolated = None
    baseline = _fds()

    def corrupt(dispatched_request, *, admission=None):
        nonlocal original_payload, isolated
        result = original(dispatched_request, admission=admission)
        original_payload = repository_preparation_value_to_payload(result)
        assert len(result.effects) == 3 and (target / ".git/HEAD").is_file()
        isolated = (
            dispatched_request is not request
            and result.request is not runtime.last_evidence.request
            and result.request is not runtime.last_original_result.request
        )
        if mutation == "caller":
            object.__setattr__(request, "repository_root", "/foreign")
        elif mutation == "reported_request":
            object.__setattr__(result.request, "repository_root", "/foreign")
        else:
            object.__setattr__(result.effects[-1], "state", "none")
        return result

    monkeypatch.setattr(runtime, "prepare_repository", corrupt)
    with client.plan_repository_preparation(request) as plan:
        admission = client.admit_repository_preparation(plan)
        with pytest.raises(RepositoryPreparationError) as raised:
            client.prepare_repository(request, admission=admission)
        evidence = raised.value.evidence
        payload = repository_preparation_value_to_payload(evidence)
        assert evidence.code == "repository_result_invalid"
        assert evidence.request.repository_root == str(target)
        assert evidence.provider_invoked and evidence.attempt_ref is not None
        assert payload["request"] == original_payload["request"]
        assert payload["attempt_ref"] == original_payload["attempt_ref"]
        assert payload["effects"] == original_payload["effects"]
        assert isolated
        assert evidence.cleanup_state == "completed"
        assert evidence.evidence_grade == "unvalidated_provider_report"
        assert not evidence.ledger_complete and not evidence.authorizes_retry
        assert plan.observe().phase == "consumed"
        if mutation == "reported_request":
            assert (
                payload["reported_result"]["request"]["repository_root"] == "/foreign"
            )
            assert request.repository_root == str(target)
        elif mutation == "reported_effect":
            assert payload["reported_result"]["effects"][-1]["state"] == "none"
            assert payload["effects"][-1]["state"] == "applied"
        else:
            assert request.repository_root == "/foreign"
            assert payload["reported_result"]["request"]["repository_root"] == str(
                target
            )
        assert (target / ".git/HEAD").read_text() == "ref: refs/heads/main\n"
        assert _fds() == baseline
        with pytest.raises(RepositoryPreparationError):
            client.prepare_repository(
                RepositoryPrepareRequest(str(target), True), admission=admission
            )
        assert repository_preparation_value_to_payload(evidence) == payload
    assert _fds() == baseline


def test_result_failure_correlation_cannot_replace_original_dispatch_ledger(selected):
    target, client = selected
    result = _apply(client, RepositoryPrepareRequest(str(target), True))
    original = repository_preparation_value_to_payload(result)
    runtime = authority._CLIENTS[client]
    error = runtime.result_failure(
        RepositoryPrepareRequest("/foreign", True), {"request": "uncorrelated report"}
    )
    evidence = repository_preparation_value_to_payload(error.evidence)
    for field in ("request", "execution_id", "attempt_ref", "effects", "cleanup_state"):
        assert evidence[field] == original[field]
    assert evidence["provider_invoked"] and not evidence["ledger_complete"]
    assert not evidence["authorizes_retry"] and (target / ".git/HEAD").is_file()


@pytest.mark.parametrize(
    "field,value", [("repository_root", 17), ("create_if_missing", 1)]
)
def test_invalid_request_snapshot_still_retires_original_admission(
    selected, field, value
):
    target, client = selected
    request = RepositoryPrepareRequest(str(target), True)
    with client.plan_repository_preparation(request) as plan:
        admission = client.admit_repository_preparation(plan)
        object.__setattr__(request, field, value)
        with pytest.raises(RepositoryPreparationError) as raised:
            client.prepare_repository(request, admission=admission)
        assert plan.observe().phase == "retired"
        assert raised.value.evidence.request == RepositoryPrepareRequest(
            str(target), True
        )
        assert raised.value.evidence.attempt_ref is not None
        assert not raised.value.evidence.provider_invoked
        assert not raised.value.evidence.effects and not target.exists()
        with pytest.raises(RepositoryPreparationError):
            client.prepare_repository(
                RepositoryPrepareRequest(str(target), True), admission=admission
            )


@pytest.mark.parametrize("failure", ["readback", "git_interrupt", "git_failure"])
def test_late_actual_creation_failure_retains_known_or_unknown_effects(
    selected, monkeypatch, failure
):
    from aware_workspace_fs_adapter import repository_preparation as physical

    target, client = selected
    original = physical._git
    published = False

    def fail(root, *arguments):
        nonlocal published
        result = original(root, *arguments)
        if "init" in arguments:
            published = True
            if failure == "git_interrupt":
                raise KeyboardInterrupt("actual init followed by interruption")
            if failure == "git_failure":
                return replace_process(result, 1)
        elif published and failure == "readback":
            raise OSError("late readback failed")
        return result

    monkeypatch.setattr(physical, "_git", fail)
    baseline = _fds()
    with pytest.raises(RepositoryPreparationError) as raised:
        _apply(client, RepositoryPrepareRequest(str(target), True))
    evidence = raised.value.evidence
    git_effect = next(
        item
        for item in evidence.effects
        if item.kind == "git_repository_initialization"
    )
    assert git_effect.state == ("applied" if failure == "readback" else "unknown")
    assert (target / ".git/HEAD").is_file()
    assert not evidence.authorizes_retry and not evidence.ledger_complete
    assert _fds() == baseline


def replace_process(result, returncode):
    return subprocess.CompletedProcess(
        result.args, returncode, result.stdout, result.stderr
    )


def test_metadata_no_replace_race_preserves_foreign_directory(selected, monkeypatch):
    from aware_workspace_fs_adapter import repository_preparation as physical

    target, client = selected
    target.mkdir()
    original = physical.os.mkdir

    def race(path, *args, **kwargs):
        if path == ".git":
            original(path, *args, **kwargs)
            (target / ".git/foreign").write_bytes(b"preserve")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(physical.os, "mkdir", race)
    with pytest.raises(RepositoryPreparationError) as raised:
        _apply(client, RepositoryPrepareRequest(str(target), True))
    assert (target / ".git/foreign").read_bytes() == b"preserve"
    assert not (target / ".git/HEAD").exists()
    assert raised.value.evidence.effects[-1].state == "unknown"


def test_cleanup_failure_cannot_be_reclassified_by_later_release(selected, monkeypatch):
    from aware_workspace_fs_adapter import repository_preparation as physical

    target, client = selected
    request = RepositoryPrepareRequest(str(target), True)
    baseline = _fds()
    plan = client.plan_repository_preparation(request)
    admission = client.admit_repository_preparation(plan)
    owner_descriptors = set(authority._CLIENTS[client].plans[plan].physical.descriptors)
    original = physical.os.close
    once = False

    def fail(descriptor):
        nonlocal once
        original(descriptor)
        if descriptor in owner_descriptors and not once:
            once = True
            raise OSError("close observation unavailable")

    monkeypatch.setattr(physical.os, "close", fail)
    with pytest.raises(RepositoryPreparationError) as raised:
        client.prepare_repository(request, admission=admission)
    assert raised.value.evidence.cleanup_state == "unknown"
    assert raised.value.evidence.effects and (target / ".git/HEAD").exists()
    plan.release()
    assert raised.value.evidence.cleanup_state == "unknown" and _fds() == baseline


def test_detached_values_and_strict_codec(selected):
    target, client = selected
    result = client.prepare_repository(
        RepositoryPrepareRequest(str(target), True, True)
    )
    encoded = repository_preparation_value_to_json(result)
    decoded = repository_preparation_value_from_json(type(result), encoded)
    assert (
        decoded == result
        and decoded is not result
        and decoded.request is not result.request
    )
    payload = repository_preparation_value_to_payload(result)
    for bad in ({**payload, "extra": True}, {**payload, "provider_invoked": 0}):
        with pytest.raises(RepositoryPreparationValueError):
            repository_preparation_value_from_payload(type(result), bad)
    with pytest.raises(RepositoryPreparationValueError, match="duplicate"):
        repository_preparation_value_from_json(
            type(result), '{"contract":1,"contract":2}'
        )


def test_production_authored_contract_uses_genuine_lowering():
    from tree_sitter_aware.neutral_ir import parse_neutral_aware_source
    from tree_sitter_aware.ontology_meaning_resolver import (
        OntologyMeaningPackageInput,
        resolve_ontology_meaning,
    )

    home = WORKSPACE / "sdks/workspace/aware"
    paths = (
        home / "repository_preparation_values.aware",
        home / "repository_preparation_sdk.aware",
    )
    documents = tuple(
        parse_neutral_aware_source(path.read_text(), source_path=str(path))
        for path in paths
    )
    meaning = resolve_ontology_meaning(
        (
            OntologyMeaningPackageInput(
                package_name="workspace-preparation",
                fqn_prefix="aware_workspace_sdk",
                sources_root=str(home),
                dependencies=(),
                documents=documents,
                namespace_by_source_path=tuple((str(path), "") for path in paths),
            ),
        ),
        selected_package_names=frozenset({"workspace-preparation"}),
    )
    assert meaning
    fixture = ROOT / "tools/cli/tests/fixtures/portable_initializer_repository.aware"
    # Exact accepted declarations, not a renamed operation or new evaluator.
    assert (
        paths[0].read_text().split("enum ", 1)[1]
        == fixture.read_text()
        .split("enum ", 1)[1]
        .split("sdk repository_sdk", 1)[0]
        .rstrip()
        + "\n"
    )
    assert (
        paths[1].read_text().split("sdk repository_sdk", 1)[1]
        == fixture.read_text().split("sdk repository_sdk", 1)[1]
    )
    for name in (
        "RepositoryPrepareRequest",
        "RepositoryPreparationEffect",
        "RepositoryPreparationPlanObservation",
        "RepositoryPrepareResult",
        "RepositoryPreparationErrorEvidence",
    ):
        declaration = (
            paths[0]
            .read_text()
            .split("class " + name + " : inline_value {", 1)[1]
            .split("}", 1)[0]
        )
        expected = [
            line.strip().split()[0] for line in declaration.splitlines() if line.strip()
        ]
        assert [item.name for item in fields(getattr(values, name))] == expected


def test_production_sdk_manifest_parity_through_original_oracle(monkeypatch):
    supplier = (
        ROOT / "workspaces/aware_kernel/modules/sdk/libs/contract_runtime_source/python"
    )
    monkeypatch.syspath_prepend(str(supplier))
    from aware_sdk_contract_runtime_source import materialize_sdk_source_contract

    home = WORKSPACE / "sdks/workspace/aware"
    result = materialize_sdk_source_contract(
        sdk_toml_text=(home / "aware.sdk.toml").read_text(),
        source_text_by_path={
            name: (home / name).read_text()
            for name in (
                "repository_preparation_values.aware",
                "repository_preparation_sdk.aware",
            )
        },
        selected_operation_refs=("repository_sdk.prepare_repository",),
    )
    assert result.manifest.sdk_ref == "repository_sdk"
    assert len(result.manifest.operations) == 1
    operation = result.manifest.operations[0]
    assert operation.operation_ref == "repository_sdk.prepare_repository"
    assert operation.provider_operation_ref == "repository.prepare"
    assert {
        ref for part in result.manifest.schema_slices for ref in part.root_type_refs
    } == {
        "aware_workspace_sdk.RepositoryPrepareRequest",
        "aware_workspace_sdk.RepositoryPrepareResult",
        "aware_workspace_sdk.RepositoryPreparationErrorEvidence",
    }


def test_runtime_has_no_physical_io_or_process_writer():
    path = (
        WORKSPACE
        / "libs/workspace_runtime/aware_workspace_runtime/repository_preparation.py"
    )
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(
                item.name not in ("pathlib", "subprocess", "aware_workspace_fs_adapter")
                for item in node.names
            )
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in (
                "stat",
                "lstat",
                "open",
                "mkdir",
                "unlink",
                "read_bytes",
                "write_bytes",
            )


def test_source_selection_does_not_import_service_or_generated_owners(selected):
    target, _client = selected
    source_roots = [
        str(WORKSPACE / item)
        for item in (
            "sdks/workspace/python/public",
            "libs/workspace_runtime",
            "sdks/workspace/filesystem_adapter/python",
        )
    ]
    body = """
import importlib.abc, sys
class Deny(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(("aware_issue", "aware_local_service", "aware_workspace_service", "aware_ontology", "aware_orm")):
            raise AssertionError("forbidden integration: " + fullname)
sys.meta_path.insert(0, Deny())
from aware_workspace_sdk.repository_preparation import WorkspaceRepositoryPreparationClient, RepositoryPrepareRequest
client = WorkspaceRepositoryPreparationClient.filesystem(repository_root=sys.argv[1], execution_id="codex-preparation-controlled-test")
assert client.prepare_repository(RepositoryPrepareRequest(sys.argv[1], True, True)).outcome == "planned"
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", body, str(target)],
        env={**os.environ, "PYTHONPATH": os.pathsep.join(source_roots)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_concurrent_admission_is_single_use(selected):
    from concurrent.futures import ThreadPoolExecutor

    target, client = selected
    request = RepositoryPrepareRequest(str(target), True)
    with client.plan_repository_preparation(request) as plan:
        admission = client.admit_repository_preparation(plan)

        def invoke():
            try:
                return client.prepare_repository(request, admission=admission).outcome
            except RepositoryPreparationError:
                return "refused"

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _index: invoke(), range(2)))
        assert sorted(results) == ["created", "refused"]


@pytest.mark.parametrize(
    "kind", [RepositoryPreparationPlan, RepositoryPreparationAdmission]
)
def test_forged_unregistered_handle_has_no_authority(selected, kind):
    target, client = selected
    forged = object.__new__(kind)
    with pytest.raises((ValueError, RepositoryPreparationError)):
        if kind is RepositoryPreparationPlan:
            client.admit_repository_preparation(forged)
        else:
            client.prepare_repository(
                RepositoryPrepareRequest(str(target), True), admission=forged
            )
    assert not target.exists()


def test_physical_port_requires_original_spent_claim(selected):
    target, client = selected
    request = RepositoryPrepareRequest(str(target), True)
    with client.plan_repository_preparation(request) as plan:
        physical = authority._CLIENTS[client].plans[plan].physical
        with pytest.raises(
            ValueError, match="original_preparation_physical_claim_required"
        ):
            physical.prepare()
        assert not target.exists() and not physical.effects


@pytest.mark.parametrize("change", ["new_file", "replacement", "mode", "symlink"])
def test_admission_freshness_failure_retires_original_plan(selected, change):
    target, client = selected
    target.mkdir()
    request = RepositoryPrepareRequest(str(target), True)
    baseline = _fds()
    plan = client.plan_repository_preparation(request)
    if change == "new_file":
        (target / "foreign").write_bytes(b"preserve")
    elif change in ("replacement", "symlink"):
        target.rename(target.parent / "retained-original")
        if change == "replacement":
            target.mkdir()
        else:
            target.symlink_to(
                target.parent / "retained-original", target_is_directory=True
            )
    else:
        target.chmod(0o700)
    with pytest.raises(RepositoryPreparationError):
        client.admit_repository_preparation(plan)
    assert plan.observe().phase == "retired"
    assert _fds() == baseline and not (target / ".git").exists()


def test_plan_cleanup_is_independent(selected):
    target, client = selected
    request = RepositoryPrepareRequest(str(target), True)
    first = client.plan_repository_preparation(request)
    with client.plan_repository_preparation(request) as second:
        first.release()
        admission = client.admit_repository_preparation(second)
        assert (
            client.prepare_repository(request, admission=admission).outcome == "created"
        )


def test_ambiguous_execution_selection_is_not_preferred(selected, monkeypatch):
    target, _client = selected
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "other-provider")
    with pytest.raises(ValueError, match="unambiguous"):
        WorkspaceRepositoryPreparationClient.filesystem(
            repository_root=str(target),
            execution_id="codex-preparation-controlled-test",
        )
    assert not target.exists()


def test_cross_process_original_admission_is_unusable(selected):
    target, client = selected
    request = RepositoryPrepareRequest(str(target), True)
    with client.plan_repository_preparation(request) as plan:
        admission = client.admit_repository_preparation(plan)
        process = os.fork()
        if process == 0:
            try:
                client.prepare_repository(request, admission=admission)
            except RepositoryPreparationError:
                os._exit(0)
            except BaseException:  # noqa: BLE001 -- report child failure without invoking inherited finalizers
                os._exit(2)
            os._exit(1)
        _pid, status = os.waitpid(process, 0)
        assert os.waitstatus_to_exitcode(status) == 0 and not target.exists()
        # The child's copy cannot spend the parent's capability.
        assert (
            client.prepare_repository(request, admission=admission).outcome == "created"
        )


@pytest.mark.parametrize(
    "kind", ["plan_digest", "plan_observation", "preview_admission"]
)
def test_interrupted_entrances_release_all_retained_descriptors(
    selected, monkeypatch, kind
):
    from aware_workspace_fs_adapter import repository_preparation as physical

    target, client = selected
    baseline = _fds()
    request = RepositoryPrepareRequest(str(target), True, kind == "preview_admission")

    def interrupted(_self):
        raise KeyboardInterrupt("controlled owner interruption")

    if kind == "plan_digest":
        monkeypatch.setattr(physical._RetainedPreparation, "plan_digest", interrupted)
        with pytest.raises(RepositoryPreparationError):
            client.plan_repository_preparation(request)
    else:
        plan = client.plan_repository_preparation(request)
        if kind == "plan_observation":
            monkeypatch.setattr(
                physical._RetainedPreparation, "validate_current", interrupted
            )
            with pytest.raises(RepositoryPreparationError):
                plan.observe()
        else:
            with pytest.raises(RepositoryPreparationError):
                client.admit_repository_preparation(plan)
        plan.release()
    assert _fds() == baseline and not target.exists()


def test_git_environment_cannot_redirect_initialization(
    selected, monkeypatch, tmp_path
):
    target, client = selected
    outside = tmp_path / "foreign-git"
    outside.mkdir()
    monkeypatch.setenv("GIT_DIR", str(outside))
    monkeypatch.setenv("GIT_WORK_TREE", str(outside))
    monkeypatch.setenv("GIT_INDEX_FILE", str(outside / "index"))
    assert (
        _apply(client, RepositoryPrepareRequest(str(target), True)).outcome == "created"
    )
    assert (target / ".git/HEAD").is_file() and not list(outside.iterdir())


def test_cyclic_malformed_report_keeps_original_publication_evidence(
    selected, monkeypatch
):
    target, client = selected
    runtime = authority._CLIENTS[client]
    original = runtime.prepare_repository

    def corrupt(request, *, admission=None):
        original(request, admission=admission)
        cyclic = {}
        cyclic["self"] = cyclic
        return cyclic

    monkeypatch.setattr(runtime, "prepare_repository", corrupt)
    with pytest.raises(RepositoryPreparationError) as raised:
        _apply(client, RepositoryPrepareRequest(str(target), True))
    assert (
        raised.value.evidence.reported_result["self"]["reason"]
        == "cycle_or_depth_bound"
    )
    assert raised.value.evidence.effects and (target / ".git/HEAD").is_file()
    assert not raised.value.evidence.authorizes_retry


def test_forged_metaclass_and_equality_holder_cannot_match_originals(selected):
    class Forged(type):
        def __eq__(self, other):
            return True

    class Fake(metaclass=Forged):
        pass

    with pytest.raises(RepositoryPreparationValueError):
        repository_preparation_value_from_payload(Fake, {})
    with pytest.raises(RepositoryPreparationValueError):
        repository_preparation_value_to_payload(Fake())
    target, client = selected
    request = RepositoryPrepareRequest(str(target), True)
    with client.plan_repository_preparation(request) as plan:
        admission = client.admit_repository_preparation(plan)

        class Equal:
            def __hash__(self):
                return hash(admission)

            def __eq__(self, other):
                return True

        with pytest.raises(RepositoryPreparationError):
            client.prepare_repository(request, admission=Equal())
        assert (
            client.prepare_repository(request, admission=admission).outcome == "created"
        )
