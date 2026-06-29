from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from aware_meta.materialization.deltas.coercion import (
    int_mapping_value,
    int_value,
    mapping_value,
    optional_text,
    string_value,
    tuple_mappings,
    tuple_text,
)


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaDirtyEntry:
    payload: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaDirtyEntry | None":
        semantic_key = optional_text(payload.get("semantic_key"))
        entry_key = optional_text(payload.get("entry_key"))
        if semantic_key is None and entry_key is None:
            return None
        return cls(payload={str(key): value for key, value in payload.items()})

    @property
    def entry_key(self) -> str | None:
        return optional_text(self.payload.get("entry_key"))

    @property
    def semantic_key(self) -> str | None:
        return optional_text(self.payload.get("semantic_key"))

    @property
    def source_delta_key(self) -> str | None:
        return optional_text(self.payload.get("source_delta_key"))

    @property
    def source_refs(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("source_refs"))

    @property
    def semantic_subject_type(self) -> str | None:
        return optional_text(self.payload.get("semantic_subject_type"))

    @property
    def ontology_subject_kind(self) -> str:
        return string_value(self.payload.get("ontology_subject_kind"))

    @property
    def dirty_operation(self) -> str:
        return string_value(self.payload.get("dirty_operation"))

    @property
    def operation_kind(self) -> str:
        operation = optional_text(self.payload.get("baseline_compare_operation"))
        if operation is not None:
            return operation
        dirty_operation = optional_text(self.payload.get("dirty_operation"))
        if dirty_operation is not None and "_" in dirty_operation:
            return dirty_operation.rsplit("_", 1)[1]
        return string_value(self.payload.get("verb")) or "unknown"

    @property
    def baseline_compare_status(self) -> str | None:
        return optional_text(self.payload.get("baseline_compare_status"))

    @property
    def baseline_object_matched(self) -> bool:
        return self.payload.get("baseline_object_matched") is True

    @property
    def baseline_object_id(self) -> str | None:
        return optional_text(self.payload.get("baseline_object_id"))

    @property
    def baseline_object_kind(self) -> str | None:
        return optional_text(self.payload.get("baseline_object_kind"))

    @property
    def baseline_object_instance_graph_commit_id(self) -> str | None:
        return optional_text(
            self.payload.get("baseline_object_instance_graph_commit_id")
        )

    @property
    def baseline(self) -> dict[str, object]:
        return mapping_value(
            self.payload.get("baseline") or self.payload.get("baseline_object")
        )

    @property
    def current(self) -> dict[str, object]:
        return mapping_value(
            self.payload.get("current") or self.payload.get("payload")
        )

    @property
    def blocked(self) -> bool:
        return (
            self.payload.get("blocked") is True
            or self.operation_kind == "blocked"
            or self.baseline_compare_status == "semantic_key_missing"
        )

    @property
    def blocker_reason(self) -> str | None:
        return optional_text(
            self.payload.get("blocked_reason")
            or self.payload.get("baseline_compare_reason")
            or self.payload.get("reason")
        )

    @property
    def would_execute(self) -> bool:
        return self.payload.get("would_execute") is True

    @property
    def would_persist(self) -> bool:
        return self.payload.get("would_persist") is True

    def evidence_payload(self) -> dict[str, object]:
        return {str(key): value for key, value in self.payload.items()}


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaSemanticDirtyDiff:
    payload: Mapping[str, object]
    dirty_entries: tuple[MetaProviderDeltaDirtyEntry, ...]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaSemanticDirtyDiff":
        return cls(
            payload={str(key): value for key, value in payload.items()},
            dirty_entries=dirty_entries_from_payloads(
                payload.get("semantic_dirty_entries")
            ),
        )

    @property
    def status(self) -> str | None:
        return optional_text(self.payload.get("status"))

    @property
    def contract_version(self) -> str | None:
        return optional_text(self.payload.get("contract_version"))

    @property
    def reason(self) -> str | None:
        return optional_text(self.payload.get("reason"))

    @property
    def available(self) -> bool:
        return self.payload.get("available") is True

    @property
    def blocked(self) -> bool:
        return self.payload.get("blocked") is True

    @property
    def ready(self) -> bool:
        return (
            self.status == "semantic_dirty_diff_ready"
            and self.available
            and not self.blocked
        )

    @property
    def current_delta_fingerprint(self) -> str | None:
        return optional_text(self.payload.get("current_delta_fingerprint"))

    @property
    def baseline_index_compare_available(self) -> bool:
        return self.payload.get("baseline_index_compare_available") is True

    @property
    def baseline_index_compare_status(self) -> str | None:
        return optional_text(self.payload.get("baseline_index_compare_status"))

    @property
    def baseline_index_compare_reason(self) -> str | None:
        return optional_text(self.payload.get("baseline_index_compare_reason"))

    @property
    def dirty_entry_count(self) -> int:
        return int_value(self.payload.get("dirty_entry_count"))

    @property
    def semantic_delta_count(self) -> int:
        return int_value(self.payload.get("semantic_delta_count"))

    @property
    def stale_semantic_key_count(self) -> int:
        return int_value(self.payload.get("stale_semantic_key_count"))

    @property
    def stale_semantic_keys(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("stale_semantic_keys"))

    @property
    def dirty_entry_kind_counts(self) -> dict[str, int]:
        return int_mapping_value(self.payload.get("dirty_entry_kind_counts"))

    @property
    def dirty_operation_counts(self) -> dict[str, int]:
        return int_mapping_value(self.payload.get("dirty_operation_counts"))

    @property
    def baseline_compare_operation_counts(self) -> dict[str, int]:
        return int_mapping_value(
            self.payload.get("baseline_compare_operation_counts")
        )

    @property
    def compare_mode(self) -> str | None:
        return optional_text(self.payload.get("compare_mode"))

    @property
    def blocked_status(self) -> str | None:
        return optional_text(self.payload.get("blocked_status"))

    @property
    def blocked_reason(self) -> str | None:
        return optional_text(self.payload.get("blocked_reason"))

    def entries_for_operation(
        self,
        operation_kind: str,
    ) -> tuple[MetaProviderDeltaDirtyEntry, ...]:
        return tuple(
            entry
            for entry in self.dirty_entries
            if entry.operation_kind == operation_kind
        )

    def evidence_payload(self) -> dict[str, object]:
        payload = {str(key): value for key, value in self.payload.items()}
        payload["semantic_dirty_entries"] = tuple(
            entry.evidence_payload() for entry in self.dirty_entries
        )
        return payload


def dirty_entries_from_payloads(
    value: object,
) -> tuple[MetaProviderDeltaDirtyEntry, ...]:
    entries: list[MetaProviderDeltaDirtyEntry] = []
    for payload in tuple_mappings(value):
        entry = MetaProviderDeltaDirtyEntry.from_payload(payload)
        if entry is not None:
            entries.append(entry)
    return tuple(entries)


__all__ = [
    "MetaProviderDeltaDirtyEntry",
    "MetaProviderDeltaSemanticDirtyDiff",
    "dirty_entries_from_payloads",
]
