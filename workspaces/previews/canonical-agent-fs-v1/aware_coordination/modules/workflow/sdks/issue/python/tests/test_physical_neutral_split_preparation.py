"""Real migrated source boundaries; historical preparation receipts stay pinned."""

import ast
import hashlib
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement

SDK = Path(__file__).resolve().parents[1]
WORKFLOW = SDK.parents[2]
REPOSITORY = WORKFLOW.parents[3]
RUNTIME = WORKFLOW / "libs/issue_runtime"
SERVICE = WORKFLOW / "libs/issue_local_service_runtime"
API_VIEW = WORKFLOW / "libs/issue_api_view_source_adapters/python"
ADAPTER = SDK.parent / "service_adapter/python"


def literal_assignments(path):
    return {
        target.id: ast.literal_eval(node.value)
        for node in ast.parse(path.read_text()).body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
        and target.id
        in {"_EXPORT_MODULES", "_VIEW_STATE_EXPORTS", "_PARTICIPANT_EXPORTS"}
    }


def project(path):
    return tomllib.loads(path.read_text())["project"]


def test_existing_service_home_is_registered_not_a_proposed_second_owner():
    packages = tomllib.loads((WORKFLOW / "aware.module.toml").read_text())["packages"]
    matches = [
        package
        for package in packages
        if package["id"] == "issue_local_service_runtime"
    ]
    assert len(matches) == 1
    assert matches[0]["manifest"] == "libs/issue_local_service_runtime/pyproject.toml"
    assert (
        project(SERVICE / "pyproject.toml")["name"]
        == "aware-issue-local-service-runtime"
    )


def test_projection_and_operational_participants_remain_distinct():
    assert not (RUNTIME / "aware_issue_runtime/participant.py").exists()
    projection = ast.parse(
        (
            SERVICE / "aware_issue_local_service_runtime/projection_participant.py"
        ).read_text()
    )
    operational = ast.parse(
        (SERVICE / "aware_issue_local_service_runtime/participant.py").read_text()
    )
    assert any(
        isinstance(node, ast.ClassDef)
        and node.name == "IssueProjectionLocalServiceParticipant"
        for node in projection.body
    )
    assert any(
        isinstance(node, ast.ClassDef)
        and node.name == "IssueOperationalLocalServiceParticipant"
        for node in operational.body
    )
    assert not any(
        isinstance(node, ast.ClassDef)
        and node.name == "IssueProjectionLocalServiceParticipant"
        for node in operational.body
    )


def test_runtime_service_dependency_and_exports_are_physically_removed():
    requirements = [
        Requirement(text)
        for text in project(RUNTIME / "pyproject.toml")["dependencies"]
    ]
    assert not any(
        requirement.name == "aware-local-service-runtime" and requirement.marker is None
        for requirement in requirements
    )
    module = ast.parse(
        (
            SERVICE / "aware_issue_local_service_runtime/projection_participant.py"
        ).read_text()
    )
    assert any(
        isinstance(node, ast.ImportFrom)
        and node.module == "aware_local_service_runtime"
        for node in module.body
    )
    assert "_PARTICIPANT_EXPORTS" not in literal_assignments(
        RUNTIME / "aware_issue_runtime/__init__.py"
    )


@pytest.mark.parametrize(
    "module,dependency",
    [
        ("client", "aware_content_service_dto"),
        ("markdown_import", "aware_issue_service_dto"),
        ("view_state_providers", "aware_workflow_ontology_dto"),
    ],
)
def test_three_service_facing_modules_require_actual_move_not_optional_metadata(
    module, dependency
):
    assert not (SDK / "aware_issue_sdk" / (module + ".py")).exists()
    tree = ast.parse(
        (ADAPTER / "aware_issue_service_sdk_adapter" / (module + ".py")).read_text()
    )
    assert any(
        isinstance(node, ast.ImportFrom)
        and node.module
        and node.module.startswith(dependency)
        for node in tree.body
    )


