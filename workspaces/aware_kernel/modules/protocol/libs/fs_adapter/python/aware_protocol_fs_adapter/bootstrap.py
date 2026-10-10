"""Protocol-owned input rendering and retained FileSystem composition.

No Git creator, copied file writer or Issue lifecycle policy. Preparation is
read-only until the original runtime supplies its single-spent physical claim.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
from importlib.resources import files
from pathlib import Path, PurePosixPath

from aware_protocol_runtime import ProtocolAdmissionOutcomeKind
from aware_protocol_runtime.bootstrap import (
    _PHYSICAL_TYPES,
    ProtocolBootstrapEffect,
    ProtocolBootstrapFile,
    ProtocolBootstrapInput,
    ProtocolBootstrapRequest,
    _consume_claim,
    detached,
    digest,
    protocol_bootstrap_value_to_payload,
)

from .goal_templates import canonical_relative_path
from .manifest import admit_protocol_manifest_bytes, validate_protocol_manifest_content


def _root(value):
    root = Path(value)
    if (
        not root.is_absolute()
        or str(root) != value
        or root.resolve(strict=False) != root
    ):
        raise ValueError("bootstrap_canonical_absolute_root_required")
    return root


def _issue_root(value):
    if not canonical_relative_path(value) or ".git" in PurePosixPath(value).parts:
        raise ValueError("bootstrap_issue_root_invalid")
    # Reject both equality and file/directory prefix collisions, even when
    # onboarding templates are not requested.
    for reserved in ("aware.protocol.toml", "AGENTS.md"):
        if value == reserved or value.startswith(reserved + "/"):
            raise ValueError("bootstrap_target_collision")


def _directories(root, issue_root):
    _issue_root(issue_root)
    missing = []
    parts = PurePosixPath(issue_root).parts
    for index in range(1, len(parts) + 1):
        relative = "/".join(parts[:index])
        try:
            observed = (root / relative).lstat()
        except FileNotFoundError:
            missing.append(relative)
        else:
            if not stat.S_ISDIR(observed.st_mode):
                raise ValueError("bootstrap_issue_ancestor_not_directory")
    if len(missing) > 64:
        raise ValueError("bootstrap_directory_limit_exceeded")
    return tuple(missing)


def _manifest(issue_root):
    return (
        'aware = 1\n\n[protocol]\nname = "aware.collaboration"\n'
        'profile = "aware.collaboration.fs_v1"\nsemantic_version = 1\n\n'
        '[target]\nkind = "repository"\nauthority_mode = "filesystem"\n\n'
        '[bootstrap]\nagent_contract = "AGENTS.md"\n\n'
        '[records.issue]\nprofile = "aware.issue.markdown.v1"\nrole = "authority"\n'
        "root = " + json.dumps(issue_root) + "\n"
        'path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"\n\n'
        '[records.goal]\nprofile = "aware.goal.markdown.v1"\nrole = "unavailable"\n\n'
        '[records.feed]\nprofile = "aware.feed.projection.v1"\nrole = "unavailable"\n\n'
        '[records.specification]\nprofile = "specification_fs_v1"\nrole = "unavailable"\n\n'
        '[records.evidence]\nprofile = "aware.protocol.evidence.v1"\nrole = "unavailable"\n'
    )


class FilesystemProtocolBootstrapPort:
    def __init__(self, *, repository_root):
        self.root = _root(repository_root)

    def prepare_request(self, *, issue_root, install_agent_contract, dry_run):
        request = ProtocolBootstrapRequest(
            str(self.root),
            issue_root=issue_root,
            directory_paths=_directories(self.root, issue_root),
            install_agent_contract=install_agent_contract,
            dry_run=dry_run,
        )
        self.render(request)
        return detached(request)

    def render(self, request):
        request = detached(request)
        if (
            type(request) is not ProtocolBootstrapRequest
            or _root(request.repository_root) != self.root
        ):
            raise ValueError("bootstrap_request_root_mismatch")
        if request.manifest_path != "aware.protocol.toml":
            raise ValueError("bootstrap_manifest_locator_invalid")
        if request.directory_paths != _directories(self.root, request.issue_root):
            raise ValueError("bootstrap_explicit_directory_sequence_required")
        content = _manifest(request.issue_root)
        admission = validate_protocol_manifest_content(source=content.encode())
        if admission.outcome is not ProtocolAdmissionOutcomeKind.CANONICAL_V1:
            raise ValueError(
                "bootstrap_content_invalid:" + ":".join(admission.diagnostics)
            )
        records = [(request.manifest_path, content)]
        if request.install_agent_contract:
            resource = files("aware_protocol_fs_adapter").joinpath("templates")
            records.extend(
                (
                    (
                        "AGENTS.md",
                        resource.joinpath("AGENTS.md").read_text(encoding="utf-8"),
                    ),
                    (
                        request.issue_root + "/PROTOCOL.md",
                        resource.joinpath("ISSUES-PROTOCOL.md").read_text(
                            encoding="utf-8"
                        ),
                    ),
                )
            )
        rendered = tuple(
            ProtocolBootstrapFile(path, body, digest(body.encode()), 0o644)
            for path, body in records
        )
        payload = {
            "request": protocol_bootstrap_value_to_payload(request),
            "files": [protocol_bootstrap_value_to_payload(item) for item in rendered],
        }
        return ProtocolBootstrapInput(
            request,
            rendered,
            digest(
                json.dumps(
                    payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                ).encode()
            ),
            ("profile:aware.collaboration.fs_v1", "only_issue_authority_available")
            + (
                ()
                if request.install_agent_contract
                else ("onboarding_files_not_installed",)
            ),
        )

    def retain(self, rendered):
        rendered = detached(rendered)
        if rendered != self.render(rendered.request):
            raise ValueError("bootstrap_original_rendering_required")
        return _Retained(self, rendered)


def _git_root(root):
    metadata = (root / ".git").lstat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("bootstrap_git_metadata_directory_required")
    environment = {
        name: os.environ[name]
        for name in ("PATH", "HOME", "LANG", "LC_ALL")
        if name in os.environ
    }
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
        timeout=30,
    )
    if result.returncode != 0 or result.stdout.strip() != str(root):
        raise ValueError("bootstrap_exact_git_root_required")
    observed = root.stat(follow_symlinks=False)
    if not stat.S_ISDIR(observed.st_mode):
        raise ValueError("bootstrap_repository_directory_required")
    return (observed.st_dev, observed.st_ino, observed.st_mode), (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
    )


class _Retained:
    def __init__(self, owner, rendered):
        # Optional supplier import only at explicit physical-plan issuance.
        from aware_file_system.retained_bootstrap import (
            BootstrapFileCreation,
            retain_confined_bootstrap_creation,
        )

        self.owner = owner
        self.rendered = rendered
        self.cleanup_state = "not_attempted"
        self.effects = ()
        self._released = False
        self._cleanup_uncertain = False
        self._pins = _git_root(owner.root)
        self._target_ancestors = {}
        for candidate in rendered.files:
            parts = PurePosixPath(candidate.path).parts[:-1]
            for index in range(1, len(parts) + 1):
                relative = "/".join(parts[:index])
                try:
                    observed = (owner.root / relative).lstat()
                except FileNotFoundError:
                    continue
                if not stat.S_ISDIR(observed.st_mode):
                    raise ValueError("bootstrap_target_ancestor_invalid")
                self._target_ancestors[relative] = (
                    observed.st_dev,
                    observed.st_ino,
                    stat.S_IMODE(observed.st_mode),
                )
        self._ancestors = tuple(
            (
                str(path),
                (
                    path.stat(follow_symlinks=False).st_dev,
                    path.stat(follow_symlinks=False).st_ino,
                ),
            )
            for path in (owner.root, *owner.root.parents)
        )
        self._creation = retain_confined_bootstrap_creation(
            root=owner.root,
            files=tuple(
                BootstrapFileCreation(item.path, item.content_utf8.encode(), item.mode)
                for item in rendered.files
            ),
            directory_paths=rendered.request.directory_paths,
        )

    def plan_digest(self):
        return digest(
            json.dumps(
                {
                    "git_root": self._pins,
                    "ancestors": self._ancestors,
                    "target_ancestors": self._target_ancestors,
                    "input": self.rendered.input_sha256,
                },
                sort_keys=True,
            ).encode()
        )

    def _git_current(self):
        if _git_root(self.owner.root) != self._pins:
            raise ValueError("bootstrap_git_root_changed")
        for path, identity in self._ancestors:
            observed = Path(path).stat(follow_symlinks=False)
            if (
                not stat.S_ISDIR(observed.st_mode)
                or (observed.st_dev, observed.st_ino) != identity
            ):
                raise ValueError("bootstrap_ancestor_changed")

    def validate_current(self):
        if self._released:
            raise ValueError("bootstrap_physical_terminal")
        self._git_current()
        self._creation.validate_current()

    def _capture(self):
        converted = []
        for effect in self._creation.observe_effects():
            identity = effect.after_identity
            converted.append(
                ProtocolBootstrapEffect(
                    effect.path,
                    effect.kind,
                    effect.state.value,
                    effect.durability_confirmed,
                    effect.before_digest,
                    effect.after_digest,
                    identity[0] if identity else None,
                    identity[1] if identity else None,
                    effect.mode,
                )
            )
        self.effects = tuple(detached(item) for item in converted)

    def _postimage_current(self):
        """Return-time observation after confirmed lower-owner finish, not authority renewal."""
        self._git_current()
        directories = dict(self._target_ancestors)
        for item in self.effects:
            if item.kind == "directory":
                directories[item.path] = (
                    item.after_device,
                    item.after_inode,
                    item.mode,
                )

        def verify_directories():
            for relative, expected in directories.items():
                current = (self.owner.root / relative).lstat()
                if (
                    not stat.S_ISDIR(current.st_mode)
                    or (current.st_dev, current.st_ino, stat.S_IMODE(current.st_mode))
                    != expected
                ):
                    raise ValueError("bootstrap_postimage_directory_changed")

        verify_directories()
        for candidate in self.rendered.files:
            expected = next(
                item
                for item in self.effects
                if item.path == candidate.path and item.kind == "file"
            )
            descriptor = os.open(
                self.owner.root / candidate.path,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            )
            try:
                before = os.fstat(descriptor)
                limit = len(candidate.content_utf8.encode())
                if (
                    not stat.S_ISREG(before.st_mode)
                    or before.st_nlink != 1
                    or before.st_size != limit
                    or (before.st_dev, before.st_ino)
                    != (expected.after_device, expected.after_inode)
                    or stat.S_IMODE(before.st_mode) != candidate.mode
                ):
                    raise ValueError("bootstrap_postimage_file_changed")
                chunks = []
                remaining = limit + 1
                while remaining:
                    chunk = os.read(descriptor, min(remaining, 65536))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                after = os.fstat(descriptor)
                if (
                    b"".join(chunks) != candidate.content_utf8.encode()
                    or before != after
                ):
                    raise ValueError("bootstrap_postimage_bytes_changed")
            finally:
                os.close(descriptor)
        verify_directories()
        self._git_current()

    def apply(self, *, claim):
        _consume_claim(claim, self)
        try:
            self.validate_current()
            for _ in self.rendered.request.directory_paths:
                self._creation.prepare_next_directory()
            for _ in self.rendered.files:
                self._creation.create_next_file()
            self._git_current()
            manifest = next(
                item
                for item in self.rendered.files
                if item.path == "aware.protocol.toml"
            )
            admitted = admit_protocol_manifest_bytes(
                source=manifest.content_utf8.encode(), repository_root=self.owner.root
            )
            if admitted.outcome is not ProtocolAdmissionOutcomeKind.CANONICAL_V1:
                raise ValueError("bootstrap_postimage_admission_refused")
            self._creation.validate_current()
            self._git_current()
            self._creation.finish()
            self._released = True
            self.cleanup_state = "completed"
            self._capture()
            self._postimage_current()
            if admitted.manifest is None or admitted.source_sha256 is None:
                raise ValueError("bootstrap_postimage_identity_missing")
            return admitted.source_sha256, admitted.manifest.digest
        except BaseException:
            # A lower transition can have retired after uncertain disposal.
            # Later idempotent release cannot upgrade that original outcome.
            if self.cleanup_state != "completed":
                self._cleanup_uncertain = True
                self.cleanup_state = "unknown"
            raise
        finally:
            self._capture()

    def release(self):
        if not self._released:
            self._released = True  # Any interrupted release is terminal/unknown.
            self.cleanup_state = "unknown"
            self._creation.release()
            self._capture()
            if not self._cleanup_uncertain:
                self.cleanup_state = "completed"


_PHYSICAL_TYPES.add(FilesystemProtocolBootstrapPort)
