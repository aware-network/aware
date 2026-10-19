"""Source composition over real owners; terminal flags are consent unit fixtures.

Not an installed or genuine unassisted customer evaluation. Positive mutations
are confined to disposable customer roots and use original preparation/CAS/FS.
"""

import errno
import io
import json
import os
import pty
import select
import subprocess
import sys
import time

import pytest
from aware_agent_cli.main import main
from aware_workspace_sdk.repository_publication import (
    WorkspaceRepositoryPublicationClient,
)


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "source-create-first-canary")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    for name, value in {
        "GIT_AUTHOR_NAME": "Source canary",
        "GIT_COMMITTER_NAME": "Source canary",
        "GIT_AUTHOR_EMAIL": "canary@example.invalid",
        "GIT_COMMITTER_EMAIL": "canary@example.invalid",
    }.items():
        monkeypatch.setenv(name, value)
    return tmp_path / "customer"


def args(root, *more):
    return [
        "init",
        "--profile",
        "create-first",
        "--repository-root",
        str(root),
        "--create-repository",
        *more,
    ]


def records(capsys):
    output = capsys.readouterr()
    return [
        json.loads(line) for line in output.out.splitlines() if line.startswith("{")
    ]


def consent(monkeypatch, response="initialize create-first\n"):
    stream = io.StringIO(response)
    monkeypatch.setattr(stream, "isatty", lambda: True)
    monkeypatch.setattr(sys, "stdin", stream)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    return stream


def snapshot(root):
    return sorted(
        (str(p.relative_to(root)), p.read_bytes(), p.stat().st_mode)
        for p in root.rglob("*")
        if p.is_file()
    )


def git(root, *values):
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(root), *values],
        check=True,
        capture_output=True,
    ).stdout


def test_preview_uses_original_live_plan_without_creating_anything(root, capsys):
    assert main(args(root)) == 0
    (value,) = records(capsys)
    assert value["status"] == "preview"
    assert value["profile"] == "aware.collaboration.fs_v4"
    assert value["configuration"]["goal_root"] == "docs/goals"
    assert value["preparation_plan"]["request"]["dry_run"] is False
    assert value["stages"] == {}
    assert not root.exists()


def _isolate_missing_git_identity(root, monkeypatch):
    for key in (
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
        "EMAIL",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(root.parent / "absent-author-config"))


@pytest.mark.parametrize("apply", [False, True])
def test_missing_git_identity_refuses_before_confirmation_or_root_creation(
    root, monkeypatch, capsys, apply
):
    _isolate_missing_git_identity(root, monkeypatch)
    if apply:
        consent(monkeypatch)
    assert main(args(root, *(["--apply"] if apply else []))) == 2
    (result,) = records(capsys)
    assert result["status"] == "refused"
    assert result["reason"] == "git_commit_identity_unavailable"
    assert result["git_identity"]["status"] == "unavailable"
    assert not root.exists()


def test_git_identity_change_during_consent_refuses_without_refresh(
    root, monkeypatch, capsys
):
    consent(monkeypatch)
    original = sys.stdin.readline

    def changed(*args):
        monkeypatch.setenv("GIT_AUTHOR_EMAIL", "changed@example.invalid")
        return original(*args)

    monkeypatch.setattr(sys.stdin, "readline", changed)
    assert main(args(root, "--apply")) == 2
    preview, result = records(capsys)
    assert result["reason"] == "git_commit_identity_changed_after_confirmation"
    assert result["git_identity"] == preview["git_identity"]
    assert not root.exists()


