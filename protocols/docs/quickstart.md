# Install and try the filesystem reader

Prerequisites: Git, Linux x86-64, and CPython 3.12 with `venv`/`pip` support.
The interpreter and system tools are host prerequisites, not silently fetched
dependencies. No service or Aware development checkout is required.

From the public repository root:

```sh
python3.12 protocols/install.py --python-executable /usr/bin/python3.12 \
  --venv /tmp/aware-goal-preview-env
python3.12 protocols/demo.py --cli /tmp/aware-goal-preview-env/bin/aware-goal-native
```

Use your actual Python 3.12 executable and a new, user-selected environment
path. The installer rejects a different interpreter or an existing target,
verifies the exact distribution and both nested archives, and delegates to
the unchanged offline installer. It never chooses Python 3.14 automatically.
The distribution is committed at
[`protocols/distributions/aware-goal-fs-preview-linux_x86_64-py312.tar.gz`](../distributions/aware-goal-fs-preview-linux_x86_64-py312.tar.gz);
its SHA-256 is
`10b126383498b4e4561109f5eb8059161b2c03546d19065b85506f4c41a29c21`.

You can also [download only the source-attached distribution](https://raw.githubusercontent.com/aware-network/aware/main/protocols/distributions/aware-goal-fs-preview-linux_x86_64-py312.tar.gz)
instead of cloning the infrastructure tree. Verify that digest, extract into
a new directory, and follow the enclosed README: verify `SHA256SUMS`, extract
`payload/aware-goal-native-fs-v2-linux_x86_64-py312.tar.gz`, verify its checksums,
then run `PYTHON_BIN=/actual/python3.12 /bin/sh ./install.sh /absolute/new-venv`.
The archive's `cb-test` directory label is a retained build label, not a
different Protocol or authority mode. The cloned sample is optional test input;
the reader installation itself does not require this repository's workspaces.

The demo uses the committed synthetic sample, calls all four supported command
forms, retains exact JSON receipts in a temporary directory, and checks that
HEAD, index, worktree status and Goal bytes did not change. It should report
`eligible` and `current`. These are observations of a sample, not permission
to undertake customer work. A refused observation is not a reason to edit the
sample or customer records.

## Bring already-qualified input

This preview does **not** create/import your Goal or set up your manifest. An
authorized preparation owner must already provide a provenance-qualified,
committed strict V2/V3 Goal, an explicitly selected `aware.protocol.toml`, and
the exact approved Goal/Lane/Phase coordinates. The sample manifest demonstrates
syntax; copying it is not admission of a customer's Goal. If you lack qualified
inputs, use the sample and report the onboarding gap—do not invent authority.

Given those inputs, call the installed command as follows (replace placeholders):

```text
aware-goal-native --repository-root <repo> --manifest-path <repo>/aware.protocol.toml \
  --discover-goal-path <repo-relative-goal-path> --lane-key <lane> --phase-key <phase>

aware-goal-native --repository-root <repo> --manifest-path <repo>/aware.protocol.toml \
  --request-file <exact-discovery-output.json> \
  [--prerequisite-goal <goal-tag>=<repo-relative-prerequisite-path>]

aware-goal-native observe_phase_direction \
  --repository-root <repo> --manifest-path <repo>/aware.protocol.toml \
  --goal-path <repo-relative-goal-path> --goal-tag <goal-tag> \
  --lane-key <lane> --phase-key <phase>

aware-goal-native verify_phase_direction_currentness \
  --repository-root <repo> --manifest-path <repo>/aware.protocol.toml \
  --goal-path <repo-relative-goal-path> --receipt-file <exact-direction-output.json>
```

Save discovery's **exact** output as the eligibility request. Save direction's
exact output for the next execution to verify. Keep receipts outside
authoritative Goal/Issue files; report `held`, `stale` and refusals unchanged.
Only provide cross-Goal hints for explicitly approved prerequisite sources.

## Source and notices

The archive includes the complete notice envelope and an exact source capsule.
The same source capsule is extracted for inspection under
[`workspaces/`](../../workspaces/README.md). Aware source/build inputs are pinned
to `3bea9cc913644700be810398293bca899020c299`; this does not require that private
development revision to be accessible because its selected bytes are attached
and public here. The modified `jsonschema 4.26.0+aware.1` source recipe is in
the capsule with its checksum-qualified upstream source URL. It removes
benchmark resources; it does not change the 25 retained runtime modules.
Keep the accompanying third-party texts when redistributing this preview.
