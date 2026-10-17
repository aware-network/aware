from __future__ import annotations

import json
import os
import tempfile
import threading
import types as _types
from collections.abc import Mapping
from functools import partial as _identity_data
from pathlib import Path
from typing import Any, cast

from aware_workspace_runtime.change_evidence_codec import (
    repository_authorized_mutation_from_payload,
    repository_authorized_mutation_payload,
)
from aware_workspace_runtime.repository_mutation import (
    WorkspaceRepositoryAuthorizedMutation,
)

from .repository_delta_store import _atomic_write
from .repository_index_journal import (
    IndexJournal,
    IndexJournalError,
    bind_index_writer,
)

WORKSPACE_REPOSITORY_MUTATION_STORE_CONTRACT_REF = (
    "aware.workspace.repository-mutation-store.v1"
)
WORKSPACE_REPOSITORY_MUTATION_STORE_VERSION = "1"
DEFAULT_MUTATION_STORE_CAPACITY = 1024
MAX_MUTATION_STORE_CAPACITY = 4096


class WorkspaceRepositoryMutationStoreError(RuntimeError):
    pass


class WorkspaceRepositoryMutationStoreCorrupt(WorkspaceRepositoryMutationStoreError):
    pass


class WorkspaceRepositoryMutationStore:
    """Bounded repository-scoped mutation receipt metadata index."""

    def __init__(
        self,
        *,
        repository_binding_ref: str,
        state_root: Path,
        capacity: int = DEFAULT_MUTATION_STORE_CAPACITY,
        index_format: str = "json_v1",
    ) -> None:
        self._repository_binding_ref = _required(
            repository_binding_ref, "repository_binding_ref"
        )
        if (
            isinstance(capacity, bool)
            or not 0 < capacity <= MAX_MUTATION_STORE_CAPACITY
        ):
            raise ValueError("Mutation store capacity is invalid")
        self._capacity = capacity
        self._store_root = state_root.expanduser().resolve() / "repository_mutations"
        self._index_path = self._store_root / "index.json"
        self._lock = threading.RLock()
        self._records: dict[str, tuple[str, WorkspaceRepositoryAuthorizedMutation]] = {}
        try:
            self._index_journal = IndexJournal(
                self._index_path,
                binding=self._repository_binding_ref,
                kind=1,
                index_format=index_format,
            )
        except (IndexJournalError, OSError) as error:
            raise WorkspaceRepositoryMutationStoreCorrupt(
                "Repository index representation is invalid"
            ) from error
        self._load()

    @property
    def repository_binding_ref(self) -> str:
        return self._repository_binding_ref

    @property
    def retained_count(self) -> int:
        with self._lock:
            return len(self._records)

    def resolve(
        self, receipt_ref: str
    ) -> tuple[str, WorkspaceRepositoryAuthorizedMutation] | None:
        with self._lock:
            return self._records.get(_required(receipt_ref, "receipt_ref"))

    def record(
        self,
        *,
        fingerprint: str,
        result: WorkspaceRepositoryAuthorizedMutation,
    ) -> None:
        fingerprint = _required(fingerprint, "fingerprint")
        receipt = result.receipt
        if receipt.repository_binding_ref != self._repository_binding_ref:
            raise ValueError("Mutation receipt repository binding differs from store")
        receipt_ref = receipt.mutation_receipt_ref
        with self._lock:
            existing = self._records.get(receipt_ref)
            if existing is not None:
                if existing != (fingerprint, result):
                    raise ValueError("Mutation receipt identity cannot change")
                return
            self._records[receipt_ref] = (fingerprint, result)
            while len(self._records) > self._capacity:
                self._records.pop(next(iter(self._records)))
            self._persist()

    def _load(self) -> None:
        try:
            if self._index_journal.format == "events_v2":
                encoded = self._index_journal.read()
                if encoded is None:
                    return
            else:
                if not self._index_path.is_file():
                    return
                encoded = self._index_path.read_text(encoding="utf-8")
            payload = json.loads(encoded)
            root = _mapping(payload, "mutation store")
            if set(root) != {
                "contract_ref",
                "contract_version",
                "repository_binding_ref",
                "records",
            }:
                raise ValueError("Mutation store root fields differ")
            if (
                root["contract_ref"] != WORKSPACE_REPOSITORY_MUTATION_STORE_CONTRACT_REF
                or root["contract_version"]
                != WORKSPACE_REPOSITORY_MUTATION_STORE_VERSION
                or root["repository_binding_ref"] != self._repository_binding_ref
            ):
                raise ValueError("Mutation store authority differs")
            records = root["records"]
            if not isinstance(records, list) or len(records) > self._capacity:
                raise ValueError("Mutation store records are invalid")
            for raw_record in records:
                record = _mapping(raw_record, "mutation record")
                if set(record) != {"receipt_ref", "fingerprint", "result"}:
                    raise ValueError("Mutation record fields differ")
                receipt_ref = _required(record["receipt_ref"], "receipt_ref")
                fingerprint = _required(record["fingerprint"], "fingerprint")
                result = repository_authorized_mutation_from_payload(record["result"])
                if (
                    result.receipt.mutation_receipt_ref != receipt_ref
                    or result.receipt.repository_binding_ref
                    != self._repository_binding_ref
                    or receipt_ref in self._records
                ):
                    raise ValueError("Mutation record coordinate differs")
                self._records[receipt_ref] = (fingerprint, result)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            self._records.clear()
            raise WorkspaceRepositoryMutationStoreCorrupt(
                "Workspace mutation receipt metadata is corrupt"
            ) from error

    def _canonical_index(self) -> bytes:
        callee = json.dumps
        payload = {
            "contract_ref": WORKSPACE_REPOSITORY_MUTATION_STORE_CONTRACT_REF,
            "contract_version": WORKSPACE_REPOSITORY_MUTATION_STORE_VERSION,
            "repository_binding_ref": self._repository_binding_ref,
            "records": [
                {
                    "receipt_ref": receipt_ref,
                    "fingerprint": fingerprint,
                    "result": repository_authorized_mutation_payload(result),
                }
                for receipt_ref, (fingerprint, result) in self._records.items()
            ],
        }
        if _STORE_JOURNAL_NATIVE_HANDOFF is None:
            serialized = callee(payload, sort_keys=True, separators=(",", ":"))
        else:
            native: Any = "_STORE_INDEX_NATIVE_CALL_"
            context: Any = "_STORE_INDEX_NATIVE_CONTEXT_"
            serialized = native(context(), callee, payload, json)
        return (serialized + "\n").encode("utf-8")

    def _persist(self) -> None:
        if self._index_journal.format == "events_v2":
            # Original mutation encoding is deferred until the metadata writer
            # owns its pending stream. No retained result is serialized early.
            original: Any = "_ORIGINAL_INDEX_SERIALIZER_"
            original_code: Any = "_ORIGINAL_INDEX_SERIALIZER_CODE_"

            def prepare():
                if (
                    vars(type(self)).get("_canonical_index") is not original
                    or original.__code__ is not original_code
                    or original.__defaults__ is not None
                    or original.__kwdefaults__ is not None
                ):
                    raise IndexJournalError("Original index serializer was substituted")
                return original(self)

            # Preserve the original private metadata-root creation mode.
            self._store_root.mkdir(parents=True, exist_ok=True, mode=0o700)
            journal_writer: Any = "_ORIGINAL_INDEX_JOURNAL_WRITER_"
            writer_code: Any = "_ORIGINAL_INDEX_JOURNAL_WRITER_CODE_"
            writer_cells_data: Any = "_ORIGINAL_INDEX_JOURNAL_WRITER_CELLS_"
            writer_cells = writer_cells_data.args[0]
            writer_values_data: Any = "_ORIGINAL_INDEX_JOURNAL_WRITER_VALUES_"
            writer_values = writer_values_data.args[0]
            if (
                journal_writer.__code__ is not writer_code
                or journal_writer.__defaults__ is not None
                or journal_writer.__kwdefaults__ is not None
                or journal_writer.__closure__ is not writer_cells
                or any(
                    cell.cell_contents is not value
                    for cell, value in zip(
                        writer_cells or (), writer_values, strict=True
                    )
                )
            ):
                raise IndexJournalError("Original journal writer entry was substituted")
            self._index_journal.publish(prepare, writer=journal_writer)
            return
        with self._index_journal.publication_guard():
            self._store_root.mkdir(parents=True, exist_ok=True, mode=448)
            descriptor, temporary = tempfile.mkstemp(
                prefix=f".{self._index_path.name}.", dir=self._store_root
            )
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    write = stream.write
                    try:
                        callee = json.dumps
                        try:
                            payload = {
                                "contract_ref": WORKSPACE_REPOSITORY_MUTATION_STORE_CONTRACT_REF,
                                "contract_version": WORKSPACE_REPOSITORY_MUTATION_STORE_VERSION,
                                "repository_binding_ref": self._repository_binding_ref,
                                "records": [
                                    {
                                        "receipt_ref": receipt_ref,
                                        "fingerprint": fingerprint,
                                        "result": repository_authorized_mutation_payload(
                                            result
                                        ),
                                    }
                                    for receipt_ref, (
                                        fingerprint,
                                        result,
                                    ) in self._records.items()
                                ],
                            }
                            if _STORE_NATIVE_HANDOFF is None:
                                serialized = callee(
                                    payload, sort_keys=True, separators=(",", ":")
                                )
                            else:
                                native: Any = "_STORE_INDEX_NATIVE_CALL_"
                                context: Any = "_STORE_INDEX_NATIVE_CONTEXT_"
                                serialized = native(context(), callee, payload, json)
                        finally:
                            payload = None
                            callee = None
                        try:
                            write(serialized)
                        finally:
                            serialized = None
                    finally:
                        write = None
                    stream.write("\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temporary, 384)
                os.replace(temporary, self._index_path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise TypeError(f"{field} must be an object with text keys")
    return value


def _required(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field} must be non-empty trimmed text")
    return value


__all__ = [
    "DEFAULT_MUTATION_STORE_CAPACITY",
    "MAX_MUTATION_STORE_CAPACITY",
    "WORKSPACE_REPOSITORY_MUTATION_STORE_CONTRACT_REF",
    "WORKSPACE_REPOSITORY_MUTATION_STORE_VERSION",
    "WorkspaceRepositoryMutationStore",
    "WorkspaceRepositoryMutationStoreCorrupt",
    "WorkspaceRepositoryMutationStoreError",
]


_store_native_handoff = None
_store_journal_native_handoff = None
try:
    from aware_workspace_sdk._tree_native_binding import (
        bind_store_json as _bind_store_json,
    )
except ImportError:
    pass
else:
    _store_native_handoff = _bind_store_json(
        WorkspaceRepositoryMutationStore, "_persist"
    )
    _store_journal_native_handoff = _bind_store_json(
        WorkspaceRepositoryMutationStore, "_canonical_index"
    )

_STORE_NATIVE_HANDOFF = _store_native_handoff


_STORE_JOURNAL_NATIVE_HANDOFF = _store_journal_native_handoff


_journal_writer, _journal_writer_code, _journal_writer_cells, _journal_writer_values = (
    bind_index_writer(_atomic_write)
)
_journal_replacements = {
    "_ORIGINAL_INDEX_JOURNAL_WRITER_": _journal_writer,
    "_ORIGINAL_INDEX_JOURNAL_WRITER_CODE_": _journal_writer_code,
    "_ORIGINAL_INDEX_JOURNAL_WRITER_CELLS_": _identity_data(
        cast(Any, int), _journal_writer_cells
    ),
    "_ORIGINAL_INDEX_JOURNAL_WRITER_VALUES_": _identity_data(
        cast(Any, int), _journal_writer_values
    ),
}
_journal_replacements.update(
    {
        "_ORIGINAL_INDEX_SERIALIZER_": WorkspaceRepositoryMutationStore._canonical_index,
        "_ORIGINAL_INDEX_SERIALIZER_CODE_": WorkspaceRepositoryMutationStore._canonical_index.__code__,
    }
)
_journal_original = WorkspaceRepositoryMutationStore._persist
_journal_constants = tuple(
    _journal_replacements.get(value, value) if type(value) is str else value
    for value in _journal_original.__code__.co_consts
)
_journal_assembled = _types.FunctionType(
    _journal_original.__code__.replace(co_consts=_journal_constants),
    _journal_original.__globals__,
    _journal_original.__name__,
    _journal_original.__defaults__,
    _journal_original.__closure__,
)
_journal_assembled.__annotations__ = _journal_original.__annotations__
_journal_assembled.__qualname__ = _journal_original.__qualname__
WorkspaceRepositoryMutationStore._persist = _journal_assembled
