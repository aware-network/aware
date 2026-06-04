from __future__ import annotations

import builtins
import importlib
import json
import re
import subprocess
import sys
import tarfile
import tomllib
from email.parser import Parser
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import msgpack

from aware_orm.registry import ORMModelRegistry
from aware_orm.runtime.graph_binding import index_entities_from_msgpack
from aware_orm.runtime.package_artifacts import (
    ORM_GRAPH_BINDING_FILENAME,
    PYTHON_MODELS_MANIFEST_FILENAME,
)
from aware_orm.runtime.package_install import install_package_runtime_artifacts

PUBLIC_FORBIDDEN_IMPORT_ROOTS = {
    "aware_meta",
    "aware_meta_ontology",
    "aware_runtime",
    "aware_structure",
    "aware_utils",
    "asyncpg",
    "psycopg2",
    "services",
    "tomli",
}

PUBLIC_FORBIDDEN_BASE_DEPENDENCIES = {
    "aware-history-ontology",
    "aware-meta",
    "aware-meta-ontology",
    "aware-runtime",
    "aware-structure",
    "aware-utils",
    "asyncpg",
    "psycopg2-binary",
    "sql-grammar",
    "tomli",
}

PUBLIC_REQUIRED_CLASSIFIERS = {
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Operating System :: OS Independent",
    "Intended Audience :: Developers",
}

PUBLIC_REQUIRED_PROJECT_URLS = {
    "Homepage": "https://pypi.org/project/aware-orm/",
    "Source": "https://github.com/aware-network/aware-sdk",
    "Documentation": "https://github.com/aware-network/aware-sdk/tree/main/workspaces/aware_kernel/libs/orm/README.md",
    "Changelog": "https://github.com/aware-network/aware-sdk/tree/main/workspaces/aware_kernel/libs/orm/CHANGELOG.md",
    "Issues": "https://github.com/aware-network/aware-sdk/issues",
}

PUBLIC_REQUIRED_WHEEL_FILES = {
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
}


def _packb(payload: object) -> bytes:
    packed = msgpack.packb(payload, use_bin_type=True)
    if not isinstance(packed, (bytes, bytearray)):
        raise TypeError("msgpack.packb returned non-bytes payload")
    return bytes(packed)


