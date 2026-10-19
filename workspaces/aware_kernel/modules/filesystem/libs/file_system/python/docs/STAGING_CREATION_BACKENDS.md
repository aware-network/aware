# Staging creation backend feasibility

Status: bounded feasibility and conditional selection, 2026-10-18. No backend
is qualified by this study. No runtime API, service, mount, account, privilege
or deployment is introduced. The accepted [proposed custody contract](STAGING_CREATION_CUSTODY.md)
remains the requirement; P2a acceptance stays held.

## Selection result

The conditional lead is one original FileSystem worker running under a dedicated
writer identity, with a protected ancestor chain and fresh, unexposed backing.
This is an architectural candidate for a separately authorized canary, not a
selected or supported installation backend. It is preferable for further study
because it can reuse the original physical writers without implementing a
complete virtual filesystem. That is a design judgment, not measured performance.

No candidate currently supplies all three required outputs: enforceable writer
exclusion on an actual target, creation-bound original custody, and a qualified
Interface receiving port. The current ordinary same-UID parent remains
unsupported for the stronger creation guarantee. Zero-admin public installation
under this guarantee is an open product gap, not an implicit new prerequisite
for opening the Development App.

## Candidate comparison

| Candidate | Exclusion mechanism and limitation | Setup and cost | Result |
| --- | --- | --- | --- |
| Same-UID private directory plus cooperative locks | Participating writers serialize, but raw same-UID writers can still mutate | Existing source mechanisms; no added daemon | Reject for this requirement; remains useful under its existing weaker contract |
| User/mount namespace alone | Changes credentials or mount visibility; ordinary mappings/backing aliases do not establish exclusive ownership | Namespace/mapping policy and alias qualification | Reject as sufficient alone |
| Landlock applied to installer/worker | Restricts the covered tasks, not unrelated existing raw writers | Rules and coverage qualification | Reject as sole protection; possible defense in depth |
| Dedicated-UID original FileSystem worker | Kernel access checks can deny external callers while the qualified owner serializes its own operations | One-time protected-root/identity/executable/launch admission; one worker plus IPC | Conditional lead, not qualified |
| Mediated FUSE filesystem | Custom daemon could mediate mutations, but mount ownership is not per-operation custody | FUSE daemon, authenticated operations, safe backing, mount/recovery lifecycle and native dependencies | Plausible alternative; no original qualified implementation identified |
| Host-wide MAC policy or managed volume rollout | Could supply stronger enforcement if independently qualified | Administrator policy/backing rollout and broader host integration | Outside this bounded cut; do not begin rollout to close this report |

