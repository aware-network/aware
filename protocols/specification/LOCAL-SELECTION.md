# SPEC preview: local delivery selection

Status: locally integrated candidate for independent review; **not publicly
delivered, not a registry release, and not an a6/bootstrap upgrade**.
Issue: `fb/2026-10-06/specification-local-delivery-integration-v1`.

## Selected software and versions

This cut selects the exact reviewed standalone filesystem setup/read layout for
local integration. It does not allocate a new domain operation, collaboration
profile or agent-contract version.

| Version axis | Selected value |
| --- | --- |
| Delivery snapshot | `specification-setup-read-v1` |
| Collaboration profile | `aware.collaboration.fs_v1`, semantic version 1 |
| SPEC record profile | `specification_fs_v1` |
| Protocol CLI | `aware-protocol` 0.3.0 |
| SPEC CLI | `aware-spec` 0.2.0 |
| Separate agent client | a6 (`0.1.0a6`), contract `aware.agent.fs.v1` 1.2.1 |
| Proposed agent-contract extension | 1.3.0 remains unallocated |

The [installation entrance](README.md) uses its explicitly separate environment.
There is no overlay, combined installer, `aware spec` wrapper or automatic
customer `AGENTS.md` change. Source under the versioned `workspaces/` snapshot
is the accepted neutral closure, not another engine or a whole workspace export.

Packet SHA-256:
`865c57be501818dc380c9019a0fc710658d67242375a080b563258d6365a97a0`.
Payload SHA-256:
`955e423c82e431f9565e1b2351a6686855246b585d9890281bc73e8401d52eac`.
Accepted layout receipt SHA-256:
`af7c6a20c314222b9209cb71913d6c9c78674c710cb2efb3f236ae6077fe6a6d`.
All 436 reviewed paths retain their accepted bytes. The only additional files
are this selection record, the public integration check and the scoped Issue.
The [delivery map](delivery.json) remains construction evidence and is not
rewritten as a release approval.

## Instructions and capability limits

The accepted README/install entrance is retained exactly. Its embedded command
sequence and interface addendum remain **drafts**, not frozen agent instructions.
This local selection does not quietly convert them to a new contract. A later
explicit preparer/customer selection can name these separate commands; an agent
must not discover a replacement environment when a selected operation refuses.

Setup requires the customer's approved In Progress Issue, exact byte guards and
explicit directory effects. It creates directories and manifest binding only.
Reading requires independently qualified documents and exact selections. Without
those documents a new customer stops after setup. Supported authoring/import,
approved iterations, approval, durable binding, SPEC-guarded publication, Service
authority and ActorWorld are not admitted here. a6 remains the selected Issue and
repository client; its supported closure and root bootstrap are unchanged.

## Evidence and next decision

Producer review coordinates are retained for provenance, not acquisition:
layout implementation `1c197b2e46ca09ef9e70b806928d051b9200a671`,
handoff `b7d9f5421ef4d846b7abeff7a2d8f42c4b640fc4`, acceptance
`7d94490fde84925bc63cfb99c255b88b8fa0478c`, bounded closeout
`378ef0ddf10a0a679f10ecc992f66de4a6b3f25b`. Actual software, source and notices
are attached locally; no private producer checkout is a consumer dependency.

Maintainer accounting checks are in `test_delivery_integration.py`; they require
Git history containing the pinned preintegration baseline, not just a shallow
export. Set `AWARE_SPEC_INSTALL_REPLAY_ROOT` to an explicitly prepared private
mode-0700 scratch directory with no `env` child; the real installation case needs
Linux, Bubblewrap and `/usr/bin/python3.12`. Supply exact
`AWARE_SPEC_PRODUCER_ROOT` and `AWARE_SPEC_PUBLIC_PRODUCER_PARENT` paths for the
replay namespace to hide; these are diagnostic inputs, not consumer dependencies.
It retains installation evidence.
These checks cover carriage and preservation, not domain policy or authorization.
The unchanged payload's prior installed domain proof is not replaced by them.

Next: independent review of this actual repository integration and selection
record. Consumer instruction freeze, any further version allocation, evaluation
admission and **Luis's explicit publication authorization** remain separate.
No public coordinate or public availability is claimed by a local commit.
