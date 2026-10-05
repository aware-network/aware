# Filesystem Goal reader OSS preview verification

Publication target: `aware-network/aware`, early read-only preview dated
2026-10-05. This is a Git consumer overlay, not a WorkspaceRevision or a
registry release. The canonical exporter is `export_preview.py`; its receipt
binds generated outputs and preserves the earlier infrastructure README.

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
  70 wheel-source matches, 107 exported output hashes, pinned exporter hash,
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
as explicitly synthetic input. Its read-only replay is checked separately after
the governed implementation commit; it is not customer Goal creation/import.
Any subsequent replay must use the sample's committed revision rather than
manually rewriting Goal authority.

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
