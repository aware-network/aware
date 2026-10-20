"""Assisted installed CLI qualification, not an unassisted customer evaluation.

The positive customer journey uses only the real installed aware executable.
Negative retained-failure fixtures use installed original public SDK owners,
never manufactured records or a substitute writer. Test-local execution labels
and automated terminal responses are not authentic Identity or Human approval.
Retain full invocation output and original provider records.
"""

import errno
import hashlib
import importlib
import importlib.metadata
import json
import os
import pty
import select
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("AWARE_MOUNTED_INSTALLED_CANARY") != "1",
    reason="requires the pinned non-editable Agent-with-Goal installed candidate",
)


def command(*args):
    executable = Path(sys.executable).with_name("aware")
    assert executable.is_file() and os.access(executable, os.X_OK)
    return [str(executable), *map(str, args)]


def run(*args):
    result = subprocess.run(
        command(*args), capture_output=True, text=True, timeout=180, check=False
    )
    print(result.stdout + result.stderr, end="")
    return result.returncode, result.stdout + result.stderr


def terminal(args, response, before_confirm=None, *, expect_confirmation=True):
    """Actual OS terminal; respond only after the product's full live preview."""
    master, slave = pty.openpty()
    process = subprocess.Popen(command(*args), stdin=slave, stdout=slave, stderr=slave)
    os.close(slave)
    output = bytearray()
    confirmed = False
    deadline = time.monotonic() + 180
    try:
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(master, 65536)
                except OSError as error:
                    if error.errno == errno.EIO:
                        break
                    raise
                if not chunk:
                    break
                output.extend(chunk)
                if not confirmed and b"to confirm this exact plan: " in output:
                    assert records(output.decode())[0], (
                        "confirmation preceded complete preview"
                    )
                    if before_confirm is not None:
                        before_confirm()
                    os.write(master, (response + "\n").encode())
                    confirmed = True
            elif process.poll() is not None:
                break
        else:
            raise AssertionError("installed command terminal timeout")
        assert confirmed is expect_confirmation, output.decode(errors="replace")
        print(output.decode(), end="")
        return process.wait(timeout=5), output.decode()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        os.close(master)


def records(text):
    return [
        json.loads(line)
        for line in text.replace("\r\n", "\n").splitlines()
        if line.startswith("{")
    ]


def git(root, *args):
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(root), *args],
        check=True,
        capture_output=True,
    ).stdout


def snapshot(root):
    return tuple(
        sorted(
            (
                str(p.relative_to(root)),
                hashlib.sha256(p.read_bytes()).hexdigest(),
                p.stat().st_mode,
            )
            for p in root.rglob("*")
            if p.is_file()
        )
    )


def setup_args(root):
    return [
        "init",
        "--profile",
        "create-first",
        "--repository-root",
        root,
        "--create-repository",
    ]


def location(root):
    return ["--repository-root", root, "--protocol-manifest", "aware.protocol.toml"]


def project_args(root):
    return ["project", "create", "home", "--title", "Home", *location(root)]


def goal_args(root):
    return [
        "goal",
        "create",
        "release",
        "--project",
        "home",
        "--title",
        "First release",
        "--intent",
        "Make the first useful release.",
        "--date",
        "2026-10-18",
        *location(root),
    ]


@pytest.fixture
def root(tmp_path, monkeypatch):
    # Deliberately diagnostic local-policy correlation, NOT genuine Identity.
    monkeypatch.setenv("CODEX_THREAD_ID", "installed-mounted-diagnostic")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    for name, value in (
        ("GIT_AUTHOR_NAME", "Installed diagnostic"),
        ("GIT_COMMITTER_NAME", "Installed diagnostic"),
        ("GIT_AUTHOR_EMAIL", "canary@example.invalid"),
        ("GIT_COMMITTER_EMAIL", "canary@example.invalid"),
    ):
        monkeypatch.setenv(name, value)
    return tmp_path / "customer"


def configure(root):
    code, output = terminal(
        [*setup_args(root), "--apply", "--format", "summary"], "initialize create-first"
    )
    assert code == 0, output
    preview, result = records(output)
    assert preview["status"] == "preview" and result["status"] == "configured"
    assert result["completion_verified"] is True
    assert result["configuration"] == preview["configuration"]
    assert result["assurance"] == "cooperative_same_execution_local_policy"
    assert (
        result["stages"]["terminal_qualification"]["original_result"]
        == result["stages"]["configuration_publication"]
    )
    assert not (root / "AGENTS.md").exists()
    assert "No RUN authority" in output
    return result


