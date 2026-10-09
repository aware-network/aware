"""Source metadata/lazy-integration proof, not a resolved or installed closure."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
from aware_protocol_fs_adapter import (
    SpecificationDraftSelectionError,
    admit_specification_draft_target,
    bind_specification_draft_physical_plan,
    release_specification_draft_target,
)
from aware_protocol_fs_adapter import specification_draft_target as implementation
from packaging.requirements import Requirement
from test_specification_selection import TARGET, source

PACKAGE = Path(__file__).parents[1]
OWNER_EXPORTS = (
    "require_retained_package_plan",
    "observe_package_plan",
    "require_retained_package_postimage",
    "retain_package_postimage_read",
    "require_package_postimage_read",
    "validate_package_postimage_read",
    "release_package_postimage_read",
)


def metadata():
    return tomllib.loads((PACKAGE / "pyproject.toml").read_text(encoding="utf-8"))


def test_version_and_default_dependency_contract():
    project = metadata()["project"]
    assert project["version"] == "0.6.3"
    assert project["dependencies"] == [
        "aware-protocol-runtime>=0.1.0",
        "aware-protocol-sdk>=0.3.0,<0.4.0",
        "jsonschema>=4.23.0,<5.0.0",
    ]
    assert project["optional-dependencies"]["draft"] == [
        "aware-file-system>=0.3.0,<0.4.0"
    ]
    assert metadata()["tool"]["uv"]["sources"]["aware-file-system"] == {
        "workspace": True
    }


@pytest.mark.parametrize(
    ("version", "admitted"),
    [
        ("0.1.5", False),
        ("0.1.6", False),
        ("0.2.0", False),
        ("0.2.1", False),
        ("0.3.0", True),
        ("0.3.1", True),
        ("0.4.0", False),
    ],
)
def test_nominated_physical_release_bounds(version, admitted):
    requirement = Requirement(
        metadata()["project"]["optional-dependencies"]["draft"][0]
    )
    assert requirement.name == "aware-file-system"
    assert requirement.specifier.contains(version) is admitted


def test_default_reader_works_without_optional_owner_imports(tmp_path):
    root = next(p for p in PACKAGE.parents if (p / ".git").exists())
    roots = [
        str(root / p)
        for p in (
            "workspaces/aware_kernel/modules/protocol/libs/runtime/python",
            "workspaces/aware_kernel/modules/protocol/sdks/protocol/python",
            "workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python",
        )
    ]
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(source())
    code = f"""
import sys
from pathlib import Path
sys.path[:0] = {roots!r}
attempts = []
class BlockOwners:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('aware_file_system', 'aware_issue', 'aware_specification')):
            attempts.append(fullname)
            raise ModuleNotFoundError(fullname)
sys.meta_path.insert(0, BlockOwners())
from aware_protocol_fs_adapter import (
    admit_specification_selection, require_specification_selection,
    release_specification_selection,
)
admission = admit_specification_selection(
    repository_root=Path({str(tmp_path)!r}),
    manifest_path=Path('aware.protocol.toml'),
    selected_manifest_paths=({TARGET!r},),
)
assert admission.selection is not None
try:
    require_specification_selection(admission.selection)
    admission.selection.revalidate()
finally:
    release_specification_selection(admission.selection)
assert not attempts, attempts
"""
    subprocess.run([sys.executable, "-I", "-B", "-c", code], check=True, timeout=30)


@pytest.mark.parametrize("missing", [None, *OWNER_EXPORTS])
def test_missing_or_incompatible_owner_exports_refuse_before_effects(
    tmp_path, monkeypatch, missing
):
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(source())
    parent = tmp_path / "customer/specs"
    parent.mkdir(parents=True)
    target = admit_specification_draft_target(
        repository_root=tmp_path,
        manifest_path=manifest,
        selected_manifest_path=TARGET,
        expected_manifest_sha256="sha256:"
        + hashlib.sha256(manifest.read_bytes()).hexdigest(),
    )
    attempts = []

    def forbidden_call(*args, **kwargs):
        pytest.fail("incompatible physical owner must not be invoked")

    exports = dict.fromkeys(OWNER_EXPORTS, forbidden_call)
    if missing is not None:
        exports[missing] = None

    def selected_import(name):
        attempts.append(name)
        if missing is None:
            raise ModuleNotFoundError(name)
        return SimpleNamespace(**exports)

    monkeypatch.setattr(implementation, "import_module", selected_import)
    try:
        with pytest.raises(SpecificationDraftSelectionError) as caught:
            bind_specification_draft_physical_plan(target, physical_plan=object())
        assert caught.value.code == "specification_draft_integration_unavailable"
        assert attempts == ["aware_file_system.retained_package"]
        assert target.phase == "retired"
        assert not tuple(parent.iterdir())
    finally:
        release_specification_draft_target(target)
