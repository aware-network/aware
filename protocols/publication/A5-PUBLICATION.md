# A5 public selection and delivery

Date: 2026-10-05. Execution: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`.
Owning [Issue](../../docs/issues/2026/10/05/fb-2026-10-05-a5-publication.md).
Luis explicitly authorized promotion, aligned instructions/bootstrap and
non-force publication to `aware-network/aware/main` in this task.

## Accepted input, unchanged payload

Independent review accepted candidate `81929f50acf8` and reproduced 222
installed tests and 28 accounting/layout checks, zero skipped. Candidate
closeout: `b5fa86f917e4`. See [the candidate receipt](../agent/A5-CANDIDATE.md).

- Exact archive SHA-256:
  `0e6a2c98a0d8c691b7078ab48194363971d547689514b5c8fa3a3d2f7ccc9184`.
- Selected manifest SHA-256:
  `dea4c561c37f557dbb9012838522f4e96d076b323e220e164eba7e24c3442bc0`.
- The selected manifest exactly equals `release-a5-candidate.json`; the archive
  was not rebuilt, and no wheel or domain source changed during promotion.
- Historical [a4 manifest](../agent/release-a4.json) SHA-256:
  `a3e57d5e430cbc37194b9a16a264961e07e17781493703e8fd4ca5b44415a6c0`.
  Its archive and all earlier published contracts remain unchanged.
- 22 packages, 35 active requirements; four versioned wheels changed from a4
  and the other 18 are byte-identical. Only neutral source is present.

## Deliberate public experience migration

The public bootstrap explicitly migrated from 1.0.0 to the reviewed authored
`aware.agent.fs.v1` / 1.2.0 through the scoped renderer. Packaged contract bytes
already matched the candidate and were unchanged. This is a producer-approved
repository migration, not an automatic upgrade of customer installations.
`docs/alignment/CURRENT.md` is then an approved authored context amendment;
its initial-render hash is setup provenance, not an immutable strategy record.

This execution retained its explicitly selected installed a4 governance command
for the already admitted publication Issue. Its initial content was recorded by
supported append-update before migration; no manual Issue edits or retroactive
claim of a5-authored content was made.

The current quickstart requires real approved problem/objective/acceptance
inputs at open. The owner writes them; acceptance starts unchecked. Summaries
reuse the shared implementation and retain publication state, actual receipts
and operation-specific index evidence. Full SDK JSON remains the default.
No new acceptance evaluator or repository commit engine was added.

The existing exporter now supports `--refresh-readme-only`: it verifies all
other 105 projected outputs against the pinned envelope before writing the
README and its receipt. Source drift refuses before either write. This avoids
rewriting unchanged source while maintaining the inspectable original 106-output
Goal publication receipt. The separate Goal payload remains untouched.

## Verification and delivery status

Promotion checks: **57 passed, zero skipped** (18 selected-bundle accounting
cases including inherited baseline cases, 10 source-layout cases, 13 publication/
bootstrap-projection cases and 16 evaluation-validator cases). This is a replay
against the retained a5 installation, not another fresh-install claim. All six
quickstart shell blocks pass Bash syntax checks. `git diff --check` passes.
JUnit: `/tmp/aware-a5-candidate.CIusBO/promotion.xml`, SHA-256
`ee8da69036f18e12b3e3d4e0b907da458b161d1b0e55ece89d8f7e4b0391483a`.
README receipt SHA-256:
`b091567712948380996ce3ba8df533399429adbd27dd623994c9b87c07e6a2b9`.
All 106 outputs match; only the README output changed from the prior receipt,
along with the explicit exporter implementation hash. No Goal source changed.

Public delivery replay is recorded below as it completes. Selection alone is
not remote delivery.
Remote main was observed at `415460aa8118add0fb86601ff2377d6dc96d1d22` before
promotion. Ancestry must be rechecked immediately before a non-force push.
After publication, anonymously retrieve the revision-pinned archive and match
its exact digest, then freshly replay installation with checkouts hidden,
networking disabled and inherited environment cleared.

No registry release, independent rebuild, exhaustive rights/privacy review,
external a5 U/V/R acceptance, authenticated actor identity, sandbox, Goal writer,
automatic interrupted-unborn recovery, Service/API or Experience is claimed.
Applied publication with pending reconciliation is debt, not a clean checkout.
