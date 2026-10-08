# Repository Pulse V1 Contract

Status: immutable fixture contract  
Owner: Coordination / Issue  
Consumer: Aware Development and later canonical Coordination service adapters

## Authority

`aware.coordination.repository-pulse.v1` is a bounded cross-Issue read
projection over authoritative Issue activity occurrences. It does not read
FEED, infer correspondence, replace Issue Markdown, or create a new activity
authority.

Each row is identified and routed by exact `activity_ref`. The projection
preserves absolute activity time and its authority, semantic-kind
classification, actor, references, Issue identity and projection revision.
Activities without trusted activity time remain diagnostic counts and never
enter the time window.

Non-unique historical `activity_ref` values are also excluded as identity
conflicts. Pulse never chooses an arbitrary occurrence or synthesizes a second
identity to make malformed history look routable.

Goal is a facet only. `goal_resolution` is:

- `resolved` when the exact canonical Goal document is present in the same
  Workspace snapshot;
- `unresolved` when an Issue declares a Goal ref that is absent; and
- `unavailable` when the Issue declares no Goal ref.

## Query and continuation

The default window is the twelve hours ending at the admitted repository
observation. `since_at` and `until_at` are inclusive. Pages are ordered by
descending `(activity_at, activity_ref)`.

The continuation cursor seals the repository revision, window, and last exact
activity identity. A repository or window mismatch fails stale instead of
silently continuing over different truth.

The Issue Local Service participant hydrates the complete Issue candidate
corpus independently of the Development navigator page and reuses unchanged
projection revisions. Development owns later time buckets, kind prominence,
run collapse, filters, and visual routing.

## Non-claims

V1 adds no FEED parser, unseen state, Needs-attention claim, presentation
bucket, run collapse, filesystem watcher, source mutation, Goal authority,
Workspace commit, ontology, materialization, Attention, or Reactivity proof.
