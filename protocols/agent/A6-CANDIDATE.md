# a6 feedback correction — candidate checkpoint

Status: producer technical checkpoint, pending independent review, not a
promoted customer release. Published a5 and
the root bootstrap remain selected and byte-identical to public revision
`8ecf22d67b834ece5aa845171c70344b2069411e`. No Specification capability is added.

Input: [the immutable a5 client evaluation](https://github.com/aware-network/aware-client-evaluations/blob/984d99987b1fe1ff629f954e51cfbeeaeab2da12/evaluations/2026/10/05/aware-a5-greeting-codex-01a10d1b-7bc6-7731-8789-216a58845dde/evaluation.md).
Its v2 submission independently validates: 20 artifacts, 108 interactions,
12 findings. Validation establishes format/references/digests, not a reenactment.

F-001–F-008 report strengths and remain historical client evidence. F-009 is a
reproduced label defect: a5 metadata/root say 1.2.0, its modular index says 1.1.0.
New authored contract **1.2.1** corrects that defect, with semantic label tests.
F-010 clarifies Issue day-index/FEED versus Git-index publication evidence.
F-011 explains unchecked authored criteria without inventing an acceptance writer.
F-012 requires same-execution task interpreter capture separately from the Aware
installation interpreter; the client's missing historical version remains unknown.

The built client version is **0.1.0a6**. Only its version literal and packaged
contract documentation change. Issue SDK/provider/CLI and repository owner
implementations are unchanged. Candidate accounting proves one changed wheel and
21 byte-identical wheels; the package closure remains 22, with no new dependencies.

Procedure: scoped `prepare_feedback_a6.py`, packaged-only contract renderer,
source-layout recorder; commit reviewed source before building in a separate
scratch checkout. Retain a separate candidate release/binding and replay actual
installed owner tests under checkout-hidden, network-disabled isolation.
Candidate review precedes any separately authorized promotion or push. No root
template upgrade is implicit, including in already initialized customer targets.

## Exact candidate

The unchanged builder ran in a separate checkout of local source checkpoint
`59a53ad59a6f45c1bce1734ff04262027b7448ce`. No implicit owner-source refresh was
used. This local source coordinate is not a remotely published revision.
The source and notices accompany the archive; access to a private evaluation
or the Aware development checkout is not an installation dependency.

| Record | SHA-256 |
| --- | --- |
| `distribution/aware-agent-fs-0.1.0a6-linux_x86_64-py312.tar.gz` (3,574,644 bytes) | `c3d6e593fd5894a927d338da5347a32e9c9eda3aec0aadcf9a662d51e348b804` |
| `release-a6-candidate.json` | `1f33866867c3385d817776b9afa179751ab669ca280ddab76e8d2080f7b0a08b` |
| `feedback-a6-candidate-binding.json` | `1489d389ef4dfc18bb714e75a60365b891c720bc3eb403d63e265d4619168c31` |
| Embedded/current `source-provenance.json` | `028d3ce88810996f34575199b631b5c8ef2fdf4aeb67ad708623f62a4ea3796d` |
| Unchanged `build_bundle.py` | `0a7eacd4752dad4c1bac06c0e20ac6256283ed7b1aaeaff7e2a8e004a11119cb` |

The archive retains 396 members / 395 checksums. New agent wheel SHA-256:
`a2a1d670f41a011bc1158f080ba3c2c5171ff55a62d187277d08311af5b1c449`.
The other 21 wheel filenames and hashes match a5 exactly. All six domain-owner
module pins in the candidate binding remain unchanged. Sources are neutral only:
no generated Service/API/DTO, ontology/ORM or Experience modules or benchmark
subtree. The new wheel retains the same in-wheel Apache license and scoped NOTICE.
This is bounded byte/content accounting, not exhaustive rights/privacy clearance.

Manifest `source_revision` retains the historical extraction coordinate
`728831f6636a611a8baac61dbc258ed563a0e466`; the actual build revision is separately
bound in `public_workspace_revision` and the candidate binding. Old receipts and
archives have not been relabeled. The live release still points to a5, even though
current producer source/provenance now describes preparation of a6.

## Producer evidence

- **224 installed tests passed, zero skipped**: 175 pinned domain-owner cases,
  the 47 retained workflow/bootstrap/repository/usability cases, and two new
  installed feedback cases. The inherited harness's expected versions now come
  from the exact selected binding; its decision/refusal logic is unchanged.
- Fresh Linux x86-64 / Python 3.12.3 installation under Bubblewrap: producer
  checkouts and earlier installations hidden, networking disabled, inherited
  environment cleared, offline wheel installation and dependency checks clean.
  Imports are contained in the new environment; zero editables/direct URLs.
  Separately supplied pytest 9.0.2 tools are not payload dependencies.
- Actual installed setup advertises 1.2.1 consistently in metadata, root and
  modular index. Actual owner results retain `issue_day_index:pending` and
  `feed:unavailable` alongside applied Git-index reconciliation and clean scoped
  Git status. Verified closeout leaves authored acceptance unchecked.
- **64 accounting/publication/evaluation checks passed, zero skipped**, plus
  three subtest assertions: eight live-a5 baseline accounting cases, eleven a6
  accounting cases, ten source-layout, six feedback regression, thirteen retained
  publication/bootstrap and sixteen v2 evaluation-validator cases. These include
  schema/format checks, not new external evaluation or authenticated authority.

The first layout run failed an outdated assertion counting every changed README
as a historical link-only edit; it now distinguishes explicitly admitted
amendments and still requires all six original provenance-link edits. An initial
build invocation arrived before the scratch clone finished and failed before
opening its builder; the retry waited for the completed clone. Neither changed
candidate bytes. No installed failure/retry occurred. No reproducible-build claim
is made; the rebuilt unchanged wheels matching prior hashes is narrower evidence.

Installed JUnit: `/tmp/aware-a6-candidate.wcCcl6V2/clean-proof/installed.xml`,
SHA-256 `ed8710cb5ff32875124754e11ce032686f456dfbaeadb6154127d93c50d14ecf`.
Accounting JUnit: `/tmp/aware-a6-candidate.wcCcl6V2/source-accounting.xml`,
SHA-256 `0eb3af5c9bde6265f987fea4a220e45a29a57cce64e088f80bfb2e83fe3612bc`.
Runner: `/tmp/aware-a6-candidate.wcCcl6V2/clean-proof/run_installed.py`,
SHA-256 `b2441a9e9351ad2f8af23721f8e7550fadb21a53aaef9c1c3f6f7e1cd5c90da0`.
These temporary producer receipts are not customer prerequisites.

## Independent replay and next boundary

Prepare a fresh disposable packet with the exact archive, candidate binding,
unchanged `protocols/install.py` and agent installer, pinned owner tests, the six
installed test files and authored contracts. Copy `release-a6-candidate.json` as
the packet's `release.json` only; never modify this checkout's live selection to
run a candidate. Supply pytest helpers separately, with no Aware product modules.

The retained packet and runner are at `/tmp/aware-a6-candidate.wcCcl6V2/clean-proof`.
For replay, copy `packet`, `test-tools` and `run_installed.py` to a fresh scratch
directory, create its empty `tmp` directory and do not copy `env`. Bind only that
proof directory beneath a hidden `/tmp`, hide `/home` and `/root`, clear the
environment and use Bubblewrap `--unshare-net`. Run `/usr/bin/python3.12 -I -B`
on the copied runner. It checks exact release/archive pins and installs into a
new environment before tests. `--reuse-installed-for-tests` is explicitly only
an installed replay, not a fresh-install claim.

Next: independent candidate review, then a separately governed promotion/root
contract migration if authorized. Publication and customer evaluation follow
their own authorization. SPEC is a later separate capability cut. No public
push, root-bootstrap upgrade, Goal capability or service authority follows here.
