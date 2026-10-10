# Issue: Structured Issue projection

- Slug: `structured-issue-projection`
- Tag: `fb/2026-08-20/structured-issue-projection`
- Status: In Progress
- Owner: `codex-session-1`
- Priority: P0
- Goal: `goal/aware-dev`
- Captured: 2026-08-20
- Source: `fixture`

## Ownership Scope
- `docs/issues/example.md`
- `workspaces/aware_coordination/modules/workflow`

## Problem
1. Raw Markdown is slow to inspect.
2. File events are not Issue semantics.

## Goal
1. Publish one structured read projection.

## Acceptance Checklist
- [x] Parse identity.
- [ ] Publish activity.

## Verified-by
- `proofs/parser.json`

## Updates (append-only)
- 2026-08-20T06:00:00Z — Opened projection work. (recorder: `codex-session-1`)
- 2026-08-20T06:10:00+00:00 - Parser passed. (command: `pytest`) (command exit: `0`) (outcome: `pass`) (actor: `codex-session-1`)

## Resolution
Projection core is ready.

## Custom Notes
This stays lossless.
