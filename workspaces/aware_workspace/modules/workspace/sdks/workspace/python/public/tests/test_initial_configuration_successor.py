"""Real original-owner failed publication and one successor; disposable roots."""

import copy
import json
import os
import pickle
import shutil
import subprocess
import sys
import threading

import pytest
from aware_protocol_fs_adapter.project_bootstrap import (
    prepare_planning_project_configuration,
)
from aware_workspace_sdk.initial_authoring.configuration_successor import (
    DOMAIN,
    ConfigurationSuccessorAdmission,
    InitialConfigurationSuccessorRequest,
    validate_origin,
)
from aware_workspace_sdk.initial_authoring.values import initial_reference
from aware_workspace_sdk.repository_preparation import (
    RepositoryPrepareRequest,
    WorkspaceRepositoryPreparationClient,
)
from aware_workspace_sdk.repository_publication import (
    WorkspaceRepositoryPublicationClient,
)


def git(root, *arguments):
    return subprocess.run(
        ["git", "-C", str(root), *arguments], capture_output=True, text=True, check=True
    ).stdout.strip()


def snapshot(path):
    return sorted(
        (str(p.relative_to(path)), p.read_bytes(), p.stat().st_mode, p.stat().st_ino)
        for p in path.rglob("*")
        if p.is_file()
    )