def test_recovery_returns_exact_failed_result_without_retry_or_identity_requirement(
    root, monkeypatch, capsys
):
    consent(monkeypatch)
    original_publish = (
        WorkspaceRepositoryPublicationClient.publish_initial_configuration
    )

    def fail_at_original_writer(self, admission):
        _isolate_missing_git_identity(root, monkeypatch)
        return original_publish(self, admission)

    monkeypatch.setattr(
        WorkspaceRepositoryPublicationClient,
        "publish_initial_configuration",
        fail_at_original_writer,
    )
    assert main(args(root, "--apply")) == 3
    _, failed = records(capsys)
    original = failed["stages"]["configuration_publication"]
    assert original["publication_state"] == "not_published"
    before = snapshot(root)

    def forbidden(*a, **k):
        pytest.fail("recovery must not invoke any writer or live preparation")

    monkeypatch.setattr(
        WorkspaceRepositoryPublicationClient, "publish_initial_configuration", forbidden
    )
    monkeypatch.setattr(
        WorkspaceRepositoryPublicationClient, "plan_initial_configuration", forbidden
    )
    monkeypatch.setattr(
        WorkspaceRepositoryPublicationClient, "project_initial_configuration", forbidden
    )
    recovery = [
        "init",
        "--profile",
        "create-first",
        "--repository-root",
        str(root),
        "--recover",
    ]
    assert main(recovery) == 0
    (recovered,) = records(capsys)
    assert recovered["status"] == "recovered" and not recovered["completion_verified"]
    assert recovered["original_selection"]["recovery"]["original_result"] == original
    assert not recovered["authorizes_retry"] and not recovered["authorizes_redispatch"]
    assert snapshot(root) == before
    assert main(recovery) == 0
    assert records(capsys)[0]["original_selection"] == recovered["original_selection"]
    assert snapshot(root) == before
    # New process, exact original failure; diagnostic fixture identity only.
    process = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "import sys; from aware_agent_cli.main import main; raise SystemExit(main(sys.argv[1:]))",
            *recovery,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert process.returncode == 0, process.stderr
    cold = json.loads(process.stdout)
    assert cold["original_selection"] == recovered["original_selection"]
    assert not cold["authorizes_retry"] and not cold["completion_verified"]
    assert snapshot(root) == before


def test_recovery_does_not_claim_currentness_or_create_success(
    root, monkeypatch, capsys
):
    consent(monkeypatch)
    assert main(args(root, "--apply")) == 0
    _, configured = records(capsys)
    before = snapshot(root)
    assert (
        main(
            [
                "init",
                "--profile",
                "create-first",
                "--repository-root",
                str(root),
                "--recover",
            ]
        )
        == 0
    )
    (result,) = records(capsys)
    assert result["status"] == "recovered"
    assert (
        result["original_selection"]["recovery"]["original_result"]
        == configured["stages"]["configuration_publication"]
    )
    assert result["historical_only"] and not result["completion_verified"]
    assert snapshot(root) == before


def test_recovery_missing_terminal_result_remains_uncertain(root, monkeypatch, capsys):
    consent(monkeypatch)
    assert main(args(root, "--apply")) == 0
    records(capsys)
    result = root / ".git/aware-initial-authoring-v1/configuration/result.json"
    result.unlink()  # Disposable loss fixture, never customer cleanup.
    before = snapshot(root)
    assert (
        main(
            [
                "init",
                "--profile",
                "create-first",
                "--repository-root",
                str(root),
                "--recover",
            ]
        )
        == 3
    )
    (value,) = records(capsys)
    assert value["status"] == "uncertain" and not value["authorizes_redispatch"]
    assert value["original_selection"]["recovery"]["original_result"] is None
    assert snapshot(root) == before


def test_recovery_foreign_execution_refuses_without_retention_repair(
    root, monkeypatch, capsys
):
    consent(monkeypatch)
    assert main(args(root, "--apply")) == 0
    records(capsys)
    before = snapshot(root)
    monkeypatch.setenv("CODEX_THREAD_ID", "foreign-recovery-execution")
    assert (
        main(
            [
                "init",
                "--profile",
                "create-first",
                "--repository-root",
                str(root),
                "--recover",
            ]
        )
        == 2
    )
    (result,) = records(capsys)
    assert "execution_mismatch" in result["reason"]
    assert snapshot(root) == before


@pytest.mark.parametrize(
    "extra", [["--apply"], ["--create-repository"], ["--goal-root", "goals"]]
)
def test_recovery_rejects_new_write_options(root, capsys, extra):
    command = [
        "init",
        "--profile",
        "create-first",
        "--repository-root",
        str(root),
        "--recover",
        *extra,
    ]
    if "--apply" in extra:
        with pytest.raises(SystemExit) as error:
            main(command)
        assert error.value.code == 2
    else:
        assert main(command) == 2
    assert not root.exists()


