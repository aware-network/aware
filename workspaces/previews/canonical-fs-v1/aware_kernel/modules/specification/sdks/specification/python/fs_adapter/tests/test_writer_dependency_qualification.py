"""Source reader parity; producer version readiness is a separate owner gate."""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[9]
PROTOCOL_ROOTS = (
    "workspaces/aware_kernel/modules/protocol/libs/runtime/python",
    "workspaces/aware_kernel/modules/protocol/sdks/protocol/python",
    "workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python",
)
PROTOCOL04_REVISION = "b338211b0bb2"
READER_ROOTS = (
    "workspaces/aware_kernel/modules/specification/libs/runtime/python",
    "workspaces/aware_kernel/modules/specification/libs/fs_source_contract/python",
    "workspaces/aware_kernel/modules/specification/libs/fs_adapter/python",
    "workspaces/aware_kernel/modules/specification/sdks/specification/python/public",
    "workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter",
    "workspaces/aware_kernel/modules/specification/sdks/specification/python/cli",
    "workspaces/aware_kernel/libs/command_runtime/python",
)

_spec = importlib.util.spec_from_file_location(
    "spec_writer_dependency_reader_fixtures",
    Path(__file__).with_name("test_protocol_selection.py"),
)
assert _spec is not None and _spec.loader is not None
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)
canonical_tree = _fixtures.canonical_tree
selected = _fixtures.selected

# Imports are rejected in a fresh interpreter, not inferred from a source scan.
# The command still runs the real Protocol issuer, SDK and strict SPEC owner.
READ = """
import importlib.abc, json, sys
sys.path[:0] = json.loads(sys.argv[1])
class RejectWriterImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {
            'aware_file_system', 'aware_issue_sdk', 'aware_issue_fs_adapter',
            'aware_issue_service_api', 'aware_issue_service_dto',
            'aware_workflow_ontology_dto', 'aware_specification',
        }:
            raise ImportError('reader_requested_writer_or_service:' + fullname)
sys.meta_path.insert(0, RejectWriterImports())
from aware_specification_cli.main import main
raise SystemExit(main(json.loads(sys.argv[2])))
"""


def roots(protocol_base):
    return [str(ROOT / p) for p in READER_ROOTS] + [
        str(protocol_base / p) for p in PROTOCOL_ROOTS
    ]


@pytest.fixture(scope="session")
def protocol04_source_base(tmp_path_factory):
    """Use a verified explicit mirror, or extract the exact historical revision."""
    supplied = os.environ.get("AWARE_SPEC_PROTOCOL04_SOURCE_BASE")
    if supplied:
        base = Path(supplied)
    else:
        base = tmp_path_factory.mktemp("protocol04-source")
        archive = subprocess.check_output(
            ["git", "-C", str(ROOT), "archive", PROTOCOL04_REVISION, *PROTOCOL_ROOTS]
        )
        subprocess.run(
            ["tar", "-x", "-C", str(base)], input=archive, check=True, timeout=30
        )
    for path in PROTOCOL_ROOTS:
        assert (base / path).is_dir()
    tracked = subprocess.check_output(
        [
            "git",
            "-C",
            str(ROOT),
            "ls-tree",
            "-r",
            "--name-only",
            PROTOCOL04_REVISION,
            "--",
            *PROTOCOL_ROOTS,
        ],
        text=True,
    ).splitlines()
    actual = {
        file.relative_to(base).as_posix()
        for path in PROTOCOL_ROOTS
        for file in (base / path).rglob("*")
        if file.is_file()
    }
    assert set(tracked) == actual
    for path in tracked:
        assert not (base / path).is_symlink()
        committed = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", PROTOCOL04_REVISION + ":" + path]
        )
        assert (base / path).read_bytes() == committed, path
    return base


