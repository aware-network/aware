# aware-protocol-fs-adapter

Strict admission and lowering for repository-authored
`aware.protocol.toml` manifests.

This package also implements the filesystem provider for the canonical
`protocol_sdk.admit_target` operation. The provider delegates to the existing
admission implementation; it does not copy profile or containment rules, probe
for a service, or fall back from `service_api` to filesystem authority.

The adapter validates structural shape, supported collaboration record
profiles, filesystem path containment, and the filesystem authority mode. It
returns neutral `aware-protocol-runtime` values. It does not select an SDK
implementation, inspect installed CLI capabilities, discover a service, or
allow filesystem fallback from Service/API authority.

The admitted filesystem profile retains repository roots and templates beside
the neutral Protocol manifest. Those locations do not enter the canonical
record profile/role binding, so a later Service/API adapter is not forced to
model filesystem paths.

Successful filesystem admission always requires an existing repository root.
The bytes entrance is useful for retained fixtures, but it requires the same
repository context and performs the same containment checks as the on-disk
entrance. A refusal made before source bytes are read reports no source digest.

Containment walks each declared POSIX path from the resolved repository root.
Every prefix observed to exist is resolved strictly; a symlink loop, broken
symlink, file-as-parent, or other resolution failure is refused. The untouched
tail after the first genuinely missing component remains permitted so a fresh
repository need not pre-create every declared record directory. Refusals use a
stable Protocol reason plus a separate exception-class detail.

Manifest admission proves the observed bootstrap and record roots were
contained at that moment. Every owning filesystem operation must still resolve
and validate its concrete target at use time; templates and mutable filesystem
topology are not permanent authorization.

## Native Goal source capability (source implementation)

Strict admission now recognizes these separate combinations:

- `aware.collaboration.fs_v1`, semantic version 1, with the unchanged legacy
  `aware.goal.markdown.v1` record profile.
- `aware.collaboration.fs_v2`, semantic version 2, with
  `aware.goal.phase.markdown.v1`. Goal and Issue records must have authority
  roles. Other record families retain their independently declared profiles.

The v1 manifest envelope and `canonical_v1` admission outcome are unchanged;
the outcome names the admission contract, not collaboration-profile version.
Admission is not a Goal carrier decoder, an eligibility decision or installed
operation proof. The Goal owner reads exact V2/V3 and refuses native V1 or
legacy substitution. No Goal writer is introduced.

`admit_native_goal_resolver(repository_root=..., manifest_path=...)` is the
on-disk capability issuer. Its result contains the actual admission and either
a `NativeGoalResolverCapability` or no capability for a refused admission.
Requesting issuance from a valid legacy profile raises
`NativeGoalResolverError("native_goal_profile_required")`, never falls back.

The native Goal provider must call `require_native_goal_resolver(value)` at its
entrance and derive its repository from the returned capability. A caller-built
`FilesystemRecordBinding`, decoded result, digest or raw root is not accepted.
Public capability construction, subclassing, copying and pickling are refused;
even an unregistered nominal object fails the issuer-membership check. This is
a process-local caller-data boundary, not a sandbox against hostile Python
code with access to private module internals. Another process must freshly
admit the manifest through the selected composition; fork-inherited capability
objects refuse because their issuer process identity differs.

The capability retains the repository path and device/inode identity, exact
manifest coordinate and byte digest, complete admitted profile, and Goal
root/template. `revalidate()` checks current repository identity, readmits the
same on-disk manifest, and compares its bytes, profile and source coordinate.
Properties expose immutable retained metadata, not fresh observations; the
provider must revalidate at invocation and again before returning success.

The initial native template grammar is deliberately finite:

- `YYYY/MM/DD/goal-YYYY-MM-DD-<slug>.md`
- `goal-YYYY-MM-DD-<slug>.md`

Dates must be real calendar dates, repeated directory/file dates must agree,
and slugs are lowercase ASCII kebab tokens. Other templates refuse native
admission; no glob, regex or inferred layout is used. `match_goal_path(path)`
revalidates and returns location date/slug or `None` for a path outside the
declared grammar. `resolve_goal_path(path)` additionally checks current
containment beneath both repository and resolved Goal root, returning a frozen
`NativeGoalLocation`. Neither method reads Goal content or authenticates its
identity. Missing targets remain possible: Goal must prove committed source
availability, regular-file identity, unique Goal identity, V2/V3 carriage,
Gate, prerequisites and Git epoch itself. All prerequisites use the same
capability; no fixed `docs/goals` discovery is required.

`NativeGoalResolverError` carries a stable `code` and `diagnostics` tuple for
pre-source refusals. Do not turn it into an invented Goal observation digest.
No Protocol dependency is added to neutral Goal runtime, and the existing
public Protocol SDK transport remains unchanged. These are source capabilities;
native Goal integration, independent acceptance and a new customer-installed
distribution have not been proved by this package change.
