"""Original publication imports without unrelated installed owners or stubs."""

import ast
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[7]
RUNTIME_ROOT = "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime"
SDK_ROOT = "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public"
ROOT_PATH = RUNTIME_ROOT + "/aware_workspace_runtime/__init__.py"
PREIMAGE_REVISION = "0c02062d66f9301c5e01d1e8ad87aa4c3142faa4"
UNDEFINED_PREIMAGE_EXPORTS = {
    "WORKSPACE_SEMANTIC_BUNDLE_AUTHORITY_GRADE",
    "WORKSPACE_SEMANTIC_BUNDLE_BODY_MEMBERSHIP_CONTRACT",
    "WORKSPACE_SEMANTIC_BUNDLE_KIND",
    "WORKSPACE_SEMANTIC_BUNDLE_MANIFEST_CONTRACT",
}
PHYSICAL_STORE_EXPORTS = {
    "DEFAULT_MUTATION_STORE_CAPACITY",
    "MAX_MUTATION_STORE_CAPACITY",
    "WORKSPACE_REPOSITORY_MUTATION_STORE_CONTRACT_REF",
    "WORKSPACE_REPOSITORY_MUTATION_STORE_VERSION",
    "WorkspaceRepositoryMutationStore",
    "WorkspaceRepositoryMutationStoreCorrupt",
    "WorkspaceRepositoryMutationStoreError",
}


def _preimage_inventory():
    source = subprocess.check_output(
        ["git", "show", PREIMAGE_REVISION + ":" + ROOT_PATH], cwd=REPO
    )
    tree = ast.parse(source)
    exports = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            assert node.level == 1
            exports.update(
                {
                    alias.asname or alias.name: (node.module, alias.name)
                    for alias in node.names
                }
            )
        elif isinstance(node, ast.Assign):
            assert [target.id for target in node.targets] == ["__all__"]
            advertised = ast.literal_eval(node.value)
        else:
            pytest.fail("Unexpected original initializer statement")
    return exports, advertised


@pytest.mark.parametrize(
    "selected",
    [
        "aware_workspace_runtime",
        "aware_workspace_sdk.repository_publication",
        "aware_workspace_runtime.repository_publication",
    ],
)
def test_publication_import_uses_real_sources_without_other_owners(selected):
    code = f"""
import importlib.abc, importlib, json, sys
sys.path[:0] = {json.dumps([str(REPO / RUNTIME_ROOT), str(REPO / SDK_ROOT)])}
allowed = {{
    'aware_workspace_runtime', 'aware_workspace_runtime.repository_publication',
    'aware_workspace_sdk', 'aware_workspace_sdk.repository_publication',
    'aware_workspace_sdk.repository_publication.authority',
    'aware_workspace_sdk.repository_publication.codec',
    'aware_workspace_sdk.repository_publication.values',
    'aware_workspace_sdk.repository_publication.ports',
}}
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('aware_') and fullname not in allowed:
            raise ImportError('unrelated_owner_import:' + fullname)
sys.meta_path.insert(0, Guard())
importlib.import_module({selected!r})
loaded = sorted(n for n in sys.modules if n.startswith('aware_'))
assert set(loaded) <= allowed
assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
print(json.dumps(loaded))
"""
    replay = subprocess.run(
        [sys.executable, "-I", "-S", "-B", "-c", code],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert replay.returncode == 0, replay.stderr
    assert selected in json.loads(replay.stdout)


def test_every_original_defined_export_preserves_original_module_identity():
    runtime = importlib.import_module("aware_workspace_runtime")
    exports, advertised = _preimage_inventory()
    assert len(exports) == 568 and len(advertised) == 572
    assert set(advertised) - set(exports) == UNDEFINED_PREIMAGE_EXPORTS
    assert {
        name
        for name, (module, _) in exports.items()
        if module == "repository_mutation_store"
    } == PHYSICAL_STORE_EXPORTS
    exports = {
        name: value
        for name, value in exports.items()
        if name not in PHYSICAL_STORE_EXPORTS | {"WorkspaceRepositoryDeltaStore"}
    }
    assert len(exports) == 560
    expected = {
        name: (
            ("repository_delta_store_contract", attribute)
            if module == "repository_delta_store"
            and name != "WorkspaceRepositoryDeltaStore"
            else (module, attribute)
        )
        for name, (module, attribute) in exports.items()
    }
    assert runtime._EXPORT_MODULES == expected
    assert runtime.__all__ == [name for name in advertised if name in exports]
    for name, (module, attribute) in exports.items():
        original = importlib.import_module("aware_workspace_runtime." + module)
        assert getattr(runtime, name) is getattr(original, attribute)
    namespace = {}
    exec("from aware_workspace_runtime import *", namespace)  # noqa: S102 -- fixed import probe
    assert all(namespace[name] is getattr(runtime, name) for name in exports)


@pytest.mark.parametrize(
    "name",
    sorted(UNDEFINED_PREIMAGE_EXPORTS | PHYSICAL_STORE_EXPORTS) + ["foreign_api"],
)
def test_unavailable_exports_refuse_without_import_attempt(name, monkeypatch):
    # Test only the explicit facade, never a guessed owner/module fallback.
    runtime = importlib.import_module("aware_workspace_runtime")

    def forbidden_import(*args, **kwargs):
        pytest.fail("An unavailable facade export attempted an import")

    monkeypatch.setattr(importlib, "import_module", forbidden_import)
    with pytest.raises(AttributeError):
        getattr(runtime, name)
    assert name not in runtime.__all__


def test_directory_includes_exact_defined_public_exports():
    runtime = importlib.import_module("aware_workspace_runtime")
    exports, _ = _preimage_inventory()
    assert set(exports) - PHYSICAL_STORE_EXPORTS - {"WorkspaceRepositoryDeltaStore"} <= set(dir(runtime))
    assert not PHYSICAL_STORE_EXPORTS.intersection(dir(runtime))
    assert not UNDEFINED_PREIMAGE_EXPORTS.intersection(dir(runtime))
