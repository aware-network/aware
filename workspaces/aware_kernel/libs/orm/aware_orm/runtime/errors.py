"""Runtime-layer error types.

Keep error semantics explicit so we don't conflate:
- package rail failures (embedded artifacts)
- bundle rail failures (environment manifest/bundle)
"""

from __future__ import annotations


class ORMRailError(RuntimeError):
    """Base class for ORM runtime installation/binding errors."""


class BundleInstallError(ORMRailError):
    """Errors when installing from an environment bundle (manifest + artifacts)."""


class PackageInstallError(ORMRailError):
    """Errors when installing from embedded package artifacts."""