def test_issue_first_recovery_is_not_a_fallback(root, capsys):
    assert main(["init", "--repository-root", str(root), "--recover"]) == 2
    assert "recovery_requires_create_first" in capsys.readouterr().err
    assert not root.exists()


def test_recovery_corrupt_result_refuses_without_repair(root, monkeypatch, capsys):
    consent(monkeypatch)
    assert main(args(root, "--apply")) == 0
    records(capsys)
    result = root / ".git/aware-initial-authoring-v1/configuration/result.json"
    result.write_bytes(b"corrupt retained result")
    before = snapshot(root)
    assert (
        main(
            [
                "init",
                "--profile",
                "create-first",
                "--repository-root",
                str(root),
                "--recover",
            ]
        )
        == 2
    )
    (value,) = records(capsys)
    assert value["status"] == "refused"
    assert snapshot(root) == before


def test_recovery_busy_attempt_refuses_without_permission(root, monkeypatch, capsys):
    import fcntl

    consent(monkeypatch)
    assert main(args(root, "--apply")) == 0
    records(capsys)
    before = snapshot(root)
    lock = root / ".git/aware-initial-authoring-v1/configuration/lock"
    with lock.open("r+b") as retained:
        fcntl.flock(retained, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert (
            main(
                [
                    "init",
                    "--profile",
                    "create-first",
                    "--repository-root",
                    str(root),
                    "--recover",
                ]
            )
            == 2
        )
    (value,) = records(capsys)
    assert "attempt_busy" in value["reason"]
    assert not value["authorizes_redispatch"]
    assert snapshot(root) == before


def test_bootstrap_real_project_goal_membership_and_qualified_show(
    root, monkeypatch, capsys
):
    consent(monkeypatch)
    assert main(args(root, "--apply")) == 0
    preview, configured = records(capsys)
    assert (
        configured["status"] == "configured"
        and configured["completion_verified"] is True
    )
    assert preview["configuration"] == configured["configuration"]
    publication = configured["stages"]["configuration_publication"]
    assert publication["publication_state"] == "published"
    assert (
        configured["stages"]["terminal_qualification"]["original_result"] == publication
    )
    assert (
        configured["stages"]["protocol_admission"]["profile"]
        == "aware.collaboration.fs_v4"
    )
    assert git(root, "rev-list", "--count", "HEAD").strip() == b"1"
    assert not (root / "AGENTS.md").exists()
    location = [
        "--repository-root",
        str(root),
        "--protocol-manifest",
        "aware.protocol.toml",
        "--format",
        "json",
    ]
    consent(monkeypatch, "create home\n")
    assert (
        main(["project", "create", "home", "--title", "Home", *location, "--apply"])
        == 0
    )
    _, project = records(capsys)
    assert project["result"]["disposition"] == "created"
    consent(monkeypatch, "create release\n")
    assert (
        main(
            [
                "goal",
                "create",
                "release",
                "--project",
                "home",
                "--title",
                "Release",
                "--intent",
                "A useful release",
                "--date",
                "2026-10-18",
                *location,
                "--apply",
            ]
        )
        == 0
    )
    _, goal = records(capsys)
    assert goal["result"]["disposition"] == "created_and_linked"
    assert goal["result"]["original_result"]
    assert goal["result"]["attachment"]["original_result"]
    before = snapshot(root)
    assert main(["project", "show", "home", *location]) == 0
    records(capsys)
    assert main(["goal", "show", "release", *location]) == 0
    (shown,) = records(capsys)
    assert "not_yet_decomposed" in json.dumps(shown)
    assert snapshot(root) == before
    assert git(root, "rev-list", "--count", "HEAD").strip() == b"4"
    assert not (root / "docs/issues").exists()
    assert b"Issue-Tag:" not in git(root, "log", "--format=%B")


@pytest.mark.parametrize("response", ["", "yes\n", "initialize another\n"])
def test_cancel_has_no_effect(root, monkeypatch, capsys, response):
    consent(monkeypatch, response)
    assert main(args(root, "--apply")) == 2
    _, result = records(capsys)
    assert result["reason"] == "exact_plan_confirmation_not_given"
    assert result["stages"] == {}
    assert not root.exists()


def test_noninteractive_apply_refuses_before_preparation(root, capsys):
    assert main(args(root, "--apply")) == 2
    (value,) = records(capsys)
    assert (
        value["reason"]
        == "noninteractive_apply_requires_original_durable_review_binding"
    )
    assert not root.exists()


def test_missing_optional_registrar_refuses_before_preparation(
    root, monkeypatch, capsys
):
    from aware_agent_cli import main as entry

    original = entry.importlib.import_module

    def imports(name):
        if name == "aware_goal_native_cli.customer_commands":
            raise ImportError("missing optional qualified Goal supplier")
        return original(name)

    monkeypatch.setattr(entry.importlib, "import_module", imports)
    assert main(args(root)) == 2
    (value,) = records(capsys)
    assert "missing optional" in value["reason"]
    assert not root.exists()


def test_source_drift_after_preview_does_not_refresh_repair_or_publish(
    root, monkeypatch, capsys
):
    stream = consent(monkeypatch)

    def changed():
        root.mkdir()
        (root / "foreign").write_bytes(b"keep")
        return "initialize create-first\n"

    monkeypatch.setattr(stream, "readline", changed)
    assert main(args(root, "--apply")) == 2
    _, value = records(capsys)
    assert value["status"] == "refused"
    assert value["reason"] == "git_identity_repository_source_refused"
    assert value["stages"] == {}  # Earlier observation now refuses before dispatch.
    assert value["authorizes_retry"] is False
    assert not (root / ".git").exists()
    assert (root / "foreign").read_bytes() == b"keep"


def test_projection_failure_preserves_original_publication_and_never_retries(
    root, monkeypatch, capsys
):
    consent(monkeypatch)
    calls = []

    def unavailable(*a, **k):
        calls.append(1)
        raise ValueError("injected_projection_unavailable")

    monkeypatch.setattr(
        WorkspaceRepositoryPublicationClient,
        "project_initial_configuration",
        unavailable,
    )
    assert main(args(root, "--apply")) == 3
    _, result = records(capsys)
    assert result["status"] == "uncertain"
    assert result["failed_stage"] == "configuration_projection"
    assert (
        result["stages"]["configuration_publication"]["commit_hash"].encode()
        == git(root, "rev-parse", "HEAD").strip()
    )
    assert calls == [1]
    assert not (root / "aware.protocol.toml").exists()
    assert result["authorizes_redispatch"] is False


def test_final_manifest_drift_is_uncertain_with_original_receipt_retained(
    root, monkeypatch, capsys
):
    from aware_protocol_fs_adapter import project_resolver

    original = project_resolver.require_project_resolver

    def changed(capability):
        result = original(capability)
        (root / "aware.protocol.toml").write_bytes(b"foreign manifest\n")
        return result

    monkeypatch.setattr(project_resolver, "require_project_resolver", changed)
    consent(monkeypatch)
    assert main(args(root, "--apply")) == 3
    _, result = records(capsys)
    assert result["status"] == "uncertain"
    assert result["failed_stage"] == "terminal_qualification"
    assert (
        result["stages"]["configuration_publication"]["publication_state"]
        == "published"
    )
    assert (root / "aware.protocol.toml").read_bytes() == b"foreign manifest\n"


@pytest.mark.parametrize("format", ["json", "summary"])
def test_output_failure_never_dispatches_and_preserves_evidence_on_remaining_channel(
    root, monkeypatch, capsys, format
):
    from aware_agent_cli import initialization

    original = initialization._report_init_output
    calls = []

    def report(value, stream):
        calls.append("stdout" if stream is sys.stdout else "stderr")
        return False if stream is sys.stdout else original(value, stream)

    monkeypatch.setattr(initialization, "_report_init_output", report)
    consent(monkeypatch)
    assert main(args(root, "--apply", "--format", format)) == 3
    value = json.loads(capsys.readouterr().err)
    assert value["status"] == "preview"
    assert value["configuration"]["content_utf8"]
    assert calls == ["stdout", "stderr"]
    assert not root.exists()


def test_existing_configured_root_is_not_reenrolled_or_redispatched(
    root, monkeypatch, capsys
):
    consent(monkeypatch)
    assert main(args(root, "--apply")) == 0
    records(capsys)
    before = snapshot(root)
    assert main(args(root, "--apply")) == 2
    (value,) = records(capsys)
    assert value["status"] == "refused"
    assert snapshot(root) == before


def test_custom_roots_come_from_original_protocol_and_are_committed(
    root, monkeypatch, capsys
):
    consent(monkeypatch)
    assert (
        main(
            args(
                root,
                "--apply",
                "--goal-root",
                "customer/goals",
                "--project-root",
                "customer/projects",
                "--issue-root",
                "customer/issues",
            )
        )
        == 0
    )
    _, value = records(capsys)
    assert value["configuration"]["goal_root"] == "customer/goals"
    assert 'root = "customer/projects"' in (root / "aware.protocol.toml").read_text()
    assert not (root / "customer").exists()


@pytest.mark.parametrize(
    "extra", [["--no-agent-contract"], ["--goal-root", "docs/projects/nested"]]
)
def test_invalid_setup_does_not_prepare(root, extra, capsys):
    assert main(args(root, *extra)) == 2
    (value,) = records(capsys)
    assert value["stages"] == {}
    assert not root.exists()


def test_issue_first_refuses_planning_only_flags_without_upgrading(root, capsys):
    assert main(["init", "--repository-root", str(root), "--goal-root", "goals"]) == 2
    assert "planning_roots_require_create_first" in capsys.readouterr().err
    assert not root.exists()


def test_create_first_requires_separate_repository_creation_intent(root, capsys):
    assert (
        main(["init", "--profile", "create-first", "--repository-root", str(root)]) == 2
    )
    (value,) = records(capsys)
    assert value["reason"] == "create_first_requires_explicit_create_repository"
    assert not root.exists()


@pytest.mark.parametrize(
    "family,registrar",
    [
        ("project", "register_project_commands"),
        ("goal", "register_create_first_goal_commands"),
    ],
)
def test_mounts_exact_original_handlers(family, registrar):
    from aware_agent_cli.main import register_family_commands
    from aware_command_runtime import AwareCommandRegistry
    from aware_goal_native_cli import customer_commands

    mounted, original = AwareCommandRegistry(), AwareCommandRegistry()
    register_family_commands(mounted, family)
    getattr(customer_commands, registrar)(original)
    assert mounted.names() == original.names()
    assert [(c.name, c.handle, c.operation_ref) for c in mounted] == [
        (c.name, c.handle, c.operation_ref) for c in original
    ]


def test_real_terminal_setup_confirms_only_after_the_original_live_preview(root):
    """Genuine subprocess/PTY, still source-backed and deliberately assisted."""
    master, slave = pty.openpty()
    script = "from aware_agent_cli.main import main; import sys; raise SystemExit(main(sys.argv[1:]))"
    process = subprocess.Popen(
        [sys.executable, "-B", "-c", script, *args(root, "--apply")],
        stdin=slave,
        stdout=slave,
        stderr=slave,
    )
    os.close(slave)
    output = bytearray()
    confirmed = False
    deadline = time.monotonic() + 45
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
                    assert not root.exists()
                    wire = [
                        json.loads(line)
                        for line in output.decode().splitlines()
                        if line.startswith("{")
                    ]
                    assert wire[0]["status"] == "preview"
                    assert wire[0]["configuration"]["content_utf8"].startswith(
                        "aware = 1"
                    )
                    os.write(master, b"initialize create-first\n")
                    confirmed = True
            elif process.poll() is not None:
                break
        assert confirmed, output.decode(errors="replace")
        assert process.wait(timeout=5) == 0, output.decode(errors="replace")
        wire = [
            json.loads(line)
            for line in output.decode().splitlines()
            if line.startswith("{")
        ]
        assert wire[-1]["status"] == "configured"
        assert (
            wire[-1]["stages"]["configuration_publication"]["commit_hash"].encode()
            == git(root, "rev-parse", "HEAD").strip()
        )
        assert not (root / "docs/issues").exists()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        os.close(master)
