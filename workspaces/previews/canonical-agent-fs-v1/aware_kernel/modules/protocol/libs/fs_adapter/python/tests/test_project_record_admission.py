"""Project source declaration admission; not Project Object or target issuance."""

from pathlib import Path

from aware_protocol_fs_adapter import (
    admit_protocol_manifest_bytes,
    match_project_path,
)
from aware_protocol_runtime import ProtocolAdmissionOutcomeKind


MANIFEST = """aware = 1

[protocol]
name = "aware.collaboration"
profile = "aware.collaboration.fs_v3"
semantic_version = 3

[target]
kind = "repository"
authority_mode = "filesystem"

[bootstrap]
agent_contract = "AGENTS.md"

[records.goal]
profile = "aware.goal.phase.markdown.v1"
role = "authority"
root = "customer/goals"
path_template = "goal-YYYY-MM-DD-<slug>.md"

[records.issue]
profile = "aware.issue.markdown.v1"
role = "authority"
root = "customer/issues"
path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"

[records.feed]
profile = "aware.feed.projection.v1"
role = "unavailable"

[records.specification]
profile = "specification_fs_v1"
role = "unavailable"

[records.evidence]
profile = "aware.protocol.evidence.v1"
role = "unavailable"

[records.project]
profile = "aware.project.context.toml.v1"
role = "authority"
root = "customer/projects"
path_template = "project-<slug>.toml"
"""


def _admit(root: Path, source: str = MANIFEST):
    return admit_protocol_manifest_bytes(
        source=source.encode("utf-8"), repository_root=root
    )


def test_project_binding_is_admitted_without_claiming_object_or_target(tmp_path: Path) -> None:
    result = _admit(tmp_path)
    assert result.outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1
    assert result.source_sha256 is not None
    assert result.filesystem_profile is not None
    assert result.manifest is not None
    assert result.manifest.protocol.profile == "aware.collaboration.fs_v3"
    assert result.manifest.to_wire()["records"]["project"] == {
        "profile": "aware.project.context.toml.v1", "role": "authority"
    }
    assert any(
        binding.record_key == "project"
        and binding.root == "customer/projects"
        and binding.path_template == "project-<slug>.toml"
        for binding in result.filesystem_profile.record_bindings
    )


def test_project_is_not_silently_added_to_existing_profiles(tmp_path: Path) -> None:
    for profile, version in (("aware.collaboration.fs_v1", 1), ("aware.collaboration.fs_v2", 2)):
        source = MANIFEST.replace("aware.collaboration.fs_v3", profile).replace(
            "semantic_version = 3", f"semantic_version = {version}"
        )
        result = _admit(tmp_path, source)
        assert result.outcome is ProtocolAdmissionOutcomeKind.FOREIGN_PROFILE
        assert result.diagnostics == ("project_record_requires_fs_v3",)


def test_fs_v3_requires_declared_project_record(tmp_path: Path) -> None:
    result = _admit(tmp_path, MANIFEST.split("[records.project]")[0])
    assert result.outcome is ProtocolAdmissionOutcomeKind.MALFORMED_V1
    assert result.diagnostics == ("project_record_required_for_fs_v3",)


def test_wrong_project_family_and_version_are_foreign(tmp_path: Path) -> None:
    for other in ("aware.issue.markdown.v1", "aware.project.context.toml.v999"):
        result = _admit(tmp_path, MANIFEST.replace("aware.project.context.toml.v1", other))
        assert result.outcome is ProtocolAdmissionOutcomeKind.FOREIGN_PROFILE
        assert result.diagnostics == (f"record_profile_mismatch:project:{other}",)


def test_project_requires_authority_and_finite_template(tmp_path: Path) -> None:
    projected = _admit(tmp_path, MANIFEST.replace(
        '[records.project]\nprofile = "aware.project.context.toml.v1"\nrole = "authority"',
        '[records.project]\nprofile = "aware.project.context.toml.v1"\nrole = "projection"',
    ))
    assert projected.diagnostics == ("project_record_requires_authority",)
    arbitrary = _admit(tmp_path, MANIFEST.replace(
        'path_template = "project-<slug>.toml"',
        'path_template = "<anything>.toml"',
    ))
    assert arbitrary.diagnostics == ("project_template_unsupported",)


def test_project_root_lexical_and_containment_refusals(tmp_path: Path) -> None:
    traversal = _admit(tmp_path, MANIFEST.replace(
        'root = "customer/projects"', 'root = "customer/../projects"'
    ))
    assert traversal.outcome is ProtocolAdmissionOutcomeKind.MALFORMED_V1
    assert any(item.startswith("schema_error:records.project.root:") for item in traversal.diagnostics)

    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / "customer").mkdir()
    (tmp_path / "customer" / "projects").symlink_to(outside, target_is_directory=True)
    escaped = _admit(tmp_path)
    assert escaped.outcome is ProtocolAdmissionOutcomeKind.MALFORMED_V1
    assert escaped.diagnostics == ("repository_containment_error:records.project.root",)


def test_project_root_existing_file_refuses_but_missing_root_is_allowed(tmp_path: Path) -> None:
    assert _admit(tmp_path).outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1
    (tmp_path / "customer").mkdir()
    (tmp_path / "customer" / "projects").write_text("not a directory")
    result = _admit(tmp_path)
    assert result.diagnostics == ("project_root_not_directory",)


def test_location_slug_is_not_project_identity() -> None:
    assert match_project_path("project-<slug>.toml", "project-alpha-2.toml") == "alpha-2"
    for tail in ("sub/project-alpha.toml", "project-Alpha.toml", "project-../x.toml", "alpha.toml"):
        assert match_project_path("project-<slug>.toml", tail) is None
    assert match_project_path("<slug>.toml", "project-alpha.toml") is None
