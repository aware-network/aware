# Canonical initializer — local integration

Status: bounded local integration independently accepted. Nothing in
this record selects a consumer version, freezes instructions or authorizes push.

## Exact inputs and effects

- Incoming public main: `f760ac28066191e50ba12d249928c0fd553f79b4`, independently
  acquired into a new private checkout. Retained dirty and clean checkouts are
  not projection targets.
- Accepted layout receipt: `31ffd2ea0c41d76a01e7bec728640ba2e18f0e48fd0913d724a01d300b52b2a1`.
  Its 1,086 files, all source bytes and Git executable modes remain exact.
- Whole-envelope SHA-256:
  `5f0edebe568d1cfd8a06a33e6122cd4e0d3dd68f764058b1aa098456cc2df13c`.
- Accepted payload SHA-256:
  `2d812c489485ee187cf45fca012fffdfda5fcdf93d60495a02b843f94e4a8b68`.
- Exact mechanical projection: 1,008 file writes and 4,011 tracked-file
  retirements. All prior files remain recoverable from the incoming revision.
  Of 2,360 explicit empty-directory candidates, 2,358 were removed; two Issue
  ancestors remain because they contain this task's newly admitted Issue.
  No recursive removal or foreign-content deletion was performed.
- Five integration extras: the tooling-created Issue, accepted layout receipt,
  generated integration plan, this record and the maintainer integration test.
  The plan is evidence derived from the accepted layout, not a package selector
  or source-write authority.

Contributor governance remains the retained installed a6 command and contract
1.2.1. The 40-package initializer installation is a separate proof target; it is
not a silent contributor CLI replacement. Source effects are
`provider_native_compatibility`, not invented Workspace CAS receipts.

Publication is a bounded sequence through the original Issue/Workspace owner.
Its `Owned-Paths` message argument cannot safely carry all 5,024 paths at once.
The exact plan partitions those paths into 13 disjoint batches, each below
48,000 UTF-8 path bytes, with the Issue in the first batch. Each batch requires a
fresh Issue observation and an identical dry-run/apply pair. This is not an
atomic migration; any incomplete receipt requires inspection, not blind retry.

All 13 implementation batches returned `outcome=applied`,
`reference_update=cas_applied`, `shared_index_projection=applied` and
`index_reconciliation_pending=false`. Final migration receipt:
`git:dcc76b861887df78762690751929c3b2508466be`. The worktree and index were clean
after that receipt. Independent acceptance is recorded below.

Raw diagnostic command:
`git diff --check f760ac28066191e50ba12d249928c0fd553f79b4 dcc76b861887df78762690751929c3b2508466be`.
It returns exit `2`, one finding in the exact accepted committed-source README
at `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/contracts/semantic_target/v1/README.md`.
Raw stdout SHA-256:
`ec1a96bbd4eca24dbcb701aa1f10a53057c5ede6d2bcb7ff2ec4b49e99a2ee19`.
That source byte sequence is retained, not normalized. Authored integration
extras are checked separately; a full-diff whitespace PASS is not claimed.

## Reproduce integration accounting and installation

From this repository, use a new private scratch directory and the producer's
installed pytest command (not a new consumer dependency):

```sh
initializer_replay="$(mktemp -d /tmp/aware-initializer-integration-replay.XXXXXXXX)"
chmod 700 "$initializer_replay"
AWARE_INITIALIZER_INTEGRATION_REPLAY_ROOT="$initializer_replay" \
  python -B -m pytest -q releases/canonical-initializer-fs-v1/test_local_integration.py \
  --junitxml="$initializer_replay/integration.xml"
```

The eight checks compare accepted layout bytes/modes, exact retirement and
pinned history, disjoint publication batches, bootstrap/contributor authority,
the one committed profile source home, complete envelope attachments, guidance
and a fresh offline installation. The installation uses Linux `bwrap` and
Python 3.12, hides `/home`, `/root` and unrelated `/tmp`, clears inherited
environment variables and disables networking. It checks all 40 package
versions, dependencies, no editables/direct URLs, retained source/legal inputs,
command activation, missing-harness refusal without effects and reuse refusal.
An absent prerequisite is a replay blocker, not a reason to substitute source
imports or fabricate a harness execution.

The source guards are separately replayed in the implementing repository. No
domain matrix, actual customer onboarding, U/V/R or service startup is claimed
by these layout checks.

## Carriage and limits

Implementer replay: **eight integration checks passed**, including the fresh
offline installation, and **19 projection/owner-delegation guards passed** in
the implementing repository. These are local technical receipts, not an
independent acceptance. The installation did not repeat the earlier 2,098-case
domain matrix or execute an unassisted customer workflow.

Private integration JUnit: `/tmp/aware-initializer-public-integration.GaSgT0dX/integration.xml`.
Private installed receipt: `/tmp/aware-initializer-integration-install.5raz0Kk2/installed-receipt.json`.
Private guard JUnit: `/tmp/aware-initializer-public-integration.GaSgT0dX/guards-final.xml`.
These maintainer evidence coordinates are not customer source prerequisites;
the replay above produces independent receipts without those paths.

The complete envelope, 1,023 committed sources, notices, corresponding-source
treatment and raw audit remain exact. Six package-local legal-file gaps remain
visible; accepted whole-envelope carriage does not clear detached wheels.
All twelve relative-fixture audit findings remain visible without suppression.
No wheel-only acquisition is advertised.

Natural-language guidance, tooling installation, repository preparation,
Protocol configuration and service startup remain distinct. New-repository
preview provides a Workspace preparation preview and prospective Protocol
inputs, not two admitted plans. Apply obtains fresh Protocol admission after
repository preparation. Default bootstrap prepares Issue configuration; it
does not commit, stage, set a remote, open an Issue, approve a SPEC or start a
resident service. Guard discovery and unassisted onboarding remain unfinished.

Instructions remain draft. Selection, contributor migration, public delivery
and publication are separate decisions.

## Independent local integration acceptance

The independent reviewer accepted aware-dev checkpoint
`3ca43e1bbd958dee53ce8d00f9c8fa993cb0605d` and public handoff
`0a7431742155cb6ab578b6c1b0ba7272ea598bfa` without a bounded integration blocker.
Nineteen guards and eight integration checks reproduced, including a fresh
offline, checkout-hidden installation of all 40 packages.

Independent JUnit: `/tmp/aware-initializer-integration-review.fPMk135p/integration.xml`;
SHA-256 `c05f7f79f812495560ab99438d5c6d2a060d32d74a5f13704b41359cc1c1d875`.
This private maintainer evidence is not a customer installation prerequisite.

All 1,086 accepted files retain exact bytes/executable modes. The reviewer
matched all 4,011 retired files to recoverable pinned-history bytes/modes and
all 13 publication batches to actual deltas, Issue scope and receipts. No index
reconciliation is pending. Contributor authority, complete source/notice
carriage and the raw audit remain unchanged. The known source-whitespace
finding reproduces exactly; no full-diff whitespace PASS is claimed.

Acceptance remains whole-envelope-only; six detached-wheel legal gaps are not
repaired. This does not repeat the 2,098-case domain proof or establish
unassisted onboarding. No test, installation, source payload, selection or
push occurred while recording this acceptance. Bounded Issue closeout follows
through the original owner; local selection and instruction alignment remain
separately governed.
