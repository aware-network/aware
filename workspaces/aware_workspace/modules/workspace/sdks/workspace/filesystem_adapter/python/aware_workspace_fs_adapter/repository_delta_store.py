from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path

from aware_workspace_runtime.change_evidence_codec import (
    repository_content_delta_from_payload,
    repository_content_delta_payload,
    repository_delta_capture_from_payload,
    repository_delta_capture_payload,
)
from aware_workspace_runtime.repository_delta import (
    WorkspaceRepositoryContentDelta,
    WorkspaceRepositoryDeltaCapture,
    repository_delta_body_ref,
    validate_repository_delta_capture_advance,
)
from aware_workspace_runtime.repository_delta_store_contract import (
    DEFAULT_DELTA_BODY_BYTES,
    DEFAULT_DELTA_BODY_CAPACITY,
    DEFAULT_DELTA_CAPTURE_CAPACITY,
    DEFAULT_DELTA_TRANSITION_CAPACITY,
    MAX_DELTA_BODY_BYTES,
    MAX_DELTA_BODY_CAPACITY,
    MAX_DELTA_CAPTURE_CAPACITY,
    MAX_DELTA_TRANSITION_CAPACITY,
    WORKSPACE_REPOSITORY_DELTA_STORE_CONTRACT_REF,
    WORKSPACE_REPOSITORY_DELTA_STORE_VERSION,
    WorkspaceRepositoryDeltaStoreCapacityError,
    WorkspaceRepositoryDeltaStoreCorrupt,
    WorkspaceRepositoryDeltaStoreError,  # noqa: F401 -- preserve the original value import coordinate
    WorkspaceRepositoryDeltaStoreMetrics,
    WorkspaceRepositoryDeltaStoreSnapshot,
)

_PERFORMANCE_PROBE: ContextVar[object | None] = ContextVar(
    "aware_workspace_repository_performance_probe", default=None
)


def set_performance_probe(probe):
    """Install an optional diagnostic sink for repository body operations."""

    return _PERFORMANCE_PROBE.set(probe)


def reset_performance_probe(token) -> None:
    _PERFORMANCE_PROBE.reset(token)


def _performance_count(name: str, amount: int = 1) -> None:
    probe = _PERFORMANCE_PROBE.get()
    if probe is None:
        return
    record = getattr(probe, "record", None)
    if record is None:
        return
    try:
        record(kind="counter", name=name, amount=amount)
    except Exception:
        return


@dataclass(slots=True)
class _BodyRecord:
    body_ref: str
    content_digest: str
    size_bytes: int
    created_sequence: int
    last_access_sequence: int


