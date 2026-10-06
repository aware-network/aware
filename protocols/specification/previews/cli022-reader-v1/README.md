# SPEC CLI 0.2.2 reader successor — local selection

Status: selected locally; independent selection review pending; not publicly delivered.
a6 is unchanged. The published aware-protocol 0.3.1 / aware-spec 0.2.0 predecessor
remains intact. This versioned selection uses aware-protocol 0.3.1 / aware-spec
0.2.2, using SDK 0.2.0, FS SDK adapter 0.3.0 and Protocol FS adapter 0.4.0.
The SDK/provider/domain owners are unchanged; no new evaluator or writer exists.
See [the selection record](SELECTION.md); public delivery is a separate decision.

## Explicit separate installation

Only after explicit preparer selection, from the repository root, choose your
actual Python 3.12 executable and an absent environment under a private existing
parent. The wrapper itself rejects existing files, directories and dangling links:

```sh
python3.12 protocols/specification/previews/cli022-reader-v1/install.py \
  --python-executable /usr/bin/python3.12 --venv /tmp/aware-spec-cli022-env
/tmp/aware-spec-cli022-env/bin/aware-protocol version
/tmp/aware-spec-cli022-env/bin/aware-spec --help
```

Never overlay a6 or earlier SPEC preview environments/wheelhouses.
The wrapper verifies the exact packet and payload, retains source/notices and
delegates to the unchanged shipped offline install.sh. consumer-lock.json is
an audit inventory, not a pip requirements file. Linux x86-64 / Python 3.12 are
the installation target; Git is needed for customer work. After acquisition no
network, editable import or Aware development checkout is required. Parent
permissions remain unchanged. Failed installation can leave evidence and
partial effects; rollback and continuous confinement are not claimed.

## Supported scope

Only aware-protocol (admit, setup-specification) and aware-spec (observe,
iteration-identity) are supported interfaces. This separate 27-package closure
activates only the protocol adapter extra: governed and draft remain unselected.
Dormant owner exports are not admitted customer writers. Unsupported writer
syntax proves capability absence, not approval-policy enforcement.

Setup takes explicit approved inputs and fresh Issue-owned admission; it changes
only admitted directories and the manifest binding. Preview is non-authorizing;
apply is explicit. Publication and closeout remain separate a6 operations.
Reading requires already qualified SPEC documents and exact coordinates. New
customers without them stop after setup: authoring/import, approved iterations,
durable iteration-to-Issue binding and protected SPEC publication are unavailable.
No manual authority creation substitutes for those missing operations.
No Goal, Service/API, generated API/DTO, ontology/ORM or Experience rail is added.
Currentness is observed state, not every-write detection or continuous confinement.

## Exact bytes, source and notices

- [Accepted packet](distribution/aware-specification-cli022-source-notice-review-v1.tar.gz): SHA-256 `578b25b0d68bed3546ac54fbfeb426062415e6b519df0a7829172e33a8340c2e`.
- Payload SHA-256 `52d2d443ea8d7b2a5cf4533d78460f1f3c9c62a6bd65ee9a853e15bb07e694d0`.
- [Delivery map](delivery.json): all 449 original packet members and tree hashes.
- [Neutral source snapshot](../../../../workspaces/previews/specification-cli022-reader-v1/README.md): all 151 source
  files under workspaces/, without overwriting existing source snapshots.
- [Source index](packet/SOURCE-INDEX.json), [notice bindings](packet/NOTICE-BINDINGS.json),
  [boundaries](packet/REVIEW-BOUNDARIES.md), [packet README](packet/README.md).
- [Evaluation protocol](../../../evaluations/README.md).

The packet root is aware-specification-cli022-source-notice-review-v1. The inner
root is aware-specification-cli022-reader-internal-v1. These names do not allocate
semantic protocol versions. Source indexes retain packet-relative coordinates;
delivery.json maps each to the actual public tree. Original packet checksums
must be verified against the unchanged extracted distribution, not the source-
remapped tree. The snapshot is composite neutral source, not a full workspace
revision, editable installation or competing operational rail. Attached recipes
are provenance, not a checkout-independent reproducible wheel-build claim.

All 45 in-wheel legal copies and 236 inherited notice files remain exact.
Bounded source/notice accounting and instruction correction are accepted, not an
exhaustive legal/privacy warranty, binary linkage attestation or public release.
Historical instruction drafts and wider package READMEs remain historical,
unfrozen owner inputs; this page describes only the narrower local selection.
Customer AGENTS.md, a6 contract 1.2.1 and predecessor artifacts stay unchanged.
Contract 1.3.0 remains unallocated; no combined client or aware spec wrapper is
supplied. Accepted layout/integration receipts retain their historical unselected
fields; they are not rewritten by this decision. Independent selection review,
instruction freeze and publication remain separate. No delivery or publication
authority follows from local selection.
