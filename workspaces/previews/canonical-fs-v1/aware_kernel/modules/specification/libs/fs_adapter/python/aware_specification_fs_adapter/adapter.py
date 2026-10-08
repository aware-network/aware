"""Installed Specification filesystem adapter and public operations."""

from __future__ import annotations

import fcntl
import json
import os
import threading
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import cast

from aware_specification_fs_source_contract import (
    SpecificationFsParserProfileCoordinate,
    SpecificationFsSourceClosure,
)
from jsonschema import Draft202012Validator

from .contracts import (
    MANIFEST_SCHEMA_DIGEST,
    MANIFEST_SCHEMA_REF,
    SpecificationFsAdaptationResult,
    SpecificationFsAdapterError,
    SpecificationFsAdapterErrorKind,
    SpecificationFsObservationGrade,
    SpecificationFsProfileOutcome,
    SpecificationFsProfileOutcomeKind,
    SpecificationFsSchemaResolutionContext,
    validate_adaptation_result,
    validate_context,
)
from .lowering import LoweringError, lower_closures
from .observation import (
    ObservationError,
    fd_mount_id,
    mount_namespace_identity,
    observe_root,
)

_MAX_RESULTS = 128


@dataclass(frozen=True, slots=True)
class _ResultRecord:
    installation_token: object
    attempt_token: object
    result_identity: int
    outcomes_identity: int
    outcome_identities: tuple[int, ...]
    outcome_snapshots: tuple[tuple[object, ...], ...]
    lowering_identity: int
    lowering_snapshot: tuple[object, ...]
    result_snapshot: tuple[object, ...]


class SpecificationFsAdapter:
    """Installation-local adapter. Construct only through the public installer."""

    __slots__ = (
        "_active",
        "_base_fd",
        "_base_identity",
        "_condition",
        "_context",
        "_installation_token",
        "_namespace_identity",
        "_profile",
        "_registrations",
        "_reserved",
        "_schema_bytes",
        "_state",
        "_validator",
    )

    def __init__(
        self,
        authority: object,
        *,
        base_fd: int,
        base_identity: tuple[int, int, int],
        namespace_identity: tuple[int, int, int],
        schema_bytes: bytes,
        context: SpecificationFsSchemaResolutionContext,
        validator: Draft202012Validator,
        profile: SpecificationFsParserProfileCoordinate,
    ) -> None:
        if authority is not _INSTALL_AUTHORITY:
            raise TypeError("SpecificationFsAdapter construction is private")
        self._base_fd = base_fd
        self._base_identity = base_identity
        self._namespace_identity = namespace_identity
        self._schema_bytes = bytes(schema_bytes)
        self._context = context
        self._validator = validator
        self._profile = profile
        self._installation_token = object()
        self._condition = threading.Condition(threading.RLock())
        self._state = "open"
        self._active = 0
        self._reserved = 0
        self._registrations: dict[int, _ResultRecord] = {}

    def __copy__(self) -> None:
        raise TypeError("SpecificationFsAdapter is not copyable")

    def __deepcopy__(self, memo: object) -> None:
        raise TypeError("SpecificationFsAdapter is not copyable")


_INSTALL_AUTHORITY = object()


def _error(
    kind: SpecificationFsAdapterErrorKind, code: str, **values: object
) -> SpecificationFsAdapterError:
    return SpecificationFsAdapterError(
        kind,
        code,
        spec_root=cast(str | None, values.get("spec_root")),
        profile_outcome=cast(
            SpecificationFsProfileOutcome | None, values.get("profile_outcome")
        ),
    )


def _exact_adapter(value: object, code: str) -> SpecificationFsAdapter:
    if type(value) is not SpecificationFsAdapter:
        raise _error(SpecificationFsAdapterErrorKind.INPUT, code)
    return cast(SpecificationFsAdapter, value)


def _validate_schema_bytes(value: object) -> tuple[bytes, Draft202012Validator]:
    if type(value) is not bytes:
        raise _error(
            SpecificationFsAdapterErrorKind.INPUT, "invalid_installation_input"
        )
    body = cast(bytes, value)
    if f"sha256:{sha256(body).hexdigest()}" != MANIFEST_SCHEMA_DIGEST:
        raise _error(
            SpecificationFsAdapterErrorKind.INPUT, "invalid_installation_input"
        )
    try:
        decoded = body.decode("utf-8", "strict")
        schema = json.loads(decoded)
        if type(schema) is not dict:
            raise ValueError("schema root")
        if (
            schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
            or schema.get("$id") != MANIFEST_SCHEMA_REF
            or schema.get("title") != "Aware Specification Filesystem Manifest V1"
            or schema.get("x-aware-schema-identity")
            != "aware.specification.filesystem_manifest"
            or type(schema.get("x-aware-schema-version")) is not int
            or schema.get("x-aware-schema-version") != 1
        ):
            raise ValueError("schema identity")
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(MappingProxyType(schema))
    except Exception as error:
        raise _error(
            SpecificationFsAdapterErrorKind.INPUT, "invalid_installation_input"
        ) from error
    return bytes(body), validator


