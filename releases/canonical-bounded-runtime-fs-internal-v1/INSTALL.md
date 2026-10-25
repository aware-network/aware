# Private supplied-runtime installation

This delivery is for private qualification on the reference Linux x86_64 host
(Ubuntu 24.04/glibc 2.39). It is not public release or legal/disclosure clearance.
No host Python is needed. /bin/sh, dirname, sha256sum, the exact qualified native
tar/gzip tools and ELF libraries, and CPython's platform libraries are still
required; see ENTRANCE.json. Git is separately required for repository operations.

Use absolute paths below. The installation root must already be private and
owned by the consumer; the separate runtime root must satisfy the original
runtime helper's fresh-root requirements. Keep the complete delivery together,
including its descriptor/resource data and source/notice carriage.

```sh
set -eu
entrance=/absolute/path/to/cold-entrance
runtime=/absolute/path/to/fresh-runtime
target=/absolute/path/to/private-install-root
apply_log=/absolute/path/to/retained-original-apply.stdout

"$entrance/install-aware" runtime-preview "$runtime"
"$entrance/install-aware" runtime-apply "$runtime"
"$entrance/install-aware" install-preview "$target" "$runtime"
```

Review the original installation plan. Set reviewed_fp to its exact fingerprint;
do not reuse a fingerprint from another target, runtime selection or packet.
Retain complete original stdout without filtering, selecting or reencoding JSON:

```sh
reviewed_fp=REPLACE_WITH_EXACT_REVIEWED_PLAN_SHA256
"$entrance/install-aware" install-apply "$target" "$runtime" "$reviewed_fp" >"$apply_log"
"$entrance/install-aware" configure "$target" "$runtime" "$reviewed_fp" "$apply_log"
"$entrance/install-aware" run "$target" --help
```

Continue only after each preceding command succeeds. Retain failed/unknown
results and state; do not retry configure or clean up unknown state automatically.
Configure explicitly creates bootstrap-receipt.json and env/aware-native-current.json
once through the original retained initializer. This DATA setup is not Issue
admission, native authority or permission for an SDK operation.

For useful work, replace --help with the original SDK command and its arguments:
install-aware run INSTALL_ROOT [AWARE_ARGS...]. Quote each argument normally; run
forwards them unchanged to the installed original SDK console entry using its
installed interpreter with -I -B. Use this entrance for subsequent CLI launches
to prevent bytecode-cache writes to the supplied runtime. Original SDK commands,
review/admission requirements and errors remain in effect; no commands or policy
are supplied by this guide. No native operation is proved by installation/setup.

For the original typed specification DATA example, see [SPECIFICATION.md](SPECIFICATION.md).
