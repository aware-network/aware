"""Actual owner composition and CLI carriage, not mock authorization."""

import importlib
import importlib.util
import json
import os
from pathlib import Path

import pytest
from aware_command_runtime import AwareCommandRegistry, build_parser
from aware_file_system import retained_package as physical
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_protocol_fs_adapter import specification_draft_target as target_owner
from aware_specification_cli import draft_commands as command
from aware_specification_cli.main import main
from aware_specification_runtime import (
    SpecificationSnapshot,
    encode_specification_snapshot,
)
from aware_specification_sdk import SpecificationOperationError, SpecificationSdkClient


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "cli_draft_original_fixture",
        Path(__file__).parents[2] / "fs_adapter/tests/test_governed_draft.py",
    )
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    source = fixture.context.__wrapped__(tmp_path, monkeypatch)
    root, manifest, issue, kwargs = next(source)
    body = encode_specification_snapshot(
        SpecificationSnapshot((kwargs["request"].definition,))
    )
    request_path = root / "customer-input.json"
    request_path.write_bytes(body)
    args = [
        "create-draft",
        "--repository-root",
        str(root),
        "--protocol-manifest",
        "configuration/team/aware.protocol.toml",
        "--spec-manifest",
        "customer/specs/widget/aware.spec.toml",
        "--snapshot-json",
        str(request_path),
        "--author-ref",
        kwargs["request"].author_ref,
        "--authoring-intent-ref",
        kwargs["request"].authoring_intent_ref,
        "--client-intent-id",
        "cli-source-attempt",
        "--issue-ref",
        kwargs["issue_ref"],
        "--expected-issue-sha256",
        fixture.digest(issue.read_bytes()),
        "--expected-manifest-sha256",
        fixture.digest(manifest.read_bytes()),
        "--expected-input-sha256",
        fixture.digest(body),
    ]
    yield root, manifest, issue, request_path, args
    monkeypatch.undo()  # Restore faults before test-only original-holder disposal.
    with pytest.raises(StopIteration):
        next(source)


def run(args, capsys, *, exit_code=2):
    assert main(args) == exit_code
    streams = capsys.readouterr()
    assert streams.err == ""
    return json.loads(streams.out)


def bodies(root):
    return {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }


