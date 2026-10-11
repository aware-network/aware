"""Original bounded input reader, now behind the explicitly selected SDK port."""

import errno
import hashlib
import os
import stat
from dataclasses import replace
from importlib import metadata
from pathlib import Path

from aware_specification_sdk.input_observation import (
    SPECIFICATION_INPUT_LIMIT,
    SpecificationInputCleanup,
    SpecificationInputObservationError,
    SpecificationInputObservationRequest,
    SpecificationInputObservationResult,
)


def _identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


class SpecificationFsInputObservationProvider:
    def observe_draft_input(
        self, request: SpecificationInputObservationRequest
    ) -> SpecificationInputObservationResult:
        if type(request) is not SpecificationInputObservationRequest:
            raise SpecificationInputObservationError("input_request_invalid")
        try:
            request = replace(request)
        except (AttributeError, TypeError, ValueError) as error:
            raise SpecificationInputObservationError("input_request_invalid") from error
        base = Path(request.base_ref)
        if not base.is_absolute():
            raise SpecificationInputObservationError(
                "draft_input_base_absolute_required",
                request=request,
                provider_invoked=True,
            )
        path = Path(request.source_ref)
        if not path.is_absolute():
            path = base / path
        descriptor = None
        body = None
        primary = None
        code = None
        diagnostics = ()
        cleanup = SpecificationInputCleanup.NOT_ACQUIRED
        try:
            descriptor = os.open(
                path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
            )
            cleanup = SpecificationInputCleanup.UNKNOWN
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode):
                code = "draft_input_regular_file_required"
                raise ValueError(code)
            if before.st_size > SPECIFICATION_INPUT_LIMIT:
                code = "draft_input_too_large"
                raise ValueError(code)
            parts = []
            count = 0
            while True:
                part = os.read(
                    descriptor, min(65536, SPECIFICATION_INPUT_LIMIT + 1 - count)
                )
                if not part:
                    break
                parts.append(part)
                count += len(part)
                if count > SPECIFICATION_INPUT_LIMIT:
                    code = "draft_input_too_large"
                    raise ValueError(code)
            body = b"".join(parts)
            after = os.fstat(descriptor)
            named = path.lstat()
            if (
                _identity(before) != _identity(after)
                or _identity(after) != _identity(named)
                or count != before.st_size
            ):
                code = "draft_input_changed"
                raise ValueError(code)
        except BaseException as error:  # noqa: BLE001 - settle original descriptor before return
            primary = error
            if code is None:
                code = (
                    "draft_input_open_failed"
                    if descriptor is None
                    else "draft_input_read_failed"
                )
                reasons = {
                    errno.ENOENT: "not_found",
                    errno.ENOTDIR: "parent_not_directory",
                    errno.EACCES: "permission_denied",
                    errno.EPERM: "permission_denied",
                    errno.ELOOP: "symlink_or_loop",
                }
                error_number = getattr(error, "errno", None)
                reason = (
                    reasons.get(error_number, "unavailable")
                    if isinstance(error_number, int)
                    else "unavailable"
                )
                diagnostics = (
                    "draft_input_reason:" + reason,
                    "draft_input_detail:" + type(error).__name__,
                )
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                    cleanup = SpecificationInputCleanup.CLOSED
                except BaseException as error:  # noqa: BLE001 - never invent successful release
                    if primary is None:
                        primary = error
                        code = "draft_input_cleanup_unverified"
                    diagnostics += ("input_cleanup_failed:" + type(error).__name__,)
        if primary is not None:
            raise SpecificationInputObservationError(
                code or "draft_input_read_failed",
                request=request,
                provider_invoked=True,
                cleanup=cleanup,
                effect="unknown"
                if cleanup is SpecificationInputCleanup.UNKNOWN
                else "none",
                diagnostics=diagnostics,
                source_ref=str(path),
                observed_body_hex=None if body is None else body.hex(),
            ) from primary
        if body is None:
            raise SpecificationInputObservationError(
                "draft_input_body_unavailable",
                request=request,
                provider_invoked=True,
                cleanup=cleanup,
                source_ref=str(path),
            )
        try:
            try:
                version = metadata.version("aware-specification-fs-sdk-adapter")
            except metadata.PackageNotFoundError:
                version = "source"
            return SpecificationInputObservationResult(
                request,
                str(path),
                "aware_specification_fs_sdk_adapter.input.v1",
                "aware-specification-fs-sdk-adapter",
                version,
                body.hex(),
                len(body),
                "sha256:" + hashlib.sha256(body).hexdigest(),
                cleanup,
            )
        except BaseException as error:
            raise SpecificationInputObservationError(
                "draft_input_result_failed",
                request=request,
                provider_invoked=True,
                cleanup=cleanup,
                source_ref=str(path),
                observed_body_hex=body.hex(),
                diagnostics=("input_result_failure:" + type(error).__name__,),
            ) from error
