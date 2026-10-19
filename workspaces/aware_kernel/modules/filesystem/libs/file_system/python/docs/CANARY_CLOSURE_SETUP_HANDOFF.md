# Canary executable closure and setup approval handoff

This extends the [canary source and setup plan](DEDICATED_WORKER_CANARY.md)
with the exact receiving requirements for packaging and two separately approved
host operations. It freezes source coordinates and a setup/controller plan,
not executable artifact bytes. The canary is not ready for setup or launch.
P2a remains held.

## Renewed consumer selection

For future packaging use the current qualified Kernel context in the
[renewed Release handoff](../../../../../../../../docs/reports/filesystem-canary-release-role-current-context-20261018.md),
not the historical locks below. Kernel and Development now both record
FileSystem 0.3.9 and Kernel offline validation passes. This worker selects
`workspaces/aware_kernel`, its registered FileSystem package and its own
`uv.lock`; Development is corroboration, not a second selected context. The
dirty repository lock remains unselected. No further lock alignment is requested
by this plan. Original Release role/packaging and executable closure remain
pending; the setup/controller and two-approval obligations below still apply.

## Historical source inputs and unresolved executable selection

The accepted source commit is
`557238a891c016bd6d6f9504ab67c79f51fe8e8d`. Its complete original FileSystem
package subtree is:

```text
workspaces/aware_kernel/modules/filesystem/libs/file_system/python
Git tree a1008ea6784e743a51ce7a2eeeeb314d60bde57e
138 tracked members; 79 beneath aware_file_system
```

These counts include authored support and test files; they are not the wheel
membership or runtime dependency closure. Hashing the exact output of
`git ls-tree -r 557238a891c0 -- workspaces/aware_kernel/modules/filesystem/libs/file_system/python`
with SHA256 gives
`cfb795d6d2d277c9a415d43337f463d9b59eb8245174fb079685dd8aab224f42`.
The tree and command bind names, Git modes and blob identities at that revision.

Package initialization imports models, configuration, introspection and index
modules before the canary runs. Package metadata declares Python >=3.12 and
pyyaml, msgpack, pathspec and pydantic. Do not copy only the worker module,
inject checkout paths or relabel an Agent artifact as a worker artifact.

Historical inputs at that source revision are observations, not a qualified
build selection:

| Input | Git blob | SHA256 |
| --- | --- | --- |
| `workspaces/aware_kernel/pyproject.toml` | `0398e2013e5fe06284a0aff61d94fb750006b962` | `7eaa55f905e62ecc939f111d62f6b959273015b72851a903c4abb54802621e63` |
| `workspaces/aware_kernel/uv.lock` | `bc0b26448730863917fe1f41572729436e34d2ac` | `45214a00f3b180fb2960799dad39bb7e7538a187d65459e93b9d3d2bdba8cf62` |
| `uv.lock` | `fe899a8684b97a00b36532787c6302c7746e3b1c` | `54ac5d346f1e31332b84c520c2813e1bbde444d35ee1d915c1fca9852fb68172` |

The package metadata is 0.3.9; the Kernel lock records aware-file-system 0.3.7
and msgpack 1.2.1; the repository lock records aware-file-system 0.3.8 and
msgpack 1.1.2. Neither is admitted here as the canary resolution context. The
next source cut must declare the real registered consumer context and align
only its admitted package-manager inputs through the original Workspace rail.
Do not hand-edit locks or manufacture a standalone resolution root. Renew the
source and closure pins after that change; old source acceptance does not
automatically certify new package metadata.

The existing managed-release build-plan schema and loader admit only Provider,
Recovery, Development and Agent classes with their fixed roles. There is no
canary worker role in those entrances. The Release receiving cut must first
define how this fixed diagnostic payload is admitted through the original
packaging and launcher owners, preserving the current class/role refusals.
This handoff does not create a new artifact class, selector or installer.

## Executable closure required before setup approval

Release must return one immutable diagnostic candidate and independent verifier
receipt, with all of these bound together:

- Exact renewed source, registered package and selected lock context, plus
  dependency-resolution and package-version correspondence.
- Python interpreter, standard library, extension modules, wheels, installed
  package files, native libraries and loader/ABI prerequisites. Record actual
  member paths, types, sizes, modes and digests, including how native dependency
  resolution is constrained; archive hashes alone do not close runtime imports.
- Exact installed runtime path beneath `/usr/local/lib/aware-filesystem-canary`,
  derived from the admitted artifact identity. No mutable `current` link or
  producer checkout is a launch input. The digest-specific path is not yet known.
- Reviewed setup mechanism, trusted launcher, controller and ordinary-UID probe
  executable closures. A policy table or caller-authored record is not executable
  admission. The worker cannot verify code that already executed during import.
- Capacity observation and funding for acquisition, installed bytes, controller
  evidence and retained failure residue. Proposed worker limits are not measured
  operational fit.

There is no selected executable closure, artifact digest or runnable privileged
command in this handoff. Missing values must fail readiness rather than be
filled with zeros, source-tree hashes or invented installed paths.

## Approval A for setup only

Before asking for approval, bind the actual target host and authenticated
administrative entrance, the reviewed setup executable closure, the complete
planned write set, current destination preimages, account/group collision
observations, resources and retained evidence location. The host has not been
selected merely by cwd or by historical NSS observations.

The fixed proposed semantic targets remain:

