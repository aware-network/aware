# Aware FileSystem library

`aware-file-system` supplies neutral filesystem mechanisms used by Aware's
Issue and Specification tooling. It does not decide Issue scope, approve a
Specification or publish Git commits. Those decisions stay with the owning
SDK operation and its admitted provider.

Version **0.3.8** adds retained private-directory IO and lossless owner evidence
codecs over the original bounded reader and no-replace writer. Supplier artifacts
do not establish installed Workspace/Agent readiness or public release.
Dependency requirements remain unchanged.

## Using this package

Agents normally consume the supported commands and installation instructions
in the [Aware repository](https://github.com/aware-network/aware). This library
is a dependency, not a separate agent CLI or an alternative authority entrance.
Use the exact distribution supplied by your selected, verified installation;
do not overlay a different wheel or infer availability from this README alone.

Library consumers can obtain the installed distribution version without
assuming that a source checkout is the active installation:

```python
from importlib.metadata import version

print(version("aware-file-system"))
```

Python 3.12 or newer is required by the package. Retained physical operations
use POSIX descriptors and OS-specific no-replace publication primitives. The
portable consumer candidate qualifies Linux x86-64 with Python 3.12; this does
not qualify every operation on every OS or Python version permitted by metadata.

## Physical mechanisms

- `confined_mutation` observes and mutates bounded file bytes through a
  no-follow descriptor walk with expected-state checks. Legacy create may
  prepare missing parents; it is not governed setup authorization.
- `retained_mutation` retains manifest identity and exact byte guards,
  prepares only explicitly admitted directory paths, and permits one guarded
  replacement. The owning operation supplies authorization separately.
- `retained_bootstrap` retains absent targets and explicit ancestors for up to
  three files and 64 directories. It reuses the original traversal, directory
  creation and temporary-write helpers. New directories use `0700` and files
  `0644`; existing files refuse even when bytes match. Every newly created
  ancestor is explicitly admitted. Published bytes survive later refusals;
  scratch cleanup requires the original identity, otherwise residue is reported.
- `retained_package` stages and publishes a new package without replacing an
  existing target. Original custody claims govern resource transfer and
  once-only cleanup; detached observations cannot mint another claim.
- `private_directory` retains an explicit existing canonical directory owned by
  the effective user with exact `0700` permissions. Flat CREATE-only sequences
  and bounded reads use the original descriptor-correlated IO. Root drift
  terminally retires preparation; ordinary hard-linked, symlink and FIFO leaves
  refuse. Parent and child custody remain separate, and cleanup preserves known
  disposal, partial effects and unknown returns without retry. Privacy is an
  observed namespace property, not per-file `0600`, continuous confinement,
  protection from same-user/privileged processes or guaranteed disk allocation.
  Eleven detached evidence types and two strict codecs retain binary/read/error
  evidence; decoding never reconstructs handles or authority.
- `retained_tree_projection` is an unreleased physical source checkpoint.
  It retains native requests, original read pins and fixed scratch coordinates;
  `apply_next_transition` spends one original ordinal before checks or effects.
  CREATE is no-replace; UPDATE/DELETE guard exact original preimages. Explicit
  directories use `0755`, while mode-only changes preserve file identity.
  `validate_current` retains full-plan semantics; `validate_next_current` checks
  only the intrinsic next ordinal's root, ancestors, leaf and assigned scratch
  without spending. Later-leaf drift may therefore leave a valid applied prefix;
  full final verification is still mandatory. The original root descriptor is
  borrowed through owner custody, with fresh identity/mode checks and one actual
  release. All actual acquisition records remain in complete cleanup evidence.
  `finish` verifies the complete postimage; `validate_consumed_current` remains
  read-only until release. Refusals retain known effects, uncertain returns and
  scratch/descriptor cleanup without replay or rollback. Linux mode restoration
  uses an original descriptor-derived `/proc/self/fd` coordinate; other platforms
  are not qualified by the source tests. This supplies neither Issue permission
  nor installed or joined Workspace tree readiness.
- `local_json_state` provides cooperative POSIX JSON read/write transactions
  for compatibility state. Reading can create a parent or lock file. This is
  not confined source admission and must not substitute for a governed writer.

The distribution also contains indexing, filtering and change-detection
utilities. Their presence does not promise a qualified resident watcher,
native engine, service deployment or performance level in the consumer bundle.
No native build or internal service setup is required to consume the qualified
neutral Issue/Specification composition.

## Currentness and effects

Currentness checks compare observed bytes, identities and filesystem metadata.
They are **observed-state checks**, not a log of every intervening write.
Equal-byte writes can leave all compared fields unchanged. Cooperative
descriptor confinement is **not continuous confinement**: an opened directory
descriptor does not stop an uncoordinated process from relocating the directory.
Consumers needing every-write detection or continuous confinement cannot infer
those guarantees from this profile.

Results distinguish applied effects, durability and cleanup. A refusal or
exception can occur after replacement or package publication. Preserve known
effects, unknown outcomes and residual scratch evidence; do not automatically
retry, delete published bytes or treat a fresh observation as renewed write
authority. Lower-owner physical evidence is not authenticated actor evidence.

## Local cooperating-writer source custody

The opt-in `aware_file_system.cooperative_source` module (0.3.9) supplies
physical source custody, not Object, Subject, branch or Actor authority.
Its explicit profile is `aware.filesystem.local-cooperating-source.v1` on
local POSIX filesystems with working `flock` semantics. It does not establish
remote-filesystem support or protect against arbitrary OS writes, hostile
Python reflection, control-file deletion or a writer that ignores the protocol.

`initialize_source_authority(root)` explicitly creates the root's private
`.aware-source-authority.v1` lock/epoch file. Participating writer setup may
also create it. These are physical setup effects, not read effects or semantic
allocation. `capture_source_read(root, paths)` never initializes it and refuses
an uninitialized root. Canonical, explicit regular-file paths are opened with
descriptor-relative no-follow traversal; symlinks and multiply linked leaves
refuse. Bounds are 1,024 paths, 256 KiB per file and 8 MiB total.

The original `RetainedSourceRead` exposes immutable captured `sources`,
`require_current()`, `release()` and `reserve_publication()`. A capture retains
descriptors, not a writer lock across application fulfillment. Its short,
nonblocking publication reservation rereads every captured input and holds an
actual shared OS lock against participating writers. Use the reservation only
for a synchronous final validation/publication interval: yielding an asyncio
task retires the read permanently and releases the reservation. Tokens cannot
be copied, serialized or used by another task/thread/process. Unknown cleanup
remains unknown on retry; only owned descriptors are released.

The public reservation context checks its actual entering process, thread and
Task before exit. A foreign exit refuses without consuming the context or
releasing the owner's lock; the owner retains its cleanup rights. Contexts are
single-use and noncopyable. Owner-process teardown explicitly unlocks its
open-file description before close, so a live forked child's inherited copy
cannot prolong the lock. A child cannot use that context or unlock the parent's
active reservation. Other reads retain their own independent reservations.

Every participating source effect must run synchronously inside
`cooperative_source_write(root)`, which holds the exclusive lock and durably
spends the root epoch before yielding. Even failed/no-effect attempts invalidate
older reads conservatively. Never reset, replace or delete the control file
to renew a read. Change-and-restore cannot revive one. Raw OS writes are not
excluded; physical/content rereads detect observed differences, not all possible
uncooperative intervening history. A consumer must qualify its complete source
inventory, authorizations and all relevant writer participation separately.
This module does not infer domain completeness from the explicit path list.

## Scope and license

This dependency does not supply Service/API authority, ontology materialization,
approved iterations, dispatch or an Experience interface. Installing it does not
select an authority mode, authorize an operation or replace the higher-level
record protocol. Follow the selected SDK/CLI's request and admission contract.

Aware-authored files are licensed under Apache-2.0; the complete text is in
`LICENSE`. Keep applicable notices and upstream dependency terms with the
distribution. Historical implementation recipes and receipts are retained in
the source repository's module reports, not presented as current installation
instructions in this package metadata.
