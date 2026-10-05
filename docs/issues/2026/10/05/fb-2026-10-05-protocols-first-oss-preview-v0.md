# Issue: Publish protocols-first neutral filesystem OSS preview

- Slug: protocols-first-oss-preview-v0
- Tag: fb/2026-10-05/protocols-first-oss-preview-v0
- Status: Closed
- Owner: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Priority: P0
- Goal: TBD
- Captured: 2026-10-05
- Recorder: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Source: Luis: publish a protocols-first OSS preview to aware-network/aware now; no force push or unrelated changes.

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
- [x] Exact reviewed outer/payload/source digests preserved and source inspectable.
- [x] Fresh offline installation with development checkout unavailable.
- [x] Installed CLI demonstrates discovery, eligibility, direction and currentness
  on committed synthetic input without changing customer/repository state.
- [x] Public boundaries exclude customer creation/import, effectful writers,
  service/API, ontology/ORM and complete-workflow claims.
- [x] License/source/notice attachments accompany the public distribution.
- [x] Focused publication proofs and bounded content review pass.
- [x] Selected CLI dry-run/apply publication and non-force push to the explicitly
  authorized `aware-network/aware/main`, with public bytes independently fetched.


## Verified-by
- 10 publication tests; fresh offline checkout-hidden install; 4 installed sample operations eligible/current with repository unchanged; public commit-pinned artifact digest and GitHub branch confirmation.

## Updates (append-only)
- 2026-10-05T00:26:07Z — Opened the issue via `aware-cli issue open`. Initial lifecycle state is `In Progress`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- 2026-10-05 — Implementation `1c6f557ef18b1019471500e8626bf9ca8fd7d779` published the root README/exporter, `protocols` consumer/source/distribution files and the exact Issue/day-index/feed paths through selected `aware-cli` dry-run/apply. No raw Git lifecycle mutation. Compatibility authority remains selected; the shared development tree was not modified. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- 2026-10-05 — Sample-only correction `f43e16a2ff06c66cb9900d0fc05f78f484ec1f89` committed `protocols/examples/read-only/aware.protocol.toml` and its README. Real admission had refused the missing native-profile Issue authority binding; this supplies the required binding without adding an Issue writer. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- 2026-10-05 — Ten publication tests pass. Fresh corrected-sandbox offline installation passes. Committed sample replay runs all four installed operations: eligible/current, repository unchanged. Exact payload remains `02dfda3a…5456f1`; exact source-attached envelope remains `10b12638…29c21`. Scope is explicitly public read-only preview, not complete self-serve collaboration; supported authoring remains a Goal-owner follow-up. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- 2026-10-05 — Evidence commit `6514a02b88f824310d7c406b56eec71e23dce021` updates exactly this Issue and `protocols/publication/VERIFICATION.md`. Non-force push advanced public `aware-network/aware/main` from `2fcb995bb8dd91733d8964c2db783b670354e2a8` to that revision under Luis's explicit publication authorization. GitHub's branch API independently confirms the tip; an unauthenticated download of the commit-pinned archive matches SHA-256 `10b126383498b4e4561109f5eb8059161b2c03546d19065b85506f4c41a29c21`. Public quickstart access is confirmed. No registry release, tags, ref deletion or service effect. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- 2026-10-05T00:40:14Z — Published neutral FS read-only preview to aware-network/aware/main; public archive hash and quickstart verified. Next product gate is supported Goal creation/import and manifest preparation, not services or infrastructure expansion. Implementation commit: `6514a02b88f824310d7c406b56eec71e23dce021`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)

## Resolution
Public protocols-first early preview delivered: exact 13-package payload, source/notices, installer and committed synthetic reader demo; no full-workflow or effectful-authority claim.