| Target | Required treatment |
| --- | --- |
| `aware-fs-canary`, UID/GID 62041 | Fresh locked account/group; no shell or unrelated workload; refuse collisions |
| `/etc/aware/filesystem-staging-canary/v1/9cd6bc0f8e9753b8b5ce318eef15b2ae/setup.json` | Fresh root-owned, single-link 0444 metadata after root creation |
| `/var/lib/aware/filesystem-staging-canary/v1/9cd6bc0f8e9753b8b5ce318eef15b2ae/writer` | Fresh worker-owned 0700 leaf beneath root-owned 0755 ancestors |
| `/usr/local/lib/aware-filesystem-canary` | Protected executable parent; exact immutable descendant supplied by Release |

The actual setup write set must also enumerate the selected account database
effects and every missing intermediate ancestor. This table is not that complete
write set and grants no permission to create broad parent trees. Do not adopt,
chmod or chown an unknown preexisting case into apparent freshness.

Approval A permits only its exact setup effects, not worker launch. Setup must
retain creation history, actual device/inode and final metadata, account and
group state, namespace/ACL/mount and writable-alias exclusion evidence, installed
closure verification and partial/uncertain effects. Any retained writable alias
or unexcluded ordinary/predecessor writer prevents progression. Root host
administration is trusted; override or unaccounted mutation invalidates the
qualification interval.

After successful setup, publish the exact bounded setup bytes and SHA256. The
record uses the existing worker schema and actual new root identity; its
`closure_sha256` must name the selected verified executable closure, not this
source subtree. Because root identity is created during setup, an actual setup
digest cannot be a precondition of Approval A. Freeze the recipe first, actual
bytes afterward. Unknown setup outcome is retained with no automatic retry,
cleanup or fixed-case reuse.

## Approval B for one bounded launch

Request launch approval only against the successful setup receipt, actual setup
bytes/digest, verified runtime/launcher/controller/probe closures, current host
and resource observations and exact effect/evidence paths. Setup approval alone
does not grant launch. Refuse any mismatch or intervening posture change.

The launcher plan must satisfy the original worker checks without relaxing
them: fixed installed interpreter and `-I -B -m
aware_file_system.staging_worker_canary`, sole `--setup-sha256` value, sanitized
environment, UID/GID 62041 with no other groups, initial identity maps, zero
active/inheritable capabilities and no-new-privileges. FD 0/1/2 are private
root-owned anonymous pipes in the required directions, with no extra live
inherited descriptor. The trusted controller must retain the appropriate pipe
ends; a pipe inode check does not authenticate its peer.

Soft and hard limits are CPU 10 seconds, AS 256 MiB, NOFILE 64, FSIZE 1 MiB and
CORE zero. The controller owns a 20-second wall deadline, 16 KiB combined output
bound and five-second boundary acknowledgments. Resource evidence must report
actual usage and how descendant settlement is verified. These limits do not
authorize a general service, arbitrary commands or a reusable worker session.

## Controller and proof sequence

The only worker mutations are the fixed `writer/probe` directory and
`writer/probe/payload` file. Before dispatch, Approval B must additionally name
the root-owned evidence output and ordinary-UID foreign-directory probe targets,
their expected absent preimages and retained-result handling. No arbitrary probe
path or shell callback may be accepted at runtime.

1. Verify the exact approved closure, setup, fresh unspent case and enforced
   writer-exclusion posture. Start one worker through the admitted launcher.
2. At `mkdir_return`, retain the worker boundary and independently execute the
   fixed substitution attempt as UID 1000. Record credentials, operation,
   target, observed errno, target identities and outcome. Require access refusal
   caused by the intended boundary, not a missing path or malformed attack.
3. Only after that evidence, send exact `continue:mkdir_return\n` once through
   the private controller pipe.
4. Repeat at `first_open`, with independent attempt and evidence, then send
   exact `continue:first_open\n`. Acknowledgments alone are not attack proofs.
5. Collect the worker's positive stored-byte/mode observation, effect and
   cleanup ledger, process outcome and resource observations. Check the root
   and foreign-directory postimages without modifying them. Verify the probe
   tools and worker have settled before concluding the interval.

Any successful substitution, unattributed writer, malformed/truncated output,
lost acknowledgment, unknown effect, resource breach, custody mismatch or
unsettled process stops progression. Preserve residue and evidence; no implicit
retry or deletion. The controller cannot upgrade worker output to
`qualified_backend=true` merely because its own checks passed. Independent
review decides what the actual evidence establishes.

One fixed-case positive run can exercise both boundaries. Interrupted/unknown
outcome deployment controls need their own separately approved fresh cases and
reviewed source coordinates; never reuse this spent case. Current source keeps
`qualified_backend=false` and `namespace_sealed=false` even on success. This
canary does not qualify general nested staging, an exported custody handle,
Interface integration or public installation.

## Smallest next cuts

First, admit original Release class/role and executable-closure receiving design,
plus the real package/lock alignment context. Then implement only the admitted
packaging, verifier and fixed launcher/controller joins with effect-free and
temporary-root controls. Do not widen into a platform rollout or alter current
Product selection. Only a returned exact executable packet makes Approval A
requestable. Setup's actual receipt and digest make Approval B requestable.

After approved empirical evidence, complete general nested staging and retained
custody through original FileSystem ownership, then Interface's exact-snapshot
extractor join. P2a acceptance requires the full positive and substitution
cohort. P2/P3 App installation and public delivery remain separate. ONE APP.
