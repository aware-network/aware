# Aware Issue Operational Runtime

Workflow-owned, materialization-independent Issue operation authority. It
defines immutable snapshots, typed intents, deterministic lifecycle movement,
strict serialization, persistence-first receipts, and bounded observation.

The neutral aggregate codec remains lossless, but hosts may expose compact-head
and exact-Issue persistence ports. Normal mutations then apply the unchanged
reducer to the target Issue and exact idempotency record instead of requiring a
historical catalog read. Full aggregate persistence remains the compatibility
path for stores without indexes and for authority reconciliation.

Scope evolution is a typed additive Issue transition. It requires the exact
`in_progress` owner, expected Issue revision, canonical bounded additions, and
returns a distinct before/after amendment receipt. It cannot remove or replace
scope, change lifecycle, lock repository paths, infer paths from source state,
or retroactively adopt source effects.

The package has no runtime dependencies. It does not parse Markdown, access a
filesystem, expose Local Service transport, import generated Issue DTOs, invoke
Ontology/Meta, or claim canonical graph authority. The existing
`aware-issue-runtime` remains the separate read-only source projection lane.

Version 0.3 adds the shared pure source-scope policy. It preserves publication's
owner-first, status-second, first-out-of-scope refusal ordering; status spelling
normalization and exact-or-directory-prefix scope remain unchanged. A positive
decision is not an Issue admission, authenticated actor evidence or permission
to mutate. Actual issuers must observe original authority and revalidate it at
use. Workspace publication may consume this policy without importing a parser
or another source writer.

The ACT-01A-P surface adds strict, portable Workflow Issue activity evidence.
One owner observation anchors the current retained store/journal epoch;
current members match that authority, while historical members preserve their
exact event-time authority. Historical requests carry only an Issue revision:
the separately governed Workflow host remains the sole activity selector.
