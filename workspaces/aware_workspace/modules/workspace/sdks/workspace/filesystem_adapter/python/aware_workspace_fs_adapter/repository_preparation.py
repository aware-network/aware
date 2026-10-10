"""Original Git preparation algorithm behind retained filesystem custody.

The Git invocation/environment and empty/exact-root requirements come from the
published Repository FS provider at 095b9c5cad57. No seed publication or staging
is introduced. Descriptor traversal is cooperative confinement, not continuous
confinement of the Git subprocess. Currentness is observed state, not every-write
detection. This owner never issues Issue or authenticated actor authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from dataclasses import replace
from pathlib import Path

from aware_workspace_sdk.repository_preparation.values import (
    RepositoryPreparationEffect,
)


def _identity(metadata):
    return (metadata.st_dev, metadata.st_ino, metadata.st_mode)


def _git(root, *arguments):
    environment = {
        key: value
        for key, value in os.environ.items()
        if key in {"PATH", "HOME", "LANG", "LC_ALL"}
    }
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


class FilesystemRepositoryPreparationPort:
    """One selected physical owner; retained observations are private."""

    def __init__(self, *, repository_root):
        root = Path(repository_root)
        if (
            not root.is_absolute()
            or str(root) != repository_root
            or ".." in root.parts
            or root == Path("/")
        ):
            raise ValueError("canonical_absolute_repository_root_required")
        self.root = root

    def retain(self, request):
        if request.repository_root != str(self.root):
            raise ValueError("physical_preparation_root_mismatch")
        return _RetainedPreparation(self.root, request)


class _RetainedPreparation:
    def __init__(self, root, request):
        self.root = root
        self.request = request
        self.descriptors = []
        self.ancestors = []
        self.parent_fd = None
        self.root_fd = None
        self.effects = []
        self.cleanup_state = "not_attempted"
        self.closed = False
        self.snapshot = None
        try:
            self._open_parent()
            self._open_root_if_present()
            self.snapshot = self._observe()
        except BaseException:
            self.release()
            raise

    def _open_parent(self):
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        descriptor = os.open("/", flags)
        self.descriptors.append(descriptor)
        self.ancestors.append((Path("/"), _identity(os.fstat(descriptor))))
        path = Path("/")
        for component in self.root.parent.parts[1:]:
            descriptor = os.open(component, flags, dir_fd=descriptor)
            self.descriptors.append(descriptor)
            path /= component
            self.ancestors.append((path, _identity(os.fstat(descriptor))))
        self.parent_fd = descriptor

    def _open_root_if_present(self):
        try:
            descriptor = os.open(
                self.root.name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=self.parent_fd,
            )
        except FileNotFoundError:
            return
        self.descriptors.append(descriptor)
        self.root_fd = descriptor

    def _validate_topology(self):
        if self.closed:
            raise ValueError("repository_preparation_retired")
        for path, identity in self.ancestors:
            if _identity(os.stat(path, follow_symlinks=False)) != identity:
                raise ValueError("repository_ancestor_changed")
        if self.root_fd is None:
            try:
                os.stat(self.root.name, dir_fd=self.parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                return
            raise ValueError("repository_target_substituted")
        if _identity(
            os.stat(self.root.name, dir_fd=self.parent_fd, follow_symlinks=False)
        ) != _identity(os.fstat(self.root_fd)):
            raise ValueError("repository_target_substituted")

    def _observe(self):
        self._validate_topology()
        probe = self.root if self.root_fd is not None else self.root.parent
        discovery = _git(probe, "rev-parse", "--show-toplevel")
        result = {
            "outcome": "refused",
            "diagnostics": [],
            "head": None,
            "root_identity": _identity(os.fstat(self.root_fd))
            if self.root_fd is not None
            else None,
            "metadata_identity": None,
        }
        if discovery.returncode == 0:
            actual = Path(discovery.stdout.strip()).resolve(strict=True)
            if actual != self.root:
                result["diagnostics"] = [
                    "select_exact_git_repository_root",
                    "nested_repository_creation_refused",
                ]
            else:
                metadata = os.stat(".git", dir_fd=self.root_fd, follow_symlinks=False)
                result["metadata_identity"] = _identity(metadata)
                if stat.S_ISLNK(metadata.st_mode):
                    result["diagnostics"] = ["repository_metadata_symlink_refused"]
                else:
                    head = _git(self.root, "rev-parse", "--verify", "HEAD^{commit}")
                    result["outcome"] = "existing"
                    result["head"] = (
                        head.stdout.strip() if head.returncode == 0 else None
                    )
        elif _git(probe, "rev-parse", "--is-bare-repository").returncode == 0:
            result["diagnostics"] = ["bare_repository_unsupported"]
        elif not self.request.create_if_missing:
            result["diagnostics"] = [
                "git_repository_required",
                "use_init_create_repository_for_an_empty_target",
            ]
        elif self.root_fd is not None and os.listdir(self.root_fd):
            result["diagnostics"] = ["repository_creation_requires_empty_target"]
        else:
            result["outcome"] = "planned"
            result["diagnostics"] = ["empty_repository_preparation_only_no_commit"]
        self._validate_topology()
        return result

    def validate_current(self):
        if self._observe() != self.snapshot:
            raise ValueError("repository_preparation_stale")

    def plan_digest(self):
        return (
            "sha256:"
            + hashlib.sha256(
                json.dumps(
                    self.snapshot, sort_keys=True, separators=(",", ":")
                ).encode()
            ).hexdigest()
        )

    def ordered_effect_paths(self):
        if self.snapshot is None:
            raise ValueError("original_preparation_snapshot_required")
        if self.snapshot["outcome"] != "planned":
            return ()
        return ((str(self.root),) if self.root_fd is None else ()) + (
            str(self.root / ".git"),
        )

    def _effect(self, path, kind):
        self.effects.append(RepositoryPreparationEffect(path, kind, "unknown", False))
        return len(self.effects) - 1

    def _confirm(self, index, metadata):
        self.effects[index] = replace(
            self.effects[index],
            state="applied",
            after_device=metadata.st_dev,
            after_inode=metadata.st_ino,
            mode=stat.S_IMODE(metadata.st_mode),
        )

    def prepare(self, *, claim=None):
        from aware_workspace_sdk.repository_preparation.authority import (
            _consume_physical_claim,
        )

        _consume_physical_claim(claim, self)
        self.validate_current()
        if self.snapshot is None:
            raise ValueError("original_preparation_snapshot_required")
        if self.snapshot["outcome"] != "planned":
            return self.snapshot
        if self.root_fd is None:
            index = self._effect(str(self.root), "repository_directory_creation")
            os.mkdir(self.root.name, mode=0o700, dir_fd=self.parent_fd)
            self.effects[index] = replace(self.effects[index], state="applied")
            self._open_root_if_present()
            if self.root_fd is None:
                raise ValueError("created_repository_identity_unproven")
            self._confirm(index, os.fstat(self.root_fd))
        self._validate_topology()
        if os.listdir(self.root_fd):
            raise ValueError("repository_creation_target_changed")
        metadata_index = self._effect(
            str(self.root / ".git"), "git_metadata_directory_creation"
        )
        # Reserve the concrete metadata directory no-replace. The original Git
        # command may populate this owner's empty directory, not adopt a racer.
        os.mkdir(".git", mode=0o700, dir_fd=self.root_fd)
        self.effects[metadata_index] = replace(
            self.effects[metadata_index], state="applied"
        )
        metadata_fd = os.open(
            ".git",
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=self.root_fd,
        )
        self.descriptors.append(metadata_fd)
        self._confirm(metadata_index, os.fstat(metadata_fd))
        index = self._effect(str(self.root / ".git"), "git_repository_initialization")
        created = _git(
            self.root,
            "-c",
            "init.templateDir=",
            "init",
            "--template=",
            "--initial-branch=main",
            ".",
        )
        if created.returncode:
            raise ValueError("git_init_failed_inspect_retained_target_before_retry")
        # Success of the original command is known even if postimage reading fails.
        self.effects[index] = replace(self.effects[index], state="applied")
        metadata = os.stat(".git", dir_fd=self.root_fd, follow_symlinks=False)
        if _identity(metadata) != _identity(os.fstat(metadata_fd)):
            raise ValueError("repository_metadata_identity_unproven")
        self._confirm(index, metadata)
        observed = self._observe()
        if observed["outcome"] != "existing" or observed["head"] is not None:
            raise ValueError("created_repository_identity_unproven")
        branch = _git(self.root, "symbolic-ref", "HEAD")
        if branch.returncode or branch.stdout.strip() != "refs/heads/main":
            raise ValueError("created_repository_branch_unproven")
        observed["outcome"] = "created"
        observed["diagnostics"] = ["unborn_head_first_publication_requires_issue"]
        return observed

    def release(self):
        if self.closed:
            return
        self.closed = True
        failed = None
        for descriptor in reversed(self.descriptors):
            try:
                os.close(descriptor)
            except BaseException as error:  # noqa: BLE001 -- close all retained descriptors even on interruption
                if failed is None:
                    failed = error
        self.descriptors.clear()
        self.cleanup_state = "unknown" if failed is not None else "completed"
        if failed is not None:
            raise failed


from aware_workspace_runtime.repository_preparation import _PREPARATION_PORT_TYPES

_PREPARATION_PORT_TYPES.add(FilesystemRepositoryPreparationPort)
