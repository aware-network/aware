# Bounded staging plan admission

Source-only first cut toward the [creation custody contract](STAGING_CREATION_CUSTODY.md).
It admits detached physical input, not a namespace, creation handle, authenticated
operation or backend. P2a remains held. No filesystem operation occurs here.

## Original owner entrance

`aware_file_system.staging_plan` defines frozen `StagingDirectory(path, mode)`,
`StagingFile(path, mode, size_bytes, content_digest)`, `StagingPlanLimits` and
`StagingPlan`. `validate_staging_plan(plan)` revalidates every original value
and returns `StagingPlanSummary(plan_digest, member_count, total_file_bytes,
encoded_bytes)`. Exact types are required. Decoding or constructing these
values does not acquire authority. There is no destination/root or raw fd.

All members are one explicitly ordered tuple. Each ancestor must occur earlier
as a declared directory. Files and directories share a case-sensitive namespace;
duplicate paths and file-as-parent shapes refuse. Paths must be canonical NFC
POSIX relative names, with no control characters, backslashes or empty, dot or
parent components. Validation never silently normalizes or reorders input.
Directory modes are 0700 or 0755; regular-file modes are 0444, 0555, 0600,
0644, 0700 or 0755. File modes declare the exact digest-bound final state,
including read-only artifacts; they are not temporary write modes and are never
silently rewritten. Future physical writes must establish and verify that
declared final mode before sealing. Links and special files are not represented.
Digests use exact lowercase
`sha256:` form; an empty file must declare the known empty-content digest.

Limits are explicit positive integers, bounded by candidate admission ceilings:
10,000 members, 256 MiB per file and total file bytes, 1,024 UTF-8 bytes per
path, 64 components and 4 MiB canonical encoded metadata. Callers may narrow,
not enlarge them. These metadata ceilings do not raise the existing physical
writer's 1 MiB/1024-step limits or qualify memory/disk fit. Aggregate path bytes
are checked before metadata encoding. No file bodies are retained in a plan.

The digest covers a versioned canonical JSON array containing limits and every
ordered member's kind, path, mode, length and digest. JSON uses UTF-8, no ASCII
escaping, compact separators and no floating-point fields. Reordering even
independent members changes the digest: the writer must consume that exact plan.

## Receiving joins still missing

Interface must derive this plan from the one original immutable archive/profile
snapshot, including its manifest. FileSystem must revalidate it at the actual
operation admission; a summary/digest alone is not an admission token. The
future worker must then bind the plan to its authenticated lifetime and genuine
creation custody, consume bounded chunks, verify lengths/hashes/modes, and
reread/seal under the same owner. This cut implements none of those physical or
transport effects and exposes no injected writer callback. See the
[backend feasibility study](STAGING_CREATION_BACKENDS.md). Installation and
public delivery remain separate; ONE APP is unchanged.
