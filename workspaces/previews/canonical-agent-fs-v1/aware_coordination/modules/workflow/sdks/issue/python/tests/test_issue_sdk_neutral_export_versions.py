"""Successor source export/range checks, not installed neutral clearance."""

import ast
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from test_issue_sdk_authored_closure import source_contract

SDK = Path(__file__).resolve().parents[1]
ISSUE = SDK.parent
WORKFLOW = ISSUE.parents[1]


def project(path):
    return tomllib.loads(path.read_text())["project"]


def dependencies(path):
    return {
        requirement.name: requirement
        for value in project(path)["dependencies"]
        for requirement in (Requirement(value),)
    }


@pytest.fixture(scope="module")
def ordinary_contract():
    return source_contract()


def test_all_seventeen_real_roots_resolve_without_optional_or_lower_imports(
    ordinary_contract,
):
    names = [
        root.removeprefix("aware_issue_sdk.")
        for schema in ordinary_contract.manifest.schema_slices
        for root in schema.root_type_refs
    ]
    assert len(names) == 17
    # This is a fresh source diagnostic, not an installed package claim.
    code = """
import importlib.abc
import sys
blocked = []
prefixes = ('aware_content_service', 'aware_issue_service', 'aware_issues',
    'aware_workflow_ontology', 'aware_orm', 'aware_local_service',
    'aware_file_system', 'aware_protocol', 'aware_issue_fs_adapter',
    'aware_workspace_operator', 'aware_specification')
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(prefixes):
            blocked.append(fullname)
            raise ImportError('optional_or_lower_import_forbidden:' + fullname)
sys.meta_path.insert(0, Guard())
import aware_issue_sdk as sdk
names = NAMES
for name in names:
    assert name in sdk.__all__, name
    value = getattr(sdk, name)
    assert value is getattr(sdk, name)
    assert value.__module__ == 'aware_issue_sdk.operation', name
assert not blocked, blocked
assert not any(name.startswith(prefixes) for name in sys.modules)
for name, module in sdk._EXPORT_MODULES.items():
    if module == 'aware_issue_sdk.source_change':
        assert name in sdk.__all__, name
        getattr(sdk, name)
assert not blocked, blocked
# Removed explicit exports must refuse without an optional import attempt.
try:
    sdk.IssueApiClient
except AttributeError:
    pass
else:
    raise AssertionError('removed API lookup unexpectedly resolved')
assert not blocked, blocked
# Prove the import guard itself is active.
try:
    __import__('aware_issue_service_dto')
except ImportError as error:
    assert 'optional_or_lower_import_forbidden:' in str(error)
else:
    raise AssertionError('guard did not refuse generated import')
assert blocked == ['aware_issue_service_dto']
""".replace("NAMES", repr(names))
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_public_lazy_map_and_advertised_names_match():
    module = ast.parse((SDK / "aware_issue_sdk/__init__.py").read_text())
    values = {
        target.id: ast.literal_eval(node.value)
        for node in module.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
        and target.id in {"_EXPORT_MODULES", "_VIEW_STATE_EXPORTS", "__all__"}
    }
    advertised = values["__all__"]
    assert len(advertised) == len(set(advertised))
    assert "_VIEW_STATE_EXPORTS" not in values
    assert set(advertised) == set(values["_EXPORT_MODULES"])


@pytest.mark.parametrize(
    "relative_path,version",
    [
        ("python/pyproject.toml", "0.10.1"),
        ("filesystem_adapter/python/pyproject.toml", "0.9.1"),
        ("cli/python/pyproject.toml", "0.7.1"),
    ],
)
def test_compatible_successor_versions(relative_path, version):
    assert project(ISSUE / relative_path)["version"] == version


