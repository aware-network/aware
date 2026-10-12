"""Real read-only owner composition followed by separately requested effects."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest
from aware_agent_cli import draft_preparation as preparation
from aware_agent_cli.main import main
from aware_issue_fs_adapter import FilesystemIssueOperationProvider

ROOT = Path(__file__).resolve().parents[8]
SPEC = ROOT / "workspaces/aware_kernel/modules/specification/sdks/specification/python"
loader = importlib.util.spec_from_file_location(
    "agent_guard_preparation_fixture", SPEC / "cli/tests/test_draft_commands.py"
)
fixture = importlib.util.module_from_spec(loader)
loader.loader.exec_module(fixture)
inputs = fixture.inputs


def digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def bodies(root):
    return {
        str(path.relative_to(root)): (path.read_bytes(), path.stat().st_mode)
        for path in root.rglob("*")
        if path.is_file()
    }


def fds():
    return set(os.listdir("/proc/self/fd"))


def arguments(original, *, format="json"):
    result = ["spec", "prepare-draft", "--format", format]
    for flag in (
        "--repository-root",
        "--protocol-manifest",
        "--spec-manifest",
        "--snapshot-json",
        "--issue-ref",
        "--author-ref",
        "--authoring-intent-ref",
        "--client-intent-id",
    ):
        result.extend((flag, original[original.index(flag) + 1]))
    return result


def prepare(original, capsys):
    assert main(arguments(original)) == 0
    return json.loads(capsys.readouterr().out)


def test_original_guard_sources_and_no_write_admission(inputs, capsys, monkeypatch):
    from aware_file_system import retained_package as physical
    from aware_protocol_fs_adapter import specification_draft_target as target

    root, manifest, issue, source, original = inputs
    before = bodies(root)
    descriptors = fds()

    def forbidden(*args, **kwargs):
        pytest.fail(
            "read-only preparation invoked retained publication or write custody"
        )

    monkeypatch.setattr(physical, "retain_package_publication", forbidden)
    monkeypatch.setattr(target, "admit_specification_draft_target", forbidden)
    monkeypatch.setattr(
        FilesystemIssueOperationProvider, "retain_draft_inputs", forbidden
    )
    result = prepare(original, capsys)
    assert result["effect"] == "none"
    assert result["write_admission_issued"] is result["apply_invoked"] is False
    assert result["observations_atomic"] is False
    assert result["guards"] == {
        "issue_source_bytes": digest(issue.read_bytes()),
        "protocol_manifest_bytes": digest(manifest.read_bytes()),
        "snapshot_input_bytes": digest(source.read_bytes()),
    }
    assert len(result["members"]) == 6
    fit = result["owner_observations"]["target_fit"]
    assert fit["fit"] == "match"
    assert fit["scope"] == "binding_layout_only"
    assert fit["cleanup"] == "closed"
    assert fit["source_sha256"] == result["guards"]["protocol_manifest_bytes"]
    assert (
        fit["request"]["supplied_spec_manifest_locator"]
        == original[original.index("--spec-manifest") + 1]
    )
    assert bodies(root) == before
    assert fds() == descriptors


@pytest.mark.parametrize("apply", [False, True])
def test_reviewed_original_command_runs_without_digest_copy(inputs, capsys, apply):
    root, _, issue, source, original = inputs
    before = bodies(root)
    request = prepare(original, capsys)
    argv = request["apply_argv" if apply else "preview_argv"]
    assert argv[:3] == ["aware", "spec", "create-draft"]
    assert ("--apply" in argv) is apply
    assert main(argv[1:]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["effect"] == ("published" if apply else "none")
    assert result["consumer_completion_verified"] is True
    assert result["input_sha256"] == request["guards"]["snapshot_input_bytes"]
    assert issue.read_bytes() == before[str(issue.relative_to(root))][0]
    assert source.read_bytes() == before[str(source.relative_to(root))][0]
    assert bodies(root).items() >= before.items()


@pytest.mark.parametrize("changed", ["issue", "manifest", "input"])
def test_stale_review_refuses_without_repreparation(inputs, capsys, changed):
    root, manifest, issue, source, original = inputs
    reviewed = prepare(original, capsys)
    selected = {"issue": issue, "manifest": manifest, "input": source}[changed]
    selected.write_bytes(selected.read_bytes() + b"\n")
    before = bodies(root)
    descriptors = fds()
    assert main(reviewed["apply_argv"][1:]) == 2
    refused = json.loads(capsys.readouterr().out)
    assert refused["error"]
    assert not (root / "customer/specs/widget").exists()
    assert reviewed["guards"] == {
        "issue_source_bytes": original[original.index("--expected-issue-sha256") + 1],
        "protocol_manifest_bytes": original[
            original.index("--expected-manifest-sha256") + 1
        ],
        "snapshot_input_bytes": original[original.index("--expected-input-sha256") + 1],
    }
    assert bodies(root) == before
    assert fds() == descriptors


def test_relative_input_is_bound_to_observed_absolute_coordinate(
    inputs, monkeypatch, capsys
):
    root, _, _, source, original = inputs
    original = list(original)
    original[original.index("--snapshot-json") + 1] = source.name
    monkeypatch.chdir(root)
    result = prepare(original, capsys)
    assert result["preview_argv"][
        result["preview_argv"].index("--snapshot-json") + 1
    ] == str(source)
    monkeypatch.chdir("/")
    assert main(result["apply_argv"][1:]) == 0
    assert json.loads(capsys.readouterr().out)["consumer_completion_verified"] is True


def test_summary_is_readable_and_json_remains_available(inputs, capsys):
    _, _, _, _, original = inputs
    assert main(arguments(original, format="summary")) == 0
    summary = capsys.readouterr().out
    assert "no write admission" in summary
    assert "Explicit apply only after review:" in summary
    assert "no atomic snapshot" in summary
    assert "Expected target shape: customer/specs/<spec-key>/aware.spec.toml" in summary
    assert "Target fit: match" in summary
    assert "not Issue eligibility" in summary
    assert (
        len(summary.encode()) < 8192
    )  # Ordinary fixture measurement, not a truncation rule.


def test_missing_input_supplier_refuses_before_any_owner_observation(
    inputs, monkeypatch, capsys
):
    root, _, _, _, original = inputs
    before = bodies(root)
    importer = preparation.importlib.import_module

    def unavailable(name):
        if name == "aware_specification_sdk":
            raise ImportError("input port unavailable")
        return importer(name)

    monkeypatch.setattr(preparation.importlib, "import_module", unavailable)
    assert main(arguments(original)) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["owner_observations"] == {}
    assert output["effect"] == "none"
    assert "apply_argv" not in output
    assert bodies(root) == before


def forbid_later_observation(monkeypatch):
    from aware_specification_sdk import SpecificationInputObservationClient

    def forbidden(*args, **kwargs):
        pytest.fail("refused target fit reached Issue/input observation")

    monkeypatch.setattr(
        FilesystemIssueOperationProvider, "resolve_read_projection", forbidden
    )
    monkeypatch.setattr(
        SpecificationInputObservationClient, "observe_draft_input", forbidden
    )


def refusal(original, capsys, *, format="json"):
    assert main(arguments(original, format=format)) == 2
    streams = capsys.readouterr()
    assert streams.err == ""
    # Summary retains the original structured failure after its explanation.
    result = json.loads(streams.out.splitlines()[-1])
    assert result["status"] == "refused"
    assert result["write_admission_issued"] is result["apply_invoked"] is False
    assert result["authorizes_retry"] is False
    assert "preview_argv" not in result and "apply_argv" not in result
    assert "issue" not in result["owner_observations"]
    assert "input" not in result["owner_observations"]
    return result, streams.out


@pytest.mark.parametrize("format", ["json", "summary"])
@pytest.mark.parametrize(
    "target",
    [
        "customer/specs/aware.spec.toml",
        "other/widget/aware.spec.toml",
        "customer/specs/a/b/aware.spec.toml",
        "customer/specs/widget/other.toml",
    ],
)
def test_layout_mismatch_explains_original_shape_without_guidance(
    inputs, monkeypatch, capsys, format, target
):
    root, manifest, _, _, original = inputs
    original = list(original)
    original[original.index("--spec-manifest") + 1] = target
    before, descriptors = bodies(root), fds()
    forbid_later_observation(monkeypatch)
    result, text = refusal(original, capsys, format=format)
    fit = result["owner_observations"]["target_fit"]
    assert (
        result["error"]
        == fit["reason"]
        == "specification_selection_target_outside_binding"
    )
    assert fit["fit"] == "mismatch"
    assert fit["request"]["supplied_spec_manifest_locator"] == target
    assert fit["configured_root"] == "customer/specs"
    assert fit["path_template"] == "<spec-key>/aware.spec.toml"
    assert fit["expected_shape"] == "customer/specs/<spec-key>/aware.spec.toml"
    assert fit["cleanup"] == "closed" and result["effect"] == "none"
    assert fit["source_sha256"] == digest(manifest.read_bytes())
    assert "create-draft" not in text and "prepared" not in text
    if format == "summary":
        assert "Supplied SPEC target: " + target in text
        assert "Expected target shape: " + fit["expected_shape"] in text
        assert "Target fit: mismatch" in text
    assert bodies(root) == before and fds() == descriptors


@pytest.mark.parametrize(
    "target",
    [
        "/absolute/aware.spec.toml",
        "../widget/aware.spec.toml",
        "customer//specs/widget/aware.spec.toml",
    ],
)
def test_invalid_target_retains_original_typed_refusal(
    inputs, monkeypatch, capsys, target
):
    root, _, _, _, original = inputs
    original = list(original)
    original[original.index("--spec-manifest") + 1] = target
    before, descriptors = bodies(root), fds()
    forbid_later_observation(monkeypatch)
    result, _ = refusal(original, capsys)
    error = result["owner_error"]
    assert error["code"] == result["error"] == "specification_selection_paths_invalid"
    assert error["request"]["supplied_spec_manifest_locator"] == target
    assert error["cleanup"] == "not_acquired"
    assert error["evidence_grade"] == "provider_observation"
    assert error["observed_fit"] is None and result["effect"] == "none"
    assert bodies(root) == before and fds() == descriptors


@pytest.mark.parametrize("role", ["projection", "unavailable"])
def test_unavailable_binding_is_not_prepared_or_repaired(
    inputs, monkeypatch, capsys, role
):
    from test_specification_selection import source

    root, manifest, _, _, original = inputs
    manifest.write_text(source(role=role))
    before, descriptors = bodies(root), fds()
    forbid_later_observation(monkeypatch)
    result, _ = refusal(original, capsys)
    assert result["owner_error"]["code"] == "specification_selection_authority_required"
    assert result["owner_error"]["observed_fit"] is None
    assert bodies(root) == before and fds() == descriptors


@pytest.mark.parametrize("format", ["json", "summary"])
def test_changed_manifest_between_observations_retains_reviewed_guard(
    inputs, monkeypatch, capsys, format
):
    from aware_protocol_sdk import ProtocolSdkClient

    root, manifest, _, _, original = inputs
    guard = digest(manifest.read_bytes())
    admit = ProtocolSdkClient.admit_target

    def intervening_change(self, request):
        result = admit(self, request)
        manifest.write_bytes(manifest.read_bytes() + b"\n# byte drift\n")
        return result

    monkeypatch.setattr(ProtocolSdkClient, "admit_target", intervening_change)
    forbid_later_observation(monkeypatch)
    descriptors = fds()
    result, _ = refusal(original, capsys, format=format)
    error = result["owner_error"]
    assert error["code"] == "specification_selection_manifest_changed"
    assert error["request"]["expected_manifest_sha256"] == guard
    assert (
        result["owner_observations"]["protocol"]["admission"]["source_sha256"] == guard
    )
    assert error["observed_source_sha256"] == digest(manifest.read_bytes()) != guard
    assert error["cleanup"] == "closed" and fds() == descriptors
    assert manifest.read_bytes().endswith(b"# byte drift\n")
    assert not (root / "customer/specs/widget").exists()


@pytest.mark.parametrize("missing", ["client", "provider", "method"])
def test_missing_target_fit_ports_refuse_before_observation(
    inputs, monkeypatch, capsys, missing
):
    import aware_protocol_fs_adapter as protocol_fs
    import aware_protocol_sdk as protocol

    root, _, _, _, original = inputs
    before = bodies(root)
    if missing == "client":
        monkeypatch.delattr(protocol, "ProtocolSpecificationTargetFitClient")
    elif missing == "provider":
        monkeypatch.delattr(
            protocol_fs, "FilesystemProtocolSpecificationTargetFitProvider"
        )
    else:
        monkeypatch.setattr(
            protocol_fs.FilesystemProtocolSpecificationTargetFitProvider,
            "observe_specification_target_fit",
            None,
        )
    result, _ = refusal(original, capsys)
    assert result["error"] == "draft_preparation_supplier_unavailable"
    assert result["owner_observations"] == {} and result["effect"] == "none"
    assert bodies(root) == before


@pytest.mark.parametrize("format", ["json", "summary"])
def test_unknown_target_fit_cleanup_retains_observation_without_guidance(
    inputs, monkeypatch, capsys, format
):
    from aware_protocol_fs_adapter import (
        FilesystemProtocolSpecificationTargetFitProvider as Provider,
    )
    from aware_protocol_fs_adapter import specification_target_fit as owner

    root, _, _, _, original = inputs
    before, descriptors = bodies(root), fds()
    close = owner.os.close
    interrupted = []
    active = []
    observe = Provider.observe_specification_target_fit
    version = owner.version
    fit_observed = []

    def after_fit(distribution):
        fit_observed.append(True)
        return version(distribution)

    def observed(self, request):
        active.append(True)
        try:
            return observe(self, request)
        finally:
            active.pop()

    def original_close_interrupted(fd):
        selected = os.readlink(f"/proc/self/fd/{fd}") == str(root)
        close(fd)
        if active and fit_observed and selected and not interrupted:
            interrupted.append(fd)
            raise KeyboardInterrupt("original root close outcome unavailable")

    monkeypatch.setattr(owner.os, "close", original_close_interrupted)
    monkeypatch.setattr(Provider, "observe_specification_target_fit", observed)
    monkeypatch.setattr(owner, "version", after_fit)
    forbid_later_observation(monkeypatch)
    result, text = refusal(original, capsys, format=format)
    error = result["owner_error"]
    assert interrupted and error["observed_fit"] == "match"
    assert error["cleanup"] == "unknown" and result["effect"] == "unknown"
    assert "target_fit" not in result["owner_observations"]
    assert "create-draft" not in text
    assert bodies(root) == before and fds() == descriptors


def test_unvalidated_provider_result_cannot_become_prepared(
    inputs, monkeypatch, capsys
):
    from aware_protocol_fs_adapter import (
        FilesystemProtocolSpecificationTargetFitProvider as Provider,
    )

    root, _, _, _, original = inputs
    before, descriptors = bodies(root), fds()
    observe = Provider.observe_specification_target_fit

    def malformed(self, request):
        return observe(self, request).to_wire()

    monkeypatch.setattr(Provider, "observe_specification_target_fit", malformed)
    forbid_later_observation(monkeypatch)
    result, _ = refusal(original, capsys)
    error = result["owner_error"]
    assert error["code"] == "target_fit_provider_return_unverified"
    assert error["evidence_grade"] == "unvalidated_provider_report"
    assert error["reported_result"]["fit"] == "match"
    assert error["cleanup"] == result["effect"] == "unknown"
    assert bodies(root) == before and fds() == descriptors


def test_target_fit_local_predispatch_failure_has_no_effects(
    inputs, monkeypatch, capsys
):
    from aware_protocol_sdk import specification_target_fit as owner

    root, _, _, _, original = inputs
    before, descriptors = bodies(root), fds()

    detach = owner._detached
    failures = []

    def interrupted(value):
        if not failures:
            failures.append(True)
            raise KeyboardInterrupt("request snapshot interrupted")
        return detach(value)

    monkeypatch.setattr(owner, "_detached", interrupted)
    forbid_later_observation(monkeypatch)
    result, _ = refusal(original, capsys)
    error = result["owner_error"]
    assert error["code"] == "target_fit_dispatch_preparation_failed"
    assert error["provider_invoked"] is False
    assert error["cleanup"] == "not_acquired" and result["effect"] == "none"
    assert bodies(root) == before and fds() == descriptors


def test_uncorrelated_provider_result_retains_report_without_guidance(
    inputs, monkeypatch, capsys
):
    from dataclasses import replace

    from aware_protocol_fs_adapter import (
        FilesystemProtocolSpecificationTargetFitProvider as Provider,
    )

    root, _, _, _, original = inputs
    before, descriptors = bodies(root), fds()
    observe = Provider.observe_specification_target_fit

    def foreign(self, request):
        result = observe(self, request)
        return replace(
            result,
            request=replace(
                request,
                supplied_spec_manifest_locator="customer/specs/other/aware.spec.toml",
            ),
        )

    monkeypatch.setattr(Provider, "observe_specification_target_fit", foreign)
    forbid_later_observation(monkeypatch)
    result, _ = refusal(original, capsys)
    error = result["owner_error"]
    assert error["code"] == "target_fit_provider_return_unverified"
    assert (
        error["request"]["supplied_spec_manifest_locator"]
        == "customer/specs/widget/aware.spec.toml"
    )
    assert (
        error["reported_result"]["request"]["supplied_spec_manifest_locator"]
        == "customer/specs/other/aware.spec.toml"
    )
    assert result["effect"] == "unknown" and error["cleanup"] == "unknown"
    assert bodies(root) == before and fds() == descriptors


def test_late_manifest_change_does_not_turn_observed_match_into_guidance(
    inputs, monkeypatch, capsys
):
    from aware_protocol_fs_adapter import specification_target_fit as owner

    root, manifest, _, _, original = inputs
    version = owner.version
    initial = digest(manifest.read_bytes())

    def late_change(distribution):
        manifest.write_bytes(manifest.read_bytes() + b"\n# late byte drift\n")
        return version(distribution)

    monkeypatch.setattr(owner, "version", late_change)
    forbid_later_observation(monkeypatch)
    descriptors = fds()
    result, _ = refusal(original, capsys)
    error = result["owner_error"]
    assert error["code"] == "specification_selection_manifest_changed"
    assert error["observed_fit"] == "match" and error["cleanup"] == "closed"
    assert error["request"]["expected_manifest_sha256"] == initial
    assert "target_fit" not in result["owner_observations"]
    assert fds() == descriptors and not (root / "customer/specs/widget").exists()


def test_layout_match_does_not_admit_symlink_destination(inputs, capsys):
    root, _, _, _, original = inputs
    foreign = root / "foreign"
    foreign.mkdir()
    (foreign / "preserved.txt").write_text("foreign work\n")
    target = root / "customer/specs/widget"
    target.symlink_to(foreign, target_is_directory=True)
    before, descriptors = bodies(root), fds()
    result = prepare(original, capsys)
    assert result["owner_observations"]["target_fit"]["fit"] == "match"
    assert "Destination availability" in result["next_action"]
    assert main(result["preview_argv"][1:]) == 2
    assert json.loads(capsys.readouterr().out)["error"]
    assert target.is_symlink() and bodies(root) == before and fds() == descriptors


@pytest.mark.parametrize("absolute", [False, True])
def test_original_nested_protocol_coordinate_and_guard_are_preserved(
    inputs, capsys, absolute
):
    root, manifest, _, _, original = inputs
    original = list(original)
    if absolute:
        original[original.index("--protocol-manifest") + 1] = str(manifest)
    result = prepare(original, capsys)
    selected = original[original.index("--protocol-manifest") + 1]
    fit = result["owner_observations"]["target_fit"]
    assert fit["request"]["protocol_manifest_locator"] == selected
    assert fit["request"]["expected_manifest_sha256"] == digest(manifest.read_bytes())
    assert (
        result["preview_argv"][result["preview_argv"].index("--protocol-manifest") + 1]
        == selected
    )
    assert fit["request"]["repository_root"] == str(root)


def test_target_fit_dependency_floors_exclude_portless_predecessors():
    import tomllib

    from packaging.requirements import Requirement

    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())[
        "project"
    ]
    deps = {r.name: r for r in map(Requirement, project["dependencies"])}
    for name, accepted, old, ceiling in (
        ("aware-protocol-sdk", "0.3.2", "0.3.1", "0.4.0"),
        ("aware-protocol-fs-adapter", "0.6.5", "0.6.4", "0.7.0"),
    ):
        assert accepted in deps[name].specifier
        assert old not in deps[name].specifier and ceiling not in deps[name].specifier


def test_unknown_input_cleanup_is_preserved_and_yields_no_apply_command(
    inputs, monkeypatch, capsys
):
    from aware_specification_fs_sdk_adapter import input_observation as owner

    root, _, _, source, original = inputs
    close = owner.os.close
    before = bodies(root)
    descriptors = fds()

    def interrupted(fd):
        selected = os.readlink(f"/proc/self/fd/{fd}") == str(source)
        close(fd)
        if selected:
            raise KeyboardInterrupt("close observation unavailable")

    monkeypatch.setattr(owner.os, "close", interrupted)
    assert main(arguments(original)) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["effect"] == "unknown"
    error = result["owner_error"]["value"]
    assert error["cleanup"] == "unknown"
    assert error["observed_body_hex"] == source.read_bytes().hex()
    assert "apply_argv" not in result
    assert bodies(root) == before
    assert fds() == descriptors


@pytest.mark.parametrize("kind", ["issue", "input"])
def test_missing_selected_source_has_no_apply_command(inputs, capsys, kind):
    root, _, _, _, original = inputs
    original = list(original)
    flag = "--issue-ref" if kind == "issue" else "--snapshot-json"
    original[original.index(flag) + 1] = (
        "fb/2026-10-06/absent" if kind == "issue" else str(root / "absent.json")
    )
    before = bodies(root)
    assert main(arguments(original)) == 2
    result = json.loads(capsys.readouterr().out)
    assert "apply_argv" not in result
    assert bodies(root) == before


def test_prepare_rejects_apply_flag_before_effects(inputs, capsys):
    root, _, _, _, original = inputs
    before = bodies(root)
    with pytest.raises(SystemExit) as caught:
        main([*arguments(original), "--apply"])
    assert caught.value.code == 2
    capsys.readouterr()
    assert bodies(root) == before


def test_observed_wrong_owner_does_not_grant_write_authority(inputs, capsys):
    root, _, issue, _, original = inputs
    issue.write_text(
        issue.read_text().replace(
            "codex-spec-governed-real-source-proof", "codex-other-execution"
        )
    )
    reviewed = prepare(original, capsys)
    assert reviewed["write_admission_issued"] is False
    before = bodies(root)
    assert main(reviewed["apply_argv"][1:]) == 2
    refused = json.loads(capsys.readouterr().out)
    assert refused["error"]
    assert not (root / "customer/specs/widget").exists()
    assert bodies(root) == before


def test_protocol_refusal_retains_original_diagnostics_and_stops(inputs, capsys):
    root, manifest, _, _, original = inputs
    manifest.write_text("broken [TOML")
    before = bodies(root)
    assert main(arguments(original)) == 2
    refused = json.loads(capsys.readouterr().out)
    assert refused["error"] == "protocol_observation_not_canonical"
    assert refused["owner_observations"]["protocol"]["admission"]["diagnostics"]
    assert "issue" not in refused["owner_observations"]
    assert "apply_argv" not in refused
    assert bodies(root) == before