def create_project(root):
    code, output = terminal([*project_args(root), "--apply"], "create home")
    assert code == 0, output
    preview, result = records(output)
    assert preview["stage"] == "preview" and result["stage"] == "result"
    assert result["result"]["disposition"] == "created"
    return result["result"]


def create_goal(root):
    code, output = terminal([*goal_args(root), "--apply"], "create release")
    assert code == 0, output
    preview, result = records(output)
    assert preview["stage"] == "preview" and result["stage"] == "result"
    assert result["result"]["disposition"] == "created_and_linked"
    assert "not yet decomposed" in output and "No work started" in output
    return result["result"]


def test_installed_origins_entrypoint_and_isolation():
    assert "PYTHONPATH" not in os.environ
    for name in ("AWARE_HIDDEN_CHECKOUT", "AWARE_HIDDEN_SOURCE"):
        assert list(Path(os.environ[name]).iterdir()) == []
    with socket.socket() as probe:
        assert probe.connect_ex(("203.0.113.1", 443)) == errno.ENETUNREACH
    for name in (
        "aware_agent_cli.main",
        "aware_agent_cli.create_first_initialization",
        "aware_goal_native_cli.customer_commands",
        "aware_workflow.project_customer",
        "aware_workflow.goal_customer",
        "aware_workspace_sdk.repository_publication",
        "aware_workspace_fs_adapter",
        "aware_workspace_fs_adapter.git_identity",
        "aware_workspace_fs_adapter.initial_configuration_successor",
        "aware_workspace_sdk.initial_authoring.configuration_successor",
        "aware_protocol_fs_adapter",
    ):
        module = importlib.import_module(name)
        assert module.__file__ is not None
        path = Path(module.__file__).resolve()
        assert (
            Path(sys.prefix).resolve() in path.parents and "site-packages" in path.parts
        )
    distributions = list(importlib.metadata.distributions())
    assert "aware-workflow" not in {d.metadata["Name"] for d in distributions}
    assert importlib.metadata.version("aware-agent-cli") == "0.2.0a16"
    assert importlib.metadata.version("aware-protocol-fs-adapter") == "0.6.6"
    entries = [e for d in distributions for e in d.entry_points if e.name == "aware"]
    assert len(entries) == 1 and entries[0].value == "aware_agent_cli.main:main"
    for distribution in distributions:
        direct = distribution.read_text("direct_url.json")
        if direct:
            assert json.loads(direct).get("dir_info", {}).get("editable") is not True


def test_mounted_terminal_journey_and_cold_reads_keep_both_complete_receipts(root):
    code, output = run(*setup_args(root))
    assert code == 0 and records(output)[0]["status"] == "preview"
    assert not root.exists()
    configuration = configure(root)
    project = create_project(root)
    assert project["reading"]["reading"]["content"]["goals"] == []
    code, output = run("project", "show", "home", *location(root), "--format", "json")
    assert code == 0, output
    assert records(output)[0]["result"]["reading"]["content"]["goals"] == []
    goal = create_goal(root)
    before = snapshot(root)
    readings = []
    for family, name in (("goal", "release"), ("project", "home")):
        code, output = run(family, "show", name, *location(root), "--format", "json")
        assert code == 0, output
        readings.append(records(output)[0]["result"]["reading"])
        assert snapshot(root) == before
    assert readings[0] == readings[1]
    reading = readings[0]
    assert (
        reading["goal_creation_publication"]["original_result"]
        == goal["original_result"]
    )
    assert (
        reading["membership_publication"]["original_result"]
        == goal["attachment"]["original_result"]
    )
    assert reading["goal"]["definitions"] == reading["goal"]["lanes"] == []
    assert reading["planning_status"] == "not_yet_decomposed"
    assert reading["project"]["goal_tags"] == ["goal/2026-10-18/release"]
    assert git(root, "rev-list", "--count", "HEAD").strip() == b"4"
    assert (
        configuration["stages"]["configuration_publication"]["commit_hash"].encode()
        == git(root, "rev-list", "--max-parents=0", "HEAD").strip()
    )
    assert not (root / "docs/issues").exists()
    assert b"Issue-Tag:" not in git(root, "log", "--format=%B")
    assert git(root, "status", "--porcelain") == b""
    code, _ = run(
        "goal",
        "eligibility",
        *location(root),
        "--goal-path",
        "docs/goals/2026/10/18/goal-2026-10-18-release.md",
        "--lane-key",
        "not-authored",
        "--phase-key",
        "not-authored",
    )
    assert code == 2
    assert snapshot(root) == before


