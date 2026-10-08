import ast
import hashlib
from dataclasses import replace
from pathlib import Path

import pytest
from aware_protocol_fs_adapter.specification_setup import prepare_specification_setup
from aware_protocol_sdk import (
    ProtocolSpecificationSetupError,
    ProtocolSpecificationSetupRequest,
)


def protocol_source():
    return b"""aware = 1
# retain unrelated customer comment
[protocol]
name = "aware.collaboration"
profile = "aware.collaboration.fs_v1"
semantic_version = 1
[target]
kind = "repository"
authority_mode = "filesystem"
[bootstrap]
agent_contract = "AGENTS.md"
[records.goal]
profile = "aware.goal.markdown.v1"
role = "unavailable"
[records.issue]
profile = "aware.issue.markdown.v1"
role = "authority"
root = "issues"
path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"
[records.feed]
profile = "aware.feed.projection.v1"
role = "unavailable"
[records.specification] # retain table comment
profile = "specification_fs_v1"
role = 'unavailable' # retain role comment
# retain end of section
[records.evidence]
profile = "aware.protocol.evidence.v1"
role = "unavailable"
"""


def digest(source):
    return "sha256:" + hashlib.sha256(source).hexdigest()


def request_for(root, source, **kwargs):
    return ProtocolSpecificationSetupRequest(
        repository_root=str(root),
        manifest_path="aware.protocol.toml",
        expected_manifest_sha256=digest(source),
        issue_ref="fb/2026-10-06/setup",
        expected_issue_sha256=digest(b"fixture issue"),
        specification_root="contracts",
        directory_paths=("contracts",),
        client_intent_id="setup-1",
        **kwargs,
    )


@pytest.fixture
def source_setup(tmp_path):
    source = protocol_source()
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_bytes(source)
    (tmp_path / "AGENTS.md").write_text("Fixture bootstrap")
    return tmp_path, source, manifest, request_for(tmp_path, source)


@pytest.mark.parametrize("line_endings", [b"\n", b"\r\n"])
def test_candidate_changes_only_bound_source_span_and_preserves_comments(
    source_setup, line_endings
):
    root, source, manifest, request = source_setup
    source = source.replace(b"\n", line_endings)
    manifest.write_bytes(source)
    candidate = prepare_specification_setup(
        replace(request, expected_manifest_sha256=digest(source))
    )
    role = b"role = 'unavailable' # retain role comment" + line_endings
    new_role = b"role = 'authority' # retain role comment" + line_endings
    inserted = (
        b'root = "contracts"'
        + line_endings
        + b'path_template = "<spec-key>/aware.spec.toml"'
        + line_endings
    )
    assert candidate.postimage == source.replace(role, new_role + inserted)
    assert manifest.read_bytes() == source and not (root / "contracts").exists()


def test_identical_binding_candidate_is_byte_noop(source_setup):
    _, _, manifest, request = source_setup
    first = prepare_specification_setup(request)
    manifest.write_bytes(first.postimage)
    second = prepare_specification_setup(
        replace(request, expected_manifest_sha256=first.postimage_sha256)
    )
    assert second.postimage == second.preimage == first.postimage


@pytest.mark.parametrize(
    "change",
    ["foreign_root", "projection", "inline_table", "dotted_role", "multiline_comment"],
)
def test_unsupported_reconfiguration_or_source_forms_refuse_without_writes(
    source_setup, change
):
    root, source, manifest, request = source_setup
    if change == "foreign_root":
        source = prepare_specification_setup(request).postimage.replace(
            b'root = "contracts"', b'root = "other"'
        )
    elif change == "projection":
        source = prepare_specification_setup(request).postimage.replace(
            b"role = 'authority'", b"role = 'projection'"
        )
    elif change == "inline_table":
        source = source.replace(
            b"[records.specification] # retain table comment\nprofile = \"specification_fs_v1\"\nrole = 'unavailable' # retain role comment\n",
            b'[records]\nspecification = {profile = "specification_fs_v1", role = "unavailable"}\n',
        )
    elif change == "dotted_role":
        source = source.replace(
            b"[records.specification] # retain table comment\nprofile = \"specification_fs_v1\"\nrole = 'unavailable' # retain role comment\n",
            b'[records]\nspecification.profile = "specification_fs_v1"\nspecification.role = "unavailable"\n',
        )
    else:
        source = source + b'\n# """ unsupported finite editing form\n'
    manifest.write_bytes(source)
    with pytest.raises(ProtocolSpecificationSetupError):
        prepare_specification_setup(
            replace(request, expected_manifest_sha256=digest(source))
        )
    assert manifest.read_bytes() == source and not (root / "contracts").exists()


def test_comment_only_preimage_change_refuses(source_setup):
    _, source, manifest, request = source_setup
    manifest.write_bytes(source + b"\n# changed\n")
    with pytest.raises(ProtocolSpecificationSetupError, match="preimage_changed"):
        prepare_specification_setup(request)


def test_unrelated_directory_preparation_refuses(source_setup):
    root, source, manifest, request = source_setup
    with pytest.raises(ProtocolSpecificationSetupError, match="not_root_ancestor"):
        prepare_specification_setup(replace(request, directory_paths=("unrelated",)))
    assert manifest.read_bytes() == source and not (root / "unrelated").exists()


@pytest.mark.parametrize(
    "value", ["../escape", "/absolute", "a//b", "a/./b", "a\\b", "x\x00y"]
)
def test_invalid_request_paths_refuse(source_setup, value):
    from aware_protocol_runtime import ProtocolContractError

    *_, request = source_setup
    with pytest.raises(ProtocolContractError):
        replace(request, specification_root=value)


@pytest.mark.parametrize("kind", ["fifo", "symlink", "hardlink", "wrong_filename"])
def test_manifest_source_refusals_are_typed_and_effect_free(source_setup, kind):
    import os

    root, _source, manifest, request = source_setup
    if kind == "fifo":
        manifest.unlink()
        os.mkfifo(manifest)
    elif kind == "symlink":
        manifest.rename(root / "real.toml")
        manifest.symlink_to(root / "real.toml")
    elif kind == "hardlink":
        os.link(manifest, root / "alias")
    else:
        request = replace(request, manifest_path="other.toml")
    with pytest.raises(ProtocolSpecificationSetupError):
        prepare_specification_setup(request)
    assert not (root / "contracts").exists()


def test_protocol_candidate_imports_no_issue_workspace_or_service():
    module = (
        Path(__file__).parents[1] / "aware_protocol_fs_adapter/specification_setup.py"
    )
    imports = [
        node.module
        for node in ast.walk(ast.parse(module.read_text()))
        if isinstance(node, ast.ImportFrom) and node.module
    ]
    assert not any(
        name.startswith(
            (
                "aware_issue",
                "aware_workspace",
                "aware_local_service",
                "aware_specification",
            )
        )
        for name in imports
    )
