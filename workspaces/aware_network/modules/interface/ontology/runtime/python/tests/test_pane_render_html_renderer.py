from __future__ import annotations

from pathlib import Path

from aware_interface.renderers.html import render_pane_source_html


def test_render_pane_source_html_renders_identity_admission_entry_surface() -> None:
    repo_root = Path(__file__).resolve().parents[8]
    source = (
        repo_root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "identity"
        / "interfaces"
        / "panes"
        / "identity_admission"
        / "identity_admission.aware"
    ).read_text(encoding="utf-8")
    state = {
        "status": "ready",
        "status_tone": "neutral",
        "display_name": "Luis",
        "public_handle": "@luis",
        "bio": "# Builder of Aware",
    }

    html = render_pane_source_html(source, state=state)

    assert "Create your Aware identity" in html
    assert "Choose how this Interface presents you" in html
    assert "Public identity" in html
    assert "Admission profile" in html
    assert "Choose a display name" not in html
    assert "Add a short bio" not in html
    assert "Bio preview" in html
    assert "Markdown is supported" in html
    assert "Admit identity" in html
    assert "row-layout-pane-header" in html
    assert "node-typography-pane-title" in html
    assert "field-display-prose" in html
    assert "field-display-identifier" in html


def test_render_pane_source_html_renders_goal_disclosure_legibly() -> None:
    repo_root = Path(__file__).resolve().parents[8]
    source = (
        repo_root
        / "workspaces"
        / "aware_coordination"
        / "modules"
        / "workflow"
        / "panes"
        / "goal"
        / "goal.aware"
    ).read_text(encoding="utf-8")
    state = {
        "title": "Coordination Interface",
        "status": "Active",
        "status_tone": "pending",
        "priority": "P0",
        "priority_tone": "warning",
        "lanes": [
            {
                "lane_key": "previewer",
                "status": "Active",
                "status_tone": "pending",
                "role_label": "Render keystone",
                "owner_execution_id": "TBD",
                "scope": "Disclosure primitive + parse/lower authored render-spec -> HTML preview.",
                "last_receipt_ref": "Pending",
                "issues": [
                    {
                        "row_number": 1,
                        "row_key": "previewer-proof",
                        "title": "Render source panes as HTML previews.",
                        "summary": ".aware pane -> HTML preview with disclosure, no control machinery.",
                        "status": "In Progress",
                        "status_token": "in_progress",
                        "status_tone": "pending",
                        "owner_execution_id": "codex-019e0b89-f3ab-7d33-bb6e-ab2f38edf0f1",
                        "gate": ".aware pane -> HTML preview with disclosure, no control machinery.",
                        "receipt_ref": "Pending",
                        "issue_ref": "fb/2026-06-05/pane-render-spec-disclosure-html-previewer-v0",
                        "display_ref": "pane-render-spec-disclosure-html-previewer-v0",
                        "planned_issue_tag": "fb/2026-06-05/pane-render-spec-disclosure-html-previewer-v0",
                        "tick": "[ ]",
                    }
                ],
            }
        ],
    }

    html = render_pane_source_html(source, state=state)

    assert "Coordination Interface" in html
    assert "previewer" in html
    assert '<span class="value">1</span><span class="label">lanes</span>' in html
    assert "1 issue" in html
    assert "1 issues" not in html
    assert '<div class="section-header">Lanes</div>' not in html
    assert "Unassigned" not in html
    assert "Pending" not in html
    assert "TBD" not in html
    assert "Blocker / next" not in html
    assert "disclosure-static" in html
    assert "row-layout-pane-header" in html
    assert "row-align-center" in html
    assert (
        ".row.row-layout-pane-header .row-layout-metadata-bar { width: auto; }" in html
    )
    assert "node-typography-pane-title" in html
    assert "node-align-center" in html
    assert "row-layout-metadata-bar" in html
    assert "row-align-center" in html
    assert "row-layout-summary-bar" in html
    assert "list-item-layout-compact-row" in html
    assert "Render source panes as HTML previews." in html
    assert "in_progress" in html
    assert "tone-pending" in html
    assert "tone-warning" in html
    assert "status-token-" not in html
    assert "node-overflow-truncate" in html
    assert "field-display-prose" in html
    assert "field-display-identifier" in html
    assert "field-display-chip" in html
    assert "Row</span>" not in html
    assert "Tick</span>" not in html
    assert "codex-019e0b89...38edf0f1" in html
    assert 'title="Owner: codex-019e0b89-f3ab-7d33-bb6e-ab2f38edf0f1"' in html
    assert 'title="Render source panes as HTML previews."' in html
    assert (
        ".aware pane -&gt; HTML preview with disclosure, no control machinery." in html
    )
    assert "pane-render...iewer-v0" in html


def test_render_pane_source_html_renders_conversation_message_layout() -> None:
    repo_root = Path(__file__).resolve().parents[8]
    source = (
        repo_root
        / "workspaces"
        / "aware_coordination"
        / "modules"
        / "conversation"
        / "panes"
        / "conversation"
        / "conversation.aware"
    ).read_text(encoding="utf-8")
    state = {
        "title": "Coordination",
        "description": "Humans and AI evolving goals together",
        "status": "active",
        "messages": [
            {
                "text": "I'll take the previewer lane - disclosure primitive next.",
                "created_at": "11:04",
                "author_handle": "codex-operator",
                "author_kind": "agent",
                "author_tone": "pending",
            },
            {
                "text": "Board renders from raw .aware now - opening the issue.",
                "created_at": "",
            },
        ],
    }

    html = render_pane_source_html(source, state=state, render_name="home")

    assert "Coordination" in html
    assert "Humans and AI evolving goals together" in html
    assert "repeat-layout-message-thread" in html
    assert html.count('class="list-item list-item-layout-message-bubble"') == 2
    assert "row-layout-composer" in html
    assert "No messages yet." not in html
    assert "I&#x27;ll take the previewer lane" in html
    assert "codex-operator" in html
    assert "agent" in html
    assert "11:04" in html
    assert "field-display-scalar" in html
    assert "field-display-chip" in html
    assert "tone-pending" in html
    assert "tone-neutral" in html
    assert "Message this conversation" in html