class WorkspaceRepositoryDeltaStore:
    """Repository-scoped bounded CAS and transition metadata index.

    Startup loads only the compact JSON index. Body bytes are opened only by
    explicit ``resolve_body`` calls; recording metadata or inspecting a
    snapshot never reads retained bodies.
    """

    def __init__(
        self,
        *,
        repository_binding_ref: str,
        state_root: Path,
        body_capacity: int = DEFAULT_DELTA_BODY_CAPACITY,
        maximum_bytes: int = DEFAULT_DELTA_BODY_BYTES,
        capture_capacity: int = DEFAULT_DELTA_CAPTURE_CAPACITY,
        delta_capacity: int = DEFAULT_DELTA_TRANSITION_CAPACITY,
    ) -> None:
        self._repository_binding_ref = _required(
            repository_binding_ref, "repository_binding_ref"
        )
        _bounded(body_capacity, MAX_DELTA_BODY_CAPACITY, "body_capacity")
        _bounded(maximum_bytes, MAX_DELTA_BODY_BYTES, "maximum_bytes")
        _bounded(capture_capacity, MAX_DELTA_CAPTURE_CAPACITY, "capture_capacity")
        _bounded(delta_capacity, MAX_DELTA_TRANSITION_CAPACITY, "delta_capacity")
        self._body_capacity = body_capacity
        self._maximum_bytes = maximum_bytes
        self._capture_capacity = capture_capacity
        self._delta_capacity = delta_capacity
        binding_digest = hashlib.sha256(
            self._repository_binding_ref.encode("utf-8")
        ).hexdigest()
        self._store_root = (
            state_root.expanduser().resolve() / "repository_delta" / binding_digest
        )
        self._body_root = self._store_root / "bodies"
        self._index_path = self._store_root / "index.json"
        self._lock = threading.RLock()
        self._sequence = 0
        self._bodies: dict[str, _BodyRecord] = {}
        self._captures: dict[str, WorkspaceRepositoryDeltaCapture] = {}
        self._deltas: dict[str, WorkspaceRepositoryContentDelta] = {}
        self._retained_body_bytes = 0
        self._body_hash_count = 0
        self._body_read_count = 0
        self._body_read_bytes = 0
        self._body_write_count = 0
        self._body_write_bytes = 0
        self._index_write_count = 0
        self._evicted_body_count = 0
        self._evicted_capture_count = 0
        self._evicted_delta_count = 0
        self._load_index()

    @property
    def repository_binding_ref(self) -> str:
        return self._repository_binding_ref

    @property
    def store_root(self) -> Path:
        return self._store_root

    def snapshot(self) -> WorkspaceRepositoryDeltaStoreSnapshot:
        with self._lock:
            return WorkspaceRepositoryDeltaStoreSnapshot(
                repository_binding_ref=self._repository_binding_ref,
                retained_body_count=len(self._bodies),
                retained_body_bytes=self._retained_body_bytes,
                retained_capture_count=len(self._captures),
                retained_delta_count=len(self._deltas),
                metrics=self._metrics(),
            )

    def record_body(self, content: bytes) -> str:
        return self.record_bodies((content,))[0]

    def record_bodies(self, contents: tuple[bytes, ...]) -> tuple[str, ...]:
        if not contents:
            return ()
        prepared: list[tuple[str, str, bytes]] = []
        for content in contents:
            if not isinstance(content, bytes):
                raise TypeError("Repository delta bodies must be bytes")
            if len(content) > self._maximum_bytes:
                raise WorkspaceRepositoryDeltaStoreCapacityError(
                    "Repository delta body exceeds store byte capacity"
                )
            digest = "sha256:" + hashlib.sha256(content).hexdigest()
            prepared.append((repository_delta_body_ref(digest), digest, content))
        unique = {body_ref: (digest, content) for body_ref, digest, content in prepared}
        if (
            len(unique) > self._body_capacity
            or sum(len(content) for _digest, content in unique.values())
            > self._maximum_bytes
        ):
            raise WorkspaceRepositoryDeltaStoreCapacityError(
                "Repository delta body batch exceeds store capacity"
            )
        with self._lock:
            self._body_hash_count += len(contents)
            protected = set(unique)
            index_changed = False
            for body_ref, (digest, content) in unique.items():
                record = self._bodies.get(body_ref)
                body_path = self._body_path(digest)
                if record is None:
                    self._sequence += 1
                    record = _BodyRecord(
                        body_ref=body_ref,
                        content_digest=digest,
                        size_bytes=len(content),
                        created_sequence=self._sequence,
                        last_access_sequence=self._sequence,
                    )
                    self._write_body(body_path, content)
                    self._bodies[body_ref] = record
                    self._retained_body_bytes += len(content)
                    index_changed = True
                else:
                    if record.content_digest != digest or record.size_bytes != len(
                        content
                    ):
                        raise WorkspaceRepositoryDeltaStoreCorrupt(
                            "Repository delta body identity collision"
                        )
                    if not body_path.is_file():
                        self._write_body(body_path, content)
                    self._sequence += 1
                    record.last_access_sequence = self._sequence
            evictions_before = self._evicted_body_count
            self._enforce_body_limits(protected=protected)
            if index_changed or self._evicted_body_count != evictions_before:
                self._persist_index()
        return tuple(body_ref for body_ref, _digest, _content in prepared)

    def contains_body(self, body_ref: str) -> bool:
        with self._lock:
            record = self._bodies.get(_required(body_ref, "body_ref"))
            return (
                record is not None and self._body_path(record.content_digest).is_file()
            )

    def resolve_body(self, body_ref: str) -> bytes | None:
        _performance_count("workspace.retained_body_resolution")
        with self._lock:
            record = self._bodies.get(_required(body_ref, "body_ref"))
            if record is None:
                return None
            body_path = self._body_path(record.content_digest)
            try:
                content = body_path.read_bytes()
            except FileNotFoundError:
                return None
            self._body_read_count += 1
            self._body_read_bytes += len(content)
            digest = "sha256:" + hashlib.sha256(content).hexdigest()
            self._body_hash_count += 1
            if digest != record.content_digest or len(content) != record.size_bytes:
                raise WorkspaceRepositoryDeltaStoreCorrupt(
                    "Repository delta body does not match its index"
                )
            self._sequence += 1
            record.last_access_sequence = self._sequence
            return content

    def record_capture(self, value: WorkspaceRepositoryDeltaCapture) -> None:
        if value.repository_binding_ref != self._repository_binding_ref:
            raise ValueError("Delta capture repository binding differs from store")
        with self._lock:
            existing = self._captures.get(value.capture_ref)
            if existing == value:
                return
            if existing is not None:
                validate_repository_delta_capture_advance(existing, value)
                self._captures[value.capture_ref] = value
            else:
                self._captures[value.capture_ref] = value
                while len(self._captures) > self._capture_capacity:
                    self._captures.pop(next(iter(self._captures)))
                    self._evicted_capture_count += 1
            self._persist_index()

    def resolve_capture(
        self, capture_ref: str
    ) -> WorkspaceRepositoryDeltaCapture | None:
        with self._lock:
            return self._captures.get(_required(capture_ref, "capture_ref"))

    def retained_captures(self) -> tuple[WorkspaceRepositoryDeltaCapture, ...]:
        with self._lock:
            return tuple(self._captures.values())

    def record_delta(self, value: WorkspaceRepositoryContentDelta) -> None:
        if value.repository_binding_ref != self._repository_binding_ref:
            raise ValueError("Content delta repository binding differs from store")
        with self._lock:
            if value.capture_ref not in self._captures:
                raise ValueError("Content delta capture is not retained by store")
            self._require_body_refs(
                tuple(
                    body_ref
                    for body_ref in (value.old_body_ref, value.new_body_ref)
                    if body_ref is not None
                )
            )
            existing = self._deltas.get(value.delta_ref)
            if existing is not None:
                if existing != value:
                    raise ValueError("Content delta ref cannot change transition")
                return
            self._deltas[value.delta_ref] = value
            while len(self._deltas) > self._delta_capacity:
                self._deltas.pop(next(iter(self._deltas)))
                self._evicted_delta_count += 1
            self._persist_index()

    def resolve_delta(self, delta_ref: str) -> WorkspaceRepositoryContentDelta | None:
        with self._lock:
            return self._deltas.get(_required(delta_ref, "delta_ref"))

    def retained_deltas(self) -> tuple[WorkspaceRepositoryContentDelta, ...]:
        with self._lock:
            return tuple(self._deltas.values())

    def _require_body_refs(self, body_refs: tuple[str, ...]) -> None:
        for body_ref in body_refs:
            if body_ref not in self._bodies:
                raise ValueError("Repository delta references an unretained body")

    def _enforce_body_limits(self, *, protected: set[str]) -> None:
        while (
            len(self._bodies) > self._body_capacity
            or self._retained_body_bytes > self._maximum_bytes
        ):
            referenced = self._referenced_body_refs()
            candidates = [
                record
                for record in self._bodies.values()
                if record.body_ref not in protected
            ]
            if not candidates:
                raise WorkspaceRepositoryDeltaStoreCapacityError(
                    "Protected repository delta bodies exceed store capacity"
                )
            record = min(
                candidates,
                key=lambda item: (
                    item.body_ref in referenced,
                    item.last_access_sequence,
                    item.created_sequence,
                    item.body_ref,
                ),
            )
            self._bodies.pop(record.body_ref)
            self._retained_body_bytes -= record.size_bytes
            self._body_path(record.content_digest).unlink(missing_ok=True)
            self._evicted_body_count += 1

    def _referenced_body_refs(self) -> set[str]:
        refs = {
            path.body_ref
            for capture in self._captures.values()
            for path in capture.path_states
            if path.body_ref is not None
        }
        refs.update(
            body_ref
            for delta in self._deltas.values()
            for body_ref in (delta.old_body_ref, delta.new_body_ref)
            if body_ref is not None
        )
        return refs

    def _body_path(self, content_digest: str) -> Path:
        digest_hex = content_digest.removeprefix("sha256:")
        return self._body_root / digest_hex[:2] / f"{digest_hex}.blob"

    def _write_body(self, path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_file():
            existing_size = path.stat().st_size
            if existing_size == len(content):
                return
            raise WorkspaceRepositoryDeltaStoreCorrupt(
                "Repository delta body path already has a different size"
            )
        _atomic_write(path, content)
        self._body_write_count += 1
        self._body_write_bytes += len(content)

    def _load_index(self) -> None:
        if not self._index_path.is_file():
            return
        try:
            payload = json.loads(self._index_path.read_text(encoding="utf-8"))
            _exact_keys(
                payload,
                {
                    "contract_ref",
                    "version",
                    "repository_binding_ref",
                    "sequence",
                    "bodies",
                    "captures",
                    "deltas",
                },
                "repository delta store index",
            )
            if (
                payload["contract_ref"] != WORKSPACE_REPOSITORY_DELTA_STORE_CONTRACT_REF
                or payload["version"] != WORKSPACE_REPOSITORY_DELTA_STORE_VERSION
                or payload["repository_binding_ref"] != self._repository_binding_ref
            ):
                raise ValueError("Repository delta store index identity differs")
            sequence = _non_negative_int(payload["sequence"], "sequence")
            bodies_payload = _list(payload["bodies"], "bodies")
            captures_payload = _list(payload["captures"], "captures")
            deltas_payload = _list(payload["deltas"], "deltas")
            bodies: dict[str, _BodyRecord] = {}
            for raw in bodies_payload:
                item = _mapping(raw, "body")
                _exact_keys(
                    item,
                    {
                        "body_ref",
                        "content_digest",
                        "size_bytes",
                        "created_sequence",
                        "last_access_sequence",
                    },
                    "body",
                )
                content_digest = _required(item["content_digest"], "content_digest")
                body_ref = _required(item["body_ref"], "body_ref")
                if body_ref != repository_delta_body_ref(content_digest):
                    raise ValueError("Repository delta body ref is not deterministic")
                record = _BodyRecord(
                    body_ref=body_ref,
                    content_digest=content_digest,
                    size_bytes=_non_negative_int(item["size_bytes"], "size_bytes"),
                    created_sequence=_non_negative_int(
                        item["created_sequence"], "created_sequence"
                    ),
                    last_access_sequence=_non_negative_int(
                        item["last_access_sequence"], "last_access_sequence"
                    ),
                )
                if body_ref in bodies:
                    raise ValueError("Repository delta body refs must be unique")
                bodies[body_ref] = record
            captures = tuple(
                repository_delta_capture_from_payload(item) for item in captures_payload
            )
            deltas = tuple(
                repository_content_delta_from_payload(item) for item in deltas_payload
            )
            if any(
                value.repository_binding_ref != self._repository_binding_ref
                for value in (*captures, *deltas)
            ):
                raise ValueError("Repository delta index value binding differs")
            if len({value.capture_ref for value in captures}) != len(captures):
                raise ValueError("Repository delta capture refs must be unique")
            if len({value.delta_ref for value in deltas}) != len(deltas):
                raise ValueError("Repository content delta refs must be unique")
            if (
                len(bodies) > self._body_capacity
                or sum(value.size_bytes for value in bodies.values())
                > self._maximum_bytes
                or len(captures) > self._capture_capacity
                or len(deltas) > self._delta_capacity
            ):
                raise ValueError("Repository delta index exceeds configured capacity")
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise WorkspaceRepositoryDeltaStoreCorrupt(
                "Repository delta store index is invalid"
            ) from error
        self._sequence = sequence
        self._bodies = bodies
        self._captures = {value.capture_ref: value for value in captures}
        self._deltas = {value.delta_ref: value for value in deltas}
        self._retained_body_bytes = sum(value.size_bytes for value in bodies.values())

    def _persist_index(self) -> None:
        payload = {
            "contract_ref": WORKSPACE_REPOSITORY_DELTA_STORE_CONTRACT_REF,
            "version": WORKSPACE_REPOSITORY_DELTA_STORE_VERSION,
            "repository_binding_ref": self._repository_binding_ref,
            "sequence": self._sequence,
            "bodies": [
                {
                    "body_ref": value.body_ref,
                    "content_digest": value.content_digest,
                    "size_bytes": value.size_bytes,
                    "created_sequence": value.created_sequence,
                    "last_access_sequence": value.last_access_sequence,
                }
                for value in self._bodies.values()
            ],
            "captures": [
                repository_delta_capture_payload(value)
                for value in self._captures.values()
            ],
            "deltas": [
                repository_content_delta_payload(value)
                for value in self._deltas.values()
            ],
        }
        encoded = (
            json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        self._store_root.mkdir(parents=True, exist_ok=True)
        _atomic_write(self._index_path, encoded)
        self._index_write_count += 1

    def _metrics(self) -> WorkspaceRepositoryDeltaStoreMetrics:
        return WorkspaceRepositoryDeltaStoreMetrics(
            body_hash_count=self._body_hash_count,
            body_read_count=self._body_read_count,
            body_read_bytes=self._body_read_bytes,
            body_write_count=self._body_write_count,
            body_write_bytes=self._body_write_bytes,
            index_write_count=self._index_write_count,
            evicted_body_count=self._evicted_body_count,
            evicted_capture_count=self._evicted_capture_count,
            evicted_delta_count=self._evicted_delta_count,
        )


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary_path.unlink(missing_ok=True)
        raise


def _bounded(value: int, maximum: int, field_name: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 < value <= maximum
    ):
        raise ValueError(f"{field_name} must be positive and bounded")


def _required(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _non_negative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _mapping(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{field_name} must be an object")
    return value


def _list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be an array")
    return value


def _exact_keys(value: dict[str, object], expected: set[str], field_name: str) -> None:
    missing = expected - value.keys()
    unknown = value.keys() - expected
    if missing or unknown:
        detail = []
        if missing:
            detail.append("missing: " + ", ".join(sorted(missing)))
        if unknown:
            detail.append("unknown: " + ", ".join(sorted(unknown)))
        raise ValueError(f"{field_name} fields differ ({'; '.join(detail)})")