def test_default_issue_first_still_creates_no_seed_commit(root):
    code, output = run("init", "--repo-root", root, "--create-repository", "--apply")
    assert code == 0, output
    result = json.loads(output)
    assert result["profile"] == "aware.collaboration.fs_v1"
    assert result["completion_verified"] is True
    assert result["workspace"]["result"]["head"] is None
    assert (root / "AGENTS.md").is_file()
    assert not (root / ".git/index").exists()
    assert b"fs_v1" in (root / "aware.protocol.toml").read_bytes()
    assert git(root, "rev-list", "--all") == b""


@pytest.mark.parametrize("family", ["init", "project", "goal"])
def test_noninteractive_apply_refuses_without_creating_customer(root, family):
    args = (
        setup_args(root)
        if family == "init"
        else project_args(root)
        if family == "project"
        else goal_args(root)
    )
    code, output = run(*args, "--apply")
    assert code == 2, output
    result = records(output)[-1]
    assert (
        result["reason"]
        == "noninteractive_apply_requires_original_durable_review_binding"
    )
    assert result["authorizes_redispatch"] is False
    assert not root.exists()


def test_cancelled_setup_has_no_effect(root):
    code, output = terminal([*setup_args(root), "--apply"], "no")
    assert (
        code == 2
        and records(output)[-1]["reason"] == "exact_plan_confirmation_not_given"
    )
    assert not root.exists()


def test_cancelled_project_preserves_original_configuration(root):
    configure(root)
    before = snapshot(root)
    code, output = terminal([*project_args(root), "--apply"], "no")
    assert (
        code == 2
        and records(output)[-1]["reason"] == "exact_plan_confirmation_not_given"
    )
    assert snapshot(root) == before


def test_changed_setup_target_after_preview_refuses_without_repair(root):
    def change():
        assert not root.exists()
        root.mkdir(mode=0o700)
        (root / "foreign").write_bytes(b"keep this work\n")

    code, output = terminal(
        [*setup_args(root), "--apply"], "initialize create-first", change
    )
    assert code == 2, output
    result = records(output)[-1]
    assert result["status"] == "refused" and result["authorizes_retry"] is False
    assert result["reason"] == "git_identity_repository_source_refused"
    assert result["stages"] == {}
    assert (root / "foreign").read_bytes() == b"keep this work\n"
    assert not (root / ".git").exists()


def test_changed_project_after_goal_preview_preserves_foreign_work(root):
    configure(root)
    create_project(root)
    target = root / "docs/projects/project-home.toml"
    head, index = git(root, "rev-parse", "HEAD"), (root / ".git/index").read_bytes()

    def change():
        target.write_bytes(target.read_bytes() + b"\n# retained foreign change\n")

    code, output = terminal([*goal_args(root), "--apply"], "create release", change)
    assert code == 3, output
    assert records(output)[-1]["authorizes_redispatch"] is False
    assert git(root, "rev-parse", "HEAD") == head
    assert (root / ".git/index").read_bytes() == index
    assert target.read_bytes().endswith(b"# retained foreign change\n")
    assert not (root / "docs/goals").exists()


def test_dirty_goal_refuses_both_cold_readers_without_repair(root):
    configure(root)
    create_project(root)
    create_goal(root)
    target = root / "docs/goals/2026/10/18/goal-2026-10-18-release.md"
    target.write_bytes(target.read_bytes() + b"\nforeign change\n")
    before = snapshot(root)
    for family, name in (("goal", "release"), ("project", "home")):
        code, output = run(family, "show", name, *location(root), "--format", "json")
        assert code == 2, output
        assert records(output)[-1]["stage"] == "refused"
        assert snapshot(root) == before


def test_existing_setup_does_not_adopt_or_redispatch(root):
    configure(root)
    before = snapshot(root)
    code, output = run(*setup_args(root))
    assert code == 2, output
    assert records(output)[-1]["status"] == "refused"
    assert snapshot(root) == before


def missing_metadata(root, monkeypatch):
    for name in (
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
        "EMAIL",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(root.parent / "absent-global"))


