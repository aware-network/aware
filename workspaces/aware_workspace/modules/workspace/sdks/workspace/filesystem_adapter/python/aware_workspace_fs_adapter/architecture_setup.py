"""Physical setup effects via original FileSystem CAS; explicit UV utility."""

from __future__ import annotations

import fcntl
import os
import stat
import subprocess
from contextlib import contextmanager
from pathlib import Path

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
        self.fd = os.open(repository_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        current = os.fstat(self.fd)
        self.identity = (current.st_dev, current.st_ino)
        self.uv = uv_executable

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

    @contextmanager
    def lease(self):
        self.current()
        fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            self.current()
            yield
        finally:
            fcntl.flock(self.fd, fcntl.LOCK_UN)

    def read(self, path):
        self.current()
        observation = observe_confined_file(
            root=self.root, path=path, maximum_bytes=1024 * 1024
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
