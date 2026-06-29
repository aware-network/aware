from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, cast

API_TESTS_ROOT = Path(__file__).resolve().parent
API_RUNTIME_ROOT = API_TESTS_ROOT.parent
API_ONTOLOGY_ROOT = API_TESTS_ROOT.parents[2]
API_MODULE_ROOT = API_TESTS_ROOT.parents[3]
NETWORK_WORKSPACE_ROOT = API_TESTS_ROOT.parents[5]
REPO_ROOT = API_TESTS_ROOT.parents[7]
KERNEL_WORKSPACE_ROOT = REPO_ROOT / "workspaces/aware_kernel"

API_RAW_PYTHON_ROOT = API_MODULE_ROOT / "libs/api/python"

API_META_PACKAGE_MANIFEST_PATHS = (
    KERNEL_WORKSPACE_ROOT / "modules/storage/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/content/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/code/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/history/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/meta/ontology/structure/aware.toml",
    API_ONTOLOGY_ROOT / "structure/aware.toml",
)

API_META_PYTHON_ROOTS = (
    KERNEL_WORKSPACE_ROOT / "modules/storage/ontology/structure/python/orm_runtime",
    KERNEL_WORKSPACE_ROOT / "modules/storage/ontology/structure/python/orm_models",
    KERNEL_WORKSPACE_ROOT / "modules/content/ontology/structure/python/orm_runtime",
    KERNEL_WORKSPACE_ROOT / "modules/content/ontology/structure/python/orm_models",
    KERNEL_WORKSPACE_ROOT / "modules/code/ontology/structure/python/orm_runtime",
    KERNEL_WORKSPACE_ROOT / "modules/code/ontology/structure/python/orm_models",
    KERNEL_WORKSPACE_ROOT / "modules/history/ontology/structure/python/orm_runtime",
    KERNEL_WORKSPACE_ROOT / "modules/history/ontology/structure/python/orm_models",
    KERNEL_WORKSPACE_ROOT / "modules/meta/ontology/structure/python/orm_runtime",
    KERNEL_WORKSPACE_ROOT / "modules/meta/ontology/structure/python/orm_models",
    API_ONTOLOGY_ROOT / "structure/python/orm_runtime",
    API_ONTOLOGY_ROOT / "structure/python/orm_models",
    API_RUNTIME_ROOT,
    API_RAW_PYTHON_ROOT,
)


def prepend_api_meta_python_roots(monkeypatch: Any) -> None:
    syspath_prepend = cast(Callable[[str], None], monkeypatch.syspath_prepend)
    for python_root in API_META_PYTHON_ROOTS:
        if python_root.exists():
            syspath_prepend(str(python_root))
