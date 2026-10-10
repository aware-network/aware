from __future__ import annotations

import json
import os
import tempfile
import threading
from collections.abc import Mapping
from pathlib import Path

from aware_workspace_runtime.change_evidence_codec import (
    repository_authorized_mutation_from_payload,
    repository_authorized_mutation_payload,
)
from aware_workspace_runtime.repository_mutation import (
    WorkspaceRepositoryAuthorizedMutation,
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
        if not self._index_path.is_file():
            return
        try:
            payload = json.loads(self._index_path.read_text(encoding="utf-8"))
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

    def _persist(self) -> None:
        self._store_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{self._index_path.name}.", dir=self._store_root
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(
                    {
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
                    },
                    stream,
                    indent=2,
                    sort_keys=True,
                )
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
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
