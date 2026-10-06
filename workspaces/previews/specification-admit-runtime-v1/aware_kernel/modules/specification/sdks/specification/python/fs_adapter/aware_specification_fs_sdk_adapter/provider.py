"""Existing adapter composition; retained capabilities are not decoded DTOs."""

import os
import threading
from collections.abc import Callable
from importlib.resources import files

from aware_specification_fs_adapter import (
    SpecificationFsAdaptationResult,
    SpecificationFsAdapterError,
    SpecificationFsSchemaResolutionContext,
    adapt_specification_fs_roots,
    close_specification_fs_adapter,
    consume_specification_fs_adaptation,
    install_specification_fs_adapter,
)
from aware_specification_fs_adapter.observation import (
    fd_mount_id,
    mount_namespace_identity,
    validate_source_base,
)
from aware_specification_fs_source_contract.values import canonical_relative_path
from aware_specification_runtime import (
    SpecificationIterationIdentity,
    SpecificationSnapshot,
    resolve_iteration_identity,
)
from aware_specification_sdk import (
    SpecificationDraftRequest,
    SpecificationDraftResult,
    SpecificationObservation,
    SpecificationObserveRequest,
    SpecificationOperationError,
)

from .draft import cleanup_stage, rename_no_replace, render_draft, stage_files
from .source_evidence import SpecificationIterationSourceEvidence

_ISSUE_KEY = object()


class SpecificationIterationAdmission:
    __slots__ = ("_identity", "_observation", "_provider")

    def __init__(self, key: object, provider, observation, identity) -> None:
        if key is not _ISSUE_KEY:
            raise TypeError("iteration admission construction is private")
        self._provider = provider
        self._observation = observation
        self._identity = identity

    @property
    def identity(self) -> SpecificationIterationIdentity:
        return self._identity

    @property
    def observation(self) -> SpecificationObservation:
        return self._observation

    def __copy__(self):
        raise TypeError("iteration admission is not copyable")

    def __deepcopy__(self, memo):
        raise TypeError("iteration admission is not copyable")


def _fingerprint(
    observation: SpecificationObservation, identity: SpecificationIterationIdentity
):
    if (
        type(observation) is not SpecificationObservation
        or type(identity) is not SpecificationIterationIdentity
    ):
        raise SpecificationOperationError("invalid_iteration_admission")
    try:
        observation.__post_init__()
        identity.__post_init__()
    except (AttributeError, TypeError, ValueError) as error:
        raise SpecificationOperationError("invalid_iteration_admission") from error
    return (
        observation.source_digest,
        observation.source_context_digest,
        observation.snapshot.snapshot_digest,
        observation.provider_ref,
        identity.iteration_ref,
        identity.plan_digest,
    )


