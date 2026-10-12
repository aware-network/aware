"""Authored Python Code creation profile; no semantic target or IO authority."""

from __future__ import annotations

import json
import keyword
import re
import tomllib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PythonCodePackageSetup:
    distribution: str
    import_root: str
    version: str = "0.1.0"
    requires_python: str = ">=3.12"
    dependencies: tuple[str, ...] = ()

    def __post_init__(self):
        if type(self.distribution) is not str or not re.fullmatch(
            r"[a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*", self.distribution
        ):
            raise ValueError("invalid_python_distribution")
        if (
            type(self.import_root) is not str
            or not re.fullmatch(r"[a-z_][a-z0-9_]*", self.import_root)
            or keyword.iskeyword(self.import_root)
        ):
            raise ValueError("invalid_python_import_root")
        if type(self.version) is not str or not re.fullmatch(
            r"\d+\.\d+\.\d+", self.version
        ):
            raise ValueError("unsupported_python_version_profile")
        if type(self.requires_python) is not str or not self.requires_python.strip():
            raise ValueError("python_support_required")
        if type(self.dependencies) is not tuple or any(
            type(item) is not str or not item.strip() for item in self.dependencies
        ):
            raise ValueError("invalid_python_dependencies")


def render_python_code_package(
    spec: PythonCodePackageSetup,
) -> tuple[tuple[str, bytes], ...]:
    if type(spec) is not PythonCodePackageSetup:
        raise TypeError("original_python_setup_profile_required")
    q = json.dumps
    text = (
        "[project]\n"
        f"name = {q(spec.distribution)}\nversion = {q(spec.version)}\n"
        f"requires-python = {q(spec.requires_python)}\n"
        f"dependencies = {q(list(spec.dependencies))}\n\n"
        '[build-system]\nrequires = ["hatchling>=1.27.0"]\n'
        'build-backend = "hatchling.build"\n\n'
        "[tool.hatch.build.targets.wheel]\n"
        f"packages = [{q('src/' + spec.import_root)}]\n"
    )
    tomllib.loads(text)
    return (
        ("pyproject.toml", text.encode()),
        (
            f"src/{spec.import_root}/__init__.py",
            f"__version__ = {q(spec.version)}\n".encode(),
        ),
    )
