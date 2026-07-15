from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CommitAttributionEntry:
    actor_id: str | None
    actor_label: str | None
    branch_id: str | None
    projection_hash: str | None
    commit_id: str | None
    operation_label: str | None
    head_version: int | None

    def to_dict(self) -> dict[str, Any]:
        return dict(asdict(self))


def parse_actor_label_mappings(raw_items: Sequence[str]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for raw in raw_items:
        text = str(raw or "").strip()
        if not text:
            continue
        if "=" not in text:
            raise ValueError(f"Invalid actor label mapping {text!r}; expected <actor_uuid>=<label>.")
        raw_actor_id, raw_label = text.split("=", 1)
        actor_id_text = str(raw_actor_id or "").strip()
        label_text = str(raw_label or "").strip()
        if not actor_id_text or not label_text:
            raise ValueError(f"Invalid actor label mapping {text!r}; actor uuid and label are required.")
        try:
            actor_uuid = UUID(actor_id_text)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid actor label mapping {text!r}; actor uuid is invalid.") from exc
        labels[str(actor_uuid)] = label_text
    return labels


def resolve_actor_labels(
    *,
    primary_actor_id: UUID | None,
    raw_mappings: Sequence[str],
    primary_label: str = "human",
) -> dict[str, str]:
    labels = parse_actor_label_mappings(raw_mappings)
    if primary_actor_id is not None:
        labels.setdefault(str(primary_actor_id), str(primary_label or "human"))
    return labels


def build_commit_attribution_entries(
    *,
    commit_receipts: Sequence[Mapping[str, Any]],
    actor_labels: Mapping[str, str],
) -> list[CommitAttributionEntry]:
    out: list[CommitAttributionEntry] = []
    for receipt in commit_receipts:
        actor_id = _read_non_empty_text(receipt.get("actor_id"))
        out.append(
            CommitAttributionEntry(
                actor_id=actor_id,
                actor_label=actor_labels.get(actor_id, actor_id) if actor_id else None,
                branch_id=_read_non_empty_text(receipt.get("branch_id")),
                projection_hash=_read_non_empty_text(receipt.get("projection_hash")),
                commit_id=_read_non_empty_text(receipt.get("commit_id")),
                operation_label=_read_non_empty_text(receipt.get("operation_label")),
                head_version=(receipt.get("head_version") if isinstance(receipt.get("head_version"), int) else None),
            )
        )
    return out


def render_commit_timeline_lines(
    *,
    entries: Sequence[CommitAttributionEntry],
    limit: int = 32,
    line_prefix: str = "turn.commit",
) -> list[str]:
    if not entries:
        return []
    bounded_limit = max(int(limit), 1)
    out = [f"{line_prefix}_timeline count={len(entries)}"]
    for idx, entry in enumerate(entries[:bounded_limit], start=1):
        actor_label = (entry.actor_label or "unknown").strip() or "unknown"
        operation_label = (entry.operation_label or "<unknown>").strip() or "<unknown>"
        commit_id = (entry.commit_id or "unknown").strip() or "unknown"
        lane = f"{_short_token(entry.branch_id, width=8)}/" f"{_short_token(entry.projection_hash, width=12)}"
        line = f"{line_prefix}[{idx:02d}] actor={actor_label} op={operation_label} " f"commit={commit_id} lane={lane}"
        if entry.head_version is not None:
            line = f"{line} head={entry.head_version}"
        out.append(line)
    remaining = len(entries) - bounded_limit
    if remaining > 0:
        out.append(f"{line_prefix}.more={remaining}")
    return out


def _read_non_empty_text(raw_value: object) -> str | None:
    text = str(raw_value or "").strip()
    return text or None


def _short_token(raw_value: object, *, width: int = 12) -> str:
    text = str(raw_value or "").strip()
    if not text:
        return "none"
    if len(text) <= width:
        return text
    return text[:width]


__all__ = [
    "CommitAttributionEntry",
    "build_commit_attribution_entries",
    "parse_actor_label_mappings",
    "render_commit_timeline_lines",
    "resolve_actor_labels",
]
