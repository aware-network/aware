from __future__ import annotations

from pathlib import Path

import pytest

from aware_protocol_fs_adapter import (
    FilesystemProtocolProfile,
    admit_protocol_manifest,
    admit_protocol_manifest_bytes,
    resolve_repository_path_at_use,
)
from aware_protocol_runtime import ProtocolAdmissionOutcomeKind


def _manifest(**replacements: str) -> bytes:
    text = """aware = 1

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
root = "docs/goals"
role = "authority"
path_template = "YYYY/MM/DD/goal-YYYY-MM-DD-<slug>.md"

[records.issue]
profile = "aware.issue.markdown.v1"
root = "docs/issues"
role = "authority"
path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"

[records.feed]
profile = "aware.feed.projection.v1"
role = "unavailable"

[records.specification]
profile = "specification_fs_v1"
root = "docs/specs"
role = "authority"
path_template = "<spec-key>/aware.spec.toml"

[records.evidence]
profile = "aware.protocol.evidence.v1"
root = "docs/coordination/evidence"
role = "authority"
path_template = "<kind>/<stable-id>.json"
"""
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode()


def test_canonical_filesystem_manifest_lowers_to_neutral_contract(tmp_path: Path) -> None:
    result = admit_protocol_manifest_bytes(
        source=_manifest(),
        repository_root=tmp_path,
    )
    assert result.outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1
    assert result.manifest is not None
    assert result.manifest.protocol.name == "aware.collaboration"
    assert result.manifest.to_wire()["records"]["feed"]["role"] == "unavailable"
    assert result.manifest.bootstrap.agent_contract_ref == "repository:AGENTS.md"
    assert result.filesystem_profile is not None
    assert result.filesystem_profile.agent_contract_path == "AGENTS.md"
    assert tuple(
        binding.record_key for binding in result.filesystem_profile.record_bindings
    ) == ("evidence", "goal", "issue", "specification")
    assert result.filesystem_profile.record_bindings[1].root == "docs/goals"


def test_at_use_resolution_rechecks_concrete_target_containment(
    tmp_path: Path,
) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / "docs").symlink_to(outside, target_is_directory=True)

    result = resolve_repository_path_at_use(
        repository_root=tmp_path,
        relative_path="docs/goals/2026/09/20/goal-2026-09-20-example.md",
        field_name="records.goal.target",
    )

    assert result.path is None
    assert result.diagnostics == (
        "repository_containment_error:records.goal.target",
    )


def test_unknown_record_version_reaches_strict_admission(tmp_path: Path) -> None:
    result = admit_protocol_manifest_bytes(
        source=_manifest(**{"aware.goal.markdown.v1": "aware.goal.markdown.v999"}),
        repository_root=tmp_path,
    )
    assert result.outcome is ProtocolAdmissionOutcomeKind.FOREIGN_PROFILE
    assert result.diagnostics == (
        "record_profile_mismatch:goal:aware.goal.markdown.v999",
    )


def test_record_family_swap_reaches_strict_admission(tmp_path: Path) -> None:
    result = admit_protocol_manifest_bytes(
        source=_manifest(**{"aware.goal.markdown.v1": "aware.issue.markdown.v1"}),
        repository_root=tmp_path,
    )
    assert result.outcome is ProtocolAdmissionOutcomeKind.FOREIGN_PROFILE
    assert result.diagnostics == (
        "record_profile_mismatch:goal:aware.issue.markdown.v1",
    )


def test_parent_traversal_is_schema_rejected(tmp_path: Path) -> None:
    result = admit_protocol_manifest_bytes(
        source=_manifest(**{"docs/goals": "docs/../../outside"}),
        repository_root=tmp_path,
    )
    assert result.outcome is ProtocolAdmissionOutcomeKind.MALFORMED_V1
    assert any(
        item.startswith("schema_error:records.goal.root:")
        for item in result.diagnostics
    )


def test_existing_symlink_cannot_escape_repository_root(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "goals").symlink_to(outside, target_is_directory=True)

    result = admit_protocol_manifest_bytes(
        source=_manifest(),
        repository_root=tmp_path,
    )

    assert result.outcome is ProtocolAdmissionOutcomeKind.MALFORMED_V1
    assert result.diagnostics == (
        "repository_containment_error:records.goal.root",
    )


def test_operator_configuration_is_not_manifest_truth(tmp_path: Path) -> None:
    result = admit_protocol_manifest_bytes(
        source=_manifest() + b'\n[operator]\nkind = "aware-cli"\n',
        repository_root=tmp_path,
    )
    assert result.outcome is ProtocolAdmissionOutcomeKind.MALFORMED_V1
    assert any("operator" in item for item in result.diagnostics)


def test_service_authority_is_not_silently_run_as_filesystem(
    tmp_path: Path,
) -> None:
    result = admit_protocol_manifest_bytes(
        source=_manifest(**{
            'authority_mode = "filesystem"': (
                'authority_mode = "service_api"\n'
                'authority_ref = "service:customer-collaboration"'
            )
        }),
        repository_root=tmp_path,
    )
    assert result.outcome is ProtocolAdmissionOutcomeKind.AUTHORITY_UNAVAILABLE
    assert result.diagnostics == (
        "filesystem_adapter_requires_filesystem_authority",
    )


