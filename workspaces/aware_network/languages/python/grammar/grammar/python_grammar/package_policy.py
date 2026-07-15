from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PythonPackagePolicy:
    """Package-time policy for Python package generation."""

    # When True, package `__init__.py` installs ORM runtime artifacts (OCG→ORM binding).
    # API packages MUST set this to False.
    install_runtime_artifacts: bool = True

    @classmethod
    def orm_default(cls) -> "PythonPackagePolicy":
        return cls(install_runtime_artifacts=True)

    @classmethod
    def api_default(cls) -> "PythonPackagePolicy":
        return cls(install_runtime_artifacts=False)

    @classmethod
    def ontology_dto_default(cls) -> "PythonPackagePolicy":
        return cls(install_runtime_artifacts=False)


__all__ = ["PythonPackagePolicy"]
