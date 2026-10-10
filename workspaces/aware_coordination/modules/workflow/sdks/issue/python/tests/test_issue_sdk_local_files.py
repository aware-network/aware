from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from aware_issue_runtime import parse_issue_source
from aware_issue_sdk import (
    FeedLocalFileSdk,
    append_day_index_update,
    append_feed_line,
    build_issue_document,
    parse_issue_document,
    parse_issue_document_text,
    snapshot_issue_document,
    status_token_to_display,
    upsert_day_index_entry,
    write_issue_document,
)


def test_issue_sdk_writes_and_parses_local_issue_document(tmp_path: Path) -> None:
    issue_path = tmp_path / "docs" / "issues" / "2026" / "05" / "07" / "fb.md"
    document = build_issue_document(
        title="SDK local rail",
        slug="sdk-local-rail",
        tag="fb/2026-05-07/sdk-local-rail",
        status_display=status_token_to_display("in_progress"),
        owner_session_id="codex-test",
        priority="P0",
        goal="goal/local",
        captured="2026-05-07",
        recorder="codex-test",
        source="unit test",
        ownership_scope=(
            "workspaces/aware_coordination/modules/workflow/sdks/issue",
            "workspaces/aware_coordination/modules/social/sdks/social",
        ),
        updates=("- 2026-05-07T00:00:00Z - opened",),
    )

    write_issue_document(issue_doc_path=issue_path, document=document)
    snapshot = snapshot_issue_document(
        document=parse_issue_document(issue_doc_path=issue_path)
    )

    assert snapshot.title == "SDK local rail"
    assert snapshot.tag == "fb/2026-05-07/sdk-local-rail"
    assert snapshot.status_token == "in_progress"
    assert snapshot.owner_session_id == "codex-test"
    assert snapshot.ownership_scope == (
        "workspaces/aware_coordination/modules/workflow/sdks/issue",
        "workspaces/aware_coordination/modules/social/sdks/social",
    )


def test_issue_sdk_document_parser_matches_runtime_source_core() -> None:
    markdown = """# Issue: Shared parser

- Tag: `fb/shared-parser`

## Custom
exact source line
"""
    sdk_document = parse_issue_document_text(text=markdown)
    runtime_document = parse_issue_source(markdown)
    assert sdk_document.title == runtime_document.title
    assert [(item.field, item.value) for item in sdk_document.headers] == [
        (item.field, item.value) for item in runtime_document.headers
    ]
    assert [(item.heading, item.lines) for item in sdk_document.sections] == [
        (item.heading, list(item.lines)) for item in runtime_document.sections
    ]


def test_issue_sdk_upserts_day_index_entry_without_duplicates(tmp_path: Path) -> None:
    day_index = tmp_path / "docs" / "issues" / "2026" / "05" / "07.md"

    upsert_day_index_entry(
        day_index_path=day_index,
        issue_doc_relpath="docs/issues/2026/05/07/fb.md",
        status_display="In Progress",
        owner_session_id="codex-test",
        priority="P0",
        summary="initial summary",
        title="SDK local rail",
    )
    upsert_day_index_entry(
        day_index_path=day_index,
        issue_doc_relpath="docs/issues/2026/05/07/fb.md",
        status_display="Closed",
        owner_session_id="codex-test",
        priority="P0",
        summary="closed summary",
        title="SDK local rail",
    )

    text = day_index.read_text(encoding="utf-8")
    assert text.count("docs/issues/2026/05/07/fb.md") == 1
    assert "CLOSED" in text
    assert "closed summary" in text


def test_issue_sdk_appends_day_index_update_section(tmp_path: Path) -> None:
    day_index = tmp_path / "issues.md"

    append_day_index_update(day_index_path=day_index, line="- update")

    assert (
        day_index.read_text(encoding="utf-8") == "## Updates (append-only)\n- update\n"
    )


def test_issue_sdk_appends_feed_line(tmp_path: Path) -> None:
    feed_path = tmp_path / "docs" / "feed" / "2026" / "07" / "07.md"

    append_feed_line(feed_daily_log_path=feed_path, line="- first")
    receipt = FeedLocalFileSdk().append_line(
        feed_daily_log_path=feed_path,
        line="- second",
    )

    assert receipt.feed_daily_log_path == feed_path
    assert receipt.appended_line == "- second"
    assert feed_path.read_text(encoding="utf-8") == "- first\n- second\n"


def test_issue_sdk_local_exports_do_not_import_ontology_runtime() -> None:
    code = textwrap.dedent(
        """
        import sys
        from aware_issue_sdk import build_issue_document, status_token_to_display

        forbidden = tuple(
            name
            for name in sys.modules
            if name.startswith("aware_workflow_ontology")
            or name.startswith("aware_workflow_ontology_dto")
            or name.startswith("aware_orm")
        )
        raise SystemExit(1 if forbidden else 0)
        """
    )

    completed = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