def test_bytes_entrance_requires_repository_context() -> None:
    with pytest.raises(TypeError, match="repository_root"):
        admit_protocol_manifest_bytes(source=_manifest())  # type: ignore[call-arg]


def test_on_disk_entrance_returns_contextual_canonical_result(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_bytes(_manifest())

    result = admit_protocol_manifest(
        manifest_path=manifest,
        repository_root=tmp_path,
    )

    assert result.outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1
    assert result.source_sha256 is not None
    assert result.filesystem_profile is not None


def test_outside_manifest_is_refused_before_content_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    external = tmp_path / "outside" / "aware.protocol.toml"
    external.parent.mkdir()
    external.write_bytes(_manifest())

    def unexpected_read(_path: Path) -> bytes:
        raise AssertionError("outside manifest content must not be read")

    monkeypatch.setattr(Path, "read_bytes", unexpected_read)

    result = admit_protocol_manifest(
        manifest_path=external,
        repository_root=repository,
    )

    assert result.outcome is ProtocolAdmissionOutcomeKind.MALFORMED_V1
    assert result.source_sha256 is None
    assert result.diagnostics == ("manifest_outside_repository_root",)


def test_wrong_filename_is_refused_before_content_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = tmp_path / "other.toml"
    manifest.write_bytes(_manifest())

    def unexpected_read(_path: Path) -> bytes:
        raise AssertionError("wrong-filename content must not be read")

    monkeypatch.setattr(Path, "read_bytes", unexpected_read)

    result = admit_protocol_manifest(
        manifest_path=manifest,
        repository_root=tmp_path,
    )

    assert result.outcome is ProtocolAdmissionOutcomeKind.MALFORMED_V1
    assert result.source_sha256 is None
    assert result.diagnostics == ("manifest_filename_must_be:aware.protocol.toml",)


def test_missing_manifest_returns_typed_source_unavailable(tmp_path: Path) -> None:
    result = admit_protocol_manifest(
        manifest_path=tmp_path / "aware.protocol.toml",
        repository_root=tmp_path,
    )

    assert result.outcome is ProtocolAdmissionOutcomeKind.SOURCE_UNAVAILABLE
    assert result.source_sha256 is None
    assert result.diagnostics == ("manifest_unavailable:FileNotFoundError",)


def test_control_character_in_path_is_schema_rejected(tmp_path: Path) -> None:
    result = admit_protocol_manifest_bytes(
        source=_manifest(**{"docs/goals": "docs/\\u0000goals"}),
        repository_root=tmp_path,
    )

    assert result.outcome is ProtocolAdmissionOutcomeKind.MALFORMED_V1
    assert any(
        item.startswith("schema_error:records.goal.root:")
        for item in result.diagnostics
    )


def test_unresolvable_record_root_returns_typed_refusal(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "goals").symlink_to("goals")

    result = admit_protocol_manifest_bytes(
        source=_manifest(),
        repository_root=tmp_path,
    )

    assert result.outcome is ProtocolAdmissionOutcomeKind.MALFORMED_V1
    assert result.diagnostics[0] == (
        "repository_path_unresolvable:records.goal.root:symlink_loop"
    )
    assert result.diagnostics[1].startswith(
        "repository_path_resolution_detail:records.goal.root:"
    )


def test_unresolvable_bootstrap_is_refused_on_disk(tmp_path: Path) -> None:
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_bytes(_manifest())
    (tmp_path / "AGENTS.md").symlink_to("AGENTS.md")

    result = admit_protocol_manifest(
        manifest_path=manifest,
        repository_root=tmp_path,
    )

    assert result.outcome is ProtocolAdmissionOutcomeKind.MALFORMED_V1
    assert result.diagnostics[0] == (
        "repository_path_unresolvable:bootstrap.agent_contract:symlink_loop"
    )
    assert result.diagnostics[1].startswith(
        "repository_path_resolution_detail:bootstrap.agent_contract:"
    )


def test_missing_record_root_after_existing_prefix_is_permitted(
    tmp_path: Path,
) -> None:
    (tmp_path / "docs").mkdir()

    result = admit_protocol_manifest_bytes(
        source=_manifest(),
        repository_root=tmp_path,
    )

    assert result.outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1


def test_broken_symlink_record_root_is_unresolvable(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "goals").symlink_to("missing-target")

    result = admit_protocol_manifest_bytes(
        source=_manifest(),
        repository_root=tmp_path,
    )

    assert result.outcome is ProtocolAdmissionOutcomeKind.MALFORMED_V1
    assert result.diagnostics[0] == (
        "repository_path_unresolvable:records.goal.root:resolution_failure"
    )
    assert result.diagnostics[1] == (
        "repository_path_resolution_detail:records.goal.root:FileNotFoundError"
    )


def test_filesystem_profile_defensively_freezes_bindings(tmp_path: Path) -> None:
    result = admit_protocol_manifest_bytes(
        source=_manifest(),
        repository_root=tmp_path,
    )
    assert result.filesystem_profile is not None
    source_profile = result.filesystem_profile
    bindings = list(source_profile.record_bindings)
    profile = FilesystemProtocolProfile(
        protocol_manifest=source_profile.protocol_manifest,
        agent_contract_path=source_profile.agent_contract_path,
        record_bindings=bindings,  # type: ignore[arg-type]
    )

    bindings.clear()

    assert type(profile.record_bindings) is tuple
    assert len(profile.record_bindings) == 4
