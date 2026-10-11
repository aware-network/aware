# Draft preparation local selection

The independently integrated whole-envelope successor is selected locally against
incoming revision `36fe95aeac603df8a36fd0ff1028701faaf0a369`. Instructions remain
draft; public delivery is not authorized. [SELECTED.json](../SELECTED.json) binds
accepted artifacts, not a package catalog or operation authority.

Execution: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`.
Issue: `fb/2026-10-11/canonical-draft-preparation-local-selection-v0`.
Contributor governance remains unchanged a6 / contract 1.2.1; the successor does
not publish itself. Original typed Issue and Workspace publication receipts are
retained separately. Actor evidence is harness-declared, not authenticated.

## Exact bindings and preservation

Whole envelope: `3e1fab9a79c19476ece55a1f0d62aa7784e911d52a01d32b65655617bacdb9f8`.
Payload: `f2ef55bd871ee054e2f707189537ea533c46d013e8fdbc676a830f9968b94513`.
Source index: `ebbbb117031c1e8dde82ee3ade6d2b9c1bc26c880808d003315105c646c8e0b7`.
Workspace `portable_protocols` remains the sole selector: 26 Aware packages and
1,057 committed sources; forty reachable packages in one installation.

The eight-file selection scope changes five presentation/pointer files and adds
its Issue, this ledger and the maintainer test. All 1,196 unaffected baseline files
and all 1,201 baseline executable modes must remain exact. Software, installer,
sources, notices, audit, preparation workflow, predecessor releases and contributor
bootstrap are unchanged. The prior pointer is recoverable from the incoming Git
revision. Six detached-wheel legal gaps and twelve raw findings remain visible;
whole-envelope carriage is required, never detached or stripped acquisition.

## Verification and independent review

The maintainer test checks exact scope, every baseline byte/mode, delivery bindings,
contributor/predecessor preservation, authored links and status-only root changes.
It delegates fresh installation to the unchanged integration smoke, hash-pinned
at `98209f8845fa18d90042791e7a3df721e1115060328dc374a67a161b56284596`.
That smoke hides checkouts and inherited environment, disables networking, verifies
forty versions and dependencies, and checks missing-identity and reuse refusals.
It does not repeat preparation, the domain matrix or unassisted evaluation.

For independent replay, choose a new private scratch directory; never reuse an
installation target or relax the original guards:

```sh
set -eu
selection_scratch="$(mktemp -d /tmp/aware-draft-selection-review.XXXXXXXX)"
AWARE_INITIALIZER_INTEGRATION_REPLAY_ROOT="$selection_scratch" \
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m pytest -q -p no:cacheprovider \
  releases/canonical-draft-preparation-fs-v1/test_local_selection.py \
  --junitxml="$selection_scratch/selection.xml"
```

Seven checks passed, zero skipped, including fresh offline, checkout-hidden
installation of all forty packages, clean dependencies and no editable/direct URLs.
Missing identity refuses with no effects; reuse refuses and private-parent mode
remains 0700. Six overlapping accounting/link-fragment checks pass with installation
explicitly deselected after strengthening authored fragment resolution. Lint,
formatting and scoped whitespace pass. Software and the pinned installation smoke
remain unchanged; no workflow or full domain matrix is replayed.

Private proof: `/tmp/aware-draft-local-selection.mw5twbTQ/selection.xml`, SHA-256
`81abad5e423842aa5f67adf9e053ac80a2cbe7fa366699b9fbf9937def70a4f5`.
Installed receipt: `/tmp/aware-draft-selection-installed.ewDzQgLi/installed-receipt.json`,
SHA-256 `1a94993d9fb378b6a0d80fcd8d0dc1cb6bd4440963b7be53893d939233955b52`.
These are proof coordinates, not public acquisition prerequisites.
Original publication receipts follow after governed dry-run and identical apply.
Independent bounded review remains pending. Local selection does not freeze
instructions, establish unassisted onboarding or authorize transfer/publication.
