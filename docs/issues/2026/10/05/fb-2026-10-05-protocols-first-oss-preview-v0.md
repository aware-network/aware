# Issue: Publish protocols-first neutral filesystem OSS preview

- Slug: `protocols-first-oss-preview-v0`
- Tag: `fb/2026-10-05/protocols-first-oss-preview-v0`
- Status: In Progress
- Owner: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`
- Priority: P0
- Goal: `TBD`
- Captured: 2026-10-05
- Recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`
- Source: `Luis: publish a protocols-first OSS preview to aware-network/aware now; no force push or unrelated changes.`

## Ownership Scope
- `README.md`
- `protocols`
- `docs/issues/2026/10/05/fb-2026-10-05-protocols-first-oss-preview-v0.md`
- `docs/issues/2026/10/05/issues-2026-10-05.md`
- `docs/feed/2026/10/05.md`

## Problem
1. The public entrypoint foregrounds infrastructure while reviewed consumer
   tooling lacks a public source/download coordinate. Delay prevents agents
   from trying even the admitted read-only functionality.

## Goal
1. Publish the unchanged, reviewed neutral filesystem distribution as an honest
   early OSS preview, with exact source/notices, consumer instructions and a
   runnable synthetic read-only sample. Keep the existing infrastructure trees.
2. Use the Issue-named `protocols/publication/export_preview.py` as the canonical
   generator for the root README, source snapshot, artifact and digest receipt.
   This is a repository-owned Git consumer overlay, not a new WorkspaceRevision.
3. Operate through the environment-selected compatibility CLI; no resident
   session or service admission is selected for this publication.

## Acceptance Checklist
- [ ] Exact reviewed outer/payload/source digests preserved and source inspectable.
- [ ] Fresh offline installation with development checkout unavailable.
- [ ] Installed CLI demonstrates discovery, eligibility, direction and currentness
  on committed synthetic input without changing customer/repository state.
- [ ] Public boundaries exclude customer creation/import, effectful writers,
  service/API, ontology/ORM and complete-workflow claims.
- [ ] License/source/notice attachments accompany the public distribution.
- [ ] Focused publication proofs and bounded content review pass.
- [ ] Selected CLI dry-run/apply publication and non-force push to the explicitly
  authorized `aware-network/aware/main`, with public bytes independently fetched.

## Updates (append-only)
- 2026-10-05T00:26:07Z — Opened the issue via `aware-cli issue open`. Initial lifecycle state is `In Progress`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
