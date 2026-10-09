# Issue Development Read Projection V2 Contract

Status: immutable fixture contract  
Owner: Coordination / Issue SDK  
Consumer: Aware Development and later canonical Issue service adapters

## Authority

`IssueDevelopmentReadProjectionV2` is a read projection of canonical Issue
Markdown. It does not replace the Markdown Issue authority and creates no
Workspace commit, ontology, materialization, Attention, or Reactivity evidence.

The Coordination-owned `aware_issue_runtime` owns:

- canonical Markdown parsing;
- Issue identity, structured content, activity order, and exact source; and
- absolute activity time with explicit time authority.

The Python Issue SDK adapter owns only:

- lifecycle and semantic-activity closed vocabularies;
- raw value and `declared | normalized_alias | inferred | unknown`
  classification provenance;
- deterministic headline/detail and commit/path reference facets; and
- blocker/Human-direction candidates keyed by activity occurrence.

The separately owned Workspace-backed Issue runtime participant owns source
observation/replay and Local Service publication. This V2 adapter performs no
filesystem access, provider I/O, or transport.

A later declared or inferred `resolved` activity closes the currently open
candidate occurrences by recording `resolved_by_activity_ref` and, when
available, `resolved_at`. A later blocker or Human direction always creates a
new candidate identity.

Dart and service adapters consume these values. They do not repeat this logic.

## Declared Syntax

New Issue activities may declare their semantic kind with either:

```text
activity_kind=human_direction
(activity_kind: `human_direction`)
```

Known legacy aliases are normalized with provenance. Historical heuristic
classification is always `inferred`; unrecognized values remain `unknown`.

## Time

An activity timestamp at the start of an update bullet is
`source_declared`. Source observation is recorded separately on `source` and
never becomes activity time. A missing or unparseable latest activity timestamp
produces `activity_at: null` and `time_authority: unavailable`.

## Fixtures

`issue-development-read-projection-v2-fixtures.json` is immutable once Phase 01
closes. Phase 02 creates reducer/envelope fixtures around these exact items;
later Dart and canonical Issue service adapters must pass them byte-for-value.

The fixture covers:

- lifecycle alias normalization;
- declared and inferred semantic kinds;
- occurrence-keyed Human direction;
- reference extraction and unknown-section preservation; and
- active lifecycle with unavailable latest activity time.