The Linux [user namespace rules](https://man7.org/linux/man-pages/man7/user_namespaces.7.html)
retain relevant authority for the namespace owner in its parent, and filesystem
access uses mapped credentials. [Mount namespaces](https://man7.org/linux/man-pages/man7/mount_namespaces.7.html)
separate mount views. Neither observation proves that writable backing aliases
or same-user access have been removed. This is why a namespace flag is not the
required exclusion evidence.

[Landlock](https://docs.kernel.org/userspace-api/landlock.html) constrains the
covered task and descendants. Applying it only to our worker does not exclude
an unrelated writer. A broader sandbox policy needs its own coverage proof.

[FUSE](https://docs.kernel.org/filesystems/fuse/fuse.html) supports nonprivileged
mounts through its userspace framework and helper, but permission policy still
needs a real implementation. An ordinary same-UID passthrough mount does not
meet this model. A candidate must mediate raw operations and prevent access to
mutable backing outside that mediation; daemon integrity, aliases, unmount and
failure behavior also need qualification. This study does not declare FUSE
impossible or infer a working backend from an installed helper.

## Dedicated writer qualification requirements

The conditional candidate uses these conjunctive requirements:

1. A separately admitted Host/setup operation establishes a fresh root outside
   the client-controlled repository/home ancestry. Non-writer callers cannot
   rename the anchor or mutate its contents. Every ancestor and the backing
   permissions/ACLs must be qualified, not just the staging leaf's mode.
2. Only the qualified FileSystem executable may run as the writer identity in
   the supported environment. The executable and launch inputs are immutable
   to clients and to that worker; no arbitrary code, argv, environment, import
   path or general-purpose privileged command is accepted through the endpoint.
3. Ordinary callers have neither that identity nor bypass capabilities. No
   writable descriptor, mount alias, imported hardlink, preexisting writer or
   writable block-device path may bypass the owner. Original setup must prove
   fresh provenance before exposure, not try to enumerate away an unknown past.
4. The worker is the sole mutator of the active namespace. Its actual operation
   serialization covers creation through acquisition, every write and final
   verification. A cooperating lock may implement internal serialization, but
   external exclusion must come from the qualified physical boundary.
5. The original owner retains the created directory before exposing successful
   acquisition. Loss of the creation/acquisition return preserves uncertainty.
   It must never reopen an unbound name to adopt its current occupant.

The candidate relies on Linux's [credential and directory access checks](https://man7.org/linux/man-pages/man7/path_resolution.7.html),
subject to privileged bypass and the trusted-host assumptions in the model.
These requirements are a conditional inference from those mechanisms, not a
proof that this machine has the candidate deployed. Selecting a UID alone is
insufficient. No new UID, path, service unit or backend enum is allocated here.

Host administration must separately admit identity/root provisioning, executable
closure, launch policy, authorization boundary, durable evidence and limits.
Normal worker execution should not retain setup privileges. Existing managed
Release authority does not automatically authorize a new FileSystem role or
public installer operation. An existing root service, sudo/docker membership,
or a setuid helper is not task-specific permission to use it.

This may require a one-time administrator-approved installation component. A
no-admin alternative would need its own qualified enforcement mechanism; it
cannot silently fall back to the rejected same-UID profile. No current public
App promise should imply this candidate is already bundled or installed.

## Exact proposed Interface handoff

The following is the logical receiving contract, not implemented Python names
or an allocated wire schema. Interface keeps archive/profile interpretation.
FileSystem owns all physical creation, member writes, rereads and resource
lifetimes. Their deployment placements may differ; the owner remains the same.

Interface first obtains the exact selected descriptor and verifies one immutable
archive snapshot through the original profile verifier. It derives a frozen
ordered physical plan of canonical relative paths, lengths, digests and modes,
with explicit cumulative bounds and the manifest member included. It must not
derive a plan from a different reopening of a mutable archive path.

| Operation | Required inputs | Original-owner result and rule |
| --- | --- | --- |
| Begin staging | Authenticated/admitted connection, owner-issued namespace binding, operation authorization reference, exact ordered plan and its digest | Either unsupported before creation, retained failure evidence, or connection/generation-bound stage reference issued only after creation custody is established |
| Write chunk | Live stage reference, exact member ordinal, next byte offset, bounded bytes | Owner permits only the next admitted CREATE/write step; verifies cumulative length/digest and mode, retaining original effects; no replay after a lost return |
| Finish staging | Live stage reference and expected plan digest | Owner verifies complete membership/bytes/modes and synchronization, seals further writes, returns original completion and resource evidence; not installation or publication |
| Observe | Same admitted lifetime and original operation/stage reference | Read-only known/unknown effect and resource evidence; no new handle or renewed write right |
| Release | Original live custody and its lifetime | Once-only resource disposition; uncertain release remains uncertain, staging is retained and no implicit removal occurs |

For a separate worker, the stage reference resolves to server-retained original
custody. It is not a serialized directory handle, bearer authorization, raw fd,
caller root path or inode assertion. Bind it to the admitted connection,
actual peer lifetime and worker generation; do not authorize all clients merely
because they share UID 1000. [Unix peer credentials](https://man7.org/linux/man-pages/man7/unix.7.html)
are connection evidence, not an operation grant or protection from a transferred
socket. Endpoint authenticity, process lifetime, descriptor-transfer policy and
operation admission must all be qualified. No existing local transport is
declared to supply that composition here.

No `SCM_RIGHTS` export of writable staging descriptors is permitted. Interface
must not implement destination mkdir/open/traversal as a fallback or pass an
arbitrary writer callback. A lost Begin/Write/Finish return retains uncertainty;
Observe cannot authorize a redispatch. Broker exit leaves retained residue and
an unknown operation, not a fresh automatically retryable reservation.

A sealed staging result does not yet provide a consumer-owned installed tree,
read exposure or executable location. That ownership/exposure transition belongs
to the later P2 install/activation scope and must not revoke active custody or
expose a writable alias prematurely.

Three concrete source gaps precede this handoff: the original public verifier
currently lives in the managed-release build tool and reopens a path; it needs
an exact-snapshot neutral receiving entrance without copying its algorithm.
Existing acquired-private-directory writes are flat CREATE-only sequences with
1 MiB file and 1024-transition caps, not an arbitrary nested App tree writer.
The authenticated worker/namespace/operation composition is also unimplemented.
No wrapper, dynamic checkout import, larger caller limit or detached receipt
can fill these gaps. Exact original-owner APIs, package declarations and locks
must be separately admitted before runtime changes.

## Resource costs and proposed canary budget

No candidate worker RSS, CPU, latency, durable-space fit or throughput was
measured. A dedicated writer adds at least one process, an authenticated IPC
channel, protected artifact/runtime bytes, bounded live descriptors and storage
for complete staging plus every retained uncertain attempt. Repeated failures
must consume a bounded admission budget; no automatic deletion may enforce it.
FUSE additionally introduces its daemon, kernel connection/mount lifecycle,
request mediation and backing/recovery cost; no measured comparison is claimed.

Static accounting for the current Interface extractor is material: compressed
snapshot capacity is 64 MiB, tar expansion cap is
`256 MiB + 10000 * 1024 + 10240` bytes (about 265.775 MiB), and a final single-file
reread can allocate 256 MiB. The sum is about 585.775 MiB before interpreter,
metadata, buffers or copies. This is a capacity sum, neither measured RSS nor a
complete memory upper bound. Existing source limits are not an operational fit.

For a possible first canary, propose one active job and 64 KiB data frames with
at most eight queued frames: 512 KiB raw queued payload, excluding transport and
serialization overhead. FileSystem should stream hash/write/reread work rather
than duplicate the archive or allocate a whole native library. This is a budget
proposal only; existing owner limits cannot be raised implicitly. Qualification
must measure total Interface plus worker peak memory/CPU/time, file/descriptors,
disk high-water and retained failures against an explicitly admitted limit.

## Stop condition and next admissible work

No backend qualifies now. Record the missing original implementation, namespace
enforcement, setup admission, positive/negative canary evidence, resource proof
and exact Interface adapter as the gap. Do not begin account creation, mounts,
MAC policy, privileged launch, new package resolution or platform rollout.

If a separately authorized setup/canary selects the conditional candidate,
first freeze its exact input closure, private root/identity/executable policy,
authentication, limits, fault controls and source/API scope. Only actual original
positive creation and both substitution controls can reopen P2a acceptance.
Other App, Pane, Agent, Protocol and Release preparation remains independent.
