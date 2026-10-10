"""Source-boundary proof; not a built or installed consumer qualification."""

import subprocess
import sys
import tomllib
from pathlib import Path


def test_core_metadata_has_no_service_requirement_or_implementation() -> None:
    root = Path(__file__).parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    assert project["version"] == "0.3.0"
    assert project["dependencies"] == ["aware-issue-operational-runtime>=0.1.0"]
    assert not (root / "aware_issue_runtime/participant.py").exists()
    assert not (root / "aware_issue_runtime/local_json_state.py").exists()


def test_every_core_export_resolves_with_service_and_generated_imports_blocked() -> (
    None
):
    code = """
import importlib
import importlib.abc
import importlib.util
import sys
forbidden = ('aware_local_service', 'aware_issue_local_service',
    'aware_issue_service', 'aware_workflow_ontology', 'aware_orm', 'sqlalchemy',
    'aware_file_system')
attempts = []
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(forbidden):
            attempts.append(fullname)
            raise ImportError('neutral_boundary:' + fullname)
sys.meta_path.insert(0, Guard())
import aware_issue_runtime as core
for name in core.__all__:
    getattr(core, name)
assert core.ISSUE_DEVELOPMENT_READ_PROJECTION_V2_SCHEMA
assert core.parse_issue_projection(text='# Issue: neutral',
    source_path='docs/issues/neutral.md').title == 'neutral'
removed = ('ISSUE_CHANGES_TOPIC', 'ISSUE_DEVELOPMENT_CHANGES_TOPIC',
    'ISSUE_DEVELOPMENT_EVOLUTION_ITEM_SCHEMA', 'ISSUE_PROJECTION_CAPABILITY',
    'ISSUE_PROJECTION_SCHEMA', 'ISSUE_PROJECTION_SCHEMA_DIGEST',
    'IssueProjectionLocalServiceParticipant')
for name in removed:
    assert name not in core.__all__
    try:
        getattr(core, name)
    except AttributeError:
        pass
    else:
        raise AssertionError(name)
assert importlib.util.find_spec('aware_issue_runtime.participant') is None
assert importlib.util.find_spec('aware_issue_runtime.local_json_state') is None
try:
    importlib.import_module('aware_issue_runtime.local_json_state')
except ModuleNotFoundError:
    pass
else:
    raise AssertionError('removed storage module unexpectedly resolved')
assert not attempts, attempts
assert not any(name.startswith(forbidden) for name in sys.modules)
try:
    importlib.import_module('aware_issue_local_service_runtime')
except ImportError as error:
    assert 'neutral_boundary:' in str(error)
else:
    raise AssertionError('guard was not enforced')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
