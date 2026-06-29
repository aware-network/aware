"""Package strategy interfaces for ObjectConfigGraph outputs."""

from __future__ import annotations

import shutil
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Any, Protocol


class ObjectConfigGraphPackagePolicy(Protocol):
    """Base type for package policies (language-specific concrete policies live in language plugins)."""


class ObjectConfigGraphPackageSpec(BaseModel):
    """Metadata describing a package to build from rendered files."""

    name: str
    version: str = "0.1.0"
    description: str | None = None
    package_name: str | None = None
    package_root: Path | None = None
    import_root: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    optional_dependencies: dict[str, list[str]] = Field(default_factory=dict)
    license_file: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ObjectConfigGraphPackageResult(BaseModel):
    """Result of producing an installable package."""

    name: str
    output_root: Path
    files: list[Path] = Field(default_factory=list)
    changed_files: list[Path] = Field(default_factory=list)


class ObjectConfigGraphPackageStrategy:
    """Base class for language-specific packaging implementations."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # Language-specific package policy (optional, injected by the environment).
        self.policy: ObjectConfigGraphPackagePolicy | None = None
        self._changed_files: list[Path] = []

    def set_policy(self, policy: ObjectConfigGraphPackagePolicy | None) -> None:
        """Inject a language-specific package policy (DTO vs ORM, etc.)."""
        self.policy = policy

    def build_package(
        self,
        rendered_files: list[Path],
        spec: ObjectConfigGraphPackageSpec,
    ) -> ObjectConfigGraphPackageResult:
        """
        Build the package incrementally (in-place).

        Canonical invariant:
        - Package outputs are deterministic and derived from rendered files + spec.
        - Strategies write into the resolved package root; unchanged files are preserved.
        """
        package_name = spec.package_name or spec.name
        if not package_name:
            raise ValueError("Package spec must define a package_name or name")

        final_root = self.resolve_package_root(spec)
        final_root.mkdir(parents=True, exist_ok=True)
        self._changed_files = []
        final_files = self.build_into(
            output_root=final_root,
            rendered_files=rendered_files,
            spec=spec,
        )

        return ObjectConfigGraphPackageResult(
            name=package_name,
            output_root=final_root,
            files=final_files or [],
            changed_files=list(self._changed_files),
        )

    def resolve_package_root(self, spec: ObjectConfigGraphPackageSpec) -> Path:
        """
        Resolve the final package root directory for the spec.

        Default behavior mirrors existing language strategies:
        - if spec.package_root is set, use it
        - otherwise, default to base_dir/<package_name>
        """
        package_name = spec.package_name or spec.name
        if not package_name:
            raise ValueError("Package spec must define a package_name or name")
        root = (
            Path(spec.package_root)
            if spec.package_root is not None
            else (self.base_dir / package_name)
        )
        return root.resolve()

    def build_into(
        self,
        *,
        output_root: Path,
        rendered_files: list[Path],
        spec: ObjectConfigGraphPackageSpec,
    ) -> list[Path]:
        """
        Language hook: populate output_root with the full package contents and return written file paths.

        Implementations MUST:
        - write only under output_root
        - return paths that are under output_root (absolute or relative)
        """
        _ = rendered_files
        _ = spec
        _ = output_root
        return []

    def _write_text_if_changed(self, path: Path, content: str) -> bool:
        try:
            if path.exists():
                existing = path.read_text(encoding="utf-8")
                if existing == content:
                    return False
        except Exception:
            pass
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self._record_changed_file(path)
        return True

    def _copy_if_changed(self, src: Path, dest: Path) -> bool:
        src = Path(src)
        dest = Path(dest)
        if dest.exists():
            try:
                if src.read_bytes() == dest.read_bytes():
                    return False
            except Exception:
                pass
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest != src:
            shutil.copy2(src, dest)
        self._record_changed_file(dest)
        return True

    def _record_changed_file(self, path: Path) -> None:
        resolved = Path(path).resolve()
        if resolved not in self._changed_files:
            self._changed_files.append(resolved)
