"""Source CLI composition; real disposable SDK owners, not customer permission."""

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
import test_initial_configuration_successor as original_fixture
from aware_agent_cli.main import main
from aware_workspace_sdk.repository_publication import (
    WorkspaceRepositoryPublicationClient,
    repository_publication_value_to_payload,
)

failed = original_fixture.failed
git = original_fixture.git
snapshot = original_fixture.snapshot


def arguments(root, *more):
    return ["init", "--profile", "create-first", "--repository-root", str(root), *more]


def records(capsys):
    output = capsys.readouterr()
    return [
        json.loads(line) for line in output.out.splitlines() if line.startswith("{")
    ]


def consent(monkeypatch, value="publish configuration successor\n"):
    stream = io.StringIO(value)
    monkeypatch.setattr(stream, "isatty", lambda: True)
    monkeypatch.setattr(sys, "stdin", stream)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    return stream


def test_continuation_preview_is_read_only_and_preserves_original_failure(
    failed, capsys
):
    root, _, _, original, _ = failed
    before = snapshot(root)
    assert main(arguments(root, "--continue-configuration")) == 0
    (value,) = records(capsys)
    assert value["status"] == "preview" and not value["completion_verified"]
    assert value["successor_plan"]["authorizes_publication"] is False
    request = value["successor_plan"]["request"]
    assert request["predecessor"]["publication"][
        "original_result"
    ] == repository_publication_value_to_payload(original)
    assert request["source"]["author"]["name"] == "Successor fixture"
    assert value["stages"] == {}
    assert snapshot(root) == before


def test_continuation_same_plan_applies_once_and_retains_both_results(
    failed, monkeypatch, capsys
):
    root, client, old_admission, original, _ = failed
    old = snapshot(root / ".git/aware-initial-authoring-v1")
    consent(monkeypatch)
    assert main(arguments(root, "--continue-configuration", "--apply")) == 0
    preview, result = records(capsys)
    assert result["status"] == "configured" and result["completion_verified"]
    assert result["successor_plan"] == preview["successor_plan"]
    publication = result["stages"]["configuration_publication"]
    assert publication["publication_state"] == "published"
    origin = result["stages"]["terminal_qualification"]
    assert origin["kind"] == "successor"
    assert origin["predecessor"]["publication"][
        "original_result"
    ] == repository_publication_value_to_payload(original)
    assert origin["effective"]["publication"]["original_result"] == publication
    assert git(root, "rev-parse", "HEAD") == publication["commit_hash"]
    assert git(root, "rev-list", "--count", "HEAD") == "1"
    assert snapshot(root / ".git/aware-initial-authoring-v1") == old
    assert not (root / "docs").exists()
    assert client.publish_initial_configuration(old_admission) == original
    # An ordinary continuation is not an implicit retry/recovery after success.
    before = snapshot(root)
    assert main(arguments(root, "--continue-configuration", "--apply")) == 2
    (refused,) = records(capsys)
    assert refused["status"] == "refused"
    assert snapshot(root) == before


@pytest.mark.parametrize(
    "option",
    [
        "--create-repository",
        "--no-agent-contract",
        "--recover",
        "--recover-successor",
        "--goal-root=elsewhere",
        "--project-root=elsewhere",
        "--issue-root=elsewhere",
    ],
)
def test_conflicting_continuation_options_refuse_before_provider(
    tmp_path, monkeypatch, capsys, option
):
    def forbidden(*a, **kw):
        pytest.fail("conflicting CLI options must refuse before provider construction")

    monkeypatch.setattr(WorkspaceRepositoryPublicationClient, "filesystem", forbidden)
    root = tmp_path / "absent"
    assert main(arguments(root, "--continue-configuration", option)) == 2
    (value,) = records(capsys)
    assert value["reason"] == "configuration_continuation_rejects_new_setup_options"
    assert not root.exists()


@pytest.mark.parametrize("option", ["--continue-configuration", "--recover-successor"])
def test_issue_first_never_falls_back_to_continuation(
    tmp_path, monkeypatch, capsys, option
):
    def forbidden(*a, **kw):
        pytest.fail("Issue-first must not select the continuation provider")

    monkeypatch.setattr(WorkspaceRepositoryPublicationClient, "filesystem", forbidden)
    assert main(["init", "--repository-root", str(tmp_path / "absent"), option]) == 2
    assert "configuration_continuation_requires_create_first" in capsys.readouterr().err