@pytest.mark.parametrize(
    "relative_path,name,old,current,next_minor",
    [
        (
            "filesystem_adapter/python/pyproject.toml",
            "aware-issue-sdk",
            "0.10.0",
            "0.10.1",
            "0.11.0",
        ),
        (
            "cli/python/pyproject.toml",
            "aware-issue-sdk",
            "0.10.0",
            "0.10.1",
            "0.11.0",
        ),
        (
            "cli/python/pyproject.toml",
            "aware-issue-fs-adapter",
            "0.9.0",
            "0.9.1",
            "0.10.0",
        ),
    ],
)
def test_requesting_new_boundary_cannot_resolve_old_or_unqualified_minor(
    relative_path, name, old, current, next_minor
):
    requirement = dependencies(ISSUE / relative_path)[name]
    assert old not in requirement.specifier
    assert old + "+custody.1" not in requirement.specifier
    assert current in requirement.specifier
    assert next_minor not in requirement.specifier
    assert not requirement.extras
    assert requirement.url is None


def test_source_dependency_ranges_accept_selected_canonical_versions():
    projects = {
        value["name"]: value
        for path in (
            SDK / "pyproject.toml",
            ISSUE / "filesystem_adapter/python/pyproject.toml",
            ISSUE / "cli/python/pyproject.toml",
        )
        for value in (project(path),)
    }
    for selected in projects.values():
        for requirement_text in selected["dependencies"]:
            requirement = Requirement(requirement_text)
            if requirement.name in projects:
                assert projects[requirement.name]["version"] in requirement.specifier, (
                    requirement_text
                )


def test_spec_governed_ranges_require_separate_breaking_qualification():
    repository = WORKFLOW.parents[3]
    manifest = repository / (
        "workspaces/aware_kernel/modules/specification/sdks/specification/"
        "python/fs_adapter/pyproject.toml"
    )
    governed = {
        requirement.name: requirement
        for text in project(manifest)["optional-dependencies"]["governed"]
        for requirement in (Requirement(text),)
    }
    assert "0.9.1" in governed["aware-issue-sdk"].specifier
    assert "0.8.1" in governed["aware-issue-fs-adapter"].specifier
    assert "0.10.0" not in governed["aware-issue-sdk"].specifier
    assert "0.9.0" not in governed["aware-issue-fs-adapter"].specifier


def test_api_and_view_extras_leave_core_with_their_implementations():
    metadata = project(SDK / "pyproject.toml")
    default = {Requirement(text).name for text in metadata["dependencies"]}
    assert "service" not in metadata["optional-dependencies"]
    assert "view" not in metadata["optional-dependencies"]
    adapter = project(ISSUE / "service_adapter/python/pyproject.toml")
    optional = {
        Requirement(text).name
        for extra in ("service", "view")
        for text in adapter["optional-dependencies"][extra]
    }
    assert default.isdisjoint(optional)


def test_runtime_service_and_storage_edges_are_physically_removed():
    requirements = dependencies(WORKFLOW / "libs/issue_runtime/pyproject.toml")
    assert "aware-local-service-runtime" not in requirements
    assert "aware-file-system" not in requirements
    assert not (
        WORKFLOW / "libs/issue_runtime/aware_issue_runtime/local_json_state.py"
    ).exists()
    repository = WORKFLOW.parents[3]
    assert (
        repository / "workspaces/aware_kernel/modules/filesystem/libs/file_system/"
        "python/aware_file_system/local_json_state.py"
    ).is_file()


def test_canonical_sdk_wheel_does_not_silently_prune_optional_source():
    metadata = tomllib.loads((SDK / "pyproject.toml").read_text())
    wheel = metadata["tool"]["hatch"]["build"]["targets"]["wheel"]
    assert wheel["packages"] == ["aware_issue_sdk"]
    assert not wheel.get("exclude")
    assert not (SDK / "aware_issue_sdk/client.py").exists()
    module = ast.parse(
        (
            ISSUE / "service_adapter/python/aware_issue_service_sdk_adapter/client.py"
        ).read_text()
    )
    assert any(
        isinstance(node, ast.ImportFrom)
        and node.module
        and node.module.startswith("aware_content_service_dto")
        for node in module.body
    )
    # Real source move, not a wheel exclusion recipe or public installation.
