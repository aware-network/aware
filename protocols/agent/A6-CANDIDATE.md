# a6 feedback correction — preparation checkpoint

Status: source preparation, not a promoted customer release. Published a5 and
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

The proposed client version is **0.1.0a6**. Only its version literal and packaged
contract documentation change. Issue SDK/provider/CLI and repository owner
implementations are unchanged; the candidate must prove one changed wheel and
21 unchanged wheels. No build or installed proof is claimed by this preparation.

Procedure: scoped `prepare_feedback_a6.py`, packaged-only contract renderer,
source-layout recorder; commit reviewed source before building in a separate
scratch checkout. Retain a separate candidate release/binding and replay actual
installed owner tests under checkout-hidden, network-disabled isolation.
Candidate review precedes any separately authorized promotion or push. No root
template upgrade is implicit, including in already initialized customer targets.