def test_noninteractive_apply_refuses_before_provider(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    def forbidden(*a, **kw):
        pytest.fail("noninteractive apply must refuse before provider construction")

    monkeypatch.setattr(WorkspaceRepositoryPublicationClient, "filesystem", forbidden)
    assert (
        main(arguments(tmp_path / "absent", "--continue-configuration", "--apply")) == 2
    )
    (value,) = records(capsys)
    assert (
        value["reason"]
        == "noninteractive_apply_requires_original_durable_review_binding"
    )


@pytest.mark.parametrize(
    "response",
    ["initialize create-first\n", "yes\n", "", "publish configuration successor \n"],
)
def test_old_or_wrong_confirmation_never_reserves_successor(
    failed, monkeypatch, capsys, response
):
    root, _, _, _, _ = failed
    before = snapshot(root)
    consent(monkeypatch, response)
    assert main(arguments(root, "--continue-configuration", "--apply")) == 2
    _, result = records(capsys)
    assert result["reason"] == "exact_successor_confirmation_not_given"
    assert snapshot(root) == before


def test_changed_source_during_confirmation_is_not_refreshed(
    failed, monkeypatch, capsys
):
    root, _, _, _, _ = failed
    stream = consent(monkeypatch)
    original_read = stream.readline
    original_prepare = (
        WorkspaceRepositoryPublicationClient.prepare_initial_configuration_successor
    )
    prepared = []

    def prepare(self):
        prepared.append(1)
        return original_prepare(self)

    def changed():
        git(root, "config", "--local", "user.name", "Changed during consent")
        return original_read()

    monkeypatch.setattr(
        WorkspaceRepositoryPublicationClient,
        "prepare_initial_configuration_successor",
        prepare,
    )
    monkeypatch.setattr(stream, "readline", changed)
    assert main(arguments(root, "--continue-configuration", "--apply")) == 3
    _, result = records(capsys)
    assert result["status"] == "uncertain" and not result["completion_verified"]
    assert prepared == [1]
    assert not (root / ".git/refs/heads/main").exists()
    assert not (root / "aware.protocol.toml").exists()


def test_projection_exception_preserves_known_successor_and_parent(
    failed, monkeypatch, capsys
):
    root, _, _, original, _ = failed
    consent(monkeypatch)

    def stop(self):
        raise OSError("fixture projection unavailable")

    monkeypatch.setattr(
        WorkspaceRepositoryPublicationClient,
        "project_initial_configuration_successor",
        stop,
    )
    assert main(arguments(root, "--continue-configuration", "--apply")) == 3
    _, result = records(capsys)
    assert (
        result["status"] == "uncertain"
        and result["failed_stage"] == "configuration_projection"
    )
    assert (
        result["stages"]["configuration_publication"]["publication_state"]
        == "published"
    )
    assert result["successor_plan"]["request"]["predecessor"]["publication"][
        "original_result"
    ] == repository_publication_value_to_payload(original)
    assert git(root, "rev-list", "--count", "HEAD") == "1"
    assert not (root / "aware.protocol.toml").exists()


def test_terminal_drift_keeps_receipts_and_never_repairs(failed, monkeypatch, capsys):
    root, _, _, _, _ = failed
    consent(monkeypatch)
    original = WorkspaceRepositoryPublicationClient.observe_initial_configuration_origin

    def drift(self, **kwargs):
        (root / "aware.protocol.toml").write_bytes(b"foreign manifest\n")
        return original(self, **kwargs)

    monkeypatch.setattr(
        WorkspaceRepositoryPublicationClient,
        "observe_initial_configuration_origin",
        drift,
    )
    assert main(arguments(root, "--continue-configuration", "--apply")) == 3
    _, result = records(capsys)
    assert (
        result["status"] == "uncertain"
        and result["failed_stage"] == "terminal_qualification"
    )
    assert (
        result["stages"]["configuration_publication"]["publication_state"]
        == "published"
    )
    assert (root / "aware.protocol.toml").read_bytes() == b"foreign manifest\n"


def test_successor_recovery_returns_original_result_without_writer(
    failed, monkeypatch, capsys
):
    root, client, _, original, _ = failed
    publication = client.publish_initial_configuration_successor(
        client.admit_initial_configuration_successor(
            client.prepare_initial_configuration_successor()
        )
    )
    before = snapshot(root)

    def forbidden(*a, **kw):
        pytest.fail("historical recovery must not prepare/publish/project")

    for name in (
        "prepare_initial_configuration_successor",
        "admit_initial_configuration_successor",
        "publish_initial_configuration_successor",
        "project_initial_configuration_successor",
    ):
        monkeypatch.setattr(WorkspaceRepositoryPublicationClient, name, forbidden)
    assert main(arguments(root, "--recover-successor")) == 0
    (result,) = records(capsys)
    assert result["status"] == "recovered" and not result["completion_verified"]
    assert result["successor_selection"][
        "original_result"
    ] == repository_publication_value_to_payload(publication)
    assert result["successor_selection"]["request"]["predecessor"]["publication"][
        "original_result"
    ] == repository_publication_value_to_payload(original)
    assert not result["authorizes_retry"] and not result["authorizes_redispatch"]
    assert snapshot(root) == before


def test_pending_successor_recovery_remains_uncertain(failed, capsys):
    root, client, _, _, _ = failed
    client.admit_initial_configuration_successor(
        client.prepare_initial_configuration_successor()
    )
    before = snapshot(root)
    assert main(arguments(root, "--recover-successor")) == 3
    (result,) = records(capsys)
    assert result["status"] == "uncertain" and not result["recovery_verified"]
    assert not result["authorizes_redispatch"]
    assert snapshot(root) == before


def test_continuation_uses_same_handle_without_fresh_setup(failed, monkeypatch, capsys):
    root, _, _, _, _ = failed
    from aware_protocol_fs_adapter import project_bootstrap
    from aware_workspace_sdk.repository_preparation import (
        WorkspaceRepositoryPreparationClient,
    )

    consent(monkeypatch)

    def forbidden(*a, **kw):
        pytest.fail(
            "continuation must not recreate preparation/enrollment/Protocol intent"
        )

    for name in (
        "enroll_initial_authoring",
        "plan_initial_configuration",
        "admit_initial_configuration",
        "publish_initial_configuration",
    ):
        monkeypatch.setattr(WorkspaceRepositoryPublicationClient, name, forbidden)
    monkeypatch.setattr(WorkspaceRepositoryPreparationClient, "filesystem", forbidden)
    monkeypatch.setattr(
        project_bootstrap, "prepare_planning_project_configuration", forbidden
    )
    prepare = (
        WorkspaceRepositoryPublicationClient.prepare_initial_configuration_successor
    )
    admit = WorkspaceRepositoryPublicationClient.admit_initial_configuration_successor
    issued = []

    def remember(self):
        plan = prepare(self)
        issued.append(plan)
        return plan

    def same(self, plan):
        assert issued == [plan]
        return admit(self, plan)

    monkeypatch.setattr(
        WorkspaceRepositoryPublicationClient,
        "prepare_initial_configuration_successor",
        remember,
    )
    monkeypatch.setattr(
        WorkspaceRepositoryPublicationClient,
        "admit_initial_configuration_successor",
        same,
    )
    assert main(arguments(root, "--continue-configuration", "--apply")) == 0
    records(capsys)


def test_preview_output_failure_never_reserves_or_publishes(
    failed, monkeypatch, capsys
):
    root, _, _, _, _ = failed
    from aware_agent_cli import initialization

    before = snapshot(root)
    original = initialization._report_init_output

    def report(value, stream):
        return False if stream is sys.stdout else original(value, stream)

    monkeypatch.setattr(initialization, "_report_init_output", report)
    consent(monkeypatch)
    assert main(arguments(root, "--continue-configuration", "--apply")) == 3
    result = json.loads(capsys.readouterr().err)
    assert result["status"] == "preview" and not result["completion_verified"]
    assert snapshot(root) == before


def test_uncertain_nested_projection_retains_complete_publication(
    failed, monkeypatch, capsys
):
    root, _, _, _, _ = failed
    consent(monkeypatch)
    original = (
        WorkspaceRepositoryPublicationClient.project_initial_configuration_successor
    )

    def stopped(self):
        result = original(self)
        return {
            **result,
            "projection_state": "uncertain",
            "original_projection_result": result,
        }

    monkeypatch.setattr(
        WorkspaceRepositoryPublicationClient,
        "project_initial_configuration_successor",
        stopped,
    )
    assert main(arguments(root, "--continue-configuration", "--apply")) == 3
    _, result = records(capsys)
    assert result["status"] == "uncertain"
    publication = result["stages"]["configuration_publication"]
    projection = result["stages"]["configuration_projection"]
    assert projection["original_result"] == publication
    assert projection["original_projection_result"]["original_result"] == publication


def test_successor_recovery_lost_result_is_not_retry_permission(failed, capsys):
    root, client, _, _, _ = failed
    client.publish_initial_configuration_successor(
        client.admit_initial_configuration_successor(
            client.prepare_initial_configuration_successor()
        )
    )
    # Deliberate disposable retention corruption, not a customer operation.
    (root / ".git/aware-initial-configuration-successor-v1/result.json").unlink()
    before = snapshot(root)
    assert main(arguments(root, "--recover-successor")) == 3
    (result,) = records(capsys)
    assert result["status"] == "uncertain"
    assert not result["authorizes_redispatch"]
    assert snapshot(root) == before


def test_successor_recovery_foreign_execution_refuses(failed, monkeypatch, capsys):
    root, client, _, _, _ = failed
    client.admit_initial_configuration_successor(
        client.prepare_initial_configuration_successor()
    )
    before = snapshot(root)
    monkeypatch.setenv("CODEX_THREAD_ID", "foreign-source-fixture")
    assert main(arguments(root, "--recover-successor")) == 2
    (result,) = records(capsys)
    assert result["status"] == "refused" and not result["authorizes_redispatch"]
    assert snapshot(root) == before


def test_summary_discloses_both_outcomes_and_full_json(failed, monkeypatch, capsys):
    root, _, _, _, _ = failed
    consent(monkeypatch)
    assert (
        main(
            arguments(
                root, "--continue-configuration", "--apply", "--format", "summary"
            )
        )
        == 0
    )
    output = capsys.readouterr()
    assert 'Original publication: "not_published"' in output.out
    assert "Selected Git attribution:" in output.out
    assert "Configuration continuation: configured" in output.out
    wires = [
        json.loads(line) for line in output.err.splitlines() if line.startswith("{")
    ]
    assert wires[0]["status"] == "preview" and wires[-1]["status"] == "configured"
    assert (
        wires[-1]["stages"]["configuration_publication"]["publication_state"]
        == "published"
    )


def test_real_terminal_continuation_confirms_fresh_plan(failed):
    root, _, _, _, _ = failed
    master, slave = pty.openpty()
    script = "from aware_agent_cli.main import main; import sys; raise SystemExit(main(sys.argv[1:]))"
    process = subprocess.Popen(
        [
            sys.executable,
            "-B",
            "-c",
            script,
            *arguments(root, "--continue-configuration", "--apply"),
        ],
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
                    assert not (
                        root / ".git/aware-initial-configuration-successor-v1"
                    ).exists()
                    wires = [
                        json.loads(line)
                        for line in output.decode().splitlines()
                        if line.startswith("{")
                    ]
                    assert wires[0]["status"] == "preview"
                    os.write(master, b"publish configuration successor\n")
                    confirmed = True
            elif process.poll() is not None:
                break
        assert confirmed, output.decode(errors="replace")
        assert process.wait(timeout=5) == 0, output.decode(errors="replace")
        wires = [
            json.loads(line)
            for line in output.decode().splitlines()
            if line.startswith("{")
        ]
        assert wires[-1]["status"] == "configured"
        assert git(root, "rev-list", "--count", "HEAD") == "1"
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        os.close(master)


def test_cli_successor_feeds_original_project_goal_membership_reading(
    failed, monkeypatch, capsys
):
    root, _, _, _, _ = failed
    from aware_workflow.goal_customer import InitialGoalCustomerClient
    from aware_workflow.project_customer import InitialProjectCustomerClient

    consent(monkeypatch)
    assert main(arguments(root, "--continue-configuration", "--apply")) == 0
    _, configured = records(capsys)
    project = InitialProjectCustomerClient.filesystem(repository_root=str(root))
    created = project.apply_create(project.prepare_create("garden", title="Garden"))
    assert created["disposition"] == "created"
    assert (
        created["request"]["source"]["configuration_origin"]
        == configured["stages"]["terminal_qualification"]
    )
    goals = InitialGoalCustomerClient(project_client=project)
    result = goals.apply_create(
        goals.prepare_create(
            "first",
            project="garden",
            date="2026-10-19",
            title="First prototype",
            intent="Build a small garden planner.",
        )
    )
    assert result["disposition"] == "created_and_linked"
    reading = goals.show("first", date="2026-10-19")["reading"]
    assert reading["goal"]["lifecycle_status"] == "proposed"
    assert reading["planning_status"] == "not_yet_decomposed"
    assert (
        reading["goal_creation_publication"]["original_result"]
        == result["original_result"]
    )
    assert (
        reading["membership_publication"]["original_result"]
        == result["attachment"]["original_result"]
    )
    assert not (root / "docs/issues").exists()
