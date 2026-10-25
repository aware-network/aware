# Supplied-Python Linux preview

This is an additive, frozen preview of the original Aware installation rail.
It carries CPython 3.12.15; host Python and the producer checkout are unnecessary.
The qualified host is Ubuntu 24.04, glibc 2.39, x86-64. Other hosts remain unqualified.
The current default public product is preserved; this preview does not adopt its
newer capabilities. Read [disclosures](DISCLOSURES.json) before acquisition.

The private installed workflow passed. Public acquisition and fresh unassisted use
remain to be demonstrated. This local layout is not yet published; use these steps
only after a publisher supplies the exact delivered Git revision and confirms both
assets exist at the bound tag. Never substitute main, latest or a producer revision.

## Acquire the pinned controls and both assets

Prerequisites are ordinary Git, HTTPS curl, /bin/sh, dirname, sha256sum, and the
helper-pinned native GNU tar/gzip and their qualified ELF libraries. The supplied
CPython also needs the declared platform libraries. Exact executable/dependency
bindings are retained in this delivery and the complete envelope; a matching
platform name alone does not qualify another host. No runtime/package resolution,
host Python installation or global `aware` replacement occurs.

This sparse public input checkout is for acquisition, not contribution. Its root
contributor AGENTS.md does not govern a customer repository. Use an absent private
control directory and the actual published revision supplied by the handoff:

```sh
set -eu
umask 077
revision=REPLACE_WITH_EXACT_PUBLISHED_40_HEX_REVISION
controls=/absolute/private/path/to/pinned-aware-controls
test ! -e "$controls"
git init "$controls"
git -C "$controls" remote add origin https://github.com/aware-network/aware.git
git -C "$controls" sparse-checkout init --no-cone
git -C "$controls" sparse-checkout set /releases/canonical-bounded-runtime-fs-internal-v1/
git -C "$controls" fetch --filter=blob:none --depth=1 origin "$revision"
git -C "$controls" checkout --detach FETCH_HEAD
test "$(git -C "$controls" rev-parse HEAD)" = "$revision"
entrance="$controls/releases/canonical-bounded-runtime-fs-internal-v1"
asset_origin=https://github.com/aware-network/aware/releases/download/supplied-runtime-linux-x86_64-20261025-preview1
curl --fail --location --proto '=https' --proto-redir '=https' --max-filesize 34340172 --output "$entrance/runtime.tar.gz" "$asset_origin/runtime.tar.gz"
curl --fail --location --proto '=https' --proto-redir '=https' --max-filesize 341704230 --output "$entrance/bundle/releases/canonical-bounded-runtime-fs-internal-v1/aware-canonical-bounded-runtime-source-notice-v1.tar.gz" "$asset_origin/aware-canonical-bounded-runtime-source-notice-v1.tar.gz"
(cd "$entrance" && sha256sum --check --strict SHA256SUMS)
```

The pinned Git revision binds the checksum/control files; release-asset names or
redirects alone do not establish byte identity. Stop on any acquisition or checksum
failure. Keep both assets, original controls, complete envelope and source/notices.
The existing entrance performs its original verification before execution.

## Install once at final private roots

Choose permanent version-specific paths now. Do not install into a temporary
location and move the runtime or venv afterward. The **installation root must
already be private and owned by you**; its `env` child must be absent. The separate
runtime root must be absent and satisfy the original helper's fresh-root checks.
Prepare only the installation directory under your existing private parent:

```sh
runtime=/absolute/private/path/to/aware-preview1-runtime
target=/absolute/private/path/to/aware-preview1-install
apply_log=/absolute/private/path/to/preview1-original-apply.stdout
test ! -e "$runtime"
test ! -e "$target"
mkdir -m 700 "$target"
"$entrance/install-aware" runtime-preview "$runtime"
"$entrance/install-aware" runtime-apply "$runtime"
"$entrance/install-aware" install-preview "$target" "$runtime"
```

Review that original plan. Use its exact fingerprint for this target, runtime and
packet. Preserve the complete original apply stdout, without filtering or rewriting:

```sh
reviewed_fp=REPLACE_WITH_EXACT_REVIEWED_PLAN_SHA256
"$entrance/install-aware" install-apply "$target" "$runtime" "$reviewed_fp" >"$apply_log"
"$entrance/install-aware" configure "$target" "$runtime" "$reviewed_fp" "$apply_log"
"$entrance/install-aware" run "$target" --help
```

Proceed only after each command succeeds. On failure or unknown completion, retain
state and the complete result; do not automatically retry or remove the roots.
The installation was qualified with a 128 MiB limit. This does not claim headroom,
a cold-cache peak or a 128 MiB ceiling for later useful/native operations.

## Do useful work through the installed client

Continue through `install-aware run INSTALL_ROOT [AWARE_ARGS...]`, which forwards
arguments to the original installed SDK with isolated, bytecode-disabled Python.
The ambient `aware` command may be another application. Use installed help and
init-created customer instructions for the available commands and Issue admission.
For typed SPEC DATA, use [SPECIFICATION.md](SPECIFICATION.md); DATA creation grants
no authority. Keep explicit review/preview/apply boundaries and original guards.

Before local customer commits, configure the customer's own Git author identity.
The installer does not invent an author, Human identity, Issue or service authority.
No automatic activation, existing-install replacement or remote publication is
included. Neither Project/Goal elevation nor I04 recovery is a first-install gate.

`ENTRANCE.json` and `INSTALL.md` remain byte-exact private packaging/proof records;
their historical scope and false acceptance flags are preserved. This README,
`DELIVERY.json` and `DISCLOSURES.json` describe the additive preview proposal.
All source/notice attachments and native provenance qualifications remain required.
