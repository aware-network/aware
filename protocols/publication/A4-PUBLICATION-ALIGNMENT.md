# A4 publication alignment and readiness

Date: 2026-10-05. Execution: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`.
Authority: filesystem; selected producer compatibility CLI retained for this
execution. Customers use installed `aware`. Owning
[Issue](../../docs/issues/2026/10/05/fb-2026-10-05-a4-publication-template-alignment.md).

## Exact candidate and observed baseline

The reviewed local public checkout was
`a50f333521cd8704898f8754ff8b1d1dddc1db9b`.
Public `aware-network/aware/main` read back as
`3788e93639c7569926db548168d7e965ba44fe22` during this cut.
Local selection is not evidence of downloaded public a4 delivery.

- Archive: `aware-agent-fs-0.1.0a4-linux_x86_64-py312.tar.gz`.
  SHA-256: `52109f772692071681570e59a161ced33ac6606ff2effdff4fa2094cd4c58cbe`.
- Selected release manifest SHA-256:
  `a3e57d5e430cbc37194b9a16a264961e07e17781493703e8fd4ca5b44415a6c0`.
- Candidate source: `cb8c93594783cfdd56f392b6e65aea0d9f07ced0`;
  candidate checkpoint: `178f4be3eada5483f971ee1a6e2d6ed625c2f761`.
- 22 packages; 17 a3 wheels unchanged, five separately versioned adopted wheels.
  See [candidate verification](../agent/REPOSITORY-A4-VERIFICATION.md).

## Review and bounded correction

Before this correction, independent replay freshly installed the exact a4
candidate offline, with the development/producer checkouts hidden and inherited
environment cleared. **177 installed/evaluation checks passed, zero skipped**:
121 owner tests, 40 bootstrap/setup/workflow/repair tests and 16 evaluation-validator
tests. Another 18 accounting/source checks passed. Installed JUnit SHA-256:
`849f940c98d44972e183ec5cb0333d114679a31066f7483200b96df2225bea51`.

Publication replay separately failed 1 of 10 tests: the 6,871-byte promoted
README no longer matched its 6,573-byte template and receipt. The canonical
exporter would have restored older instructions. This is a documentation
projection defect, not a wheel or repository-owner failure.

The authored template now equals the already reviewed promoted root README.
The named exporter regenerated its receipt through:

```sh
python3.12 -B protocols/publication/export_preview.py \
  --envelope protocols/distributions/aware-goal-fs-preview-linux_x86_64-py312.tar.gz
```

The exporter uses its adjacent `source_layout` helper. An initial isolated
`-I` invocation could not import that helper and refused before writing anything;
the invocation above uses the existing supported script entrance. No generator
implementation, installed operation or domain source changed.

All **106 output hashes** were verified. Only the README entry differs from the
previous receipt; the other 105 outputs are unchanged. Root README SHA-256:
`4011fc7ed3f9b9becfede64471891245071a8a7ddf8d893becbd236ebc7417ef`.
New [receipt](receipt.json) SHA-256:
`a0b0bd250fc786554640b699b80091f4e96696054c0854ea69091634a4d8d835`.

The publication test now compares the template with the root README, preventing
unrecorded template drift. Current workspace/alignment guidance distinguishes
selected a4 from historical public a3 proof and later external U feedback.
Historical receipts and the earlier closed adoption Issue were not rewritten.

## Focused verification

Against the unchanged installed a4 environment, this correction replayed:

| Suite | Result |
| --- | --- |
| `protocols/publication/test_preview.py` | 10 passed |
| `protocols/publication/test_source_layout.py` | 10 passed |
| `protocols/agent/test_bundle.py` | 8 passed |

Combined JUnit: **28 passed, zero skipped**. SHA-256:
`ccef703fa4fac67e41417008f7549e0c65f365ae7d8ccfa2d88d375628326bc1`.
These are this repair's focused checks, not a second fresh installation or a
repeat of the 177-case installed replay. `git diff --check` passes.
The accepted archive, selected manifest, bootstrap, contracts and historical
archives were checked against baseline committed bytes and remain unchanged.
No wheel was rebuilt; no package, legal text, evaluation submission or shared
development owner was changed.

## Handoff and limits

Ready for separately authorized **non-force publication to
`aware-network/aware/main`**, after exact scoped commit/closeout. Verify the
outgoing range and remote head again before push, then retrieve the revision-pinned
public archive anonymously and check its exact digest. Record delivery separately
and replay from the published checkout; this record does not claim that happened.

Successful local publication can retain pending index reconciliation; absent
historical fields mean unknown, not clean. Conflicting owned staging remains
explicitly pending and foreign staging is preserved. Automatic recovery after
interrupted unborn publication is unsupported. The Repository SDK remains
preparation-only: publication uses the existing Issue adapter and shared owner;
full public Repository SDK convergence is not claimed.

Root bootstrap remains 1.0.0; new-customer contract remains 1.1.0. No authenticated
actor identity, hostile-process isolation, Goal writer, Service/API, ontology/ORM,
Experience, external a4 U/V/R acceptance or registry release is admitted.

**No push, public download, transfer or new release authorization occurred in
this preparation cut.** Final implementation/closeout revisions are retained in
the owning Issue, not inferred from a transcript.