def test_exact_existing_sdk_facade_disposition():
    values = literal_assignments(SDK / "aware_issue_sdk/__init__.py")
    exports = values["_EXPORT_MODULES"]
    moved = literal_assignments(
        ADAPTER / "aware_issue_service_sdk_adapter/__init__.py"
    )["_EXPORT_MODULES"]
    assert len(moved) == 13
    assert set(moved).isdisjoint(exports)
    assert "_VIEW_STATE_EXPORTS" not in values
    assert moved["IssueSdkClient"] == "aware_issue_service_sdk_adapter.client"
    assert (
        moved["IssueMarkdownImportPlan"]
        == "aware_issue_service_sdk_adapter.markdown_import"
    )
    assert exports["IssueSdkOperationClient"] == "aware_issue_sdk.operation"
    assert exports["IssueProviderResultError"] == "aware_issue_sdk.operation"


@pytest.mark.parametrize(
    "name", ["development_read_projection", "local_files", "local_state"]
)
def test_pydantic_remains_a_real_neutral_dependency(name):
    tree = ast.parse((SDK / "aware_issue_sdk" / (name + ".py")).read_text())
    assert any(
        isinstance(node, ast.ImportFrom) and node.module == "pydantic"
        for node in tree.body
    )


@pytest.mark.parametrize(
    "filename",
    [
        "process_generation_composition.py",
        "agent_process_composition.py",
        "workspace_feature_composition.py",
    ],
)
def test_three_dev_callers_use_explicit_service_owner(filename):
    path = (
        REPOSITORY
        / "workspaces/aware_dev/modules/dev/services/local_dev/aware_local_dev_service"
        / filename
    )
    tree = ast.parse(path.read_text())
    assert any(
        isinstance(node, ast.ImportFrom)
        and node.module == "aware_issue_local_service_runtime"
        and any(alias.name == "ISSUE_PROJECTION_CAPABILITY" for alias in node.names)
        for node in tree.body
    )


def test_registered_api_view_caller_has_service_owner_dependency():
    packages = tomllib.loads((WORKFLOW / "aware.module.toml").read_text())["packages"]
    matches = [
        package
        for package in packages
        if package["id"] == "libs_issue_api_view_source_adapters_python"
    ]
    assert len(matches) == 1
    assert matches[0]["manifest"] == (
        "libs/issue_api_view_source_adapters/python/pyproject.toml"
    )
    names = {
        Requirement(text).name
        for text in project(API_VIEW / "pyproject.toml")["dependencies"]
    }
    assert "aware-issue-runtime" in names
    assert "aware-issue-local-service-runtime" in names


def test_api_view_caller_separates_service_capability_and_neutral_schema():
    tree = ast.parse(
        (API_VIEW / "aware_issue_api_view_source_adapters/local_service.py").read_text()
    )
    names = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "aware_issue_runtime"
        for alias in node.names
    }
    assert names == {
        "ISSUE_DEVELOPMENT_READ_PROJECTION_V2_SCHEMA",
    }
    assert any(
        isinstance(node, ast.ImportFrom)
        and node.module == "aware_issue_local_service_runtime"
        and any(alias.name == "ISSUE_PROJECTION_CAPABILITY" for alias in node.names)
        for node in tree.body
    )


