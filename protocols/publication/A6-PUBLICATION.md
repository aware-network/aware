# a6 authorized public Git delivery

Date: 2026-10-05. Execution: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`.
Owning [Issue](../../docs/issues/2026/10/05/fb-2026-10-05-a6-public-delivery.md).
Luis explicitly authorized a **non-force push to `aware-network/aware/main`**,
after remote ancestry checking, followed by revision-pinned public-download
verification. This authorizes the accepted Git preview and its delivery receipts,
not a registry release, new payload, SPEC implementation or customer evaluation.

## Accepted input

Candidate: `e02a06544e88`, independently reproduced fresh isolated installation,
224 installed and 64 accounting/evaluator checks, zero skips. Promotion:
`7ce94f32a1ca`, independently reproduced 70 alignment checks and an installed-only
224-test replay. Closed bounded cuts: `43826e50ab29` and `dea5783a1f05`.
See [candidate evidence](../agent/A6-CANDIDATE.md) and
[local promotion evidence](A6-PROMOTION.md) for exact review qualifications.

- Archive SHA-256:
  `c3d6e593fd5894a927d338da5347a32e9c9eda3aec0aadcf9a662d51e348b804`.
- Selected manifest SHA-256:
  `1f33866867c3385d817776b9afa179751ab669ca280ddab76e8d2080f7b0a08b`.
- Client **0.1.0a6**, contract `aware.agent.fs.v1` **1.2.1**. One agent wheel
  changed from a5; the other 21 wheel bytes match. No new dependency/domain owner.
- Historical a5, old contracts and the separate Goal reader are preserved.
  No archive/wheel rebuild is performed in this delivery cut.

## Delivery procedure and status

Remote main was read back at `8ecf22d67b834ece5aa845171c70344b2069411e` before
delivery. Fetch and require it to be an ancestor immediately before a non-force
push. Inspect the outgoing range: accepted a6 source, artifact, review records,
local alignment and this governed delivery cut only. No unrelated development
lane or private client artifact is included.

Status: authorized delivery preparation. Local selection alone is not public
availability. After push, read back the exact remote head; anonymously retrieve
the revision-pinned public archive and manifest and match their accepted hashes.
Acquire a separate public checkout for the harness, then freshly install those
public bytes offline with producer/public checkouts hidden and environment cleared.
Record actual receipts and results here; do not reuse an old fresh-install claim.

This is producer public-delivery evidence, not external U/V/R, a reproducible
build, exhaustive public-safety clearance, authenticated identity, sandbox,
Goal/Specification acceptance or service authority. Public instructions remain
honest about pending reconciliation, unchecked acceptance and unsupported writers.
