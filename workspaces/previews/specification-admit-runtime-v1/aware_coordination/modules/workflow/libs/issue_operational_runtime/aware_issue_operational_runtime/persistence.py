from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Protocol, runtime_checkable

from .contracts import IssueIntent, IssueSnapshot
from .identity import nonnegative, required_token
from .journal import IssueOperationalRecord


@dataclass(frozen=True, slots=True)
class PersistedIssueRecord:
    authority_ref: str
    generation: int
    payload: str

    def __post_init__(self) -> None:
        required_token(self.authority_ref, "authority_ref")
        nonnegative(self.generation, "generation")
        if not isinstance(self.payload, str) or not self.payload:
            raise ValueError("payload must be non-empty JSON text")


@dataclass(frozen=True, slots=True)
class PersistenceWriteResult:
    applied: bool
    current: PersistedIssueRecord


class IssueStateStore(Protocol):
    def read(self, authority_ref: str) -> PersistedIssueRecord | None: ...

    def create(self, authority_ref: str, payload: str) -> PersistenceWriteResult: ...

    def compare_and_set(
        self,
        authority_ref: str,
        *,
        expected_generation: int,
        payload: str,
    ) -> PersistenceWriteResult: ...


@runtime_checkable
class IssueIndexedStateStore(IssueStateStore, Protocol):
    """Optional bounded persistence port for exact Issue operations."""

    def read_head_record(self, authority_ref: str) -> IssueOperationalRecord | None: ...

    def read_issue_by_ref(
        self, authority_ref: str, issue_ref: str
    ) -> IssueSnapshot | None: ...

    def read_issue_by_tag(
        self, authority_ref: str, issue_tag: str
    ) -> IssueSnapshot | None: ...

    def read_mutation_record(
        self, authority_ref: str, intent: IssueIntent
    ) -> PersistedIssueRecord | None: ...

    def compare_and_set_delta(
        self,
        authority_ref: str,
        *,
        expected_generation: int,
        payload: str,
    ) -> PersistenceWriteResult: ...


class InMemoryIssueStateStore:
    def __init__(self) -> None:
        self._records: dict[str, PersistedIssueRecord] = {}
        self._lock = RLock()

    def read(self, authority_ref: str) -> PersistedIssueRecord | None:
        required_token(authority_ref, "authority_ref")
        with self._lock:
            return self._records.get(authority_ref)

    def create(self, authority_ref: str, payload: str) -> PersistenceWriteResult:
        proposed = PersistedIssueRecord(authority_ref, 0, payload)
        with self._lock:
            current = self._records.get(authority_ref)
            if current is not None:
                return PersistenceWriteResult(False, current)
            self._records[authority_ref] = proposed
            return PersistenceWriteResult(True, proposed)

    def compare_and_set(
        self,
        authority_ref: str,
        *,
        expected_generation: int,
        payload: str,
    ) -> PersistenceWriteResult:
        required_token(authority_ref, "authority_ref")
        nonnegative(expected_generation, "expected_generation")
        with self._lock:
            current = self._records.get(authority_ref)
            if current is None:
                raise KeyError(authority_ref)
            if current.generation != expected_generation:
                return PersistenceWriteResult(False, current)
            proposed = PersistedIssueRecord(
                authority_ref,
                expected_generation + 1,
                payload,
            )
            self._records[authority_ref] = proposed
            return PersistenceWriteResult(True, proposed)
