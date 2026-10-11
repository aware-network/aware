# Initializer instruction freeze

Instructions are frozen for the locally selected initializer candidate, pending
independent instruction review. This freezes customer wording, not new runtime
behavior, contributor governance or public-delivery authorization.

[INSTRUCTIONS.json](INSTRUCTIONS.json) pins the exact customer entrance,
workflow, protocol descriptions and typed draft example. Its byte counts and
SHA-256 values are evidence, not another software catalog. Workspace's authored
`portable_protocols` profile remains the sole package selector.

## Exact software and scope

Baseline: `e519fffda47ea66a9ff69b874b3919702765cca2`, the owner-backed selection
closeout. The unchanged whole envelope is
`5f0edebe568d1cfd8a06a33e6122cd4e0d3dd68f764058b1aa098456cc2df13c`;
payload `2d812c489485ee187cf45fca012fffdfda5fcdf93d60495a02b843f94e4a8b68`.
The source-index SHA-256 remains
`69b4581f7ceef335fc9eb28f5e507198a638be56ab761e662ae60d195a8edfd1`.
Installer, wheels, source, notices, raw audit and contributor a6 remain unchanged.

The workflow now uses the same whole-envelope installer as the root entrance.
It no longer directs customers to bypass source/notice carriage by installing
the inner archive alone. Generated customer guidance still comes from the
original Protocol supplier, not this instruction record.

Readable protocol guidance, tooling installation, repository preparation,
operational configuration and service startup are separate decisions.
New-repository preview supplies Workspace preparation and prospective Protocol
inputs; apply obtains fresh Protocol admission after repository preparation.
Paths, current guards and creation/apply intent stay explicit. No automatic
guard refresh, retry, overwrite, staging, seed commit, remote or Issue opening
is implied. SPEC setup remains separately Issue-governed.

## Qualifications

Six detached-wheel legal gaps remain unresolved. Delivery requires the complete
envelope, including corresponding source, license texts and all notice inputs.
The twelve raw audit findings remain unsuppressed. Conservative component
coverage is not exact binary-linkage evidence or a legal warranty.

The installed 2,098-case proof remains its own acceptance, not a result of this
wording change. No unassisted onboarding or customer workflow is claimed here.
Guard discovery, approved iterations, Goals, services and object/materialization
authority are not added. The previous selection and integration records retain
their historical instruction status and tests; they are not rewritten to pass
against this successor.

## Independent replay and next action

Use an existing maintainer Python/pytest, Linux `bwrap`, Python 3.12 and a new
private scratch directory from this checkout root:

```sh
instruction_replay="$(mktemp -d /tmp/aware-initializer-instructions.XXXXXXXX)"
chmod 700 "$instruction_replay"
AWARE_INITIALIZER_INTEGRATION_REPLAY_ROOT="$instruction_replay" \
  python -B -m pytest -q -p no:cacheprovider \
  releases/canonical-initializer-fs-v1/test_instruction_freeze.py \
  --junitxml="$instruction_replay/instructions.xml"
```

The maintainer checks verify exact instruction bytes, the ten-path effect scope,
unaffected baseline bytes/modes, executable installation guards, local links
and supported command help after fresh offline, checkout-hidden installation.
The installation test reuses the accepted owner-backed installer proof; it is
not a new participant runner or a domain-matrix replay.

The instruction index excludes this governance record, its own JSON, selection
metadata, tests and Issue receipts to avoid self-referential hashes. Those
governance bytes are retained in Git. Changed customer instructions require
new byte pins and review; old pins are not silently reused.

Next: independent instruction review and owner-backed closeout, then separately
authorized revision-pinned public delivery and acquisition proof. No transfer,
push, registry release or contributor CLI migration is authorized by this freeze.

## Implementer evidence

Seven checks passed, including one fresh offline installation with producer
checkouts hidden and inherited environment cleared. All 40 pinned package
versions matched, dependency checks passed and no editable/direct-URL records
were present. Ten documented operation help entrances activated through the
same installed `aware`. Missing harness identity refused without effects;
environment reuse refused and private-parent permissions stayed `0700`.

Instruction-index SHA-256:
`cd86d0c8ced285d86acf52410da45784ff3f83aafeab328b2276ae9c4d537c0e`.
Private JUnit: `/tmp/aware-initializer-instruction-freeze.VVscUhpI/instructions.xml`,
SHA-256 `60b352a851aabbcf317d1a92bb0c188e5095ec2dbd626ff0882543bad1f76774`.
Private installed receipt: `/tmp/aware-initializer-instruction-freeze.VVscUhpI/installed-receipt.json`,
SHA-256 `5589d41c190a70a7bed83701ccf28ad115d492113a969cafef5c6a893980a6d5`.
Private paths are maintainer evidence, not customer prerequisites.

The first accounting replay retained five passes and one failure: its negative
assertion also matched the legitimate command-variable assignment. The test
was narrowed to obsolete direct command invocations; instruction bytes did
not change. That failed JUnit remains retained as `accounting-first.xml`,
SHA-256 `30bf34b1b7adb92ef5ddcaee6719bf2b9b0f3cda00b96ce0e3231fb471e06d6c`.
This evidence is implementation proof, not independent acceptance or a repeat
of the 2,098-case domain matrix.