@pytest.mark.parametrize("role", ["AUTHOR", "COMMITTER"])
def test_installed_missing_metadata_refuses_before_confirmation_or_creation(
    root, monkeypatch, role
):
    missing_metadata(root, monkeypatch)
    other = "COMMITTER" if role == "AUTHOR" else "AUTHOR"
    monkeypatch.setenv(f"GIT_{other}_NAME", "Diagnostic selected metadata")
    monkeypatch.setenv(f"GIT_{other}_EMAIL", "chosen@example.invalid")
    code, output = terminal(
        [*setup_args(root), "--apply"], "", expect_confirmation=False
    )
    assert code == 2, output
    (result,) = records(output)
    assert result["reason"] == "git_commit_identity_unavailable"
    assert result["git_identity"][role.lower()] is None
    assert result["stages"] == {} and not result["authorizes_retry"]
    assert not root.exists()


def test_installed_metadata_change_during_consent_refuses_without_refresh(
    root, monkeypatch
):
    missing_metadata(root, monkeypatch)
    config = root.parent / "selected-global"
    config.write_text(
        "[user]\nname = Chosen diagnostic\nemail = original@example.invalid\n"
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))

    def change():
        config.write_text(
            "[user]\nname = Chosen diagnostic\nemail = changed@example.invalid\n"
        )

    code, output = terminal(
        [*setup_args(root), "--apply"], "initialize create-first", change
    )
    assert code == 2, output
    preview, result = records(output)
    assert result["reason"] == "git_commit_identity_changed_after_confirmation"
    assert result["git_identity"] == preview["git_identity"]
    assert result["stages"] == {} and not root.exists()


def recovery_args(root):
    return ["init", "--profile", "create-first", "--repository-root", root, "--recover"]


