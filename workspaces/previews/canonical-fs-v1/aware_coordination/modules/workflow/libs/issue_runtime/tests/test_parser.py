from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from aware_issue_runtime import (
    ISSUE_PROJECTION_SCHEMA_VERSION,
    IssueTimeAuthority,
    parse_issue_projection,
    parse_issue_source,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_canonical_projection_is_structured_lossless_and_provenance_exact() -> None:
    text = _fixture("canonical.md")
    projection = parse_issue_projection(
        text=text,
        source_path="docs/issues/2026/08/20/example.md",
        observed_at="2026-08-20T06:20:00Z",
    )

    assert projection.schema_version == ISSUE_PROJECTION_SCHEMA_VERSION
    assert projection.issue_ref == "fb/2026-08-20/structured-issue-projection"
    assert projection.status == "in_progress"
    assert projection.owner_ref == "codex-session-1"
    assert projection.problem_items == (
        "Raw Markdown is slow to inspect.",
        "File events are not Issue semantics.",
    )
    assert [item.checked for item in projection.acceptance_items] == [True, False]
    assert projection.activities[0].activity_at == "2026-08-20T06:00:00Z"
    assert projection.activities[0].time_authority is IssueTimeAuthority.SOURCE_DECLARED
    assert projection.activities[0].actor_ref == "codex-session-1"
    assert projection.activities[1].outcome == "pass"
    assert projection.activities[1].command == "pytest"
    assert projection.activities[1].command_exit_code == 0
    assert projection.observation_time_authority is IssueTimeAuthority.SOURCE_OBSERVED
    assert projection.evidence[0].reference == "proofs/parser.json"
    assert projection.resolution == "Projection core is ready."
    assert projection.additional_sections[0].heading == "Custom Notes"
    assert projection.raw_markdown == text
    assert projection.source_digest == (
        f"sha256:{hashlib.sha256(text.encode()).hexdigest()}"
    )


def test_legacy_projection_is_honest_about_missing_authority() -> None:
    projection = parse_issue_projection(
        text=_fixture("legacy.md"),
        source_path="docs/issues/legacy.md",
    )
    assert projection.issue_ref == "local:docs/issues/legacy.md"
    assert projection.owner_ref is None
    assert projection.goal_items == ("Keep legacy sources readable.",)
    assert projection.activities[0].activity_at is None
    assert projection.activities[0].time_authority is IssueTimeAuthority.UNAVAILABLE
    assert projection.observation_time_authority is IssueTimeAuthority.UNAVAILABLE
    assert projection.additional_sections[0].lines == ("- opaque: true",)


def test_irregular_duplicate_sections_preserve_order_and_unknown_content() -> None:
    projection = parse_issue_projection(
        text=_fixture("irregular.md"),
        source_path="docs/issues/irregular.md",
    )
    assert projection.ownership_scope == ("one/path", "two/path")
    assert len(projection.acceptance_items) == 1
    assert projection.acceptance_items[0].checked is True
    assert [item.sequence for item in projection.activities] == [1, 2]
    assert [item.reference for item in projection.evidence] == [
        "receipt-one",
        "receipt-two",
    ]
    assert [section.lines for section in projection.additional_sections] == [
        ("exact", ""),
        ("duplicate preserved",),
    ]


def test_projection_contract_is_frozen_and_payload_is_json_native() -> None:
    projection = parse_issue_projection(
        text=_fixture("canonical.md"),
        source_path="docs/issues/example.md",
    )
    with pytest.raises(FrozenInstanceError):
        projection.title = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        projection.activities[0] = projection.activities[0]  # type: ignore[index]

    payload = projection.to_payload()
    encoded = json.dumps(payload, sort_keys=True)
    assert '"time_authority": "source_declared"' in encoded
    assert payload["source"]["raw_markdown"] == projection.raw_markdown  # type: ignore[index]
    without_source = projection.to_payload(include_raw_markdown=False)
    assert without_source["source"]["raw_markdown"] is None  # type: ignore[index]


def test_source_document_parser_retains_normalized_headers_and_exact_lines() -> None:
    document = parse_issue_source(_fixture("canonical.md"))
    assert document.title == "Structured Issue projection"
    assert document.header("tag") == "fb/2026-08-20/structured-issue-projection"
    assert document.matching_sections("Custom Notes")[0].lines == (
        "This stays lossless.",
    )


def test_source_document_parser_joins_indented_header_continuations() -> None:
    document = parse_issue_source(
        """# Issue: Wrapped native coordinates

- Native Issue:
  `issue-instance:sha256:abc123`
- Native Issue revision:
  `issue-instance:sha256:abc123:revision:2`
- Source: Exact authority text that wraps after the
  first line without losing its continuation.

## Goal
Preserve metadata.
"""
    )

    assert document.header("Native Issue") == "issue-instance:sha256:abc123"
    assert document.header("Native Issue revision") == (
        "issue-instance:sha256:abc123:revision:2"
    )
    assert document.header("Source") == (
        "Exact authority text that wraps after the first line without losing its "
        "continuation."
    )


@pytest.mark.parametrize(
    "source_path",
    ["", "/docs/issues/a.md", "../a.md", "docs/../a.md", "docs\\a.md"],
)
def test_projection_rejects_noncanonical_source_paths(source_path: str) -> None:
    with pytest.raises(ValueError, match="path"):
        parse_issue_projection(text="# Issue: invalid", source_path=source_path)


def test_projection_rejects_invalid_source_observation_time() -> None:
    with pytest.raises(ValueError, match="observation time"):
        parse_issue_projection(
            text="# Issue: invalid time",
            source_path="docs/issues/a.md",
            observed_at="recently",
        )


def test_runtime_import_does_not_load_generated_or_framework_dependencies() -> None:
    code = """
import sys
import aware_issue_runtime
forbidden = (
    'pydantic', 'aware_issue_service', 'aware_workflow_ontology',
    'aware_local_service_runtime', 'sqlalchemy',
)
raise SystemExit(1 if any(name.startswith(forbidden) for name in sys.modules) else 0)
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_piped_updates_declare_their_time_and_actor() -> None:
    projection = parse_issue_projection(
        text=(
            "# Issue: Piped\n\n- Tag: fb/2026-09-24/piped\n- Status: Closed\n\n"
            "## Updates (append-only)\n"
            "- 2026-09-24T12:50:00Z | claude_code-session | Claimed.\n"
            "- 2026-09-24T13:10Z | codex-session | Landed | with a pipe.\n"
            "- 2026-09-24T14:00:00Z — Dashed form still reads.\n"
        ),
        source_path="docs/issues/2026/09/24/piped.md",
        observed_at="2026-09-24T15:00:00Z",
    )

    first, second, third = projection.activities
    assert first.activity_at == "2026-09-24T12:50:00Z"
    assert first.time_authority is IssueTimeAuthority.SOURCE_DECLARED
    assert first.actor_ref == "claude_code-session"
    assert first.message == "Claimed."
    assert second.activity_at == "2026-09-24T13:10Z"
    assert second.actor_ref == "codex-session"
    assert second.message == "Landed | with a pipe."
    assert third.activity_at == "2026-09-24T14:00:00Z"
    assert third.actor_ref is None


def test_a_prose_section_gives_its_paragraphs() -> None:
    projection = parse_issue_projection(
        text=(
            "# Issue: Prose\n\n- Tag: fb/2026-09-24/prose\n- Status: Open\n\n"
            "## Problem\n\nThe host is not native\nyet.\n\nIt blocks the Gate.\n\n"
            "## Goal\n- Host it natively.\n"
        ),
        source_path="docs/issues/2026/09/24/prose.md",
        observed_at="2026-09-24T15:00:00Z",
    )

    assert projection.problem_items == (
        "The host is not native yet.",
        "It blocks the Gate.",
    )
    assert projection.goal_items == ("Host it natively.",)