def install_specification_fs_adapter(
    source_base_fd: object,
    manifest_schema_bytes: object,
    schema_context: object,
) -> SpecificationFsAdapter:
    owned_fd: int | None = None
    try:
        if type(source_base_fd) is not int or source_base_fd < 0:
            raise _error(
                SpecificationFsAdapterErrorKind.INPUT, "invalid_installation_input"
            )
        try:
            context = validate_context(schema_context)
            schema_bytes, validator = _validate_schema_bytes(manifest_schema_bytes)
        except SpecificationFsAdapterError:
            raise
        except Exception as error:
            raise _error(
                SpecificationFsAdapterErrorKind.INPUT, "invalid_installation_input"
            ) from error
        try:
            namespace_identity = mount_namespace_identity()
            owned_fd = fcntl.fcntl(source_base_fd, fcntl.F_DUPFD_CLOEXEC, 0)
            stat_value = os.fstat(owned_fd)
            import stat

            if not stat.S_ISDIR(stat_value.st_mode):
                raise OSError("source base is not a directory")
            base_identity = (
                stat_value.st_dev,
                stat_value.st_ino,
                fd_mount_id(owned_fd),
            )
        except ObservationError as error:
            if error.code == "platform_observation_unsupported":
                raise _error(
                    SpecificationFsAdapterErrorKind.PLATFORM, error.code
                ) from error
            raise _error(
                SpecificationFsAdapterErrorKind.SOURCE, "source_base_invalid"
            ) from error
        except OSError as error:
            raise _error(
                SpecificationFsAdapterErrorKind.SOURCE, "source_base_invalid"
            ) from error
        profile = SpecificationFsParserProfileCoordinate(
            parser_implementation_ref=context.parser_implementation_ref,
            parser_implementation_digest=context.parser_implementation_digest,
        )
        result = SpecificationFsAdapter(
            _INSTALL_AUTHORITY,
            base_fd=owned_fd,
            base_identity=base_identity,
            namespace_identity=namespace_identity,
            schema_bytes=schema_bytes,
            context=context,
            validator=validator,
            profile=profile,
        )
        owned_fd = None
        return result
    except SpecificationFsAdapterError:
        raise
    except Exception as error:
        raise _error(
            SpecificationFsAdapterErrorKind.INTEGRITY,
            "specification_fs_adapter_internal_failure",
        ) from error
    finally:
        if owned_fd is not None:
            os.close(owned_fd)


def _begin(adapter: SpecificationFsAdapter, *, reserve: bool = False) -> object:
    with adapter._condition:
        if adapter._state != "open":
            raise _error(
                SpecificationFsAdapterErrorKind.LIFECYCLE,
                "specification_fs_adapter_closed",
            )
        if reserve and len(adapter._registrations) + adapter._reserved >= _MAX_RESULTS:
            raise _error(
                SpecificationFsAdapterErrorKind.CAPACITY,
                "adaptation_capacity_exhausted",
            )
        adapter._active += 1
        if reserve:
            adapter._reserved += 1
        return object()


def _end(adapter: SpecificationFsAdapter, *, reserve: bool = False) -> None:
    with adapter._condition:
        if reserve:
            adapter._reserved -= 1
        adapter._active -= 1
        adapter._condition.notify_all()


def _check_open_for_return(adapter: SpecificationFsAdapter) -> None:
    with adapter._condition:
        if adapter._state != "open":
            raise _error(
                SpecificationFsAdapterErrorKind.LIFECYCLE,
                "specification_fs_adapter_closed",
            )


def inspect_specification_fs_profile(
    adapter: object, spec_root: object
) -> SpecificationFsProfileOutcome:
    exact = _exact_adapter(adapter, "invalid_inspection_request")
    attempt = _begin(exact)
    try:
        try:
            observed = observe_root(
                exact._base_fd,
                spec_root,
                exact._base_identity[2],
                exact._namespace_identity,
                exact._profile,
                exact._validator,
            )
            _check_open_for_return(exact)
            return observed.outcome
        except ValueError as error:
            raise _error(
                SpecificationFsAdapterErrorKind.INPUT, "invalid_inspection_request"
            ) from error
        except ObservationError as error:
            kind = (
                SpecificationFsAdapterErrorKind.PLATFORM
                if error.code == "platform_observation_unsupported"
                else SpecificationFsAdapterErrorKind.SOURCE
            )
            code = (
                error.code
                if kind is SpecificationFsAdapterErrorKind.PLATFORM
                else "source_observation_failed"
            )
            raise _error(
                kind,
                code,
                **(
                    {"spec_root": spec_root}
                    if kind is SpecificationFsAdapterErrorKind.SOURCE
                    else {}
                ),
            ) from error
        except SpecificationFsAdapterError:
            raise
        except Exception as error:
            raise _error(
                SpecificationFsAdapterErrorKind.INTEGRITY,
                "specification_fs_adapter_internal_failure",
            ) from error
    finally:
        del attempt
        _end(exact)


