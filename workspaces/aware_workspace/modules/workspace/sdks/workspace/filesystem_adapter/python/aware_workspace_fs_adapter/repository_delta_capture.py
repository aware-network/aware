"""Select the original observer and guard capture roots and source visibility."""

from __future__ import annotations

import os
import stat
from pathlib import Path, PurePosixPath

from aware_workspace_runtime.contracts import WorkspaceRepositoryBinding
from aware_workspace_runtime.observation import WorkspaceRepositoryObservationSession
from aware_workspace_runtime.provider import FileSystemIndexObservationProvider

from .repository_source_projection import canonical_path


class FilesystemDeltaCapturePort:
    def __init__(self, *, repository_root: Path, cache_root: Path):
        for path in (repository_root, cache_root):
            if (
                not isinstance(path, Path)
                or not path.is_absolute()
                or path.resolve() != path
            ):
                raise ValueError("capture_canonical_absolute_root_required")
        if not repository_root.is_dir():
            raise ValueError("capture_source_root_missing")
        if cache_root.is_relative_to(repository_root) or repository_root.is_relative_to(
            cache_root
        ):
            raise ValueError("capture_separate_cache_required")
        self.binding = WorkspaceRepositoryBinding(repository_root)
        self.cache_root = cache_root
        metadata = os.stat(repository_root, follow_symlinks=False)
        self._identity = (metadata.st_dev, metadata.st_ino)
        self._pid = os.getpid()

    def verify_current(self):
        if self._pid != os.getpid():
            raise ValueError("capture_process_mismatch")
        root = self.binding.root_path
        if root.resolve() != root or self.cache_root.resolve() != self.cache_root:
            raise ValueError("capture_root_changed")
        metadata = os.stat(root, follow_symlinks=False)
        if (metadata.st_dev, metadata.st_ino) != self._identity:
            raise ValueError("capture_root_changed")

    def create_session(self):
        self.verify_current()
        return WorkspaceRepositoryObservationSession(
            binding=self.binding,
            provider=FileSystemIndexObservationProvider(
                binding=self.binding,
                cache_dir=self.cache_root,
            ),
            observation_mode="command",
        )

    def verify_paths(self, paths, *, session=None):
        self.verify_current()
        from aware_file_system.config import CanonicalSourceFilterConfig

        policy = CanonicalSourceFilterConfig()
        for path in paths:
            canonical_path(path)
            parts = PurePosixPath(path).parts
            if any(p in policy.ignored_dirs for p in parts[:-1]):
                raise ValueError("capture_path_excluded")
            if Path(path).suffix in policy.ignored_extensions:
                raise ValueError("capture_path_excluded")
            # Even an absent selected target must pass visibility; exclusion is
            # never converted into a known-absent preimage.
            if session is not None:
                absolute = str(self.binding.root_path / path)
                if absolute not in session.provider.index.scanner.filter.included_files(
                    (absolute,)
                ):
                    raise ValueError("capture_path_excluded")
            current = self.binding.root_path
            for index, part in enumerate(parts):
                current = current / part
                try:
                    metadata = current.stat(follow_symlinks=False)
                except FileNotFoundError:
                    break
                if stat.S_ISLNK(metadata.st_mode):
                    raise ValueError("capture_nonregular_path")
                if index < len(parts) - 1:
                    if not stat.S_ISDIR(metadata.st_mode):
                        raise ValueError("capture_nonregular_path")
                elif not stat.S_ISREG(metadata.st_mode):
                    raise ValueError("capture_nonregular_path")
