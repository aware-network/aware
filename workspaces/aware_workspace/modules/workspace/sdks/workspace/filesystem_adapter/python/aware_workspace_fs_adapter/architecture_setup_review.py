"""Private review retention through the original FileSystem owners only."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path

from aware_file_system import confined_mutation as mutation
from aware_file_system import private_directory as private
from aware_file_system import retained_file_sequence as sequence
from aware_issue_fs_adapter.provider import FilesystemIssueOperationProvider
from aware_issue_sdk.operation import (
    IssueReadProjectionResolveRequest,
    IssueSdkOperationClient,
)
from aware_workspace_sdk import architecture_setup_review_values as v
from aware_workspace_sdk.architecture_setup_review_codec import SetupReviewValueError

CHUNK_BYTES = 1_048_576
RAW_BYTES = 32 * CHUNK_BYTES
LOGICAL_BYTES = 64 * CHUNK_BYTES
_LIMITS = sequence.ConfinedSequenceLimits(
    ancestor_guards=1,
    binding_metadata_bytes=2_097_152,
    created_ancestor_paths=1,
    file_bytes=1_048_576,
    file_transitions=4,
    input_files=4,
    path_components=1,
    path_utf8_bytes=1024,
    physical_step_count=64,
    retained_before_and_after_bytes=4_194_304,
    scratch_paths=4,
    simultaneous_live_scratch=1,
    simultaneous_owned_descriptors=96,
)


def digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def canonical_json(payload):
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


class FilesystemSetupReview:
    """One retained existing root; no root creation, repair, selection or retries."""

    def __init__(
        self,
        *,
        repository_root: Path,
        evidence_root: Path,
        authority_manifest_locator: str,
    ):
        if type(repository_root) is not type(Path()) or type(evidence_root) is not type(
            Path()
        ):
            raise SetupReviewValueError("explicit_concrete_roots_required")
        if (
            not repository_root.is_absolute()
            or repository_root.resolve(strict=True) != repository_root
        ):
            raise SetupReviewValueError("canonical_repository_root_required")
        if (
            repository_root == evidence_root
            or repository_root in evidence_root.parents
            or evidence_root in repository_root.parents
        ):
            raise SetupReviewValueError("disjoint_external_evidence_root_required")
        self.root = evidence_root
        self.repository = repository_root
        self._directory: private.RetainedPrivateDirectory | None = None
        self.cleanup: private.PrivateDirectoryCleanup | None = None
        self.logical = self.raw_bytes = self.metadata_bytes = 0
        self.raw_files = self.metadata_files = 0
        self.observations: list[private.PrivateSequenceObservation] = []
        self.sequence_cleanup: list[private.PrivateSequenceCleanup] = []
        self.reads: list[private.PrivateFileReadResult] = []
        self.capture: v.SetupCaptureDescriptor | None = None
        self.intent: v.SetupEvidenceRef | None = None
        self.physical_refusal: private.PrivateDirectoryRefusalEvidence | None = None
        self.status: v.RetentionStatus = "not_attempted"
        self.complete = True
        self.diagnostics: list[str] = []
        self.start_ordinal = 0
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self.issue = IssueSdkOperationClient(
            FilesystemIssueOperationProvider(
                repository_root=repository_root,
                protocol_source_ref=authority_manifest_locator,
            )
        )
        try:
            self._directory = private.retain_private_directory(
                root=evidence_root,
                privacy_profile="effective_user_private_namespace_v1",
            )
            binding = private.observe_private_directory(self.directory).binding
            if binding is None:
                raise SetupReviewValueError("original_private_binding_required")
            self.binding = binding
            self.identity = v.DirectoryIdentity(self.binding.device, self.binding.inode)
            self.begin()
        except BaseException as error:
            if self._directory is not None:
                directory, self._directory = self._directory, None
                try:
                    self.cleanup = private.release_private_directory(directory)
                except BaseException as cleanup_error:  # noqa: BLE001 - retain primary construction error
                    BaseException.__setattr__(
                        error, "private_cleanup_failure", cleanup_error
                    )
            BaseException.__setattr__(error, "private_directory_cleanup", self.cleanup)
            raise

    @property
    def directory(self) -> private.RetainedPrivateDirectory:
        if self._directory is None:
            raise SetupReviewValueError("review_provider_not_current")
        return self._directory

    def current(self):
        if self._directory is None or (self.pid, self.thread) != (
            os.getpid(),
            threading.get_ident(),
        ):
            raise SetupReviewValueError("review_provider_not_current")
        observed = private.validate_private_directory(
            self.directory, expected_binding=self.binding
        )
        if observed.validation_ordinal - self.start_ordinal > 4096:
            raise SetupReviewValueError("review_validation_budget_exceeded")
        return observed

    def begin(self):
        self.logical = self.raw_bytes = self.metadata_bytes = 0
        self.raw_files = self.metadata_files = 0
        self.observations, self.sequence_cleanup, self.reads = [], [], []
        self.capture = self.intent = self.physical_refusal = None
        self.status = "not_attempted"
        self.complete = True
        self.diagnostics = []
        self.start_ordinal = private.observe_private_directory(
            self.directory
        ).validation_ordinal

    def reserve(self, count):
        if type(count) is not int or count < 0 or self.logical + count > LOGICAL_BYTES:
            raise SetupReviewValueError("review_logical_retention_budget_exceeded")
        self.logical += count

    def read_issue(self, tag):
        return self.issue.resolve_read_projection(
            IssueReadProjectionResolveRequest(tag)
        )

    def _write(self, files, *, metadata):
        """Publish one original CREATE batch, retaining its final observation/cleanup."""
        if not files or len(files) > 4 or len(self.observations) >= 16:
            raise SetupReviewValueError("review_sequence_budget_exceeded")
        size = sum(len(body) for _, body in files)
        if any(
            type(body) is not bytes or not 0 < len(body) <= CHUNK_BYTES
            for _, body in files
        ):
            raise SetupReviewValueError("review_physical_file_budget_exceeded")
        if metadata:
            if (
                self.metadata_files + len(files) > 8
                or self.metadata_bytes + size > 2 * CHUNK_BYTES
            ):
                raise SetupReviewValueError("review_metadata_budget_exceeded")
            self.metadata_files += len(files)
            self.metadata_bytes += size
        else:
            if self.raw_files + len(files) > 32 or self.raw_bytes + size > RAW_BYTES:
                raise SetupReviewValueError("review_capture_budget_exceeded")
            self.raw_files += len(files)
            self.raw_bytes += size
        # Requests, before/after/native return copies and bounded native metadata
        # coexist. This conservative reservation may refuse a nominal maximum.
        self.reserve(5 * size + 2 * CHUNK_BYTES)
        self.current()
        child = None
        observed = None
        primary = None
        try:
            child = private.retain_private_file_sequence(
                self.directory,
                expected_binding=self.binding,
                requests=tuple(
                    mutation.ConfinedFileMutationRequest(
                        mutation.ConfinedMutationKind.CREATE, name, False, None, body
                    )
                    for name, body in files
                ),
                limits=_LIMITS,
                confinement_profile=mutation.ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
            )
            observed = private.observe_private_file_sequence(child)
            if observed.binding is None:
                raise SetupReviewValueError(
                    "original_private_sequence_binding_required"
                )
            for step in observed.binding.sequence.ordered_steps:
                private.verify_private_file_sequence(
                    child, expected_binding=observed.binding
                )
                private.execute_next_private_file_step(
                    child, expected_ordinal=step.ordinal
                )
            observed = private.observe_private_file_sequence(child)
            self.status = "published"
        except BaseException as error:
            primary = error
            self.failed(error)
            raise
        finally:
            # Store custody immediately, then release once. A failed close cannot
            # erase the effect prefix or authorize another release attempt.
            if child is not None:
                try:
                    observed = private.observe_private_file_sequence(child)
                except BaseException as error:  # noqa: BLE001 - observation cannot skip independent cleanup
                    self.failed(error)
                if observed is not None:
                    self.observations.append(observed)
                try:
                    cleanup = private.release_private_file_sequence(child)
                    self.sequence_cleanup.append(cleanup)
                    if (
                        cleanup.sequence.release != "confirmed"
                        or not cleanup.sequence.ledger_complete
                    ):
                        self.complete = False
                except BaseException as error:
                    self.failed(error)
                    if primary is None:
                        raise
            if primary is None:
                self.current()
                if not self.complete:
                    raise SetupReviewValueError("review_sequence_cleanup_incomplete")

    def write_metadata(self, name, raw):
        self._write(((name, raw),), metadata=True)

    def write_capture(self, raw, *, attempt, kind):
        if type(raw) is not bytes or not 0 < len(raw) <= RAW_BYTES:
            raise SetupReviewValueError("review_capture_budget_exceeded")
        self.reserve(len(raw))
        rows = []
        for start in range(0, len(raw), 4 * CHUNK_BYTES):
            files = []
            for offset in range(
                start, min(start + 4 * CHUNK_BYTES, len(raw)), CHUNK_BYTES
            ):
                ordinal = offset // CHUNK_BYTES
                body = raw[offset : offset + CHUNK_BYTES]
                name = f"a1-{attempt}-data-{ordinal:02d}.bin"
                rows.append(
                    v.SetupChunkDescriptor(ordinal, name, len(body), digest(body))
                )
                files.append((name, body))
            self._write(tuple(files), metadata=False)
        self.capture = v.SetupCaptureDescriptor(
            kind, len(raw), digest(raw), tuple(rows)
        )
        return self.capture

    def read(self, name, *, size, sha256):
        self.current()
        if type(name) is not str or "/" in name or not name.startswith("a1-"):
            raise SetupReviewValueError("review_flat_locator_required")
        if (
            type(size) is not int
            or not 0 < size <= CHUNK_BYTES
            or len(self.reads) >= 40
        ):
            raise SetupReviewValueError("review_read_budget_exceeded")
        self.reserve(6 * size)
        try:
            result = private.observe_private_directory_file(
                self.directory,
                expected_binding=self.binding,
                path=name,
                maximum_bytes=size,
            )
        except BaseException as error:
            self.failed(error)
            raise
        self.reads.append(result)
        if (
            result.original.cleanup.outcome != "closed"
            or not result.directory_before.ledger_complete
            or not result.directory_after.ledger_complete
        ):
            self.failed(SetupReviewValueError("review_read_cleanup_incomplete"))
            raise SetupReviewValueError("review_read_cleanup_incomplete")
        raw = result.original.observation.content
        if type(raw) is not bytes or len(raw) != size or digest(raw) != sha256:
            raise SetupReviewValueError("review_stored_bytes_mismatch")
        return raw

    def read_capture(self, capture, *, attempt):
        if capture.byte_count > RAW_BYTES or len(capture.chunks) > 32:
            raise SetupReviewValueError("review_capture_budget_exceeded")
        self.reserve(capture.byte_count)
        chunks = []
        for ordinal, row in enumerate(capture.chunks):
            if (
                row.ordinal != ordinal
                or row.locator != f"a1-{attempt}-data-{ordinal:02d}.bin"
            ):
                raise SetupReviewValueError("review_capture_locator_mismatch")
            chunks.append(
                self.read(row.locator, size=row.byte_count, sha256=row.sha256)
            )
        raw = b"".join(chunks)
        if len(raw) != capture.byte_count or digest(raw) != capture.sha256:
            raise SetupReviewValueError("review_capture_digest_mismatch")
        return raw

    def failed(self, error):
        self.status = "incomplete"
        self.complete = False
        if type(error) is private.PrivateDirectoryRefusal:
            if self.physical_refusal is None:
                self.physical_refusal = error.evidence
            cleanup = error.evidence.cleanup
            if (
                type(cleanup) is private.PrivateSequenceCleanup
                and cleanup not in self.sequence_cleanup
            ):
                self.sequence_cleanup.append(cleanup)
        if len(self.diagnostics) < 16:
            self.diagnostics.append(type(error).__name__ + ":retention_incomplete")

    def retention(self):
        return v.RetentionEvidence(
            self.status,
            self.intent,
            self.capture,
            tuple(self.observations),
            tuple(self.sequence_cleanup),
            self.cleanup,
            self.complete,
            tuple(self.diagnostics),
            self.physical_refusal,
        )

    def release(self):
        if self._directory is not None:
            directory, self._directory = self._directory, None
            try:
                self.cleanup = private.release_private_directory(directory)
            except private.PrivateDirectoryRefusal as error:
                self.failed(error)
                if type(error.evidence.cleanup) is private.PrivateDirectoryCleanup:
                    self.cleanup = error.evidence.cleanup
                raise
        return self.cleanup