def _guard_forbidden_imports(monkeypatch, forbidden_roots: set[str]) -> None:
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        root = str(name).split(".", 1)[0]
        if root in forbidden_roots:
            raise AssertionError(f"forbidden import attempted: {name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)


def _assert_subprocess_import_clean(
    module_name: str,
    attribute_name: str,
    forbidden_roots: set[str] | None = None,
) -> None:
    blocked = sorted(forbidden_roots or PUBLIC_FORBIDDEN_IMPORT_ROOTS)
    code = f"""
import builtins
import importlib

original_import = builtins.__import__
forbidden_roots = {blocked!r}

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = str(name).split(".", 1)[0]
    if root in forbidden_roots:
        raise AssertionError(f"forbidden import attempted: {{name}}")
    return original_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded_import
module = importlib.import_module({module_name!r})
assert hasattr(module, {attribute_name!r})
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def _dependency_names(values: list[str]) -> set[str]:
    return {re.split(r"[<>=!~;\\[]", value, maxsplit=1)[0].strip().lower() for value in values}


def _metadata_keywords(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip().lower() for part in value.split(",") if part.strip()}


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "uv.lock").is_file() and (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("Could not locate repository root for aware-orm build")


def _build_aware_orm_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    dist_dir = tmp_path / "dist"
    result = subprocess.run(
        ["uv", "build", "--package", "aware-orm", "--out-dir", str(dist_dir)],
        cwd=_repo_root(),
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    wheels = sorted(dist_dir.glob("aware_orm-*.whl"))
    sdists = sorted(dist_dir.glob("aware_orm-*.tar.gz"))
    assert wheels, result.stdout
    assert sdists, result.stdout
    return wheels[-1], sdists[-1]


def test_base_pyproject_declares_honest_public_package_metadata() -> None:
    pyproject_path = Path(__file__).parents[2] / "pyproject.toml"
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = payload["project"]
    wheel_target = payload["tool"]["hatch"]["build"]["targets"]["wheel"]
    dependencies = _dependency_names(project["dependencies"])
    optional_dependencies = payload["project"].get("optional-dependencies", {})
    postgres_dependencies = _dependency_names(optional_dependencies.get("postgres", []))
    classifiers = set(project["classifiers"])
    keywords = {value.lower() for value in project["keywords"]}

    assert project["description"] == (
        "Installable Aware ORM core for metadata-driven projection indexes and branch-aware sessions."
    )
    assert project["license"] == {"file": "LICENSE"}
    assert PUBLIC_REQUIRED_CLASSIFIERS.issubset(classifiers)
    assert {"aware", "orm", "projection", "branch-aware", "metadata"}.issubset(keywords)
    assert project["urls"] == PUBLIC_REQUIRED_PROJECT_URLS
    assert dependencies.isdisjoint(PUBLIC_FORBIDDEN_BASE_DEPENDENCIES)
    assert "bootstrap" not in optional_dependencies
    assert {"asyncpg", "psycopg2-binary"}.issubset(postgres_dependencies)
    assert "sql-grammar" not in _dependency_names(optional_dependencies.get("dev", []))
    assert PUBLIC_REQUIRED_WHEEL_FILES.issubset(set(wheel_target["include"]))
    assert wheel_target["force-include"] == {name: name for name in PUBLIC_REQUIRED_WHEEL_FILES}


def test_readme_states_public_release_contract() -> None:
    readme_path = Path(__file__).parents[2] / "README.md"
    readme = readme_path.read_text(encoding="utf-8")

    for expected in [
        "pip install aware-orm",
        'pip install "aware-orm[postgres]"',
        "Base Package Boundary",
        "External Aware Integration Points",
        "not a standalone generic ORM",
        "The base wheel depends only on:",
        "Run the focused public gate:",
        "MIT. See `LICENSE`.",
    ]:
        assert expected in readme


def test_built_wheel_metadata_and_import_boundary(tmp_path: Path) -> None:
    wheel_path, sdist_path = _build_aware_orm_artifacts(tmp_path)

    with ZipFile(wheel_path) as wheel:
        wheel_files = set(wheel.namelist())
        metadata_name = next(name for name in wheel.namelist() if name.endswith(".dist-info/METADATA"))
        metadata = Parser().parsestr(wheel.read(metadata_name).decode("utf-8"))
    with tarfile.open(sdist_path, "r:gz") as sdist:
        sdist_files = set(sdist.getnames())

    requires = metadata.get_all("Requires-Dist") or []
    base_requires = [value for value in requires if "extra ==" not in value]
    postgres_requires = [value for value in requires if "extra == 'postgres'" in value]
    base_names = _dependency_names(base_requires)
    postgres_names = _dependency_names(postgres_requires)
    classifiers = set(metadata.get_all("Classifier") or [])
    project_urls = {
        value.split(",", 1)[0]: value.split(",", 1)[1].strip()
        for value in (metadata.get_all("Project-URL") or [])
        if "," in value
    }
    keywords = _metadata_keywords(metadata.get("Keywords"))
    license_files = metadata.get_all("License-File") or []

    assert metadata["Summary"] == (
        "Installable Aware ORM core for metadata-driven projection indexes and branch-aware sessions."
    )
    assert metadata["Description-Content-Type"] == "text/markdown"
    assert PUBLIC_REQUIRED_CLASSIFIERS.issubset(classifiers)
    assert {"aware", "orm", "projection", "branch-aware", "metadata"}.issubset(keywords)
    assert project_urls == PUBLIC_REQUIRED_PROJECT_URLS
    assert any(value.endswith("LICENSE") for value in license_files)
    assert PUBLIC_REQUIRED_WHEEL_FILES.issubset(wheel_files)
    assert any(name.endswith(".dist-info/licenses/LICENSE") for name in wheel_files)
    assert not any("__pycache__" in name or name.endswith(".pyc") for name in wheel_files)
    assert not any(name.startswith(("docs/", "tests/", "scripts/")) for name in wheel_files)
    assert not any(name.startswith("aware_orm/bootstrap/") for name in wheel_files)
    assert "aware_orm/load/lazy_relationship.py" not in wheel_files
    assert "aware_orm/runtime/binding_dtos.py" not in wheel_files
    assert "aware_orm/runtime/ocg_orm_binding.py" not in wheel_files
    assert "aware_orm/graph/builders.py" not in wheel_files
    assert "aware_orm/projection/builders.py" not in wheel_files
    assert base_names == {"pydantic", "python-dotenv"}
    assert base_names.isdisjoint(PUBLIC_FORBIDDEN_BASE_DEPENDENCIES)
    assert {"asyncpg", "psycopg2-binary"}.issubset(postgres_names)
    provided_extras = set(metadata.get_all("Provides-Extra") or [])
    assert "postgres" in provided_extras
    assert "bootstrap" not in provided_extras
    assert any(name.endswith("/aware_orm/__init__.py") for name in sdist_files)
    assert any(name.endswith("/pyproject.toml") for name in sdist_files)
    assert any(name.endswith("/README.md") for name in sdist_files)
    assert any(name.endswith("/CHANGELOG.md") for name in sdist_files)
    assert any(name.endswith("/LICENSE") for name in sdist_files)
    assert not any("/docs/" in name for name in sdist_files)
    assert not any("/tests/" in name for name in sdist_files)
    assert not any("/scripts/" in name for name in sdist_files)
    assert not any("/aware_orm/bootstrap/" in name for name in sdist_files)
    assert not any(name.endswith("/aware_orm/load/lazy_relationship.py") for name in sdist_files)
    assert not any(name.endswith("/aware_orm/runtime/binding_dtos.py") for name in sdist_files)
    assert not any(name.endswith("/aware_orm/runtime/ocg_orm_binding.py") for name in sdist_files)
    assert not any(name.endswith("/aware_orm/graph/builders.py") for name in sdist_files)
    assert not any(name.endswith("/aware_orm/projection/builders.py") for name in sdist_files)
    assert not any("/.pytest_cache/" in name for name in sdist_files)
    assert not any("__pycache__" in name or name.endswith(".pyc") for name in sdist_files)

    blocked = sorted(PUBLIC_FORBIDDEN_IMPORT_ROOTS)
    code = f"""
import builtins
import importlib
import importlib.util
import sys

sys.path.insert(0, {str(wheel_path)!r})
original_import = builtins.__import__
forbidden_roots = {blocked!r}

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = str(name).split(".", 1)[0]
    if root in forbidden_roots:
        raise AssertionError(f"forbidden import attempted: {{name}}")
    return original_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded_import
for module_name, attribute_name in [
    ("aware_orm", "ORMModel"),
    ("aware_orm.session", "Session"),
    ("aware_orm.db", "DBBootConnection"),
    ("aware_orm.runtime", "install_package_runtime_artifacts"),
    ("aware_orm.runtime.graph_artifacts", "OrmEntitySpec"),
    ("aware_orm.runtime.graph_binding", "index_entities_from_msgpack"),
]:
    module = importlib.import_module(module_name)
    assert hasattr(module, attribute_name)

assert importlib.util.find_spec("aware_orm.bootstrap") is None
assert importlib.util.find_spec("aware_orm.projection.projector") is None
assert importlib.util.find_spec("aware_orm.load.lazy_relationship") is None
assert importlib.util.find_spec("aware_orm.runtime.binding_dtos") is None
assert importlib.util.find_spec("aware_orm.runtime.ocg_orm_binding") is None
assert importlib.util.find_spec("aware_orm.graph.builders") is None
assert importlib.util.find_spec("aware_orm.projection.builders") is None

module = importlib.import_module("aware_orm")
assert ".whl/" in (module.__file__ or ""), module.__file__
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_public_core_imports_do_not_import_internals_or_optional_postgres() -> None:
    clean_imports = [
        ("aware_orm", "ORMModel"),
        ("aware_orm.models", "ORMModel"),
        ("aware_orm.local_state", "SQLiteOrmSchemaContract"),
        ("aware_orm.session", "Session"),
        ("aware_orm.db", "DBBootConnection"),
        ("aware_orm.runtime", "install_package_runtime_artifacts"),
        ("aware_orm.runtime.graph_artifacts", "OrmEntitySpec"),
        ("aware_orm.runtime.graph_binding", "index_entities_from_msgpack"),
    ]

    for module_name, attribute_name in clean_imports:
        _assert_subprocess_import_clean(module_name, attribute_name)


def test_relationship_metadata_registry_import_does_not_import_meta_or_structure(monkeypatch) -> None:
    _guard_forbidden_imports(monkeypatch, PUBLIC_FORBIDDEN_IMPORT_ROOTS)

    module = importlib.import_module("aware_orm.runtime.relationship_strategies")

    assert hasattr(module, "RelationshipMetadata")
    assert hasattr(module, "install_relationship_metadata_from_payload")
    _assert_subprocess_import_clean("aware_orm.runtime.relationship_strategies", "RelationshipMetadata")


def test_projection_imports_do_not_import_meta_or_runtime(monkeypatch) -> None:
    _guard_forbidden_imports(
        monkeypatch,
        PUBLIC_FORBIDDEN_IMPORT_ROOTS,
    )

    projection_module = importlib.import_module("aware_orm.projection")

    assert hasattr(projection_module, "ProjectionRuntime")
    assert not hasattr(projection_module, "stage_lane_projection_writes")
    assert importlib.util.find_spec("aware_orm.projection.projector") is None
    _assert_subprocess_import_clean("aware_orm.projection", "ProjectionRuntime")


def test_graph_binding_snapshot_reader_does_not_import_meta_ontology(monkeypatch) -> None:
    entity_id = uuid4()
    payload = {
        "version": "v1",
        "entities": [
            {
                "id": str(entity_id),
                "entity_fqn": "pkg.Thing",
                "name": "Thing",
                "value_mode": "graph_ref",
                "identity_mode": "contained",
                "field_bindings": [],
                "function_bindings": [],
                "relationships": [],
            }
        ],
    }

    _guard_forbidden_imports(monkeypatch, PUBLIC_FORBIDDEN_IMPORT_ROOTS)

    entity_index = index_entities_from_msgpack(_packb(payload))

    entity = entity_index[str(entity_id)]
    assert entity.id == entity_id
    assert entity.class_fqn == "pkg.Thing"
    assert entity.name == "Thing"


def test_package_install_reads_binding_snapshot_without_meta_ontology(
    tmp_path: Path,
    monkeypatch,
) -> None:
    package_root = f"aware_clean_orm_{uuid4().hex[:8]}"
    entity_id = uuid4()
    pkg_root = tmp_path / "pkgs"
    package_dir = pkg_root / package_root
    artifacts = package_dir / "_aware"
    artifacts.mkdir(parents=True, exist_ok=True)

    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "models.py").write_text(
        """
from __future__ import annotations

from aware_orm.models.orm_model import ORMModel


class Thing(ORMModel):
    name: str
""".lstrip(),
        encoding="utf-8",
    )
    (artifacts / PYTHON_MODELS_MANIFEST_FILENAME).write_text(
        json.dumps(
            {
                "language": "python",
                "classes": [
                    {
                        "class_config_id": str(entity_id),
                        "module": f"{package_root}.models",
                        "name": "Thing",
                    }
                ],
                "enums": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (artifacts / ORM_GRAPH_BINDING_FILENAME).write_bytes(
        _packb(
            {
                "version": "v1",
                "entities": [
                    {
                        "id": str(entity_id),
                        "entity_fqn": f"{package_root}.models.Thing",
                        "name": "Thing",
                        "value_mode": "graph_ref",
                        "identity_mode": "contained",
                        "field_bindings": [],
                        "function_bindings": [],
                        "relationships": [],
                    }
                ],
            }
        )
    )

    registry_snapshot = ORMModelRegistry.snapshot_state()
    sys_path_snapshot = list(sys.path)
    try:
        ORMModelRegistry.clear_registry()
        ORMModelRegistry._initialized = False  # test-local reset
        sys.path.insert(0, str(pkg_root))
        importlib.invalidate_caches()

        _guard_forbidden_imports(
            monkeypatch,
            PUBLIC_FORBIDDEN_IMPORT_ROOTS,
        )

        model_module = importlib.import_module(f"{package_root}.models")
        Thing = getattr(model_module, "Thing")
        ORMModelRegistry.register_class_stub(Thing)

        install_package_runtime_artifacts(package_prefix=package_root, artifacts_dir="_aware", strict=True)

        bound = Thing.get_class_config()
        assert bound is not None
        assert bound.id == entity_id
        assert bound.name == "Thing"
        assert ORMModelRegistry.get_class_by_class_config_id(entity_id) is Thing
    finally:
        sys.path[:] = sys_path_snapshot
        for name in list(sys.modules):
            if name == package_root or name.startswith(package_root + "."):
                sys.modules.pop(name, None)
        ORMModelRegistry.restore_state(registry_snapshot)