@pytest.fixture
def failed(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "successor-fixture")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    for key in (
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
        "EMAIL",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "absent-global"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    root = tmp_path / "customer"
    preparation = WorkspaceRepositoryPreparationClient.filesystem(
        repository_root=str(root), execution_id="codex-successor-fixture"
    )
    request = RepositoryPrepareRequest(str(root), True)
    with preparation.plan_repository_preparation(request) as plan:
        prepared = preparation.prepare_repository(
            request, admission=preparation.admit_repository_preparation(plan)
        )
    assert prepared.outcome == "created"
    client = WorkspaceRepositoryPublicationClient.filesystem(repository_root=str(root))
    enrollment = client.enroll_initial_authoring(preparation)
    protocol = prepare_planning_project_configuration(repository_root=str(root))
    original = client.plan_initial_configuration(
        enrollment, protocol, idempotency_key="configuration"
    )
    admission = client.admit_initial_configuration(original)
    result = client.publish_initial_configuration(admission)
    assert result.publication_state == "not_published" and result.ledger_complete, (
        result
    )
    assert (
        result.original_writer_report is not None
        and "Author identity unknown" in result.original_writer_report.error
    )
    git(root, "config", "--local", "user.name", "Successor fixture")
    git(root, "config", "--local", "user.email", "fixture@example.invalid")
    return root, client, admission, result, protocol


def test_real_successor_cas_projection_restart_and_original_failed_receipt(failed):
    root, client, old_admission, failed_result, _protocol = failed
    old = snapshot(root / ".git/aware-initial-authoring-v1")
    plan = client.prepare_initial_configuration_successor()
    assert plan.request.to_wire()["attempt_number"] == 1
    admission = client.admit_initial_configuration_successor(plan)
    result = client.publish_initial_configuration_successor(admission)
    assert result.publication_state == "published", result
    assert result.ledger_complete and result.admission_completion == "completed"
    assert client.publish_initial_configuration_successor(admission) == result
    assert client.publish_initial_configuration(old_admission) == failed_result
    assert not (root / "aware.protocol.toml").exists()
    projection = client.project_initial_configuration_successor()
    assert projection["projection_state"] == "installed", projection
    origin = client.observe_initial_configuration_origin(current=True)
    validate_origin(origin)
    assert origin["kind"] == "successor"
    assert (
        origin["predecessor"]["publication"]["original_result"]["publication_state"]
        == "not_published"
    )
    assert git(root, "rev-list", "--count", "HEAD") == "1"
    assert (
        git(root, "show", "-s", "--format=%an <%ae>", "HEAD")
        == "Successor fixture <fixture@example.invalid>"
    )
    assert snapshot(root / ".git/aware-initial-authoring-v1") == old
    restored = WorkspaceRepositoryPublicationClient.filesystem(
        repository_root=str(root)
    )
    assert (
        restored.observe_initial_configuration_successor()["original_result"] == result
    )
    assert restored.observe_initial_configuration_origin(current=True) == origin
    script = """
import json,sys
from aware_workspace_sdk.repository_publication import WorkspaceRepositoryPublicationClient,repository_publication_value_to_payload
c=WorkspaceRepositoryPublicationClient.filesystem(repository_root=sys.argv[1])
print(json.dumps(repository_publication_value_to_payload(c.observe_initial_configuration_successor()['original_result']),sort_keys=True))
"""
    out = subprocess.run(
        [sys.executable, "-B", "-c", script, str(root)],
        env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        capture_output=True,
        text=True,
        check=True,
    )
    from aware_workspace_sdk.repository_publication import (
        repository_publication_value_to_payload,
    )

    assert json.loads(out.stdout) == repository_publication_value_to_payload(result)
    assert snapshot(root / ".git/aware-initial-authoring-v1") == old


@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_plan_and_admission_not_copyable_or_portable(failed, operation):
    _, client, _, _, _ = failed
    plan = client.prepare_initial_configuration_successor()
    with pytest.raises(TypeError):
        operation(plan)
    admission = client.admit_initial_configuration_successor(plan)
    with pytest.raises(TypeError):
        operation(admission)


def test_decoded_request_or_constructed_handle_is_not_admission(failed):
    root, client, _, _, _ = failed
    plan = client.prepare_initial_configuration_successor()
    request = InitialConfigurationSuccessorRequest.from_wire(plan.request.to_wire())
    for value in (
        request,
        request.to_wire(),
        object.__new__(ConfigurationSuccessorAdmission),
    ):
        with pytest.raises(ValueError):
            client.publish_initial_configuration_successor(value)
    assert not (root / ".git/aware-initial-configuration-successor-v1").exists()


def test_two_prepared_creators_cannot_reserve_two_successors(failed):
    root, client, _, _, _ = failed
    other = WorkspaceRepositoryPublicationClient.filesystem(repository_root=str(root))
    one = client.prepare_initial_configuration_successor()
    two = other.prepare_initial_configuration_successor()
    client.admit_initial_configuration_successor(one)
    with pytest.raises((ValueError, FileExistsError)):
        other.admit_initial_configuration_successor(two)
    assert not (root / "aware.protocol.toml").exists()


def test_changed_config_during_review_refuses_without_refresh(failed):
    root, client, _, _, _ = failed
    plan = client.prepare_initial_configuration_successor()
    git(root, "config", "--local", "user.name", "Changed fixture")
    with pytest.raises(ValueError, match="source_changed"):
        client.admit_initial_configuration_successor(plan)
    assert not (root / ".git/aware-initial-configuration-successor-v1").exists()


def test_pending_successor_recovery_never_dispatches(failed):
    root, client, _, _, _ = failed
    client.admit_initial_configuration_successor(
        client.prepare_initial_configuration_successor()
    )
    result = WorkspaceRepositoryPublicationClient.filesystem(
        repository_root=str(root)
    ).observe_initial_configuration_successor()
    assert result["disposition"] == "pending" and not result["authorizes_redispatch"]
    assert not (root / "aware.protocol.toml").exists()


def test_lost_result_after_cas_remains_uncertain_no_redispatch(failed):
    root, client, _, _, _ = failed
    result = client.publish_initial_configuration_successor(
        client.admit_initial_configuration_successor(
            client.prepare_initial_configuration_successor()
        )
    )
    assert result.publication_state == "published"
    # Explicit destructive fixture corruption, not a supported owner operation.
    (root / ".git/aware-initial-configuration-successor-v1/result.json").unlink()
    recovered = client.observe_initial_configuration_successor()
    assert (
        recovered["disposition"] == "uncertain"
        and not recovered["authorizes_redispatch"]
    )
    with pytest.raises(ValueError):
        client.prepare_initial_configuration_successor()
    assert git(root, "rev-list", "--count", "HEAD") == "1"


@pytest.mark.parametrize(
    "kind",
    [
        "boolean",
        "head",
        "manifest",
        "unknown",
        "symlink_mode",
        "attribution",
        "foreign_root",
    ],
)
def test_redigested_malformed_request_stays_non_authorizing(failed, kind):
    root, client, _, _, _ = failed
    wire = client.prepare_initial_configuration_successor().request.to_wire()
    if kind == "boolean":
        wire["attempt_number"] = True
    elif kind == "head":
        wire["source"]["expected_head"] = False
    elif kind == "manifest":
        wire["configuration"]["content_utf8"] += "\n# substituted\n"
    elif kind == "unknown":
        wire["source"]["verified"] = True
    elif kind == "symlink_mode":
        wire["source"]["git_config_stat"][2] = 0o120777
    elif kind == "attribution":
        wire["source"]["author"]["name"] = "injected\nname"
    else:
        wire["source"]["repository_root"] += "-foreign"
    wire["request_ref"] = initial_reference(
        DOMAIN + "request", {k: v for k, v in wire.items() if k != "request_ref"}
    )
    with pytest.raises(ValueError):
        InitialConfigurationSuccessorRequest.from_wire(wire)
    assert not (root / ".git/aware-initial-configuration-successor-v1").exists()


def test_post_issue_request_mutation_refuses_repeatedly_without_repair(failed):
    root, client, _, _, _ = failed
    from aware_workspace_sdk.initial_authoring.configuration_successor import _STATES

    plan = client.prepare_initial_configuration_successor()
    request = _STATES[plan].request
    object.__setattr__(
        request,
        "request_ref",
        "workspace-initial-configuration-successor-request:sha256:" + "f" * 64,
    )
    for _ in range(2):
        with pytest.raises(ValueError):
            client.admit_initial_configuration_successor(plan)
        with pytest.raises(ValueError):
            plan.to_wire()
    assert request.request_ref.endswith("f" * 64)
    assert not (root / ".git/aware-initial-configuration-successor-v1").exists()


@pytest.mark.parametrize(
    "kind", ["target", "index", "remote", "ref", "core", "successor_symlink"]
)
def test_foreign_source_effects_preserved_and_not_admitted(failed, kind, tmp_path):
    root, client, _, _, _ = failed
    if kind == "target":
        (root / "aware.protocol.toml").write_bytes(b"foreign")
    elif kind == "index":
        (root / ".git/index").write_bytes(b"foreign staging")
    elif kind == "remote":
        git(root, "remote", "add", "origin", "https://example.invalid/customer.git")
    elif kind == "ref":
        (root / ".git/refs/heads/foreign").write_text("f" * 40 + "\n")
    elif kind == "core":
        git(root, "config", "--local", "core.filemode", "false")
    else:
        (root / ".git/aware-initial-configuration-successor-v1").symlink_to(
            tmp_path, target_is_directory=True
        )
    before = snapshot(root)
    with pytest.raises((ValueError, OSError)):
        client.prepare_initial_configuration_successor()
    assert snapshot(root) == before


def test_expired_admission_cannot_dispatch_or_refresh(failed, monkeypatch):
    root, client, _, _, _ = failed
    from aware_workspace_runtime import initial_configuration_successor as runtime
    from aware_workspace_sdk.initial_authoring.configuration_successor import _STATES

    admission = client.admit_initial_configuration_successor(
        client.prepare_initial_configuration_successor()
    )
    deadline = _STATES[admission].deadline
    monkeypatch.setattr(runtime.time, "monotonic", lambda: deadline + 1)
    with pytest.raises(ValueError, match="expired"):
        client.publish_initial_configuration_successor(admission)
    assert not (
        root / ".git/aware-initial-configuration-successor-v1/dispatch.json"
    ).exists()


def test_old_dispatcher_anchor_excludes_successor_until_original_return(
    failed, monkeypatch
):
    root, client, old_admission, original, _ = failed
    from aware_workspace_fs_adapter.initial_authoring import ConfigurationAttempt

    entered = threading.Event()
    release = threading.Event()
    errors = []
    real = ConfigurationAttempt.recover

    def paused(self):
        if threading.current_thread().name == "old-original-publication":
            entered.set()
            assert release.wait(10)
        return real(self)

    monkeypatch.setattr(ConfigurationAttempt, "recover", paused)

    def run():
        try:
            assert client.publish_initial_configuration(old_admission) == original
        except BaseException as error:  # noqa: BLE001 -- retain test-thread assertion/interrupt for parent
            errors.append(error)

    thread = threading.Thread(target=run, name="old-original-publication")
    thread.start()
    try:
        assert entered.wait(5)
        other = WorkspaceRepositoryPublicationClient.filesystem(
            repository_root=str(root)
        )
        with pytest.raises(ValueError, match="attempt_busy"):
            other.prepare_initial_configuration_successor()
    finally:
        release.set()
        thread.join(10)
    assert not thread.is_alive() and not errors
    assert not (root / ".git/aware-initial-configuration-successor-v1").exists()


def test_two_real_process_creators_have_one_durable_successor_slot(failed):
    root, _, _, _, _ = failed
    code = """
import sys
from aware_workspace_sdk.repository_publication import WorkspaceRepositoryPublicationClient
c=WorkspaceRepositoryPublicationClient.filesystem(repository_root=sys.argv[1])
p=c.prepare_initial_configuration_successor()
print('prepared',flush=True)
sys.stdin.readline()
try:
    c.admit_initial_configuration_successor(p)
except (ValueError,OSError):print('refused',flush=True)
else:print('admitted',flush=True)
"""
    children = []
    try:
        # Prepare sequentially without holding either lock, then race only the
        # two genuine admissions. No failed preparation is retried/refreshed.
        for _ in range(2):
            child = subprocess.Popen(
                [sys.executable, "-B", "-c", code, str(root)],
                env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
                text=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            children.append(child)
            assert child.stdout.readline().strip() == "prepared"
        for child in children:
            child.stdin.write("go\n")
            child.stdin.flush()
        results = [child.communicate(timeout=20) for child in children]
        assert sorted(output.strip() for output, _ in results) == [
            "admitted",
            "refused",
        ], results
        assert all(child.returncode == 0 for child in children)
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.wait()
    assert not (
        root / ".git/aware-initial-configuration-successor-v1/dispatch.json"
    ).exists()


@pytest.mark.parametrize("point", ["reservation", "dispatch", "result"])
def test_real_process_hard_exit_never_creates_retry_authority(failed, point):
    root, client, _, _, _ = failed
    code = """
import os,sys
from aware_workspace_sdk.repository_publication import WorkspaceRepositoryPublicationClient
from aware_workspace_fs_adapter import initial_configuration_successor as fs
c=WorkspaceRepositoryPublicationClient.filesystem(repository_root=sys.argv[1])
p=c.prepare_initial_configuration_successor()
point=sys.argv[2]
if point=='reservation':
    real=fs._write_record
    def stop(directory,name,value):
        if name=='admission.json':os._exit(73)
        return real(directory,name,value)
    fs._write_record=stop
a=c.admit_initial_configuration_successor(p)
if point=='dispatch':
    real=fs.SuccessorAttempt.consume
    def stop(self):
        real(self)
        os._exit(73)
    fs.SuccessorAttempt.consume=stop
if point=='result':
    def stop(self,result):os._exit(73)
    fs.SuccessorAttempt.finish=stop
c.publish_initial_configuration_successor(a)
raise AssertionError('crash point not reached')
"""
    crashed = subprocess.run(
        [sys.executable, "-B", "-c", code, str(root), point],
        env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert crashed.returncode == 73, crashed.stderr
    before = snapshot(root)
    if point == "reservation":
        with pytest.raises((ValueError, OSError)):
            client.observe_initial_configuration_successor()
    else:
        result = client.observe_initial_configuration_successor()
        assert (
            result["disposition"] == "uncertain" and not result["authorizes_redispatch"]
        )
    with pytest.raises((ValueError, OSError)):
        client.prepare_initial_configuration_successor()
    assert snapshot(root) == before
    assert not (root / "aware.protocol.toml").exists()
    if point == "result":
        assert git(root, "rev-list", "--count", "HEAD") == "1"


@pytest.mark.parametrize("mutation", ["mode", "body"])
def test_actual_isolated_tree_tampering_refuses_before_cas(
    failed, monkeypatch, mutation
):
    root, client, _, _, _ = failed
    from aware_workspace_fs_adapter import git_writer as writer

    admission = client.admit_initial_configuration_successor(
        client.prepare_initial_configuration_successor()
    )
    real = writer._run_git
    changed = False

    def substitute(*, runner, repo_root, args, command_log, environment=None, **kwargs):
        nonlocal changed
        result = real(
            runner=runner,
            repo_root=repo_root,
            args=args,
            command_log=command_log,
            environment=environment,
            **kwargs,
        )
        if not changed and args[:3] == ("git", "update-index", "--add"):
            changed = True
            cacheinfo = args[-1]
            if mutation == "mode":
                cacheinfo = cacheinfo.replace("100644,", "100755,", 1)
            else:
                blob = subprocess.run(
                    ["git", "-C", str(root), "hash-object", "-w", "--stdin"],
                    input="",
                    text=True,
                    capture_output=True,
                    check=True,
                ).stdout.strip()
                cacheinfo = "100644," + blob + ",aware.protocol.toml"
            real(
                runner=runner,
                repo_root=repo_root,
                args=("git", "update-index", "--add", "--cacheinfo", cacheinfo),
                command_log=command_log,
                environment=environment,
            )
        return result

    monkeypatch.setattr(writer, "_run_git", substitute)
    result = client.publish_initial_configuration_successor(admission)
    assert changed and result.publication_state == "not_published", result
    assert result.original_writer_report is not None
    assert "staged_tree_mismatch" in result.original_writer_report.error
    assert not (root / "aware.protocol.toml").exists()


def test_post_reservation_history_exit_index_race_issues_no_live_admission(
    failed, monkeypatch
):
    root, client, _, _, _ = failed
    from contextlib import contextmanager

    from aware_workspace_fs_adapter import initial_configuration_successor as fs

    plan = client.prepare_initial_configuration_successor()
    original = fs.anchor

    @contextmanager
    def race(port):
        with original(port) as value:
            yield value
        # Historical verification has finished, before the caller could receive
        # its nominal handle. This is foreign staging, not an owner effect.
        (root / ".git/index").write_bytes(b"foreign staging")

    monkeypatch.setattr(fs, "anchor", race)
    with pytest.raises(ValueError):
        client.admit_initial_configuration_successor(plan)
    assert (root / ".git/index").read_bytes() == b"foreign staging"
    assert (
        root / ".git/aware-initial-configuration-successor-v1/admission.json"
    ).is_file()
    assert not (
        root / ".git/aware-initial-configuration-successor-v1/dispatch.json"
    ).exists()


def test_current_origin_rechecks_index_after_historical_anchor_exit(
    failed, monkeypatch
):
    root, client, _, _, _ = failed
    from contextlib import contextmanager

    from aware_workspace_fs_adapter import initial_configuration_successor as fs

    result = client.publish_initial_configuration_successor(
        client.admit_initial_configuration_successor(
            client.prepare_initial_configuration_successor()
        )
    )
    assert result.publication_state == "published"
    assert (
        client.project_initial_configuration_successor()["projection_state"]
        == "installed"
    )
    original = fs.anchor

    @contextmanager
    def race(port):
        with original(port) as value:
            yield value
        (root / ".git/index").write_bytes(b"foreign staging")

    monkeypatch.setattr(fs, "anchor", race)
    with pytest.raises(ValueError):
        client.observe_initial_configuration_origin(current=True)
    assert (root / ".git/index").read_bytes() == b"foreign staging"


def test_pure_codec_cache_never_shares_mutated_result_or_skips_changed_bytes(failed):
    _, client, _, _, _ = failed
    from aware_workspace_sdk.initial_authoring.configuration_successor import (
        validate_publication,
    )

    request = client.prepare_initial_configuration_successor().request.to_wire()
    bundle = request["predecessor"]
    one = validate_publication(
        bundle["publication"], bundle["admission"], successor=False
    )
    object.__setattr__(one, "candidate_commit", "f" * 40)
    two = validate_publication(
        bundle["publication"], bundle["admission"], successor=False
    )
    assert two is not one and two.candidate_commit is None
    forged = copy.deepcopy(bundle["publication"])
    forged["original_result"]["work_admission_receipt_ref"] = "foreign"
    forged["publication_ref"] = initial_reference(
        "workspace-initial-publication",
        {k: v for k, v in forged.items() if k != "publication_ref"},
    )
    with pytest.raises(ValueError):
        validate_publication(forged, bundle["admission"], successor=False)


def test_caller_constructed_reservation_state_refuses_before_any_callback(failed):
    _, client, _, _, _ = failed
    from aware_workspace_sdk.initial_authoring.configuration_successor import (
        _reservation,
    )

    called = []

    class CallerState:
        owner = client._provider
        phase = "reserving"
        pid = os.getpid()

        def pins(self):
            called.append("pins")
            return ()

        def validate(self):
            called.append("validate")

    with pytest.raises(
        ValueError, match="original_configuration_successor_state_required"
    ):
        _reservation(CallerState())
    assert called == []


@pytest.mark.parametrize(
    "point", ["read-tree", "write-tree", "commit-tree", "update-ref"]
)
def test_late_git_environment_cannot_redirect_successor_cas(
    failed, monkeypatch, tmp_path, point
):
    root, client, _, _, _ = failed
    from aware_workspace_fs_adapter import git_writer as writer

    foreign = tmp_path / "foreign"
    git(tmp_path, "init", "--initial-branch=main", str(foreign))
    admission = client.admit_initial_configuration_successor(
        client.prepare_initial_configuration_successor()
    )
    original = writer._run_git
    changed = False
    before = None

    def redirect(*, args, **kwargs):
        nonlocal changed, before
        if not changed and args[:2] == ("git", point):
            # Give the foreign repository the tree already staged by the
            # legitimate transaction. A later lookup must not be our defense:
            # the selected repository must remain fixed before commit/CAS.
            shutil.copytree(
                root / ".git/objects", foreign / ".git/objects", dirs_exist_ok=True
            )
            before = snapshot(foreign)
            monkeypatch.setenv("GIT_DIR", str(foreign / ".git"))
            monkeypatch.setenv("GIT_WORK_TREE", str(foreign))
            monkeypatch.setenv("GIT_OBJECT_DIRECTORY", str(foreign / ".git/objects"))
            monkeypatch.setenv("GIT_COMMON_DIR", str(foreign / ".git"))
            monkeypatch.setenv("GIT_INDEX_FILE", str(foreign / ".git/index"))
            monkeypatch.setenv("GIT_NAMESPACE", "foreign")
            monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
            monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.worktree")
            monkeypatch.setenv("GIT_CONFIG_VALUE_0", str(foreign))
            changed = True
        return original(args=args, **kwargs)

    monkeypatch.setattr(writer, "_run_git", redirect)
    result = client.publish_initial_configuration_successor(admission)
    assert changed
    assert snapshot(foreign) == before
    # Remove the deliberately injected ambient values for independent probes.
    for key in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_NAMESPACE",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_KEY_0",
        "GIT_CONFIG_VALUE_0",
    ):
        monkeypatch.delenv(key)
    if point == "read-tree":
        # This earlier change is also observed by the independent source
        # verifier before publication. Refusal is correct, not a reason to
        # refresh authority or require publication despite a changed input.
        assert result.publication_state == "not_published", result
        assert result.candidate_commit is None
        assert result.original_writer_report is not None
        assert "attribution_unavailable" in result.original_writer_report.error
        assert not (root / ".git/refs/heads/main").exists()
        return
    assert result.publication_state == "published", result
    assert git(root, "rev-parse", "HEAD") == result.candidate_commit
    assert git(root, "rev-list", "--count", "HEAD") == "1"
    assert not (foreign / ".git/refs/heads/main").exists()
    assert not (root / "aware.protocol.toml").exists()


def test_successor_runner_freezes_environment_and_permits_only_index_overlay(
    failed, monkeypatch, tmp_path
):
    root, client, _, _, _ = failed
    from aware_workspace_fs_adapter import initial_configuration_successor as fs

    source = client.prepare_initial_configuration_successor().request.to_wire()[
        "source"
    ]
    runner = fs.attributed_runner(source)
    source["author"]["name"] = "Mutated caller"
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "foreign"))
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Foreign actor")
    monkeypatch.setenv("PATH", str(tmp_path / "foreign-bin"))
    monkeypatch.setenv("HOME", str(tmp_path / "foreign-home"))
    calls = []

    def observe(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(fs.subprocess, "run", observe)
    runner.run(args=("git", "status"), cwd=root)
    index = str(root / ".git/isolated-index")
    runner.run_with_environment(
        args=("git", "write-tree"), cwd=root, environment={"GIT_INDEX_FILE": index}
    )
    first, second = calls[0][1]["env"], calls[1][1]["env"]
    assert calls[0][0][0].startswith("/")
    assert first["GIT_DIR"] == str(root / ".git")
    assert first["GIT_WORK_TREE"] == str(root)
    assert first["GIT_OBJECT_DIRECTORY"] == str(root / ".git/objects")
    assert first["GIT_AUTHOR_NAME"] == "Successor fixture"
    assert first["GIT_CONFIG_NOSYSTEM"] == "1"
    assert first["GIT_CONFIG_GLOBAL"] == os.devnull
    assert first["HOME"] != str(tmp_path / "foreign-home")
    assert first["PATH"] != str(tmp_path / "foreign-bin")
    assert "GIT_INDEX_FILE" not in first
    assert second == {**first, "GIT_INDEX_FILE": index}
    for environment in ({"GIT_DIR": str(tmp_path)}, {"GIT_CONFIG_COUNT": "1"}):
        with pytest.raises(ValueError, match="git_environment_substituted"):
            runner.run_with_environment(
                args=("git", "update-ref"), cwd=root, environment=environment
            )
    with pytest.raises(ValueError, match="git_binding_substituted"):
        runner.run(args=("git", "status"), cwd=tmp_path)
    assert len(calls) == 2
