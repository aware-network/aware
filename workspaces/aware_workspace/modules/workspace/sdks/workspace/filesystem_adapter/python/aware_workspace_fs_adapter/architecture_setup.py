"""Physical setup effects via original FileSystem CAS; explicit UV utility."""

from __future__ import annotations

import errno
import fcntl
import os
import stat
import subprocess
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from aware_file_system import confined_mutation as retained_reader
from aware_file_system.confined_mutation import (
    ConfinedFileMutationRequest,
    ConfinedMutationKind,
    ConfinedMutationOutcome,
    ConfinedObservationOutcome,
    mutate_confined_file,
    observe_confined_file,
)
from aware_workspace_sdk.architecture_setup import (
    ArchitectureSetupError,
    ArchitectureSetupReceipt,
    PackageManagerReceipt,
)
from aware_workspace_sdk.architecture_setup_admission_values import (
    WorkspaceSetupClientCleanup,
    WorkspaceSetupPrimaryFailure,
    WorkspaceSetupResourceEvidence,
)

_A1_CLOSE = os.close
_A1_FLOCK = fcntl.flock


class FilesystemArchitectureSetup:
    def __init__(self, *, repository_root: Path, uv_executable: Path | None = None):
        if not repository_root.is_absolute():
            raise ArchitectureSetupError("absolute_prepared_repository_root_required")
        # Never convert a symlink alias into permission to work on its target.
        cursor = Path(repository_root.anchor)
        for part in repository_root.parts[1:]:
            if part in (".", ".."):
                raise ArchitectureSetupError("canonical_repository_root_required")
            cursor = cursor / part
            if stat.S_ISLNK(cursor.lstat().st_mode):
                raise ArchitectureSetupError("repository_root_symlink_denied")
        self.root = repository_root
        self.fd = -1
        self.uv = uv_executable
        self._a1_root_resource = WorkspaceSetupResourceEvidence(
            "setup-root:" + uuid4().hex,
            "aware.workspace.setup-a1.v1",
            "root_descriptor",
            str(repository_root),
            "unknown",
            False,
            "unknown",
            (),
        )
        self._a1_lease_resources = []
        self._a1_read_resources = []
        self._a1_read_complete = True
        self._a1_record_reads = False
        try:
            self.fd = os.open(
                repository_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            )
            current = os.fstat(self.fd)
            self.identity = (current.st_dev, current.st_ino)
            row = self._a1_root_resource
            self._a1_root_resource = WorkspaceSetupResourceEvidence(
                row.resource_ref,
                row.provider_ref,
                row.kind,
                row.path,
                "owned",
                False,
                "unknown",
                (),
            )
        except BaseException as error:
            row = self._a1_root_resource
            if self.fd >= 0:
                try:
                    self.release_a1_root()
                except BaseException:  # noqa: BLE001, S110 - retained resource row already records the uncertain close; never retry
                    pass
            elif isinstance(error, OSError) and error.errno in (
                errno.ENOENT,
                errno.ENOTDIR,
                errno.EACCES,
                errno.EPERM,
                errno.ELOOP,
            ):
                self._a1_root_resource = WorkspaceSetupResourceEvidence(
                    row.resource_ref,
                    row.provider_ref,
                    row.kind,
                    row.path,
                    "released",
                    False,
                    "confirmed",
                    (),
                )
            confirmed = self._a1_root_resource.release_outcome == "confirmed"
            failure = ArchitectureSetupError("setup_client_construction_failed")
            failure.client_cleanup = WorkspaceSetupClientCleanup(
                "aware.workspace.setup-a1.v1",
                None,
                None,
                (self._a1_root_resource,),
                True,
                "confirmed" if confirmed else "unknown",
                WorkspaceSetupPrimaryFailure(
                    "observed",
                    "aware.workspace.setup-a1.v1",
                    "client_construction",
                    "setup_client_construction_failed",
                    type(error).__name__,
                    not isinstance(error, Exception),
                ),
                (),
                confirmed,
            )
            raise failure from error

    def current(self):
        if self.fd < 0:
            raise ArchitectureSetupError("setup_provider_closed")
        current = os.lstat(self.root)
        if (current.st_dev, current.st_ino) != self.identity or not stat.S_ISDIR(
            current.st_mode
        ):
            raise ArchitectureSetupError("repository_root_changed")

    def close(self):
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def release_a1_root(self):
        row = self._a1_root_resource
        if row.release_attempted or self.fd < 0:
            return row
        descriptor = self.fd
        self.fd = -1  # Consume before dispatch; an uncertain fd is never retried.
        self._a1_root_resource = WorkspaceSetupResourceEvidence(
            row.resource_ref,
            row.provider_ref,
            row.kind,
            row.path,
            "unknown",
            True,
            "unknown",
            (),
        )
        _A1_CLOSE(descriptor)
        self._a1_root_resource = WorkspaceSetupResourceEvidence(
            row.resource_ref,
            row.provider_ref,
            row.kind,
            row.path,
            "released",
            True,
            "confirmed",
            (),
        )
        return self._a1_root_resource

    @contextmanager
    def lease_a1(self):
        self.current()
        if fcntl.flock is not _A1_FLOCK:
            raise ArchitectureSetupError("setup_original_lease_changed")
        ref = "setup-lease:" + uuid4().hex
        self._a1_lease_resources.append(
            WorkspaceSetupResourceEvidence(
                ref,
                "aware.workspace.setup-a1.v1",
                "lease",
                str(self.root),
                "owned",
                False,
                "unknown",
                (),
            )
        )
        position = len(self._a1_lease_resources) - 1
        try:
            _A1_FLOCK(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException as error:
            definite = isinstance(error, OSError) and error.errno in (
                errno.EAGAIN,
                errno.EACCES,
            )
            self._a1_lease_resources[position] = WorkspaceSetupResourceEvidence(
                ref,
                "aware.workspace.setup-a1.v1",
                "lease",
                str(self.root),
                "released" if definite else "unknown",
                False,
                "confirmed" if definite else "unknown",
                (),
            )
            raise
        try:
            self.current()
            yield
        finally:
            self._a1_lease_resources[position] = WorkspaceSetupResourceEvidence(
                ref,
                "aware.workspace.setup-a1.v1",
                "lease",
                str(self.root),
                "unknown",
                True,
                "unknown",
                (),
            )
            _A1_FLOCK(self.fd, fcntl.LOCK_UN)
            self._a1_lease_resources[position] = WorkspaceSetupResourceEvidence(
                ref,
                "aware.workspace.setup-a1.v1",
                "lease",
                str(self.root),
                "released",
                True,
                "confirmed",
                (),
            )

    @contextmanager
    def lease(self):
        self.current()
        fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            self.current()
            yield
        finally:
            fcntl.flock(self.fd, fcntl.LOCK_UN)

    def _adopt_a1_read(self, ledger):
        unknown = (
            ledger.acquisition_unknown
            or ledger.release_unknown
            or ledger.context_unknown
        )
        self._a1_read_complete = self._a1_read_complete and not unknown
        for row in ledger.resources:
            self._a1_read_resources.append(
                WorkspaceSetupResourceEvidence(
                    row.resource_ref,
                    "aware.workspace.setup-a1.v1",
                    row.kind,
                    row.path,
                    "unknown" if unknown else "released",
                    row.spent,
                    "unknown" if unknown else "confirmed",
                    (),
                )
            )

    def read(self, path):
        self.current()
        if self._a1_record_reads:
            if len(self._a1_read_resources) + len(path.split("/")) + 1 > 16384:
                raise ArchitectureSetupError("setup_resource_record_limit")
            try:
                view, _, ledger = retained_reader._observe_confined_file_with_custody(
                    root=self.root, path=path, maximum_bytes=1048576
                )
            except retained_reader.ConfinedFileObservationError as error:
                ledger = error._original_read_ledger
                if type(ledger) is retained_reader._ReadLedger:
                    self._adopt_a1_read(ledger)
                else:
                    self._a1_read_complete = False
                raise
            self._adopt_a1_read(ledger)
            observation = view.observation
        else:
            observation = observe_confined_file(
                root=self.root, path=path, maximum_bytes=1048576
            )
        if observation.outcome is not ConfinedObservationOutcome.OBSERVED:
            raise ArchitectureSetupError(
                "source_observation_refused:" + str(observation.error_code)
            )
        return observation.content if observation.exists else None

    def apply(self, plan):
        from aware_workspace_runtime.architecture_setup import digest

        written = []
        effect_attempted = False
        # Publish a child's original files before exposing its parent registration.
        paths = sorted(plan.outputs, key=lambda p: (plan.inputs.get(p) is not None, p))

        def receipt(status, diagnostics=()):
            return ArchitectureSetupReceipt(
                plan.request.operation,
                plan.preview.plan_sha256,
                status,
                tuple(written),
                tuple(p for p in paths if p not in written),
                diagnostics,
            )

        def current_inputs():
            for path, body in plan.inputs.items():
                expected = plan.outputs[path] if path in written else body
                if self.read(path) != expected:
                    raise ArchitectureSetupError("setup_input_drift:" + path)

        try:
            current_inputs()
            for path in paths:
                self.current()
                current_inputs()
                before = plan.inputs.get(path)
                effect_attempted = True
                result = mutate_confined_file(
                    root=self.root,
                    request=ConfinedFileMutationRequest(
                        kind=ConfinedMutationKind.CREATE
                        if before is None
                        else ConfinedMutationKind.UPDATE,
                        path=path,
                        expected_exists=before is not None,
                        expected_content_digest=digest(before),
                        content=plan.outputs[path],
                        maximum_bytes=1024 * 1024,
                    ),
                )
                if result.effect_applied:
                    written.append(path)
                if (
                    result.outcome is not ConfinedMutationOutcome.APPLIED
                    or not result.durability_confirmed
                ):
                    raise ArchitectureSetupError(
                        "setup_effect_failed:" + str(result.error_code)
                    )
                if self.read(path) != plan.outputs[path]:
                    raise ArchitectureSetupError("setup_positive_reread_failed")
            current_inputs()
        except Exception as error:
            # CREATE may leave parent directories even when its file did not complete.
            status = "uncertain" if effect_attempted else "rejected"
            raise ArchitectureSetupError(
                str(error),
                receipt=receipt(
                    status,
                    (
                        "inspect_parent_directories_and_retained_file_effects_before_retry",
                    ),
                ),
            ) from error
        return receipt("succeeded" if written else "unchanged")

    def run_uv(self, *, check, resolution_root="", inputs):
        # Retain every directory identity in the selected root's descriptor walk.
        descriptors = [os.dup(self.fd)]
        identities = [(self.root, self.identity)]
        try:
            cursor = self.root
            for part in resolution_root.split("/") if resolution_root else ():
                if part in ("", ".", ".."):
                    raise ArchitectureSetupError("invalid_resolution_root")
                cursor = cursor / part
                child = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=descriptors[-1],
                )
                descriptors.append(child)
                info = os.fstat(child)
                identities.append((cursor, (info.st_dev, info.st_ino)))

            def current():
                self.current()
                for ancestor in self.root.parents:
                    if any(
                        (ancestor / file).exists()
                        for file in ("pyproject.toml", "uv.toml")
                    ):
                        raise ArchitectureSetupError(
                            "external_ancestor_project_requires_context_qualification"
                        )
                for path, identity in identities:
                    info = path.lstat()
                    if (
                        not stat.S_ISDIR(info.st_mode)
                        or (info.st_dev, info.st_ino) != identity
                    ):
                        raise ArchitectureSetupError("resolution_root_changed")
                for path, body in inputs.items():
                    if self.read(path) != body:
                        raise ArchitectureSetupError("lock_input_drift:" + path)

            return self._run_uv(
                check=check, resolution_root=resolution_root, current=current
            )
        finally:
            for fd in reversed(descriptors):
                os.close(fd)

    def _run_uv(self, *, check, resolution_root, current):
        from aware_workspace_runtime.architecture_setup import digest

        current()
        selected = self.root / resolution_root
        lock_path = resolution_root + "/uv.lock" if resolution_root else "uv.lock"
        if self.uv is None or not self.uv.is_absolute() or not self.uv.is_file():
            raise ArchitectureSetupError("explicit_uv_executable_required")
        # UV can discover an ancestor workspace even with --project. Reject that topology.
        for ancestor in self.root.parents:
            if any(
                (ancestor / file).exists() for file in ("pyproject.toml", "uv.toml")
            ):
                raise ArchitectureSetupError(
                    "external_ancestor_project_requires_context_qualification"
                )
        env = {
            key: os.environ[key]
            for key in ("PATH", "HOME", "LANG", "XDG_CACHE_HOME")
            if key in os.environ
        }
        version = subprocess.run(
            [str(self.uv), "--version"],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if version.returncode or version.stdout.strip() not in (
            "uv 0.11.19 (x86_64-unknown-linux-gnu)",
            "uv 0.11.19",
        ):
            raise ArchitectureSetupError("unsupported_uv_version")
        current()
        command = (
            str(self.uv),
            "lock",
            "--offline",
            "--no-python-downloads",
            "--no-progress",
            "--project",
            str(selected),
        )
        if check:
            command += ("--check",)
        before = self.read(lock_path)
        current()
        try:
            result = subprocess.run(
                command,
                cwd=selected,
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except (subprocess.TimeoutExpired, OSError) as error:
            timed_out = isinstance(error, subprocess.TimeoutExpired)
            diagnostics = [
                "process_timed_out:partial_output_only"
                if timed_out
                else "process_failed:" + type(error).__name__,
                "lock_effects_uncertain:inspect_before_retry",
            ]
            after = None
            observation = "unavailable"
            try:
                current()
                after = self.read(lock_path)
                observation = "present" if after is not None else "absent"
            except (ArchitectureSetupError, OSError) as observation_error:
                diagnostics.append(
                    "after_lock_observation_failed:" + type(observation_error).__name__
                )
            receipt = PackageManagerReceipt(
                "check_locks" if check else "update_locks",
                str(selected),
                command,
                None,
                _partial_output(error.stdout) if timed_out else "",
                _partial_output(error.stderr) if timed_out else "",
                digest(before),
                digest(after) if observation != "unavailable" else None,
                status="uncertain",
                before_lock_observation="present" if before is not None else "absent",
                after_lock_observation=observation,
                diagnostics=tuple(diagnostics),
            )
            raise ArchitectureSetupError(
                "uv_timeout_inspect_lock_before_retry"
                if timed_out
                else "uv_process_failed_inspect_lock_before_retry",
                receipt=receipt,
            ) from error
        observation = "unavailable"
        after = None
        diagnostics = []
        try:
            current()
            after = self.read(lock_path)
            observation = "present" if after is not None else "absent"
            if check and before != after:
                diagnostics.append("lock_check_changed_bytes:inspect_before_retry")
        except (ArchitectureSetupError, OSError) as error:
            diagnostics.append("post_lock_currentness_failed:" + str(error))
        receipt = PackageManagerReceipt(
            "check_locks" if check else "update_locks",
            str(selected),
            command,
            result.returncode,
            result.stdout,
            result.stderr,
            digest(before),
            digest(after) if observation != "unavailable" else None,
            status="uncertain" if diagnostics else "completed",
            before_lock_observation="present" if before is not None else "absent",
            after_lock_observation=observation,
            diagnostics=tuple(diagnostics),
        )
        if diagnostics:
            raise ArchitectureSetupError("lock_effects_uncertain", receipt=receipt)
        if result.returncode:
            return receipt
        return receipt


def _partial_output(output: str | bytes | None) -> str:
    # TimeoutExpired can carry bytes even for text=True. Keep them reversible.
    return (
        output.decode("utf-8", errors="surrogateescape")
        if isinstance(output, bytes)
        else output or ""
    )


from aware_workspace_runtime.architecture_setup import _register_physical_type

_register_physical_type(FilesystemArchitectureSetup)
