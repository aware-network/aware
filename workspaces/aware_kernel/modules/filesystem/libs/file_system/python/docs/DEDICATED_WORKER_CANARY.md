# Dedicated writer canary source and setup plan

This is a Linux one-shot canary candidate, not a supported installation backend
or a general FileSystem service. Source tests cannot qualify writer exclusion.
P2a stays held. No administrator setup or privileged launch is authorized by
this document; the exact installed closure and setup digest still need approval.

## Proposed exact targets

| Input | Proposed value |
| --- | --- |
| Account and primary group | `aware-fs-canary`, numeric UID/GID `62041` |
| Ordinary requester | UID `1000`, never the worker identity |
| Fixed case | `9cd6bc0f8e9753b8b5ce318eef15b2ae` |
| Setup file | `/etc/aware/filesystem-staging-canary/v1/9cd6bc0f8e9753b8b5ce318eef15b2ae/setup.json` |
| Writer root | `/var/lib/aware/filesystem-staging-canary/v1/9cd6bc0f8e9753b8b5ce318eef15b2ae/writer` |
| Protected executable parent | `/usr/local/lib/aware-filesystem-canary` |
| Fixed effects | `writer/probe` directory, then `writer/probe/payload` regular file |

Account names and numeric IDs were absent in read-only NSS checks on 2026-10-18;
that is not a reservation. Recheck before separately admitted setup and refuse
collisions rather than adopt an existing identity. `/opt/aware` is user-owned
and is not an acceptable executable ancestor for this candidate. All selected
ancestors must be root-owned 0755; the writer leaf is UID 62041, mode 0700.
No symlinks or caller-controlled ancestor is admitted.

The installed executable release must be a reviewed, digest-pinned immutable
closure below the protected parent, not this checkout. Its exact release path,
wheel/runtime/dependency inventories and hashes are not produced by this source
cut. Existing package initialization imports other dependencies, so copying one
module or setting PYTHONPATH is not an installed closure. Freeze the complete
closure and its manifest before requesting host setup approval.

## Administrator setup and launch obligations

The separately approved administrator action must create a genuinely fresh
case and root under protected ancestors, before exposing them to any ordinary
writer. It must provision the unused locked account with no shell or unrelated
workload, qualify executable/launch integrity, inherited descriptors, aliases,
mounts and group/capability policy, and record actual root device/inode. Setup
must not chmod/chown an unknown preexisting tree into apparent freshness.
Root-owned metadata records an administrator declaration, not independent proof
that those obligations were fulfilled. An orphan or unknown attempt is retained;
there is no automatic retry, deletion or reuse of this fixed case.

The root-owned 0444, single-link `setup.json` has exactly these fields:

```json
{
  "schema": "aware.filesystem.dedicated-worker-canary.v1",
  "case_id": "9cd6bc0f8e9753b8b5ce318eef15b2ae",
  "writer_uid": 62041,
  "writer_gid": 62041,
  "requester_uid": 1000,
  "root_identity": [0, 0],
  "closure_sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "freshness": "new-root-before-any-writer-exposure"
}
```

The identity and hash above are explanatory placeholders, not launchable input.
Actual nonzero identity and closure digest are required. The launch selection
supplies the exact setup-byte SHA256 separately; setup bytes are limited to
8192. The candidate checks record shape/hash, root-owned metadata and namespace
identity. It does not independently verify a transitive release closure from
the record's declaration: the approving launcher owns that validation.

The administrator-controlled launch must use the approved isolated runtime
(`-I -B`, sanitized environment), UID/GID 62041, no other groups, no active or
inheritable capabilities, no-new-privileges and initial identity UID/GID maps.
Soft/hard limits must both equal: CPU 10 seconds, address space 256 MiB,
open descriptors 64, file size 1 MiB and core size zero. These are proposed
canary budgets, not measured fit or a production App extraction budget. The
external controller must also enforce a 20-second wall-clock deadline and a
16 KiB output limit, preserving uncertainty on timeout/kill.

Only root-owned anonymous controller pipes may occupy descriptors 0/1/2, with
read/write directions checked; no other live inherited descriptor is accepted.
The transient descriptor used to list `/proc/self/fd` may already be closed.
This necessary startup check does not prove setup history or identify every
holder of the other pipe ends. The approved launcher still owns that policy.

Linux [no-new-privileges](https://man7.org/linux/man-pages/man2/PR_SET_NO_NEW_PRIVS.2const.html)
prevents exec from granting new privileges; it is not namespace writer
exclusion. [Process status](https://man7.org/linux/man-pages/man5/proc_pid_status.5.html)
reports credentials/capabilities. [Resource limits](https://man7.org/linux/man-pages/man2/getrlimit.2.html)
bound address space, CPU, descriptors and file size, not all resident memory or
wall-clock work. Setup still needs actual resource and exclusion evidence.

## Worker and controller protocol

The module entrance is `aware_file_system.staging_worker_canary` with only
`--setup-sha256 sha256:<exact setup bytes hash>`. There is no arbitrary root,
plan, command, Python callback, private-profile fallback or unsafe mode option.
All mutations are fixed by the reviewed source and the approved setup action;
stdin acknowledgments only synchronize tests and never grant operation rights.
Protected code-file metadata is checked, but this is not self-certification of
the runtime or of code that already executed during import.

The worker emits bounded JSON boundary lines at `mkdir_return` and `first_open`.
The controller must attempt raw rename/replacement from UID 1000 at each boundary,
retain independent denial evidence and then send exactly
`continue:<boundary>\n` through its private launch pipe within five seconds.
The source does not provide a privileged controller, impersonation mechanism,
socket service or Actor-role admission. Acknowledgments cannot stand in for
proof that attacks ran. Raw descriptor/mount-alias controls require setup-level
evidence, not just a failed pathname operation.

The fixed two-member [original plan](STAGING_PLAN.md) is validated before probe
effects and its digest is reported. It supplies relative paths, final modes,
length and digest to the original mkdir, streaming writer and bounded rereader.
This is not a general plan-receiving or nested App-tree API. Original FileSystem
cleanup retains descriptor dispositions. Missing or exceptional mkdir returns retain unknown effects;
no occupant is adopted after an unknown return. The final JSON is a canary
observation with `qualified_backend=false`, even after a successful probe. It
does not export live custody, a reusable stage, installation or publication.
Externally reviewed positive creation, both real substitution controls, alias
exclusion, failure/timeout and resource evidence are still needed before backend
selection, followed by the full Interface join before P2a acceptance.

Unit tests may exercise the private fixed probe under an ordinary temporary
directory or simulate gates. Those are deliberately not deployment proofs.
ONE APP remains; App, Pane, Agent and Release preparation stays independent.