def _record(
    adapter: SpecificationFsAdapter,
    attempt: object,
    result: SpecificationFsAdaptationResult,
) -> _ResultRecord:
    outcomes = result.outcomes
    lowering = result.lowering
    return _ResultRecord(
        adapter._installation_token,
        attempt,
        id(result),
        id(outcomes),
        tuple(id(value) for value in outcomes),
        tuple(
            (value.spec_root, value.kind, value.diagnostic_code, value.outcome_digest)
            for value in outcomes
        ),
        id(lowering),
        (
            id(lowering.closures),
            tuple(id(value) for value in lowering.closures),
            id(lowering.schema_context),
            lowering.root_set_digest,
            id(lowering.snapshot),
            lowering.snapshot.snapshot_digest,
            lowering.lowering_digest,
        ),
        (
            id(result.outcomes),
            id(result.lowering),
            result.observation_grade,
            result.adaptation_digest,
        ),
    )


def adapt_specification_fs_roots(
    adapter: object,
    spec_roots: object,
    expected_root_set_digest: object = None,
) -> SpecificationFsAdaptationResult:
    exact = _exact_adapter(adapter, "invalid_adaptation_request")
    if (
        type(spec_roots) is not tuple
        or not spec_roots
        or any(type(root) is not str for root in spec_roots)
    ):
        raise _error(
            SpecificationFsAdapterErrorKind.INPUT, "invalid_adaptation_request"
        )
    roots = cast(tuple[str, ...], spec_roots)
    try:
        encoded = tuple(root.encode("utf-8", "strict") for root in roots)
    except UnicodeEncodeError as error:
        raise _error(
            SpecificationFsAdapterErrorKind.INPUT, "invalid_adaptation_request"
        ) from error
    if encoded != tuple(sorted(set(encoded))):
        raise _error(
            SpecificationFsAdapterErrorKind.INPUT, "invalid_adaptation_request"
        )
    if expected_root_set_digest is not None and (
        type(expected_root_set_digest) is not str
        or not expected_root_set_digest.startswith("sha256:")
        or len(expected_root_set_digest) != 71
        or any(
            character not in "0123456789abcdef"
            for character in expected_root_set_digest[7:]
        )
    ):
        raise _error(
            SpecificationFsAdapterErrorKind.INPUT, "invalid_adaptation_request"
        )
    attempt = _begin(exact, reserve=True)
    registered = False
    try:
        observations = []
        for root in roots:
            try:
                observed = observe_root(
                    exact._base_fd,
                    root,
                    exact._base_identity[2],
                    exact._namespace_identity,
                    exact._profile,
                    exact._validator,
                )
            except ValueError as error:
                raise _error(
                    SpecificationFsAdapterErrorKind.INPUT, "invalid_adaptation_request"
                ) from error
            except ObservationError as error:
                kind = (
                    SpecificationFsAdapterErrorKind.PLATFORM
                    if error.code == "platform_observation_unsupported"
                    else SpecificationFsAdapterErrorKind.SOURCE
                )
                code = (
                    error.code
                    if kind is SpecificationFsAdapterErrorKind.PLATFORM
                    else "source_observation_failed"
                )
                raise _error(
                    kind,
                    code,
                    **(
                        {"spec_root": root}
                        if kind is SpecificationFsAdapterErrorKind.SOURCE
                        else {}
                    ),
                ) from error
            observations.append(observed)
            if (
                observed.outcome.kind
                is not SpecificationFsProfileOutcomeKind.CANONICAL_V1
            ):
                raise _error(
                    SpecificationFsAdapterErrorKind.PROFILE,
                    "noncanonical_specification_profile",
                    spec_root=root,
                    profile_outcome=observed.outcome,
                )
        closures = tuple(cast(object, value.closure) for value in observations)
        try:
            lowering = lower_closures(
                closures, exact._context, expected_root_set_digest
            )
        except LoweringError as error:
            raise _error(
                SpecificationFsAdapterErrorKind.SEMANTIC,
                "specification_semantic_lowering_failed",
            ) from error
        result = SpecificationFsAdaptationResult(
            tuple(value.outcome for value in observations),
            lowering,
            SpecificationFsObservationGrade.LOCAL_STRUCTURAL_OBSERVATION,
        )
        record = _record(exact, attempt, result)
        with exact._condition:
            if exact._state != "open":
                raise _error(
                    SpecificationFsAdapterErrorKind.LIFECYCLE,
                    "specification_fs_adapter_closed",
                )
            exact._registrations[id(result)] = record
            registered = True
        return result
    except SpecificationFsAdapterError:
        raise
    except Exception as error:
        raise _error(
            SpecificationFsAdapterErrorKind.INTEGRITY,
            "specification_fs_adapter_internal_failure",
        ) from error
    finally:
        if not registered:
            with exact._condition:
                exact._registrations.pop(id(locals().get("result")), None)
        _end(exact, reserve=True)