def original_failed_fixture(root, monkeypatch):
    """Create real failed retention with installed owners, not injected JSON."""
    missing_metadata(root, monkeypatch)
    script = """
import json, os, sys
from aware_protocol_fs_adapter.project_bootstrap import prepare_planning_project_configuration
from aware_workspace_sdk.repository_preparation import RepositoryPrepareRequest, WorkspaceRepositoryPreparationClient
from aware_workspace_sdk.repository_publication import WorkspaceRepositoryPublicationClient, repository_publication_value_to_payload
root = sys.argv[1]
creator = WorkspaceRepositoryPreparationClient.filesystem(repository_root=root, execution_id='codex-' + os.environ['CODEX_THREAD_ID'])
request = RepositoryPrepareRequest(root, True)
with creator.plan_repository_preparation(request) as plan:
    preparation = creator.prepare_repository(request, admission=creator.admit_repository_preparation(plan))
assert preparation.outcome == 'created'
workspace = WorkspaceRepositoryPublicationClient.filesystem(repository_root=root)
enrollment = workspace.enroll_initial_authoring(creator)
configuration = prepare_planning_project_configuration(repository_root=root)
plan = workspace.plan_initial_configuration(enrollment, configuration, idempotency_key='configuration')
result = workspace.publish_initial_configuration(workspace.admit_initial_configuration(plan))
print(json.dumps(repository_publication_value_to_payload(result), sort_keys=True))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script, str(root)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    print(result.stdout + result.stderr, end="")
    assert result.returncode == 0, result.stderr
    original = json.loads(result.stdout)
    assert original["publication_state"] == "not_published"
    assert "Author identity unknown" in original["original_writer_report"]["error"]
    return original


def test_installed_recovery_preserves_original_failure_without_current_author(
    root, monkeypatch
):
    original = original_failed_fixture(root, monkeypatch)
    before = snapshot(root)
    for _ in range(2):
        code, output = run(*recovery_args(root), "--format", "summary")
        assert code == 0, output
        (result,) = records(output)
        assert result["status"] == "recovered" and result["historical_only"]
        assert not result["completion_verified"] and not result["authorizes_retry"]
        assert not result["authorizes_redispatch"]
        assert result["original_selection"]["recovery"]["original_result"] == original
        assert 'Original publication: "not_published"' in output
        assert snapshot(root) == before
    assert not (root / "aware.protocol.toml").exists()


def test_installed_recovery_published_history_is_not_new_setup_currentness(root):
    original = configure(root)["stages"]["configuration_publication"]
    before = snapshot(root)
    code, output = run(*recovery_args(root))
    assert code == 0, output
    (result,) = records(output)
    assert result["original_selection"]["recovery"]["original_result"] == original
    assert result["recovery_verified"] and not result["completion_verified"]
    assert snapshot(root) == before


def test_installed_recovery_missing_result_stays_uncertain(root, monkeypatch):
    original_failed_fixture(root, monkeypatch)
    (root / ".git/aware-initial-authoring-v1/configuration/result.json").unlink()
    before = snapshot(root)
    code, output = run(*recovery_args(root))
    assert code == 3, output
    (result,) = records(output)
    assert result["status"] == "uncertain" and not result["authorizes_redispatch"]
    assert result["original_selection"]["recovery"]["original_result"] is None
    assert snapshot(root) == before


def test_installed_recovery_foreign_execution_refuses(root, monkeypatch):
    configure(root)
    before = snapshot(root)
    monkeypatch.setenv("CODEX_THREAD_ID", "foreign-installed-reader")
    code, output = run(*recovery_args(root))
    assert code == 2, output
    assert "execution_mismatch" in records(output)[0]["reason"]
    assert snapshot(root) == before


def test_installed_recovery_corruption_refuses_without_repair(root, monkeypatch):
    original_failed_fixture(root, monkeypatch)
    (root / ".git/aware-initial-authoring-v1/configuration/result.json").write_bytes(
        b"corrupt fixture"
    )
    before = snapshot(root)
    code, output = run(*recovery_args(root))
    assert code == 2, output
    assert records(output)[0]["status"] == "refused"
    assert snapshot(root) == before


def test_installed_recovery_busy_attempt_refuses(root):
    import fcntl

    configure(root)
    before = snapshot(root)
    with (root / ".git/aware-initial-authoring-v1/configuration/lock").open(
        "r+b"
    ) as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        code, output = run(*recovery_args(root))
    assert code == 2, output
    assert "attempt_busy" in records(output)[0]["reason"]
    assert snapshot(root) == before


def test_installed_recovery_cannot_select_new_write(root):
    code, _ = run(*recovery_args(root), "--apply")
    assert code == 2 and not root.exists()
    code, output = run(*recovery_args(root), "--create-repository")
    assert code == 2 and not root.exists()
    assert records(output)[0]["reason"] == "recovery_rejects_new_setup_options"


def failed_with_local_attribution(root, monkeypatch):
    """Installed original failure plus explicitly selected test-only metadata."""
    original = original_failed_fixture(root, monkeypatch)
    git(root, "config", "--local", "user.name", "Installed successor diagnostic")
    git(root, "config", "--local", "user.email", "successor@example.invalid")
    return original


def continuation_args(root):
    return [
        "init",
        "--profile",
        "create-first",
        "--repository-root",
        root,
        "--continue-configuration",
    ]


def successor_recovery_args(root):
    return [
        "init",
        "--profile",
        "create-first",
        "--repository-root",
        root,
        "--recover-successor",
    ]


def continue_configuration(root):
    code, output = terminal(
        [*continuation_args(root), "--apply", "--format", "summary"],
        "publish configuration successor",
    )
    assert code == 0, output
    preview, configured = records(output)
    assert preview["status"] == "preview" and configured["status"] == "configured"
    assert configured["successor_plan"] == preview["successor_plan"]
    assert configured["completion_verified"] and not configured["authorizes_retry"]
    assert (
        configured["stages"]["configuration_publication"]["publication_state"]
        == "published"
    )
    assert configured["stages"]["terminal_qualification"]["kind"] == "successor"
    assert 'Original publication: "not_published"' in output
    return configured


def test_installed_successor_preview_never_reserves_or_writes(root, monkeypatch):
    original = failed_with_local_attribution(root, monkeypatch)
    before = snapshot(root)
    code, output = run(*continuation_args(root), "--format", "summary")
    assert code == 0, output
    (value,) = records(output)
    assert value["status"] == "preview"
    assert (
        value["successor_plan"]["request"]["predecessor"]["publication"][
            "original_result"
        ]
        == original
    )
    assert snapshot(root) == before


def test_installed_successor_then_project_goal_membership_and_cold_read(
    root, monkeypatch
):
    original = failed_with_local_attribution(root, monkeypatch)
    old = snapshot(root / ".git/aware-initial-authoring-v1/configuration")
    configured = continue_configuration(root)
    origin = configured["stages"]["terminal_qualification"]
    assert origin["predecessor"]["publication"]["original_result"] == original
    create_project(root)
    goal = create_goal(root)
    before = snapshot(root)
    for family, name in (("goal", "release"), ("project", "home")):
        code, output = run(family, "show", name, *location(root), "--format", "json")
        assert code == 0, output
        reading = records(output)[0]["result"]["reading"]
        assert reading["planning_status"] == "not_yet_decomposed"
        assert reading["goal"]["lifecycle_status"] == "proposed"
        assert (
            reading["goal_creation_publication"]["original_result"]
            == goal["original_result"]
        )
        assert (
            reading["membership_publication"]["original_result"]
            == goal["attachment"]["original_result"]
        )
        assert snapshot(root) == before
    code, output = run(*successor_recovery_args(root))
    assert code == 0, output
    (recovery,) = records(output)
    assert recovery["status"] == "recovered" and not recovery["completion_verified"]
    assert (
        recovery["successor_selection"]["original_result"]
        == configured["stages"]["configuration_publication"]
    )
    assert (
        recovery["successor_selection"]["request"]["predecessor"]["publication"][
            "original_result"
        ]
        == original
    )
    assert snapshot(root) == before
    assert snapshot(root / ".git/aware-initial-authoring-v1/configuration") == old
    assert git(root, "rev-list", "--count", "HEAD").strip() == b"4"
    assert not (root / "docs/issues").exists()
    assert b"Issue-Tag:" not in git(root, "log", "--format=%B")


@pytest.mark.parametrize("phrase", ["initialize create-first", "yes"])
def test_installed_successor_old_confirmation_refuses(root, monkeypatch, phrase):
    failed_with_local_attribution(root, monkeypatch)
    before = snapshot(root)
    code, output = terminal([*continuation_args(root), "--apply"], phrase)
    assert code == 2, output
    assert records(output)[-1]["reason"] == "exact_successor_confirmation_not_given"
    assert snapshot(root) == before


def test_installed_successor_noninteractive_apply_refuses(root, monkeypatch):
    failed_with_local_attribution(root, monkeypatch)
    before = snapshot(root)
    code, output = run(*continuation_args(root), "--apply")
    assert code == 2, output
    assert (
        records(output)[0]["reason"]
        == "noninteractive_apply_requires_original_durable_review_binding"
    )
    assert snapshot(root) == before


def test_installed_successor_changed_source_during_consent_never_refreshes(
    root, monkeypatch
):
    failed_with_local_attribution(root, monkeypatch)

    def change():
        git(root, "config", "--local", "user.name", "Changed during consent")

    code, output = terminal(
        [*continuation_args(root), "--apply"], "publish configuration successor", change
    )
    assert code == 3, output
    result = records(output)[-1]
    assert result["status"] == "uncertain" and not result["completion_verified"]
    assert not result["authorizes_redispatch"]
    assert not (root / ".git/refs/heads/main").exists()
    assert not (root / "aware.protocol.toml").exists()
    assert b"Changed during consent" in (root / ".git/config").read_bytes()


def test_installed_successor_published_attempt_does_not_redispatch(root, monkeypatch):
    failed_with_local_attribution(root, monkeypatch)
    continue_configuration(root)
    before = snapshot(root)
    code, output = run(*continuation_args(root))
    assert code == 2, output
    assert records(output)[-1]["status"] == "refused"
    assert snapshot(root) == before


def test_installed_successor_lost_terminal_result_stays_uncertain(root, monkeypatch):
    failed_with_local_attribution(root, monkeypatch)
    continue_configuration(root)
    # Explicit disposable-fixture retention loss, never supported customer repair.
    (root / ".git/aware-initial-configuration-successor-v1/result.json").unlink()
    before = snapshot(root)
    code, output = run(*successor_recovery_args(root))
    assert code == 3, output
    result = records(output)[0]
    assert result["status"] == "uncertain" and not result["authorizes_redispatch"]
    assert snapshot(root) == before
    code, output = run(*continuation_args(root))
    assert code == 2, output
    assert snapshot(root) == before


def test_installed_successor_recovery_cannot_publish_or_project(root, monkeypatch):
    failed_with_local_attribution(root, monkeypatch)
    configured = continue_configuration(root)
    before = snapshot(root)
    for _ in range(2):
        code, output = run(*successor_recovery_args(root), "--format", "summary")
        assert code == 0, output
        result = records(output)[0]
        assert result["historical_only"] and not result["completion_verified"]
        assert (
            result["successor_selection"]["original_result"]
            == configured["stages"]["configuration_publication"]
        )
        assert snapshot(root) == before
    monkeypatch.setenv("CODEX_THREAD_ID", "foreign-successor-installed-reader")
    code, output = run(*successor_recovery_args(root))
    assert code == 2, output
    assert records(output)[0]["status"] == "refused"
    assert snapshot(root) == before


@pytest.mark.parametrize(
    "flag", ["--apply", "--continue-configuration", "--create-repository"]
)
def test_installed_successor_recovery_rejects_write_modes(root, flag):
    code, _ = run(*successor_recovery_args(root), flag)
    assert code == 2 and not root.exists()
