from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from aware_sdk_runtime.manifest.loader import load_aware_sdk_toml_spec
from aware_sdk_runtime.manifest.spec import AwareSdkTomlSpec


@dataclass(frozen=True, slots=True)
class SdkWorkspaceSnapshot:
    repo_root: Path
    sdk_root: Path
    package_root: Path
    spec_path: Path
    spec: AwareSdkTomlSpec
    source_files: tuple[Path, ...]


class SdkWorkspace:
    _spec_path: Path
    _package_root: Path
    _repo_root: Path

    def __init__(self, *, spec_path: str | Path, repo_root: str | Path | None = None):
        resolved_spec_path = Path(spec_path).resolve()
        if not resolved_spec_path.exists():
            raise FileNotFoundError(f"aware.sdk.toml not found: {resolved_spec_path}")
        self._spec_path = resolved_spec_path
        self._package_root = resolved_spec_path.parent
        self._sdk_root = self._package_root.parent if self._package_root.name == "aware" else self._package_root
        if repo_root is None:
            self._repo_root = _resolve_repo_root(start=self._package_root)
        else:
            self._repo_root = Path(repo_root).resolve()

    @classmethod
    def from_toml(cls, *, toml_path: str | Path, repo_root: str | Path | None = None) -> SdkWorkspace:
        return cls(spec_path=toml_path, repo_root=repo_root)

    @property
    def spec_path(self) -> Path:
        return self._spec_path

    @property
    def package_root(self) -> Path:
        return self._package_root

    @property
    def sdk_root(self) -> Path:
        return self._sdk_root

    @property
    def repo_root(self) -> Path:
        return self._repo_root

    def build_snapshot(self) -> SdkWorkspaceSnapshot:
        spec = load_aware_sdk_toml_spec(toml_path=self._spec_path)

        sources_root = (self._package_root / spec.build.sources_dir).resolve()
        _assert_within(base=self._package_root, candidate=sources_root, label="[build].sources_dir")
        if not sources_root.exists():
            raise FileNotFoundError(f"SDK sources_dir does not exist: {sources_root} (from {self._spec_path})")
        if not sources_root.is_dir():
            raise NotADirectoryError(f"SDK sources_dir must be a directory: {sources_root}")

        files_by_rel: dict[str, Path] = {}
        for include in spec.build.include_paths:
            pattern = (include or "").strip()
            if not pattern:
                continue
            for candidate in sources_root.glob(pattern):
                if not candidate.is_file():
                    continue
                resolved = candidate.resolve()
                _assert_within(base=sources_root, candidate=resolved, label="include_paths")
                rel_from_sources = resolved.relative_to(sources_root).as_posix()
                if _is_excluded(rel_path=rel_from_sources, exclude_patterns=spec.build.exclude_paths):
                    continue
                rel_from_package = resolved.relative_to(self._package_root).as_posix()
                files_by_rel[rel_from_package] = Path(rel_from_package)

        ordered_source_files = tuple(files_by_rel[key] for key in sorted(files_by_rel))

        return SdkWorkspaceSnapshot(
            repo_root=self._repo_root,
            sdk_root=self._sdk_root,
            package_root=self._package_root,
            spec_path=self._spec_path,
            spec=spec,
            source_files=ordered_source_files,
        )


def _resolve_repo_root(*, start: Path) -> Path:
    cursor = start.resolve()
    for candidate in [cursor, *cursor.parents]:
        if (candidate / "aware.environment.toml").exists():
            return candidate
    return cursor


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if candidate_resolved == base_resolved or base_resolved in candidate_resolved.parents:
        return
    raise ValueError(f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}")


def _is_excluded(*, rel_path: str, exclude_patterns: list[str]) -> bool:
    token = PurePosixPath(rel_path)
    for raw_pattern in exclude_patterns:
        pattern = (raw_pattern or "").strip()
        if pattern and token.match(pattern):
            return True
    return False


__all__ = [
    "SdkWorkspace",
    "SdkWorkspaceSnapshot",
]