class SpecificationFsSdkProvider:
    @classmethod
    def from_protocol_selection(cls, selection: object) -> "SpecificationFsSdkProvider":
        """Consume original Protocol issuance; never derive authority from paths."""
        if cls is not SpecificationFsSdkProvider:
            raise SpecificationOperationError("invalid_source_provider_type")
        from .protocol_selection import provider_from_protocol_selection

        return provider_from_protocol_selection(selection)

    def __init__(self, source_base_fd: int, roots: tuple[str, ...]) -> None:
        if (
            type(source_base_fd) is not int
            or type(roots) is not tuple
            or not roots
            or any(type(r) is not str for r in roots)
        ):
            raise SpecificationOperationError("invalid_source_selection")
        try:
            for root in roots:
                canonical_relative_path(root, "spec_root")
            if roots != tuple(sorted(set(roots), key=lambda r: r.encode("utf-8"))):
                raise ValueError("roots must be explicit, unique and ordered")
            self._context = SpecificationFsSchemaResolutionContext()
            schema = (
                files("aware_specification_fs_sdk_adapter")
                .joinpath("resources/aware-spec-v1.schema.json")
                .read_bytes()
            )
            self._namespace = mount_namespace_identity()
            self._adapter = install_specification_fs_adapter(
                source_base_fd, schema, self._context
            )
            try:
                self._base_fd = os.dup(source_base_fd)
                try:
                    self._base_identity = validate_source_base(self._base_fd)
                    if mount_namespace_identity() != self._namespace:
                        raise SpecificationOperationError("source_topology_changed")
                except BaseException:
                    os.close(self._base_fd)
                    raise
            except BaseException:
                close_specification_fs_adapter(self._adapter)
                raise
        except (ValueError, OSError, SpecificationFsAdapterError) as error:
            raise SpecificationOperationError("source_installation_failed") from error
        self._roots = roots
        self._lock = threading.RLock()
        self._closed = False
        self._records: dict[int, tuple[SpecificationIterationAdmission, tuple]] = {}
        self._protocol_guard: Callable[[], None] | None = None
        self._protocol_read_only = False

    def _check(self) -> None:
        if self._closed:
            raise SpecificationOperationError("source_provider_closed")

    def _check_protocol_selection(self) -> None:
        if self._protocol_guard is not None:
            try:
                self._protocol_guard()
            except Exception:
                # Retained iteration admissions cannot outlive source-selection
                # refusal, even if a later filesystem restoration looks equal.
                self._records.clear()
                raise

    def _check_parent(self, parent_fd: int) -> None:
        if (
            validate_source_base(self._base_fd) != self._base_identity
            or mount_namespace_identity() != self._namespace
        ):
            raise SpecificationOperationError("source_topology_changed")
        current = os.dup(self._base_fd)
        try:
            for part in self._roots[0].split("/")[:-1]:
                following = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current
                )
                os.close(current)
                current = following
            first, second = os.fstat(current), os.fstat(parent_fd)
            if (first.st_dev, first.st_ino) != (
                second.st_dev,
                second.st_ino,
            ) or fd_mount_id(current) != self._base_identity[2]:
                raise SpecificationOperationError("source_topology_changed")
        finally:
            os.close(current)

    def _check_source_base(self) -> None:
        try:
            if (
                validate_source_base(self._base_fd) != self._base_identity
                or mount_namespace_identity() != self._namespace
            ):
                raise ValueError("source topology changed")
        except (OSError, ValueError) as error:
            raise SpecificationOperationError("source_topology_changed") from error

    def _observe_adaptation(
        self, request: SpecificationObserveRequest
    ) -> SpecificationFsAdaptationResult:
        if type(request) is not SpecificationObserveRequest:
            raise SpecificationOperationError("invalid_observe_request")
        request.__post_init__()
        with self._lock:
            self._check()
            self._check_protocol_selection()
            self._check_source_base()
            try:
                admitted = adapt_specification_fs_roots(self._adapter, self._roots)
                result = consume_specification_fs_adaptation(self._adapter, admitted)
                if (
                    request.expected_source_digest is not None
                    and result.lowering.root_set_digest
                    != request.expected_source_digest
                ):
                    raise SpecificationOperationError("source_changed")
                self._check_source_base()
                self._check_protocol_selection()
                return result
            except SpecificationFsAdapterError as error:
                raise SpecificationOperationError(error.code) from error

    def _observation(
        self, result: SpecificationFsAdaptationResult
    ) -> SpecificationObservation:
        snapshot = result.lowering.snapshot
        iterations = tuple(
            SpecificationIterationIdentity(
                f"specification:{d.key}/phase:{p.phase_key}", i
            )
            for d in snapshot.definitions
            for p in d.phases
            for i in p.iterations
        )
        return SpecificationObservation(
            snapshot,
            result.lowering.root_set_digest,
            "specification.fs-sdk-adapter.v1",
            "filesystem",
            result.observation_grade.value,
            result.lowering.schema_context.context_digest,
            iterations,
        )

    def observe(self, request: SpecificationObserveRequest) -> SpecificationObservation:
        with self._lock:
            result = self._observation(self._observe_adaptation(request))
            self._check_protocol_selection()
            return result

    def admit_iteration(
        self, request: SpecificationObserveRequest, requested_ref: str
    ) -> SpecificationIterationAdmission:
        with self._lock:
            self._check()
            if len(self._records) >= 128:
                raise SpecificationOperationError("iteration_admission_capacity")
            observation = self.observe(request)
            identity = resolve_iteration_identity(observation.snapshot, requested_ref)
            capability = SpecificationIterationAdmission(
                _ISSUE_KEY, self, observation, identity
            )
            self._records[id(capability)] = (
                capability,
                _fingerprint(observation, identity),
            )
            try:
                self._check_protocol_selection()
            except Exception:
                self._records.pop(id(capability), None)
                raise
            return capability

    def revalidate_iteration(
        self, capability: SpecificationIterationAdmission
    ) -> SpecificationObservation:
        return self.revalidate_iteration_source_evidence(capability).observation

    def revalidate_iteration_source_evidence(
        self, capability: SpecificationIterationAdmission
    ) -> SpecificationIterationSourceEvidence:
        with self._lock:
            self._check()
            if type(capability) is not SpecificationIterationAdmission:
                raise SpecificationOperationError("invalid_iteration_admission")
            record = self._records.get(id(capability))
            if (
                record is None
                or record[0] is not capability
                or capability._provider is not self
            ):
                raise SpecificationOperationError("invalid_iteration_admission")
            try:
                if (
                    _fingerprint(capability._observation, capability._identity)
                    != record[1]
                ):
                    raise SpecificationOperationError("invalid_iteration_admission")
                result = self._observe_adaptation(
                    SpecificationObserveRequest(record[1][0])
                )
                observed = self._observation(result)
                identity = resolve_iteration_identity(observed.snapshot, record[1][4])
                if _fingerprint(observed, identity) != record[1]:
                    raise SpecificationOperationError("source_changed")
                evidence = SpecificationIterationSourceEvidence(
                    identity,
                    observed,
                    self._base_identity,
                    self._namespace,
                    result.lowering.closures,
                )
                self._check_protocol_selection()
                return evidence
            except Exception:
                self._records.pop(id(capability), None)
                raise

    def release_iteration(self, capability: SpecificationIterationAdmission) -> None:
        with self._lock:
            self._check()
            if type(capability) is not SpecificationIterationAdmission:
                raise SpecificationOperationError("invalid_iteration_admission")
            record = self._records.get(id(capability))
            if record is None or record[0] is not capability:
                raise SpecificationOperationError("invalid_iteration_admission")
            self._records.pop(id(capability))

    def create_draft(
        self, request: SpecificationDraftRequest
    ) -> SpecificationDraftResult:
        if self._protocol_read_only:
            raise SpecificationOperationError("protocol_selected_writer_unavailable")
        if type(request) is not SpecificationDraftRequest:
            raise SpecificationOperationError("invalid_draft_request")
        request.__post_init__()
        with self._lock:
            self._check()
            if len(self._roots) != 1:
                raise SpecificationOperationError("draft_requires_one_target")
            if (
                request.definition.semantic_resolution_digest
                != self._context.semantic_resolution_digest
            ):
                raise SpecificationOperationError("draft_semantic_profile_mismatch")
            payload = render_draft(request)
            root = self._roots[0]
            parts = root.split("/")
            parent_fd = os.dup(self._base_fd)
            stage = None
            staged_adapter = None
            published = False
            try:
                for part in parts[:-1]:
                    following = os.open(
                        part,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                        dir_fd=parent_fd,
                    )
                    os.close(parent_fd)
                    parent_fd = following
                self._check_parent(parent_fd)
                try:
                    os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise SpecificationOperationError("draft_target_exists")
                stage = stage_files(parent_fd, payload)
                schema = (
                    files("aware_specification_fs_sdk_adapter")
                    .joinpath("resources/aware-spec-v1.schema.json")
                    .read_bytes()
                )
                staged_adapter = install_specification_fs_adapter(
                    parent_fd, schema, self._context
                )
                admitted = adapt_specification_fs_roots(staged_adapter, (stage,))
                checked = consume_specification_fs_adaptation(staged_adapter, admitted)
                retained_bytes = {
                    member.relative_path: member.canonical_body.encode("utf-8")
                    for member in checked.lowering.closures[0].members
                }
                if retained_bytes != payload:
                    raise SpecificationOperationError("draft_source_mismatch")
                if checked.lowering.snapshot != SpecificationSnapshot(
                    (request.definition,)
                ):
                    raise SpecificationOperationError("draft_meaning_mismatch")
                # Fresh descriptor/path observation; not a permanent topology lock.
                self._check_parent(parent_fd)
                rename_no_replace(parent_fd, stage, parts[-1])
                published = True
                observed = self.observe(SpecificationObserveRequest())
                if observed.snapshot.definitions != (request.definition,):
                    raise SpecificationOperationError(
                        "draft_meaning_mismatch", effect="published"
                    )
                return SpecificationDraftResult(
                    observed,
                    tuple(sorted(f"{root}/{p}" for p in payload)),
                    request.authoring_intent_ref,
                )
            except SpecificationOperationError as error:
                if published and error.effect == "none":
                    raise SpecificationOperationError(
                        error.code, effect="published"
                    ) from error
                raise
            except (OSError, ValueError, SpecificationFsAdapterError) as error:
                raise SpecificationOperationError(
                    "draft_publication_failed"
                    if published
                    else "draft_creation_refused",
                    effect="published" if published else "none",
                ) from error
            finally:
                if staged_adapter is not None:
                    close_specification_fs_adapter(staged_adapter)
                if stage is not None and not published:
                    cleanup_stage(parent_fd, stage, payload)
                os.close(parent_fd)

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                try:
                    close_specification_fs_adapter(self._adapter)
                finally:
                    try:
                        os.close(self._base_fd)
                    finally:
                        self._records.clear()
                        self._closed = True


def revalidate_specification_iteration_admission(
    capability: SpecificationIterationAdmission,
) -> SpecificationObservation:
    if type(capability) is not SpecificationIterationAdmission:
        raise SpecificationOperationError("invalid_iteration_admission")
    try:
        provider = capability._provider
    except AttributeError as error:
        raise SpecificationOperationError("invalid_iteration_admission") from error
    if type(provider) is not SpecificationFsSdkProvider:
        raise SpecificationOperationError("invalid_iteration_admission")
    return provider.revalidate_iteration(capability)


def revalidate_specification_iteration_source_evidence(
    capability: SpecificationIterationAdmission,
) -> SpecificationIterationSourceEvidence:
    if type(capability) is not SpecificationIterationAdmission:
        raise SpecificationOperationError("invalid_iteration_admission")
    try:
        provider = capability._provider
    except AttributeError as error:
        raise SpecificationOperationError("invalid_iteration_admission") from error
    if type(provider) is not SpecificationFsSdkProvider:
        raise SpecificationOperationError("invalid_iteration_admission")
    return provider.revalidate_iteration_source_evidence(capability)