def test_registration_has_no_supplier_import_or_effect(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("registration reached an integration import or source IO")

    registry = AwareCommandRegistry()
    monkeypatch.setattr(importlib, "import_module", forbidden)
    monkeypatch.setattr(os, "open", forbidden)
    command.register_draft_commands(registry)
    build_parser(registry, prog="test")
    assert registry.names() == ("create-draft",)
    assert (
        registry.require("create-draft").operation_ref
        == "specification_sdk.create_draft"
    )


@pytest.mark.parametrize("apply", [False, True])
def test_real_preview_and_creation_complete_only_after_original_context_exit(
    inputs, capsys, apply
):
    root, _, _, _, args = inputs
    before = bodies(root)
    fds = set(os.listdir("/proc/self/fd"))
    result = run(args + (["--apply"] if apply else []), capsys, exit_code=0)
    assert "error" not in result
    assert result["effect"] == ("published" if apply else "none")
    assert result["operation_outcome"] == ("published" if apply else "previewed")
    assert result["consumer_completion_verified"] is True
    cleanup = result["cleanup_evidence"]
    assert cleanup["context_state"] == "closed"
    assert cleanup["protocol_owner_attempted"] is True
    assert cleanup["protocol_owner_outcome"] == "completed"
    assert cleanup["protocol_invocation"]["invocation_state"] == "returned"
    assert result["caller_cleanup"] == {}
    assert bodies(root).items() >= before.items()
    assert set(os.listdir("/proc/self/fd")) == fds
    if apply:
        assert len(result["created_paths"]) == 6
        assert result["evidence"]["package_outcome"] == "published"
        assert result["observation"]["snapshot"]["definitions"][0]["key"] == "widget"
        assert not list((root / "customer/specs").glob(".aware-spec-draft-*"))
        assert not result["observation"]["iterations"]
    else:
        assert bodies(root) == before


def test_preclaim_refusal_cleans_through_original_custody(inputs, capsys):
    root, _, _, _, args = inputs
    before = bodies(root)
    args[args.index("--expected-issue-sha256") + 1] = "sha256:" + "a" * 64
    result = run(args, capsys)
    cleanup = result["cleanup_evidence"]
    assert cleanup["issue_disposition"]["physical_claim"] == "unclaimed"
    assert cleanup["physical_invocation"]["responsibility"] == "context"
    assert cleanup["input_custody"]["physical"]["owner_cleanup_outcome"] == "completed"
    assert cleanup["input_custody"]["protocol"]["owner_cleanup_outcome"] == "completed"
    assert result["caller_cleanup"] == {}
    assert bodies(root) == before


def test_manifest_refusal_before_issue_issuance_releases_original_inputs_once(
    inputs, capsys, monkeypatch
):
    root, manifest, _, _, args = inputs
    spec = importlib.import_module("aware_specification_fs_sdk_adapter")
    protocol = target_owner
    original_factory = spec.open_governed_specification_draft
    original_physical_release = physical.release_package_input
    original_target_release = protocol.release_specification_draft_input
    retained = {}
    calls = []

    def factory(**kwargs):
        # Retain the CLI-created originals solely for post-refusal inspection.
        retained["plan"] = kwargs["physical_package_plan"]
        retained["target"] = kwargs["protocol_draft_target"]
        retained["custody"] = kwargs["input_custody"]
        manager = original_factory(**kwargs)
        manifest.write_bytes(manifest.read_bytes() + b"# before context entry\n")
        return manager

    def release(value):
        calls.append("physical")
        return original_physical_release(value)

    def target_release(value):
        calls.append("protocol")
        return original_target_release(value)

    monkeypatch.setattr(spec, "open_governed_specification_draft", factory)
    monkeypatch.setattr(physical, "release_package_input", release)
    monkeypatch.setattr(protocol, "release_specification_draft_input", target_release)
    descriptors = set(os.listdir("/proc/self/fd"))
    try:
        result = run(args, capsys)
        assert result["error"] == "manifest_source_sha256_mismatch"
        assert (
            result["cleanup_evidence"]["issue_disposition"]["physical_claim"]
            == "claimed"
        )
        assert result["cleanup_evidence"]["input_custody"]["context_ref"]
        observation = physical.observe_package_cleanup(retained["plan"])
        assert observation.attempted is True
        assert observation.outcome == "completed"
        # Successor Issue transfers responsibility before freshness validation.
        assert calls == ["physical", "protocol"]
        assert set(os.listdir("/proc/self/fd")) == descriptors
        assert not (root / "customer/specs/widget").exists()
    finally:
        # Original context has disposed both holders; no raw retry of custody.
        assert set(os.listdir("/proc/self/fd")) == descriptors


@pytest.mark.parametrize("interrupted", [False, True])
def test_claimed_failed_issuance_never_retries_physical_release(
    inputs, capsys, monkeypatch, interrupted
):
    root, _, _, _, args = inputs
    calls = []
    claims = []
    original = physical.release_package_input

    def release(value):
        calls.append("physical")
        claims.append(value)
        if interrupted:
            raise KeyboardInterrupt("before original release body")
        return original(value)

    def fail(*args, **kwargs):
        raise OSError("original binding failure")

    monkeypatch.setattr(physical, "release_package_input", release)
    monkeypatch.setattr(target_owner, "bind_specification_draft_physical_plan", fail)
    result = run(args, capsys)
    disposition = result["cleanup_evidence"]["issue_disposition"]
    assert disposition["physical_claim"] == "claimed"
    assert disposition["physical_cleanup_attempted"] is True
    assert calls == ["physical"]
    assert "physical" not in result["caller_cleanup"]
    assert not (root / "customer/specs/widget").exists()
    if interrupted:
        assert disposition["physical_cleanup_outcome"] == "unknown"
        assert result["effect"] == "unknown"
        # Test-only owner disposal after an injected pre-body interruption. The
        # product correctly reports unknown and never retries the attempted call.
        original(claims[0])


def test_returned_admission_then_entry_refusal_releases_each_once(
    inputs, capsys, monkeypatch
):
    _, _, _, _, args = inputs
    calls = []
    protocol = target_owner
    original_release = physical.release_package_input
    original_target = protocol.release_specification_draft_input

    def release(value):
        calls.append("physical")
        return original_release(value)

    def target(value):
        calls.append("target")
        return original_target(value)

    def refuse(*args, **kwargs):
        raise OSError("after genuine admission returned")

    monkeypatch.setattr(physical, "release_package_input", release)
    monkeypatch.setattr(protocol, "release_specification_draft_input", target)
    monkeypatch.setattr(
        FilesystemIssueOperationProvider, "validate_draft_package", refuse
    )
    result = run(args, capsys)
    assert calls == ["physical", "target"]
    assert result["caller_cleanup"] == {}
    assert (
        result["cleanup_evidence"]["physical_invocation"]["responsibility"] == "context"
    )


def test_late_exit_refusal_preserves_actual_publication(inputs, capsys, monkeypatch):
    root, manifest, _, _, args = inputs
    original = SpecificationSdkClient.create_draft

    def publish(client, request):
        result = original(client, request)
        manifest.write_bytes(manifest.read_bytes() + b"# late change\n")
        return result

    monkeypatch.setattr(SpecificationSdkClient, "create_draft", publish)
    result = run(args + ["--apply"], capsys)
    assert result["error"] != "draft_cleanup_completion_unverified"
    assert result["effect"] == "published"
    assert result["evidence"]["package_outcome"] == "published"
    assert (root / "customer/specs/widget/aware.spec.toml").is_file()
    assert result["cleanup_evidence"]["protocol_owner_outcome"] == "completed"


def test_secondary_cleanup_observer_failure_does_not_mask_primary(
    inputs, capsys, monkeypatch
):
    _, _, _, _, args = inputs
    original_factory = importlib.import_module(
        "aware_specification_fs_sdk_adapter"
    ).open_governed_specification_draft
    spec = importlib.import_module("aware_specification_fs_sdk_adapter")

    def factory(**kwargs):
        context = original_factory(**kwargs)

        class ObserverFault:
            # Interpose the public CLI observer only, not owner internals.
            def __enter__(self):
                return context.__enter__()

            def __exit__(self, *args):
                return context.__exit__(*args)

            def observe_draft_cleanup(self):
                raise RuntimeError("secondary observer failure")

        return ObserverFault()

    monkeypatch.setattr(spec, "open_governed_specification_draft", factory)
    args[args.index("--expected-issue-sha256") + 1] = "sha256:" + "f" * 64
    result = run(args, capsys)
    assert result["error"] == "issue_source_sha256_mismatch"
    assert (
        "cli_cleanup_observation_failed:RuntimeError" in result["cleanup_diagnostics"]
    )


def test_combined_original_stage_and_cleanup_faults_keep_ordered_evidence(
    inputs, capsys, monkeypatch
):
    from aware_specification_fs_sdk_adapter import SpecificationFsSdkProvider

    root, _, _, _, args = inputs
    protocol = target_owner
    original_close = SpecificationFsSdkProvider.close
    original_target = protocol.release_specification_draft_input
    calls = []

    def invalid(self, request):
        raise SpecificationOperationError("strict_stage_primary")

    def close(self):
        calls.append("reader")
        original_close(self)
        raise OSError("reader close fault")

    def target_close(target):
        calls.append("target")
        original_target(target)
        raise OSError("target close fault")

    monkeypatch.setattr(SpecificationFsSdkProvider, "_observe_adaptation", invalid)
    monkeypatch.setattr(SpecificationFsSdkProvider, "close", close)
    monkeypatch.setattr(protocol, "release_specification_draft_input", target_close)
    result = run(args + ["--apply"], capsys)
    assert result["error"] == "strict_stage_primary"
    assert result["effect"] == "unknown"
    assert calls == ["reader", "target"]
    assert result["caller_cleanup"] == {}
    cleanup = result["cleanup_evidence"]
    assert "staged_reader_close_failed:OSError" in cleanup["cleanup_diagnostics"]
    assert cleanup["input_custody"]["physical_evidence"]["effects"]
    assert "protocol_release_failed:OSError" in cleanup["input_custody"]["diagnostics"]
    assert cleanup["protocol_invocation"]["invocation_state"] == "raised"
    assert not (root / "customer/specs/widget").exists()


def test_retirement_fault_is_not_erased_by_normal_later_protocol_release(
    inputs, capsys, monkeypatch
):
    root, manifest, _, _, args = inputs
    original_create = SpecificationSdkClient.create_draft
    original_release = target_owner._release_owned_selection
    retained = []

    def fail(selection):
        retained.append(selection)
        raise OSError("retirement cleanup fault")

    def create(client, request):
        monkeypatch.setattr(target_owner, "_release_owned_selection", fail)
        manifest.write_bytes(manifest.read_bytes() + b"# stale after admission\n")
        return original_create(client, request)

    monkeypatch.setattr(SpecificationSdkClient, "create_draft", create)
    try:
        result = run(args + ["--apply"], capsys)
        cleanup = result["cleanup_evidence"]
        assert len(retained) == 1
        assert "draft_target_cleanup_failed:OSError" in cleanup["cleanup_diagnostics"]
        assert cleanup["protocol_invocation"]["invocation_state"] == "returned"
        assert cleanup["protocol_owner_outcome"] == "incomplete"
        assert result["consumer_completion_verified"] is False
        assert not (root / "customer/specs/widget").exists()
    finally:
        monkeypatch.setattr(target_owner, "_release_owned_selection", original_release)
        for selection in retained:
            original_release(selection)  # Test-only disposal, never product recovery.


@pytest.mark.parametrize("exception", [KeyboardInterrupt, SystemExit])
def test_interrupt_preserves_termination_after_genuine_context_cleanup(
    inputs, capsys, monkeypatch, exception
):
    root, _, _, _, args = inputs
    before = bodies(root)
    fds = set(os.listdir("/proc/self/fd"))

    def interrupted(client, request):
        raise exception("caller interrupted before original write")

    monkeypatch.setattr(SpecificationSdkClient, "create_draft", interrupted)
    with pytest.raises(exception):
        main(args + ["--apply"])
    streams = capsys.readouterr()
    assert streams.out == ""
    result = json.loads(streams.err)
    assert result["effect"] == "none"
    assert result["cleanup_evidence"]["context_state"] == "closed"
    assert result["cleanup_evidence"]["protocol_owner_outcome"] == "completed"
    assert result["caller_cleanup"] == {}
    assert bodies(root) == before
    assert set(os.listdir("/proc/self/fd")) == fds


def test_json_carriage_keeps_request_bytes_and_ledger_completeness(inputs, capsys):
    _, _, _, _, args = inputs
    result = run(args, capsys, exit_code=0)
    cleanup = result["cleanup_evidence"]
    disposition = cleanup["issue_disposition"]
    exact_members = disposition["request"]["ordered_members"]
    assert len(exact_members) == len(result["members"]) == 6
    for (path, encoded), member in zip(exact_members, result["members"], strict=True):
        value = bytes.fromhex(encoded["body"])
        assert encoded["encoding"] == "hex"
        assert path == member["path"]
        assert len(value) == member["bytes"]
        import hashlib

        assert "sha256:" + hashlib.sha256(value).hexdigest() == member["sha256"]
    assert disposition["evidence"]["ledger_complete"] is True
    assert cleanup["physical_observation"]["evidence"]["ledger_complete"] is None
    assert disposition["execution_ref"] == "codex-spec-governed-real-source-proof"


def test_public_input_recipe_roundtrips_through_original_codec_and_renderer():
    from aware_specification_fs_sdk_adapter import render_specification_draft
    from aware_specification_runtime import decode_specification_snapshot
    from aware_specification_sdk import SpecificationDraftRequest

    location = Path(__file__).parents[1] / "examples/prepare_draft_input.py"
    spec = importlib.util.spec_from_file_location("cli_public_input_recipe", location)
    example = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(example)
    body = example.prepare()
    snapshot = decode_specification_snapshot(body)
    assert encode_specification_snapshot(snapshot) == body
    assert len(snapshot.definitions) == 1
    request = SpecificationDraftRequest(snapshot.definitions[0], "customer", "intent:1")
    assert len(render_specification_draft(request)) == 6


@pytest.mark.parametrize(
    "mode",
    ["symlink", "fifo", "too-large", "newline", "wrong-digest", "apply-no-digest"],
)
def test_input_refusals_do_not_create_any_draft(inputs, capsys, mode):
    root, _, _, source, args = inputs
    if mode == "symlink":
        link = root / "input-link"
        link.symlink_to(source)
        args[args.index("--snapshot-json") + 1] = str(link)
    elif mode == "fifo":
        fifo = root / "input-fifo"
        os.mkfifo(fifo)
        args[args.index("--snapshot-json") + 1] = str(fifo)
    elif mode == "too-large":
        source.write_bytes(b"x" * (command.INPUT_LIMIT + 1))
    elif mode == "newline":
        source.write_bytes(source.read_bytes() + b"\n")
        args = args[: args.index("--expected-input-sha256")]
    elif mode == "wrong-digest":
        args[args.index("--expected-input-sha256") + 1] = "sha256:" + "a" * 64
    else:
        args = args[: args.index("--expected-input-sha256")] + ["--apply"]
    result = run(args, capsys)
    assert result["effect"] == "none"
    assert not (root / "customer/specs/widget").exists()
    assert result["cleanup_evidence"] is None


def test_exact_input_limit_and_changed_file_observation(tmp_path, monkeypatch):
    source = tmp_path / "input"
    source.write_bytes(b"x" * command.INPUT_LIMIT)
    assert len(command.read_draft_input(source)) == command.INPUT_LIMIT
    original = os.read

    def read(fd, count):
        result = original(fd, count)
        if result:
            source.write_bytes(b"y" * command.INPUT_LIMIT)
        return result

    monkeypatch.setattr(os, "read", read)
    with pytest.raises(command.DraftInputError, match="draft_input_changed"):
        command.read_draft_input(source)


def test_missing_governed_supplier_is_typed_without_compatibility_fallback(
    inputs, capsys, monkeypatch
):
    _, _, _, _, args = inputs
    original = importlib.import_module

    def unavailable(name, *args, **kwargs):
        if name == "aware_file_system.retained_package":
            raise ImportError("governed supplier absent")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", unavailable)
    result = run(args, capsys)
    assert result["error"] == "governed_draft_integration_unavailable"
    assert result["effect"] == "none"


def repository_descriptors(root):
    result = set()
    for name in os.listdir("/proc/self/fd"):
        try:
            path = os.readlink("/proc/self/fd/" + name)
        except FileNotFoundError:
            continue
        if path == str(root) or path.startswith(str(root) + "/"):
            result.add((name, path))
    return result


@pytest.mark.parametrize("boundary", ["before_factory", "constructor", "context_claim"])
def test_factory_failures_dispose_original_custody_without_raw_retry(
    inputs, capsys, monkeypatch, boundary
):
    from aware_issue_fs_adapter import draft_package as issue_owner

    root, _, _, _, args = inputs
    spec = importlib.import_module("aware_specification_fs_sdk_adapter")
    original = spec.open_governed_specification_draft
    retained = {}
    raw_calls = []
    before = repository_descriptors(root)

    def factory(**kwargs):
        retained["custody"] = kwargs["input_custody"]
        if boundary == "before_factory":
            raise OSError("fault before original SPEC association")
        if boundary == "constructor":
            kwargs["request"] = object()  # Original semantic validator refuses.
        return original(**kwargs)

    def fail(*args, **kwargs):
        raise SystemExit("genuine context-claim issuance failed")

    def raw(*args, **kwargs):
        raw_calls.append(True)
        pytest.fail("CLI retried a raw custody-owned resource")

    if boundary == "context_claim":
        monkeypatch.setattr(issue_owner, "finalize", fail)
        # Allow genuine initial custody issuance; fault only its context claim.
        initial = FilesystemIssueOperationProvider.retain_draft_inputs

        def acquire(provider, **kwargs):
            monkeypatch.setattr(issue_owner, "finalize", original_finalizer)
            guard = initial(provider, **kwargs)
            monkeypatch.setattr(issue_owner, "finalize", fail)
            return guard

        original_finalizer = importlib.import_module("weakref").finalize
        monkeypatch.setattr(
            FilesystemIssueOperationProvider, "retain_draft_inputs", acquire
        )
    monkeypatch.setattr(spec, "open_governed_specification_draft", factory)
    monkeypatch.setattr(physical.RetainedPackagePublication, "release", raw)
    monkeypatch.setattr(
        importlib.import_module("aware_protocol_fs_adapter"),
        "release_specification_draft_target",
        raw,
    )
    result = run(args, capsys)
    observed = retained["custody"].observe_cleanup()
    assert observed.physical.owner_cleanup_outcome == "completed"
    assert observed.protocol.owner_cleanup_outcome == "completed"
    assert result["input_custody"]["attempt_ref"] == observed.attempt_ref
    assert result["effect"] == ("none" if boundary == "before_factory" else "unknown")
    assert not raw_calls
    assert repository_descriptors(root) == before
    assert not (root / "customer/specs/widget").exists()


@pytest.mark.parametrize("owner", ["issue", "protocol", "physical"])
def test_failed_original_issuance_retains_partial_custody_and_restores_descriptors(
    inputs, capsys, monkeypatch, owner
):
    from aware_issue_fs_adapter import draft_package as issue_owner

    root, _, _, _, args = inputs
    original_release = physical.release_package_input
    original_acquire = FilesystemIssueOperationProvider.retain_draft_inputs
    calls = []
    before = repository_descriptors(root)

    def release(value):
        calls.append(value)
        return original_release(value)

    def fail(*args, **kwargs):
        raise KeyboardInterrupt("original issuer cannot return its handle")

    monkeypatch.setattr(physical, "release_package_input", release)

    def acquire(provider, **kwargs):
        monkeypatch.setattr(
            {"issue": issue_owner, "protocol": target_owner, "physical": physical}[
                owner
            ],
            "finalize",
            fail,
        )
        return original_acquire(provider, **kwargs)

    monkeypatch.setattr(
        FilesystemIssueOperationProvider, "retain_draft_inputs", acquire
    )
    result = run(args, capsys)
    assert result["error"] == "issue_input_reservation_failed"
    assert result["cleanup_evidence"] is None
    assert result["input_custody"] is not None
    assert result["input_custody"]["physical"]["owner_cleanup_outcome"] == "completed"
    assert len(calls) <= 1  # Partial lower issuance already owns disposal.
    assert repository_descriptors(root) == before
    assert not (root / "customer/specs/widget").exists()


@pytest.mark.parametrize("boundary", ["before_reservation", "before_disposal"])
def test_competing_original_custody_survives_cli_guarded_fallback(
    inputs, capsys, monkeypatch, boundary
):
    root, _, _, _, args = inputs
    initial = FilesystemIssueOperationProvider.retain_draft_inputs
    held = {}
    original_release = physical.RetainedPackagePublication.release

    def acquire(provider, **kwargs):
        held.update(provider=provider, kwargs=kwargs)
        if boundary == "before_reservation":
            held["guard"] = initial(provider, **kwargs)
            held["before"] = held["guard"].observe_cleanup()
            held["descriptors"] = repository_descriptors(root)
            return initial(provider, **{**kwargs, "attempt_ref": "competing:attempt"})
        raise OSError("CLI acquisition failed before reserving original holders")

    def release(plan, **kwargs):
        if "guard" not in held:
            held["guard"] = initial(held["provider"], **held["kwargs"])
            held["before"] = held["guard"].observe_cleanup()
            held["descriptors"] = repository_descriptors(root)
        return original_release(plan, **kwargs)

    monkeypatch.setattr(
        FilesystemIssueOperationProvider, "retain_draft_inputs", acquire
    )
    if boundary == "before_disposal":
        monkeypatch.setattr(physical.RetainedPackagePublication, "release", release)
    before = repository_descriptors(root)
    try:
        result = run(args, capsys)
        assert held["guard"].observe_cleanup() == held["before"]
        assert result["caller_cleanup"]["physical"]["invocation_state"] == "raised"
        assert result["caller_cleanup"]["protocol"]["invocation_state"] == "raised"
        assert repository_descriptors(root) == held["descriptors"]
        assert len(held["descriptors"]) > len(before)
        assert not (root / "customer/specs/widget").exists()
    finally:
        held["guard"].release()  # Test owner disposes its own, untouched originals.
    assert repository_descriptors(root) == before


@pytest.mark.parametrize("fault", ["owner", "status", "scope", "digest"])
def test_original_issue_refusals_restore_descriptors_preserving_foreign_work(
    inputs, capsys, fault
):
    import hashlib

    root, _, issue, _, args = inputs
    if fault == "digest":
        args[args.index("--expected-issue-sha256") + 1] = "sha256:" + "0" * 64
    else:
        replacements = {
            "owner": ("codex-spec-governed-real-source-proof", "codex-foreign-owner"),
            "status": ("In Progress", "Closed"),
            "scope": ("`customer/specs`", "`unrelated.txt`"),
        }
        old, new = replacements[fault]
        issue.write_text(issue.read_text().replace(old, new))
        args[args.index("--expected-issue-sha256") + 1] = (
            "sha256:" + hashlib.sha256(issue.read_bytes()).hexdigest()
        )
    before = bodies(root)
    descriptors = repository_descriptors(root)
    result = run(args + ["--apply"], capsys)
    assert result["error"] != "draft_cleanup_completion_unverified"
    assert result["effect"] == "none"
    assert result["input_custody"]["physical"]["owner_cleanup_outcome"] == "completed"
    assert bodies(root) == before
    assert repository_descriptors(root) == descriptors


def test_original_custody_correlation_and_attempts_are_not_reused(inputs, capsys):
    _, _, _, _, args = inputs
    receipts = [run(args, capsys, exit_code=0) for _ in range(2)]
    attempts = []
    for result in receipts:
        cleanup = result["cleanup_evidence"]
        custody = cleanup["input_custody"]
        assert cleanup["attempt_ref"] == custody["attempt_ref"]
        assert custody["context_ref"].startswith("specification-context:")
        assert custody["context_ref"] != custody["attempt_ref"]
        assert custody["client_intent_id"] == "cli-source-attempt"
        assert custody["execution_ref"] == "codex-spec-governed-real-source-proof"
        assert result["input_custody"]["attempt_ref"] == custody["attempt_ref"]
        attempts.append(custody["attempt_ref"])
    assert len(set(attempts)) == 2


@pytest.mark.parametrize("fault", ["unavailable", "malformed"])
def test_cli_custody_observer_faults_do_not_grant_raw_cleanup_or_mask_primary(
    inputs, capsys, monkeypatch, fault
):
    from aware_issue_fs_adapter.draft_package import IssueDraftInputCustody

    root, _, _, _, args = inputs
    before = repository_descriptors(root)
    args[args.index("--expected-issue-sha256") + 1] = "sha256:" + "f" * 64

    def observe(self):
        if fault == "unavailable":
            raise RuntimeError("original bare-custody observer unavailable")
        return object()

    monkeypatch.setattr(IssueDraftInputCustody, "observe_cleanup", observe)
    result = run(args, capsys)
    assert result["error"] == "issue_source_sha256_mismatch"
    assert result["input_custody"] is None
    assert result["cleanup_diagnostics"]
    assert result["caller_cleanup"] == {}
    assert (
        result["cleanup_evidence"]["input_custody"]["physical"]["owner_cleanup_outcome"]
        == "completed"
    )
    assert repository_descriptors(root) == before


@pytest.mark.parametrize("forged", ["snapshot", "object"])
def test_detached_custody_cannot_replace_original_factory_authority(
    inputs, capsys, monkeypatch, forged
):
    root, _, _, _, args = inputs
    spec = importlib.import_module("aware_specification_fs_sdk_adapter")
    original = spec.open_governed_specification_draft
    before = repository_descriptors(root)

    def factory(**kwargs):
        guard = kwargs["input_custody"]
        kwargs["input_custody"] = (
            guard.observe_cleanup() if forged == "snapshot" else object()
        )
        return original(**kwargs)

    monkeypatch.setattr(spec, "open_governed_specification_draft", factory)
    result = run(args, capsys)
    assert result["error"] != "draft_cleanup_completion_unverified"
    assert result["cleanup_evidence"]["input_custody"] is None
    assert result["input_custody"]["physical"]["owner_cleanup_outcome"] == "completed"
    assert result["caller_cleanup"]["custody"]["invocation_state"] == "returned"
    assert repository_descriptors(root) == before
    assert not (root / "customer/specs/widget").exists()


@pytest.mark.parametrize("identity", ["missing", "ambiguous"])
def test_original_harness_identity_refusal_cleans_only_unreserved_cli_inputs(
    inputs, capsys, monkeypatch, identity
):
    root, _, _, _, args = inputs
    before = repository_descriptors(root)
    if identity == "missing":
        monkeypatch.delenv("CODEX_THREAD_ID")
    else:
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "different-real-execution")
    result = run(args, capsys)
    assert result["error"] != "draft_cleanup_completion_unverified"
    assert result["effect"] == "none"
    assert result["input_custody"] is None
    assert result["caller_cleanup"]["physical"]["invocation_state"] == "returned"
    assert result["caller_cleanup"]["protocol"]["invocation_state"] == "returned"
    assert repository_descriptors(root) == before
    assert not (root / "customer/specs/widget").exists()


def test_unavailable_preacquisition_observation_does_not_skip_atomic_owner_disposal(
    inputs, capsys, monkeypatch
):
    root, _, _, _, args = inputs
    before = repository_descriptors(root)

    def acquisition(*args, **kwargs):
        raise OSError("issuer unavailable before reserving original inputs")

    def observation(*args, **kwargs):
        raise RuntimeError("physical historical observation unavailable")

    monkeypatch.setattr(
        FilesystemIssueOperationProvider, "retain_draft_inputs", acquisition
    )
    monkeypatch.setattr(physical, "observe_package_cleanup", observation)
    result = run(args, capsys)
    assert result["input_custody"] is None
    assert (
        "cli_physical_observation_failed:RuntimeError" in result["cleanup_diagnostics"]
    )
    assert result["caller_cleanup"]["physical"]["invocation_state"] == "returned"
    assert "physical_observation" not in result["caller_cleanup"]
    assert repository_descriptors(root) == before
    assert not (root / "customer/specs/widget").exists()
