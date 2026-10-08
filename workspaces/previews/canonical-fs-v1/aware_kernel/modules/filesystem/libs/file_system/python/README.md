# Aware FileSystem library

`aware-file-system` supplies neutral filesystem mechanisms used by Aware's
Issue and Specification tooling. It does not decide Issue scope, approve a
Specification or publish Git commits. Those decisions stay with the owning
SDK operation and its admitted provider.

Version **0.3.2** changes this package description and distribution metadata.
Runtime code and dependency requirements are unchanged from 0.3.1.

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
- `retained_package` stages and publishes a new package without replacing an
  existing target. Original custody claims govern resource transfer and
  once-only cleanup; detached observations cannot mint another claim.
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
