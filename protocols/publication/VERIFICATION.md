# Filesystem Goal reader OSS preview verification

Publication target: `aware-network/aware`, early read-only preview dated
2026-10-05. This is a Git consumer overlay, not a WorkspaceRevision or a
registry release. The canonical exporter is `export_preview.py`; its receipt
binds generated outputs. The protocols-only cut retires the old infrastructure
README from the current tree; it remains in Git history.

## Immutable inputs

| Input | SHA-256 |
| --- | --- |
| Source-attached envelope | `10b126383498b4e4561109f5eb8059161b2c03546d19065b85506f4c41a29c21` |
| Installed 13-wheel payload | `02dfda3a5ad1c3d85fd4c317dc392a867d24cc852001fa75394f90d1245456f1` |
| Source capsule | `9abe97d23565e86954b092cf361ab6cf651fef11605789bb5794d49d9a9408c7` |

The unchanged payload previously passed an independently reviewed installed
matrix of **43 Protocol + 41 Goal cases**, with checkout hidden, network
disabled and environment cleared. These are prior candidate-bound receipts,
not 84 new executions claimed by this publication. Current-epoch rejection
remains unsupported; writer-syntax refusals demonstrate absence, not policy
enforcement. The exact source/notice envelope separately passed independent
byte/content review before this OSS cut.

## Current publication checks

- Ten standard-library publication tests: outer and nested checksum coverage,
  70 wheel-source matches, 106 current exported output hashes (107 in the first
  overlay before retiring the infrastructure README), pinned exporter hash,
  13 wheels/seven Aware packages, no benchmark members, and acquisition-wrapper
  refusal of tampering, traversal, absolute paths, links, duplicate members,
  multiple roots and incomplete checksum coverage.
- Fresh installation through the public wrapper under a filesystem sandbox
  with the Aware development checkout hidden, networking disabled and inherited
  environment cleared. Explicit CPython 3.12 selected all 13 payload packages;
  dependency and CLI activation checks passed.
- A bounded scan of the newly published source/documentation found no Aware
  private checkout/client path or selected credential pattern. This is not an
  exhaustive privacy/rights guarantee. The retained upstream publisher CI path
  in the `rpds` SBOM is not an Aware-private path and is preserved.

The sample is generated through the installed neutral Goal codec and committed
as explicitly synthetic input. Its read-only replay passed against committed
revision `f43e16a2ff06c66cb9900d0fc05f78f484ec1f89`, with networking disabled,
the development checkout hidden and the environment cleared: all four command
forms succeeded, eligibility was `eligible`, currentness was `current`, and
HEAD, index hash, worktree status and Goal bytes were unchanged. This is not
customer Goal creation/import.
Any subsequent replay must use the sample's committed revision rather than
manually rewriting Goal authority.

Exact replay output hashes (not a substitute for rerunning the operations):

| Output | SHA-256 |
| --- | --- |
| Discovery request | `4f3d654e63bbc260e1772b1c441b2c98c3f04233d89adda5fef12dca8c04fc8d` |
| Eligibility | `c537fb0721798bf2db39865908f4a084eda31e36d4a71da9fdbe86aea577f172` |
| Direction | `7266eaeb84a08b563cfc5681c87bba238baf6f2db0f99311f2e9c5199f5a93f7` |
| Currentness | `01708aeb4497366b39232fa2a28eac70dde7ca877e17a9b651b1d6294220680d` |

The first installation diagnostic failed because its sandbox accidentally made
`/dev/null` unwritable after package installation. The successful result above
used a **fresh target** and a corrected device mount; no payload byte changed.
Initial sample admission correctly refused a missing required Issue authority
binding. The sample manifest was corrected through the governed commit; the
installed admission/evaluation logic was unchanged.

## Public preparation decision

Luis explicitly authorized protocols-first public Git publication on
2026-10-05. The selected public scope is this **read-only preview with synthetic
demo and already-qualified-input consumption**, not the formerly held claim of
a self-serve complete collaboration product. The public source coordinate is
this repository's attached/extracted capsule. Previously reviewed C-R/C-S
notice bytes accompany the exact archive; the benchmark fixture is absent in
this candidate. This advances the explicit, bounded public audience decision
without asserting a new rights opinion or an unimplemented customer authoring
capability. Filesystem-only is the delivered authority mode.

Replay publication checks:

```sh
python3.12 -B -m unittest discover -s protocols/publication -p 'test_preview.py' -v
python3.12 protocols/demo.py --cli /absolute/new-venv/bin/aware-goal-native
```

The repository publication Issue retains the final committed-sample result,
non-force push receipt and independently fetched public-byte verification.
Legal/source attachments accompany the distribution. No wheel rebuild,
reproducible binary build, public legal opinion, complete collaboration loop,
customer authoring, approval, dispatch or Service/API capability is claimed.
