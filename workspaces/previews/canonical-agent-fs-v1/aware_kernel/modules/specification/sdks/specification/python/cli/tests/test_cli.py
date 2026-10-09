import importlib.util
import json
from pathlib import Path

from aware_specification_cli.main import compatibility_main as main
from aware_specification_runtime import (
    SpecificationSnapshot,
    encode_specification_snapshot,
)
from aware_specification_sdk import SpecificationSdkClient

_spec = importlib.util.spec_from_file_location(
    "spec_cli_existing_fixtures",
    Path(__file__).parents[2] / "fs_adapter/tests/test_provider.py",
)
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)
canonical_tree = _fixtures.canonical_tree


def test_cli_draft_then_observe(tmp_path, capsys):
    input_path = tmp_path / "input.json"
    input_path.write_bytes(
        encode_specification_snapshot(SpecificationSnapshot((_fixtures.definition(),)))
    )
    args = ["--source-base", str(tmp_path), "--root", "plan"]
    assert (
        main(
            [
                "create-draft",
                *args,
                "--snapshot-json",
                str(input_path),
                "--author-ref",
                "author",
                "--intent-ref",
                "intent",
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["effect"] == "published"
    assert output["phase_acceptance"] is False
    assert (
        main(["observe", *args, "--expected-source-digest", output["source_digest"]])
        == 0
    )
    observed = json.loads(capsys.readouterr().out)
    assert observed["authority_mode"] == "filesystem"
    assert observed["work_authority"] is False


def test_cli_iteration_identity_is_not_exported_authority(
    canonical_tree, capsys, monkeypatch
):
    base, root = canonical_tree
    observations = []
    original_observe = SpecificationSdkClient.observe

    def observe(client, request):
        observations.append(request)
        return original_observe(client, request)

    monkeypatch.setattr(SpecificationSdkClient, "observe", observe)
    assert (
        main(
            [
                "iteration-identity",
                "--source-base",
                str(base),
                "--root",
                root,
                "--iteration-ref",
                "specification:example.spec/phase:foundation/iteration:proof",
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["selected_iteration_ref"].endswith("/iteration:proof")
    assert output["retained_capability_exported"] is False
    assert len(observations) == 1


def test_cli_absent_source_retains_actual_owner_refusal(tmp_path, capsys):
    assert main(["observe", "--source-base", str(tmp_path), "--root", "missing"]) == 2
    output = json.loads(capsys.readouterr().out)
    # Existing lower owner classifies a missing root as its typed internal
    # failure. Preserve that diagnostic rather than inventing parallel admission.
    assert output == {
        "effect": "none",
        "error": "specification_fs_adapter_internal_failure",
    }
