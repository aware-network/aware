from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from textwrap import dedent
from uuid import uuid4


def test_pydantic_bootstrap_rebuilds_same_package_import_root_from_new_filesystem_root(
    tmp_path: Path,
) -> None:
    package_name = f"aware_bootstrap_reload_probe_{uuid4().hex}"
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    _write_probe_package(root=first_root, package_name=package_name)
    _write_probe_package(root=second_root, package_name=package_name)

    try:
        sys.path.insert(0, str(first_root))
        first_request = importlib.import_module(
            f"{package_name}.models.request"
        ).Request
        assert (
            first_request.model_validate({"context": {"value": "first"}}).context.value
            == "first"
        )

        _evict_probe_modules(package_name=package_name)
        sys.path.remove(str(first_root))
        sys.path.insert(0, str(second_root))
        importlib.invalidate_caches()

        second_request = importlib.import_module(
            f"{package_name}.models.request"
        ).Request

        assert (
            second_request.model_validate(
                {"context": {"value": "second"}}
            ).context.value
            == "second"
        )
    finally:
        _evict_probe_modules(package_name=package_name)
        for root in (str(first_root), str(second_root)):
            while root in sys.path:
                sys.path.remove(root)


def test_pydantic_bootstrap_imports_only_explicit_model_dependency_roots(
    tmp_path: Path,
) -> None:
    token = uuid4().hex
    package_name = f"aware_bootstrap_consumer_{token}"
    model_dependency_name = f"aware_bootstrap_model_dep_{token}"
    unsafe_dependency_name = f"aware_bootstrap_unsafe_dep_{token}"
    unsafe_import_marker = tmp_path / "unsafe_imported.txt"

    _write_model_dependency_package(root=tmp_path, package_name=model_dependency_name)
    _write_unsafe_dependency_package(
        root=tmp_path,
        package_name=unsafe_dependency_name,
        marker_path=unsafe_import_marker,
    )
    _write_consumer_package(
        root=tmp_path,
        package_name=package_name,
        model_dependency_name=model_dependency_name,
        unsafe_dependency_name=unsafe_dependency_name,
    )

    try:
        sys.path.insert(0, str(tmp_path))
        request_model = importlib.import_module(
            f"{package_name}.models.request"
        ).Request

        result = request_model.model_validate({"dep": {"value": "ok"}})

        assert result.dep.value == "ok"
        assert not unsafe_import_marker.exists()
        assert unsafe_dependency_name not in sys.modules
    finally:
        for name in (package_name, model_dependency_name, unsafe_dependency_name):
            _evict_probe_modules(package_name=name)
        while str(tmp_path) in sys.path:
            sys.path.remove(str(tmp_path))


def _write_probe_package(*, root: Path, package_name: str) -> None:
    package_root = root / package_name
    models_root = package_root / "models"
    aware_root = package_root / "_aware"
    models_root.mkdir(parents=True)
    aware_root.mkdir()
    (package_root / "__init__.py").write_text(
        dedent(
            """
            from __future__ import annotations

            from aware_utils.pydantic.package_bootstrap import bootstrap_pydantic_package_from_artifacts

            bootstrap_pydantic_package_from_artifacts(package_prefix=__name__)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (models_root / "__init__.py").write_text("", encoding="utf-8")
    (models_root / "context.py").write_text(
        dedent(
            """
            from __future__ import annotations

            from pydantic import BaseModel


            class Context(BaseModel):
                value: str
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (models_root / "request.py").write_text(
        dedent(
            f"""
            from __future__ import annotations

            from typing import TYPE_CHECKING

            from pydantic import BaseModel

            if TYPE_CHECKING:
                from {package_name}.models.context import Context


            class Request(BaseModel):
                context: Context | None = None
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (aware_root / "python.bootstrap.json").write_text(
        json.dumps(
            {
                "dependency_import_roots": [],
                "modules": [
                    f"{package_name}.models.context",
                    f"{package_name}.models.request",
                ],
                "package_prefix": package_name,
                "version": "v1",
            }
        ),
        encoding="utf-8",
    )


def _write_model_dependency_package(*, root: Path, package_name: str) -> None:
    package_root = root / package_name
    models_root = package_root / "models"
    aware_root = package_root / "_aware"
    models_root.mkdir(parents=True)
    aware_root.mkdir()
    (package_root / "__init__.py").write_text(
        dedent(
            """
            from __future__ import annotations

            from aware_utils.pydantic.package_bootstrap import bootstrap_pydantic_package_from_artifacts

            bootstrap_pydantic_package_from_artifacts(package_prefix=__name__)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (models_root / "__init__.py").write_text("", encoding="utf-8")
    (models_root / "dep.py").write_text(
        dedent(
            """
            from __future__ import annotations

            from pydantic import BaseModel


            class DepModel(BaseModel):
                value: str
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (aware_root / "python.bootstrap.json").write_text(
        json.dumps(
            {
                "dependency_import_roots": [],
                "modules": [f"{package_name}.models.dep"],
                "package_prefix": package_name,
                "version": "v1",
            }
        ),
        encoding="utf-8",
    )


def _write_unsafe_dependency_package(
    *,
    root: Path,
    package_name: str,
    marker_path: Path,
) -> None:
    package_root = root / package_name
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text(
        dedent(
            f"""
            from __future__ import annotations

            from pathlib import Path

            Path({str(marker_path)!r}).write_text("imported", encoding="utf-8")
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _write_consumer_package(
    *,
    root: Path,
    package_name: str,
    model_dependency_name: str,
    unsafe_dependency_name: str,
) -> None:
    package_root = root / package_name
    models_root = package_root / "models"
    aware_root = package_root / "_aware"
    models_root.mkdir(parents=True)
    aware_root.mkdir()
    (package_root / "__init__.py").write_text(
        dedent(
            """
            from __future__ import annotations

            from aware_utils.pydantic.package_bootstrap import bootstrap_pydantic_package_from_artifacts

            bootstrap_pydantic_package_from_artifacts(package_prefix=__name__)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (models_root / "__init__.py").write_text("", encoding="utf-8")
    (models_root / "request.py").write_text(
        dedent(
            f"""
            from __future__ import annotations

            from typing import TYPE_CHECKING

            from pydantic import BaseModel

            if TYPE_CHECKING:
                from {model_dependency_name}.models.dep import DepModel


            class Request(BaseModel):
                dep: DepModel | None = None
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (aware_root / "python.bootstrap.json").write_text(
        json.dumps(
            {
                "dependency_import_roots": [
                    model_dependency_name,
                    unsafe_dependency_name,
                ],
                "modules": [f"{package_name}.models.request"],
                "package_prefix": package_name,
                "pydantic_model_dependency_import_roots": [model_dependency_name],
                "version": "v1",
            }
        ),
        encoding="utf-8",
    )


def _evict_probe_modules(*, package_name: str) -> None:
    for module_name in tuple(sys.modules):
        if module_name == package_name or module_name.startswith(f"{package_name}."):
            sys.modules.pop(module_name, None)
