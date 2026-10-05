# A6 external evidence triage and evaluator-tooling checkpoint

Status: bounded source/docs checkpoint accepted by the independent review relayed
by Luis; no remote delivery or product release follows.
Owner execution: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`.
Issue: `fb/2026-10-05/evaluation-evidence-tooling-v1`.

## Input, not product authority

The input is the immutable external evaluation at private evidence-archive commit
`9bdc8a38655a11a78920b75091b1f8918c45838c`, coordinate
`evaluations/2026/10/05/aware-a6-greeting-codex-01a10da5-7e66-7b22-a5d3-84aff2e6fa29-sanitized`.
Maintainers with archive access can inspect it; the private archive is not a
customer dependency or a public source/download coordinate. No raw customer
source, private helper or evidence artifact is copied into this checkpoint.

The producer independently fetched that coordinate, matched candidate pins to
selected public a6 and ran the unchanged v2 validator: **23 artifacts, 145
interactions, 18 findings; valid**. This checks shape, digests and references,
not truth, input isolation, authenticated identity or customer operation replay.
It is external evidence, never repository/Issue authority or release acceptance.

The reported 18 findings comprise 11 strengths, two documented-behavior/clarity
observations and five evaluator evidence gaps—not 18 runtime failures. Reported
I/U/V/R completed with real refusal receipts and a distinct recovery execution;
we did not independently rerun those customer operations. Two disclosed
coordinator corrections occurred outside U, so this is not an intervention-free
or native Aware orchestration claim. The handoff is planned blocked-work recovery,
not independently established crash/lock recovery.

## Bounded response

Keep a6 selected; no reported product regression requires a new runtime candidate.
The helper addresses the evidence gaps without replacing any domain owner:

- F-014: separate deterministic freeze whose checksum list excludes itself;
  original U evidence stays unchanged.
- F-015/F-017: arrange capture before identity/discovery reads; durable start,
  exact private argv and actual timestamps. Missing historical data stays unknown.
- F-016: null-safe private receipt projection; no operation replay to repair
  display/logging; partial starts/effects remain explicit.
- F-018: constructed allowlisted metadata export, no inline source/patch/raw
  output copying by default or opt-out. Extra public text requires separate review.

Actual interpreter probes and same-execution/pass/path links preserve provenance
instead of inferring task Python from the installation or another execution.
This standard-library tooling is optional, Linux-only and outside the installed
22-package a6 closure. It is not a new SDK, product command, workflow authority
or complete submission generator. Public evaluation v2 remains unchanged.

## Verification

Linux / Python 3.12.3; tests use synthetic inputs, not private client artifacts.

- **42 helper tests passed, zero skipped**, including first-command start,
  null refusal projection, applied effect followed by logger failure, no duplicate
  replay, process serialization, special-file refusals, deterministic separate
  freeze, payload omission and same-execution/pass/path interpreter links.
- **70 adjacent checks passed, zero skipped**: 16 existing v2-validator cases,
  35 publication/alignment/layout cases and 19 bundle-accounting cases (including
  the imported historical base suite). This is not a rerun of the 224 installed
  product tests or a fresh customer evaluation.
- Ruff passed for the two new Python sources; scoped `git diff --check` passed.
- A standalone `/usr/bin/python3.12` CLI replay captured its actual interpreter
  and ran all 42 helper tests, then froze the same private input twice and exported
  metadata. Both snapshots matched. The synthetic replay uses pass label V only
  to exercise the metadata interface, not to claim an external V evaluation.

Reproduce the source tests from the public root:

```sh
/absolute/aware-env/bin/python -I -B -m unittest discover -s protocols/evaluations/tooling -p 'test_*.py' -v
/absolute/aware-env/bin/python -I -B -m unittest discover -s protocols/evaluations/v2 -p 'test_*.py' -v
/absolute/aware-env/bin/python -I -B -m unittest discover -s protocols/publication -p 'test_*.py' -v
/absolute/aware-env/bin/python -I -B -m unittest discover -s protocols/agent -p 'test_a6_bundle.py' -v
```

Retained source and replay hashes (SHA-256):

| Input/result | Digest |
| --- | --- |
| `tooling/evidence.py` | `e5df8ea5e7e684db9389088d797ed3ff1498909f888870b3a876301b9b5658bc` |
| `tooling/test_evidence.py` | `2c50e39e2f3baedcc00fac5705257660c6cbe5a7ee6992619ee1d9a925c43972` |
| Standalone helper-test stderr | `e533936f4bd9e87b810d94ee9e9f4e6965ed2d2ebd2cf4ceb42b1bb913153ad7` |
| Standalone metadata export | `641f72e155d0938c218a6864eaea1c75f77c9061993d36094dd76b9d284b394d` |
| Both private deterministic snapshot archives | `cd7f6b36c897ae1b05b592883126f25c59f852b8649573cfb26e19c7e5c3b335` |

Replay artifacts are retained locally, not attached as public customer evidence;
the snapshots include raw private command coordinates and are not export inputs.
Synthetic source tests are the supported independently replayable proof.

The selected a6 manifest remains
`1f33866867c3385d817776b9afa179751ab669ca280ddab76e8d2080f7b0a08b`;
its archive remains
`c3d6e593fd5894a927d338da5347a32e9c9eda3aec0aadcf9a662d51e348b804`.
No installed product, historical contract, owner source or v2 schema changed.

Independent review accepts source `d296cc4be9a0` and handoff `4f707fc4d376`,
reproducing 112 helper/adjacent passes. Its limits are unchanged: no independent
customer-operation replay, a6 payload change or push.

Next: separately authorized public documentation/tooling delivery.
New external evaluations can consume
the optional helper without a product-runtime upgrade. SPEC stays on its separate
owner path and will need its own candidate/integration proofs when ready.

No bundle rebuild, promotion, public transfer, push or release is authorized by
this checkpoint. SPEC/Workflow owner paths and native capabilities are unchanged.