@pytest.mark.parametrize("command", ["observe", "iteration-identity"])
@pytest.mark.parametrize("condition", ["valid", "stale-source", "symlink"])
def test_reader_subprocess_parity_without_writer_imports(
    selected, protocol04_source_base, command, condition
):
    base, _ = selected
    args = [
        command,
        "--repository-root",
        str(base),
        "--spec-manifest",
        _fixtures.ROOT + "/aware.spec.toml",
    ]
    if command == "iteration-identity":
        args += ["--iteration-ref", _fixtures.ITERATION]
    if condition == "stale-source":
        args += ["--expected-source-digest", "sha256:" + "b" * 64]
    if condition == "symlink":
        original = base / _fixtures.ROOT / "SPEC.md"
        original.rename(original.with_name("original-spec.txt"))
        original.symlink_to("original-spec.txt")
    before = _fixtures.bodies(base)
    outcomes = []
    for protocol_base in (protocol04_source_base, ROOT):
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                READ,
                json.dumps(roots(protocol_base)),
                json.dumps(args),
            ],
            cwd=base,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.stderr == ""
        expected_exit = 0 if condition == "valid" else 2
        assert result.returncode == expected_exit, result.stdout
        payload = json.loads(result.stdout)
        if condition == "valid":
            assert payload["work_authority"] is payload["phase_acceptance"] is False
            assert payload["retained_capability_exported"] is False
        else:
            assert payload["effect"] == "none"
        outcomes.append((result.returncode, payload))
        assert _fixtures.bodies(base) == before
    assert outcomes[0] == outcomes[1]


def test_accepted_neutral_profile_satisfies_direct_governed_requirements():
    """Consume the owner recipe, not the service-coupled internal metadata."""
    script = """
import hashlib, json, sys, tomllib
from pathlib import Path
repository = Path(sys.argv[1])
sys.path[:0] = [str(repository / 'docs/specs/aware-portable-protocol/conformance')]
import project_issue_draft_suppliers as owner
bodies, plan = owner.projection(repository)
packages = {
    name: tomllib.loads(bodies[root + '/pyproject.toml'].decode())['project']
    for name, (root, _) in owner.PACKAGES.items()
}
print(json.dumps({
    'owner_revision': owner.OWNER_REVISION,
    'members': len(plan['files']),
    'packages': packages,
    'plan_sha256': hashlib.sha256((json.dumps(plan, indent=2, sort_keys=True)
                                + '\\n').encode()).hexdigest(),
}, sort_keys=True))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script, str(ROOT)],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    assert result.stderr == ""
    profile = json.loads(result.stdout)
    assert profile["owner_revision"] == "b510b2117d737e34f10314bd221417e6364081a0"
    assert profile["members"] == 41
    assert profile["plan_sha256"] == (
        "80cc3b7d43d8bce2b3b05af29eb90b66ce99e4989d3481097d9f2451d3e9bdfb"
    )
    # Byte-level source/profile validation is the producer's retained proof;
    # this test joins its actual versions to SPEC's declared direct edges.
    metadata = tomllib.loads(
        Path(__file__).parents[1].joinpath("pyproject.toml").read_text()
    )["project"]
    for value in metadata["optional-dependencies"]["governed"]:
        requirement = Requirement(value)
        if requirement.name == "aware-protocol-fs-adapter":
            producer = tomllib.loads(
                (ROOT / PROTOCOL_ROOTS[2] / "pyproject.toml").read_text()
            )["project"]
        else:
            producer = profile["packages"][requirement.name]
            assert producer["version"].endswith("+draft.1")
        assert producer["version"] in requirement.specifier
        assert requirement.extras <= set(producer.get("optional-dependencies", {}))
    for producer in profile["packages"].values():
        assert "optional-dependencies" not in producer
        for value in producer["dependencies"]:
            dependency = Requirement(value)
            assert not any(
                marker in dependency.name
                for marker in ("service", "ontology", "orm", "experience")
            )
    recipe = ROOT / (
        "docs/specs/aware-portable-protocol/conformance/project_issue_draft_suppliers.py"
    )
    committed = subprocess.check_output(
        [
            "git",
            "-C",
            str(ROOT),
            "show",
            "5c3acc1405c7:" + recipe.relative_to(ROOT).as_posix(),
        ]
    )
    assert (
        hashlib.sha256(recipe.read_bytes()).digest()
        == hashlib.sha256(committed).digest()
    )
