# Unselected admit-runtime successor: local integration checkpoint

Status: local integration checks passed; independent review pending.
This is not public selection, frozen instructions or remote publication.

Execution: `codex-01a11141-c779-7971-8d1a-ef573f044314`.
Issue: [fb/2026-10-06/specification-admit-runtime-local-integration-v1](../../../../docs/issues/2026/10/06/fb-2026-10-06-specification-admit-runtime-local-integration-v1.md).

## Exact local change

The accepted layout was applied to baseline
`0b8710e7c0afb71df8f73685fc22f0632f74d722`, using the explicitly selected,
previously qualified installed a6 client (`0.1.0a6`, contract `1.2.1`).
The PATH `aware` desktop launcher was not used. Actor evidence is the declared
genuine harness execution, not authenticated identity or resident authority.

The unchanged [layout receipt](layout-review.json), SHA-256
`0d84be1c9eca5cc7d9f4104d24ba4810f48668b8dac0ffa32965c07a5cee2b3a`,
binds exactly 446 projection paths: 444 additions and two existing README changes.
All 439 packet members retain their accepted hashes. The original distribution,
payload, sources, legal files, installer and verifier remain byte-identical.
Only this checkpoint, its maintainer test, the receipt copy and the tooling-owned
Issue are added beyond that reviewed delta.

Before projection, every manifest preimage/absence and staged postimage was
checked. Only the listed paths were copied from the accepted generator output;
no directory-wide overlay was applied. All 998 other baseline files retain their
bytes, and all 1,000 pre-existing files retain their actual local POSIX permissions.
The local preimage byte-and-mode index SHA-256 is
`561414a6e0e85a8d5fb6923395d7b6c98f251e459fb1d8f046ce8eaefdaf07e8`
(the after-write comparison permits only the two approved README postimages).

Git archives retain executable state rather than complete local permissions:
some Issue files are locally 0600 but appear 0664 in the prepared archive-based
tree. Those unrelated files were not copied or chmodded. The maintained replay
checks committed bytes and Git executable state; the immediate integration
comparison additionally checked complete local permissions.

## Recorded verification

**Nine integration checks passed, zero skipped.** The final replay performed a
fresh offline installation from the actual integrated checkout, with the entire
producer home, unrelated temporary files and inherited environment unavailable.
Both supported CLIs activated. All 27 payload packages were present, dependency
checks passed, no direct-URL/editable records appeared, and reuse refused with
exit 2 without changing scratch-parent permissions. Ruff lint/format and Git
whitespace checks also pass. No wheel, payload or domain runtime changed.

Final JUnit SHA-256:
`a59a9a2dc82e2bcc6c56d9f822cb81a0438dfed97d3eb8854368276a10aad4b3`.
Final installed receipt SHA-256:
`96f1803c54bbf388e85630ff0bc08a8b17f52f77356df80717045c0786fbf678`.
These are producer integration receipts, not external evaluation or independent
acceptance. Their private scratch coordinates are not consumer dependencies.

The initial run recorded eight passing checks and one failed string assertion:
the test incorrectly expected bold version formatting in the unchanged historical
selection table. Installation succeeded in that run. The assertion was corrected
to the actual pinned table row; the selected document was not edited. Initial
JUnit SHA-256: `039b4740fd52fecf0de07c6b96e32403daa1591e18371181f54d481d81ac2961`.
An intermediate successful replay preceded strengthening namespace hiding from
the producer home directory to all of `/home`. The final replay above covers
that exact maintained test. Repeated fresh runs are nine distinct checks, not
27 distinct proofs.

Two initial read-only projection probes refused locally before any source copy:
one incorrectly compared complete archive permissions with local permissions;
the other read scope at the wrong projection field. The actual integration then
used the owner's `content.ownership_scope`, checked all preimages, and left
unrelated local permissions untouched. No refusal was bypassed or counted as a
passing owner operation.

## Applied local repository receipt

Implementation commit: `2604819adab6db917e5443f991f2af843cf02a26`.
Publication receipt: `git:2604819adab6db917e5443f991f2af843cf02a26`.
The selected a6 client called `aware_workspace_operator.run_workspace_commit.v1`
after the identical dry-run. Transaction mode: `isolated_index_atomic_ref_v1`;
reference update: `cas_applied`; shared-index projection: `applied`;
index reconciliation pending: `false`. The applied request covered 450 exact
paths, including the Issue. This is local Git publication, not a remote push.

After recording the detailed verification, eight accounting checks passed again;
the independently counted ninth installer case had already passed in its fresh
final installation and was explicitly deselected from that repeat. The Issue
remains In Progress for independent local-integration review.

## Versions and unchanged boundaries

This candidate offers Protocol CLI 0.3.1 and SPEC CLI 0.2.0 in a separate
27-package installation. Only `aware-protocol admit` adopts the existing neutral
command runtime 0.1.1. No domain implementation, SDK binding enforcement,
provider resolution or authority is added to generic dispatch.

Existing a6, root bootstrap/manifest, Goal preview and the already selected SPEC
0.3.0 / 0.2.0 entrance remain unchanged. The [successor entrance](README.md) and
its attached historical instruction drafts remain unselected and unfrozen.
The receipt's review-pending fields and earlier README review language are retained
construction evidence, not rewritten release approval. Contract 1.3.0 stays
unallocated. No combined environment or `aware spec` wrapper is selected.

Setup creates admitted directories and manifest binding only. Reading requires
qualified existing SPEC inputs. Authoring/import, approved iterations, durable
iteration-to-Issue binding and protected publication remain unavailable.
Currentness checks observed state, not every write; confinement is cooperative,
not continuous. Prior bounded source/notice acceptance is carried unchanged;
it is not a legal warranty, exhaustive secret scan or exact binary-linkage proof.

## Maintainer replay

Use a full Git checkout containing the pinned baseline. Create a fresh private
0700 scratch directory, set `AWARE_ADMIT_INTEGRATION_REPLAY_ROOT` to it, and run
the [maintainer test](test_local_integration.py) with Python 3.12. Linux x86-64,
Bubblewrap and mount-namespace support are required; missing prerequisites are
failures, not skipped installation acceptance.

The actual installer replay hides all of `/home` and unrelated `/tmp`, disables
networking, clears inherited environment and mounts this public tree read-only
at `/mnt`. Only its approved scratch is writable. Logs, retained source/notices
and `installed-receipt.json` stay in scratch. This replay tests the integrated
installer and activation, not another 262-case domain matrix.

Next: independent review of this local checkpoint. Selection/instruction decisions
and any authorized non-force public delivery are separate operations.
