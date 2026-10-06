# SPEC consumer bootstrap alignment — draft addendum

Status: internal preparation; not installed, frozen or publicly selected.
Owner Issue: `fb/2026-10-06/protocol-specification-consumer-bootstrap-alignment-v0`.

## Explicit selection, not an alternate rail

Retain the installed `aware.agent.fs.v1` / **1.2.1** bootstrap for Issue and
repository operations. A customer-approved SPEC extension additionally selects
exact installed `aware-protocol` and `aware-spec` executables. This is explicit
interface selection for different operations, not permission to substitute an
environment when the selected command refuses. Never choose from CWD, PATH
recency, socket availability, a service or a source checkout.

| Responsibility | Exact selected interface | Available operation |
| --- | --- | --- |
| Repository/scaffold preparation | a6 `aware` | Existing `init`, explicit repository creation |
| Issue work and local publication | a6 `aware` | Existing Issue operations and repository commit |
| Manifest admission and governed SPEC setup | `aware-protocol` 0.3.0 | `admit`, `setup-specification` |
| Qualified SPEC observation | `aware-spec` 0.2.0 | `observe`, `iteration-identity` |

These commands may occupy separately pinned environments. The accepted 26-package
SPEC archive does **not** ship `aware`, `aware-issue-cli`, repository creation or
agent bootstrap templates. The a6 22-package archive does **not** ship these SPEC
commands. Do not merge wheelhouses or install one over the other: shared package
names have different versions and owner projections. Separate installations
share admitted filesystem records, not Python module identity or process-local
capabilities. A future combined product needs its own dependency resolution,
source disposition, bootstrap, installed proof and content review.

## Agent-facing procedure

The customer/preparer supplies the exact repository, approved outcome and source
scope, genuine harness execution, accepted Issue/bootstrap installation and exact
SPEC installation. Resolve and retain each selected executable once. If a command
is missing or differs from its pinned selection, remain read-only for that operation;
do not install, rewrite bootstrap instructions or select a development fallback.

1. Follow a6's existing preparation and scoped Issue workflow. Existing customer
   `AGENTS.md` and modular docs remain intact; no automatic upgrade or precedence.
2. Observe that exact Issue and its byte digest through the selected Issue client.
   Observe the manifest through `aware-protocol admit` and retain its exact-byte
   `admission.source_sha256`. Neither observation is setup authorization.
3. Preview `setup-specification` with the explicit root, Issue, source digests,
   ordered directory effects and intent. Inspect the planned result; explicitly
   apply the identical request only after approval. Apply obtains fresh owner-issued
   admission; a preview, DTO or matching digest cannot replace it.
4. Preserve complete result/refusal JSON, effects, scratch paths and source guards.
   Exit 2 can follow applied or unknown effects. No implicit rollback or recovery.
5. Setup produces the declared directories and exact manifest binding **only**.
   With no independently qualified SPEC package, stop here and report that document
   authoring/import is unavailable. Do not create authority Markdown by hand.
6. For an independently qualified package, explicitly select every required
   manifest and exact iteration reference. Use the actual postimage manifest digest
   with the installed reader. Observation/iteration identity grants no Issue
   assignment, execution authority, iteration approval or Phase acceptance.
7. Source effects, local repository publication and Issue closure are separate.
   Continue through a6's existing publication workflow only within its admitted
   capabilities. This extension does not implement SPEC-guarded publication or
   durable iteration-to-Issue binding. Empty directories are not Git content.

See [the command sequence](specification-setup-customer-sequence-v1.md) for exact
flags. Full SDK JSON is the setup evidence; there is no new summary or `aware spec`
wrapper. Setup and SPEC reading use only filesystem authority. Missing Service/API
or ActorWorld support never enables a fallback for service-owned records.

## Versioning and delivery boundary

Propose a future reviewed **1.3.0 minor agent-contract update**, because supported
SPEC interface selection extends 1.2.1's Issue-only workflow. This document does
not allocate or ship that version. The canonical public templates/rendering owner
must carry an accepted change into a new template and CLI release; do not mutate
published 1.2.1 templates, wheel resources, customer bootstrap hashes or this
repository's operational `AGENTS.md` to simulate it.

Until that release cut, this remains a draft for explicitly reviewed preparer
selection, not a silently installed customer contract. Product version, contract
version, collaboration profile (`aware.collaboration.fs_v1`, semantic version 1),
record profile (`specification_fs_v1`) and internal candidate generation v3 are
separate versions.

Observed-state currentness and cooperative descriptor confinement are the disclosed
guarantees; every-write detection, continuous confinement and authenticated actor
action issuance remain unsupported. Approval, draft authoring/import, approved
iterations, pairing, durable binding and protected publication are not admitted
by this addendum. Public-content/notice/source acceptance and delivery/evaluation
admission are still required; a6 remains selected.