def _record_matches(
    adapter: SpecificationFsAdapter,
    result: SpecificationFsAdaptationResult,
    record: _ResultRecord,
) -> bool:
    try:
        outcomes = result.outcomes
        lowering = result.lowering
        return (
            record.installation_token is adapter._installation_token
            and record.result_identity == id(result)
            and record.outcomes_identity == id(outcomes)
            and record.outcome_identities == tuple(id(value) for value in outcomes)
            and record.outcome_snapshots
            == tuple(
                (
                    value.spec_root,
                    value.kind,
                    value.diagnostic_code,
                    value.outcome_digest,
                )
                for value in outcomes
            )
            and record.lowering_identity == id(lowering)
            and record.lowering_snapshot
            == (
                id(lowering.closures),
                tuple(id(value) for value in lowering.closures),
                id(lowering.schema_context),
                lowering.root_set_digest,
                id(lowering.snapshot),
                lowering.snapshot.snapshot_digest,
                lowering.lowering_digest,
            )
            and record.result_snapshot
            == (
                id(outcomes),
                id(lowering),
                result.observation_grade,
                result.adaptation_digest,
            )
        )
    except AttributeError:
        return False


def consume_specification_fs_adaptation(
    adapter: object, result: object
) -> SpecificationFsAdaptationResult:
    exact = _exact_adapter(adapter, "invalid_adaptation_result")
    if type(result) is not SpecificationFsAdaptationResult:
        raise _error(SpecificationFsAdapterErrorKind.INPUT, "invalid_adaptation_result")
    value = cast(SpecificationFsAdaptationResult, result)
    _ = _begin(exact)
    try:
        with exact._condition:
            record = exact._registrations.get(id(value))
            try:
                validate_adaptation_result(value)
            except Exception as error:
                exact._registrations.pop(id(value), None)
                raise _error(
                    SpecificationFsAdapterErrorKind.INTEGRITY,
                    "specification_fs_adaptation_invalid",
                ) from error
            if record is None or not _record_matches(exact, value, record):
                exact._registrations.pop(id(value), None)
                raise _error(
                    SpecificationFsAdapterErrorKind.INTEGRITY,
                    "specification_fs_adaptation_invalid",
                )
            exact._registrations.pop(id(value), None)
            return value
    finally:
        _end(exact)


def close_specification_fs_adapter(adapter: object) -> None:
    exact = _exact_adapter(adapter, "invalid_close_request")
    try:
        with exact._condition:
            if exact._state == "closed":
                return
            if exact._state == "closing":
                while exact._state != "closed":
                    exact._condition.wait()
                return
            exact._state = "closing"
            while exact._active:
                exact._condition.wait()
            exact._registrations.clear()
            exact._reserved = 0
            fd = exact._base_fd
            exact._base_fd = -1
            exact._state = "closed"
            exact._condition.notify_all()
        os.close(fd)
    except SpecificationFsAdapterError:
        raise
    except Exception as error:
        raise _error(
            SpecificationFsAdapterErrorKind.INTEGRITY,
            "specification_fs_adapter_internal_failure",
        ) from error


def lower_specification_fs_closures(closures: object, schema_context: object):
    if (
        type(closures) is not tuple
        or not closures
        or any(
            type(closure) is not SpecificationFsSourceClosure for closure in closures
        )
        or type(schema_context) is not SpecificationFsSchemaResolutionContext
    ):
        raise _error(SpecificationFsAdapterErrorKind.INPUT, "invalid_lowering_input")
    try:
        for closure in closures:
            closure.__post_init__()
        schema_context.__post_init__()
    except Exception as error:
        raise _error(
            SpecificationFsAdapterErrorKind.INPUT, "invalid_lowering_input"
        ) from error
    try:
        return lower_closures(closures, schema_context)
    except LoweringError as error:
        raise _error(
            SpecificationFsAdapterErrorKind.SEMANTIC,
            "specification_semantic_lowering_failed",
        ) from error
    except Exception as error:
        raise _error(
            SpecificationFsAdapterErrorKind.SEMANTIC,
            "specification_semantic_lowering_failed",
        ) from error
