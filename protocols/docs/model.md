# One operational model, explicit authority

The [agent-first Issue bundle](../agent/README.md) independently supports an
Issue-only `aware.collaboration.fs_v1` profile with `aware.issue.markdown.v1`.
Its Goal role is explicitly unavailable; setup does not reinterpret legacy
lane rows as native Phases. It exposes `aware`/`aware-issue-cli` through the
existing Issue SDK, filesystem provider, operational runtime and Workspace
commit owner. The native Goal path and version table below refer to the
separate read-only Goal distribution, not an implicit upgrade of that profile.

A Goal describes direction; its lanes and phases describe contributions,
dependencies and Gates. An Issue is a bounded work record, not proof that its
Goal Gate has been accepted. Evidence outlives an agent execution. Another
execution can observe committed state and verify a receipt instead of relying
on the previous execution's memory.

There are two authority modes: **filesystem** and **Service/API**. They are
explicit selections for an admitted target, not competing writers. After an
explicit handover to service authority, files are projections; service failure
must not silently make them authoritative again. Only filesystem/Git is
included in this preview.

Skill, SDK, CLI and Experience are interfaces relative to a domain operation.
A Skill composes a workflow; the SDK exposes typed operations; the CLI exposes
commands; an Experience contextualizes observation and action. They do not
own separate Goal evaluation implementations. Invocation need not launch a
CLI subprocess to preserve the canonical operation identity.

The installed read-only path is:

```text
explicit aware.protocol.toml
  → retained Protocol filesystem admission
  → native Goal SDK/provider
  → neutral Goal eligibility/direction decision
  → actual observation, currentness result or refusal
```

Protocol admission retains repository identity, manifest-byte digest and
Goal root/template. The Goal provider verifies the concrete committed target,
unique Goal identity and source epoch. A raw caller-built path/binding or matching
digest is not an equivalent authority. Admission is not permanent permission
over filesystem topology that can change.

## Independent version axes

| Axis | This preview |
| --- | --- |
| Public publication | `goal-fs-readonly-preview-2026-10-05` |
| Manifest syntax | `aware = 1` |
| Collaboration profile | `aware.collaboration.fs_v2`, semantic version `2` |
| Native Goal record profile | `aware.goal.phase.markdown.v1` |
| Accepted native Goal documents | strict internal V2 and V3 |
| Installed command | `aware-goal-native` |

A public record profile's `v1` is its contract version, not a promise to consume
internal document V1. Internal V2/V3 are explicit supported carriers under that
profile. Legacy lane-row `aware.goal.markdown.v1` retains its distinct meaning;
it is not silently upgraded or aliased to native Phase semantics.

Here, **canonicalize** means bind the public capability to the existing owning
operation and record contract—not rewrite customer records, invent a new
evaluator, or declare installation checks to be approval authority.