@pytest.mark.parametrize("remove_capability", [False, True])
def test_real_api_view_import_survives_core_capability_absence(remove_capability):
    # The real migrated adapter must not consult an old core export.
    code = """
import importlib
import aware_issue_runtime as core
if REMOVE_CAPABILITY:
    original = core.__getattr__
    core.__dict__.pop('ISSUE_PROJECTION_CAPABILITY', None)
    def without_capability(name):
        if name == 'ISSUE_PROJECTION_CAPABILITY':
            raise AttributeError(name)
        return original(name)
    core.__getattr__ = without_capability
assert core.ISSUE_DEVELOPMENT_READ_PROJECTION_V2_SCHEMA
adapter = importlib.import_module('aware_issue_api_view_source_adapters.local_service')
assert adapter.ISSUE_PROJECTION_CAPABILITY == 'issue.projection'
assert adapter.ISSUE_DEVELOPMENT_READ_PROJECTION_V2_SCHEMA == (
    core.ISSUE_DEVELOPMENT_READ_PROJECTION_V2_SCHEMA)
""".replace("REMOVE_CAPABILITY", repr(remove_capability))
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "source,destination",
    [
        ("test_participant.py", "test_projection_participant.py"),
        (
            "test_real_process_reconstruction.py",
            "test_projection_real_process_reconstruction.py",
        ),
        (
            "test_restart_reconstruction.py",
            "test_projection_restart_reconstruction.py",
        ),
        (
            "test_real_workspace_composition.py",
            "test_projection_real_workspace_composition.py",
        ),
    ],
)
def test_frozen_projection_test_destinations_do_not_replace_operational_tests(
    source, destination
):
    assert not (RUNTIME / "tests" / source).exists()
    assert (SERVICE / "tests/test_participant.py").is_file()
    assert (SERVICE / "tests" / destination).is_file()
    assert destination != "test_participant.py"


def test_projection_implementation_identity_matches_service_owner():
    tree = ast.parse(
        (
            SERVICE / "aware_issue_local_service_runtime/projection_participant.py"
        ).read_text()
    )
    values = [
        keyword.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for keyword in node.keywords
        if keyword.arg == "implementation_version"
        and isinstance(keyword.value, ast.Constant)
    ]
    assert values == ["aware-issue-local-service-runtime-0.1.2"]
    assert project(SERVICE / "pyproject.toml")["version"] == "0.1.2"
    # Authored source identity, not an installed Service receipt.


def test_local_dev_transport_test_also_consumes_moved_service_exports():
    tree = ast.parse(
        (
            REPOSITORY
            / "workspaces/aware_dev/modules/dev/services/local_dev/tests/test_issue_projection_transport.py"
        ).read_text()
    )
    names = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "aware_issue_local_service_runtime"
        for alias in node.names
    }
    assert names == {"ISSUE_DEVELOPMENT_CHANGES_TOPIC", "ISSUE_PROJECTION_CAPABILITY"}


def test_api_view_keeps_test_extra_without_default_ontology_edge():
    metadata = project(API_VIEW / "pyproject.toml")
    default_names = {Requirement(value).name for value in metadata["dependencies"]}
    test_names = {
        Requirement(value).name for value in metadata["optional-dependencies"]["test"]
    }
    assert "aware-ontology-runtime" not in default_names
    assert "aware-ontology-runtime" in test_names
    assert "aware-ontology" in (API_VIEW / "pyproject.toml").read_text()
    boundary = ast.parse((API_VIEW / "tests/test_boundaries.py").read_text())
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "read_text"
        for node in ast.walk(boundary)
    )
    # Actual caller boundary tests are in the Runtime migration receipt;
    # this source check does not qualify a neutral transitive closure.


def test_breaking_successor_needs_spec_range_qualification_not_silent_widening():
    path = (
        REPOSITORY
        / "workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/pyproject.toml"
    )
    requirements = {
        requirement.name: requirement
        for text in project(path)["optional-dependencies"]["governed"]
        for requirement in (Requirement(text),)
    }
    assert "0.9.1" in requirements["aware-issue-sdk"].specifier
    assert "0.10.0" not in requirements["aware-issue-sdk"].specifier
    assert "0.8.1" in requirements["aware-issue-fs-adapter"].specifier
    assert "0.9.0" not in requirements["aware-issue-fs-adapter"].specifier


def test_ordinary_operation_implementation_remains_exact_accepted_source():
    assert (
        hashlib.sha256((SDK / "aware_issue_sdk/operation.py").read_bytes()).hexdigest()
        == "4610f8f6c7738a429a7a770b5afd6941ee15bca934b5731104d35a6fd5f577dd"
    )
