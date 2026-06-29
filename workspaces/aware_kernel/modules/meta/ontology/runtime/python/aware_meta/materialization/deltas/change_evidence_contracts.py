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
class MetaProviderDeltaSemanticWorldChange:
    payload: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaSemanticWorldChange | None":
        change_key = optional_text(payload.get("change_key"))
        semantic_key = optional_text(payload.get("semantic_key"))
        if change_key is None and semantic_key is None:
            return None
        return cls(payload={str(key): value for key, value in payload.items()})

    @property
    def change_kind(self) -> str | None:
        return optional_text(self.payload.get("change_kind"))

    @property
    def contract_version(self) -> str | None:
        return optional_text(self.payload.get("contract_version"))

    @property
    def change_key(self) -> str | None:
        return optional_text(self.payload.get("change_key"))

    @property
    def change_type(self) -> str | None:
        return optional_text(self.payload.get("change_type"))

    @property
    def summary(self) -> str | None:
        return optional_text(
            self.payload.get("summary")
            or self.payload.get("narrative")
            or self.payload.get("world_change")
        )

    @property
    def semantic_key(self) -> str | None:
        return optional_text(self.payload.get("semantic_key"))

    @property
    def verb(self) -> str | None:
        return optional_text(self.payload.get("verb"))

    @property
    def subject_type(self) -> str | None:
        return optional_text(self.payload.get("subject_type"))

    @property
    def ontology_subject_kind(self) -> str | None:
        return optional_text(self.payload.get("ontology_subject_kind"))

    @property
    def subject_label(self) -> str | None:
        return optional_text(self.payload.get("subject_label"))

    @property
    def subject_description(self) -> str | None:
        return optional_text(self.payload.get("subject_description"))

    @property
    def provider_operation_type(self) -> str | None:
        return optional_text(self.payload.get("provider_operation_type"))

    @property
    def source(self) -> str | None:
        return optional_text(self.payload.get("source"))

    @property
    def source_refs(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("source_refs"))

    @property
    def delta_keys(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("delta_keys"))

    @property
    def condition_keys(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("condition_keys"))

    @property
    def baseline(self) -> dict[str, object]:
        return mapping_value(self.payload.get("baseline"))

    @property
    def current(self) -> dict[str, object]:
        return mapping_value(self.payload.get("current"))

    @property
    def ocg_operation(self) -> dict[str, object]:
        return mapping_value(self.payload.get("ocg_operation"))

    def evidence_payload(self) -> dict[str, object]:
        return {str(key): value for key, value in self.payload.items()}


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaReadableSemanticChangeChain:
    payload: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaReadableSemanticChangeChain":
        return cls(payload={str(key): value for key, value in payload.items()})

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
    def ready(self) -> bool:
        return (
            self.status == "readable_semantic_change_chain_ready"
            and self.payload.get("blocked") is not True
        )

    @property
    def blocked(self) -> bool:
        return self.payload.get("blocked") is True

    @property
    def source_change_count(self) -> int:
        return int_value(self.payload.get("source_change_count"))

    @property
    def change_count(self) -> int:
        return int_value(self.payload.get("change_count"))

    @property
    def line_count(self) -> int:
        return int_value(self.payload.get("line_count"))

    @property
    def lines(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("lines"))

    @property
    def markdown(self) -> str:
        return string_value(self.payload.get("markdown"))

    @property
    def plain_text(self) -> str:
        return string_value(self.payload.get("plain_text"))

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("blockers"))

    def evidence_payload(self) -> dict[str, object]:
        return {str(key): value for key, value in self.payload.items()}


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaSemanticChangeReport:
    payload: Mapping[str, object]
    semantic_world_changes: tuple[
        MetaProviderDeltaSemanticWorldChange,
        ...,
    ]
    readable_semantic_change_chain: MetaProviderDeltaReadableSemanticChangeChain

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaSemanticChangeReport":
        chain_payload = mapping_value(
            payload.get("minimal_readable_semantic_change_chain")
        ) or mapping_value(payload.get("readable_semantic_change_chain"))
        return cls(
            payload={str(key): value for key, value in payload.items()},
            semantic_world_changes=semantic_world_changes_from_payloads(
                payload.get("semantic_world_changes")
            ),
            readable_semantic_change_chain=(
                MetaProviderDeltaReadableSemanticChangeChain.from_payload(chain_payload)
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
    def ready(self) -> bool:
        return (
            self.status == "semantic_change_report_ready"
            and self.available
            and not self.blocked
        )

    @property
    def available(self) -> bool:
        return self.payload.get("available") is True

    @property
    def blocked(self) -> bool:
        return self.payload.get("blocked") is True

    @property
    def semantic_dirty_diff_status(self) -> str | None:
        return optional_text(self.payload.get("semantic_dirty_diff_status"))

    @property
    def provider_delta_typed_operation_status(self) -> str | None:
        return optional_text(self.payload.get("provider_delta_typed_operation_status"))

    @property
    def semantic_dirty_entry_count(self) -> int:
        return int_value(self.payload.get("semantic_dirty_entry_count"))

    @property
    def typed_operation_count(self) -> int:
        return int_value(self.payload.get("typed_operation_count"))

    @property
    def semantic_world_change_count(self) -> int:
        return int_value(self.payload.get("semantic_world_change_count"))

    @property
    def natural_language_summaries(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("natural_language_summaries"))

    @property
    def change_type_counts(self) -> dict[str, int]:
        return int_mapping_value(self.payload.get("change_type_counts"))

    @property
    def change_key_counts(self) -> dict[str, int]:
        return int_mapping_value(self.payload.get("change_key_counts"))

    @property
    def operation_family_counts(self) -> dict[str, int]:
        return int_mapping_value(self.payload.get("operation_family_counts"))

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("blockers"))

    @property
    def blocker_count(self) -> int:
        return int_value(self.payload.get("blocker_count"))

    @property
    def readable_markdown(self) -> str:
        return self.readable_semantic_change_chain.markdown

    @property
    def readable_lines(self) -> tuple[str, ...]:
        return self.readable_semantic_change_chain.lines

    @property
    def readable_line_count(self) -> int:
        return self.readable_semantic_change_chain.line_count

    def evidence_payload(self) -> dict[str, object]:
        changes = tuple(
            change.evidence_payload() for change in self.semantic_world_changes
        )
        chain = self.readable_semantic_change_chain.evidence_payload()
        payload = {str(key): value for key, value in self.payload.items()}
        payload["semantic_world_changes"] = changes
        payload["minimal_readable_semantic_change_chain"] = chain
        payload["readable_semantic_change_chain"] = chain
        payload["readable_semantic_change_chain_markdown"] = chain.get(
            "markdown",
            "",
        )
        payload["readable_semantic_change_chain_lines"] = tuple_text(chain.get("lines"))
        return payload


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaCommittedSemanticChange:
    payload: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaCommittedSemanticChange | None":
        change_key = optional_text(payload.get("change_key"))
        semantic_key = optional_text(payload.get("semantic_key"))
        if change_key is None and semantic_key is None:
            return None
        return cls(payload={str(key): value for key, value in payload.items()})

    @property
    def change_kind(self) -> str | None:
        return optional_text(self.payload.get("change_kind"))

    @property
    def contract_version(self) -> str | None:
        return optional_text(self.payload.get("contract_version"))

    @property
    def change_key(self) -> str | None:
        return optional_text(self.payload.get("change_key"))

    @property
    def change_type(self) -> str | None:
        return optional_text(self.payload.get("change_type"))

    @property
    def semantic_key(self) -> str | None:
        return optional_text(self.payload.get("semantic_key"))

    @property
    def verb(self) -> str | None:
        return optional_text(self.payload.get("verb"))

    @property
    def subject_type(self) -> str | None:
        return optional_text(self.payload.get("subject_type"))

    @property
    def ontology_subject_kind(self) -> str | None:
        return optional_text(self.payload.get("ontology_subject_kind"))

    @property
    def provider_operation_type(self) -> str | None:
        return optional_text(self.payload.get("provider_operation_type"))

    @property
    def source(self) -> str | None:
        return optional_text(self.payload.get("source"))

    @property
    def source_change_key(self) -> str | None:
        return optional_text(self.payload.get("source_change_key"))

    @property
    def source_refs(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("source_refs"))

    @property
    def delta_keys(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("delta_keys"))

    @property
    def condition_keys(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("condition_keys"))

    @property
    def payload_value(self) -> dict[str, object]:
        return mapping_value(self.payload.get("payload"))

    @property
    def baseline(self) -> dict[str, object]:
        return mapping_value(self.payload.get("baseline"))

    @property
    def current(self) -> dict[str, object]:
        return mapping_value(self.payload.get("current"))

    @property
    def ocg_operation(self) -> dict[str, object]:
        return mapping_value(self.payload.get("ocg_operation"))

    @property
    def head_refs(self) -> dict[str, object]:
        return mapping_value(self.payload.get("head_refs"))

    @property
    def commit_ref(self) -> dict[str, object]:
        return mapping_value(self.payload.get("commit_ref"))

    @property
    def metadata(self) -> dict[str, object]:
        return mapping_value(self.payload.get("metadata"))

    def evidence_payload(self) -> dict[str, object]:
        return {str(key): value for key, value in self.payload.items()}


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaSemanticCommitEvidence:
    payload: Mapping[str, object]
    committed_semantic_changes: tuple[
        MetaProviderDeltaCommittedSemanticChange,
        ...,
    ]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaSemanticCommitEvidence":
        return cls(
            payload={str(key): value for key, value in payload.items()},
            committed_semantic_changes=committed_semantic_changes_from_payloads(
                payload.get("committed_semantic_changes")
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
    def ready(self) -> bool:
        return (
            self.status == "semantic_commit_evidence_ready"
            and self.available
            and not self.blocked
        )

    @property
    def available(self) -> bool:
        return self.payload.get("available") is True

    @property
    def blocked(self) -> bool:
        return self.payload.get("blocked") is True

    @property
    def provider_delta_typed_operation_status(self) -> str | None:
        return optional_text(self.payload.get("provider_delta_typed_operation_status"))

    @property
    def provider_delta_head_move_status(self) -> str | None:
        return optional_text(self.payload.get("provider_delta_head_move_status"))

    @property
    def provider_delta_head_move_applied_receipt_status(self) -> str | None:
        return optional_text(
            self.payload.get("provider_delta_head_move_applied_receipt_status")
        )

    @property
    def provider_delta_oig_commit_receipt_status(self) -> str | None:
        return optional_text(
            self.payload.get("provider_delta_oig_commit_receipt_status")
        )

    @property
    def provider_delta_oig_commit_receipt_commit_id(self) -> str | None:
        return optional_text(
            self.payload.get("provider_delta_oig_commit_receipt_commit_id")
        )

    @property
    def committed_semantic_change_count(self) -> int:
        return int_value(self.payload.get("committed_semantic_change_count"))

    @property
    def change_type_counts(self) -> dict[str, int]:
        return int_mapping_value(self.payload.get("change_type_counts"))

    @property
    def change_key_counts(self) -> dict[str, int]:
        return int_mapping_value(self.payload.get("change_key_counts"))

    @property
    def operation_family_counts(self) -> dict[str, int]:
        return int_mapping_value(self.payload.get("operation_family_counts"))

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("blockers"))

    @property
    def blocker_count(self) -> int:
        return int_value(self.payload.get("blocker_count"))

    def changes_for_subject(
        self,
        ontology_subject_kind: str,
    ) -> tuple[MetaProviderDeltaCommittedSemanticChange, ...]:
        return tuple(
            change
            for change in self.committed_semantic_changes
            if change.ontology_subject_kind == ontology_subject_kind
        )

    def evidence_payload(self) -> dict[str, object]:
        changes = tuple(
            change.evidence_payload() for change in self.committed_semantic_changes
        )
        payload = {str(key): value for key, value in self.payload.items()}
        payload["committed_semantic_changes"] = changes
        return payload


def semantic_world_changes_from_payloads(
    value: object,
) -> tuple[MetaProviderDeltaSemanticWorldChange, ...]:
    changes: list[MetaProviderDeltaSemanticWorldChange] = []
    for payload in tuple_mappings(value):
        change = MetaProviderDeltaSemanticWorldChange.from_payload(payload)
        if change is not None:
            changes.append(change)
    return tuple(changes)


def committed_semantic_changes_from_payloads(
    value: object,
) -> tuple[MetaProviderDeltaCommittedSemanticChange, ...]:
    changes: list[MetaProviderDeltaCommittedSemanticChange] = []
    for payload in tuple_mappings(value):
        change = MetaProviderDeltaCommittedSemanticChange.from_payload(payload)
        if change is not None:
            changes.append(change)
    return tuple(changes)


__all__ = [
    "MetaProviderDeltaCommittedSemanticChange",
    "MetaProviderDeltaReadableSemanticChangeChain",
    "MetaProviderDeltaSemanticChangeReport",
    "MetaProviderDeltaSemanticCommitEvidence",
    "MetaProviderDeltaSemanticWorldChange",
    "committed_semantic_changes_from_payloads",
    "semantic_world_changes_from_payloads",
]
