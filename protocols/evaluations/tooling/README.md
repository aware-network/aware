# Optional evaluator evidence tooling v1

`evidence.py` is a standard-library **Linux producer/evaluator helper**, not an
installed Aware interface or a runtime dependency. It does not choose work,
coordinate agents, authenticate an actor, evaluate acceptance, or transfer a
report. The product stays at a6; submission schemas stay at v2.

Use this only in an approved evaluation. Do not give U a private driver, probe
plan, hidden answers or prior transcripts. A coordinator may arrange mechanical
capture without prescribing the worker's product commands; disclose that setup
and any assistance. The worker still discovers and invokes the installed product.
The helper cannot capture tool calls, file edits or observations made outside it.
Missing earlier command/timestamp evidence remains unknown, not reconstructed.

## Capture from the first observed command

The preparation owner supplies an absolute helper path, a Python 3.12+ interpreter
and a separate private evidence coordinate before discovery begins. Existing
private roots must be real, owner-held directories with no group/world permission
bits. The helper creates a missing root as 0700 but never changes an existing
root's permissions. Parents must already exist. Keep roots and outputs outside
customer authority records and source scope.

These are evaluator examples, **not a U command recipe**. Replace executables and
arguments with what that execution actually selected. Stable capture IDs reserve
one invocation each:

```sh
/absolute/helper-python -I -B /absolute/evidence.py capture \
  --private-root /private/evaluation/u --capture-id identity --pass U \
  --executable-ref selected-command -- /usr/bin/printenv CODEX_THREAD_ID

/absolute/helper-python -I -B /absolute/evidence.py capture \
  --private-root /private/evaluation/u --capture-id discovery --pass U \
  --executable-ref selected-command -- /absolute/installed/aware --help
```

The helper discovers exactly one nonblank `CODEX_THREAD_ID` or
`CLAUDE_CODE_SESSION_ID` itself and records its provider-qualified identity.
These harness adapters currently accept UUID session values; other formats are
explicitly unsupported, not permission to rename variables or borrow an ID.
Missing/ambiguous identity refuses before creating evidence or executing a child.
This is declared harness provenance, not authenticated identity.

A fsynced start precedes the subprocess. Raw exact argv, cwd, stdout and stderr
stay private. Commands run without an implicit shell; use an absolute executable.
The lock serializes capture within one root; never nest captures using that same
root (the child would wait on its parent's lock). Command stdout/stderr are redirected
to `<capture-id>/stdout` and `stderr`: inspect them privately, then choose the next
action. Do not rerun to recover display output. A completed capture returns the
child's exit status; helper failure returns 3 and instructs inspection. A child
may itself return 3: inspect the journal, not just the wrapper exit code.

Duplicate IDs and partial reservations refuse reuse. There is **no automatic
retry**, timeout or rollback. A start with no finish means completion/effect is
unknown; private streams or actual product receipts may establish more. Child
spawn failures retain null exit code and the observed exception class. A complete
capture is not proof of product success. Do not assign a new ID merely to replay
an operation after a logging, formatting or exporter failure. Obtain the current
product state through a separately captured read and follow its real owner.

## Actual interpreter evidence

Record installation and task interpreters separately in the execution/pass that
uses them. `interpreter` performs a fixed probe; it is not caller-supplied version
metadata:

```sh
/absolute/helper-python -I -B /absolute/evidence.py interpreter \
  --private-root /private/evaluation/u --capture-id task-python --pass U \
  --executable-ref task-python -- /absolute/chosen/task-python

/absolute/helper-python -I -B /absolute/evidence.py capture \
  --private-root /private/evaluation/u --capture-id task-tests --pass U \
  --executable-ref task-python -- /absolute/chosen/task-python -m unittest discover -v
```

Use the worker's actual test framework and argv, not this example by default.
Private output includes `sys.executable`, full `sys.version`, numeric version and
implementation. Export retains numeric version and implementation. A command
links to a prior probe only for the **same execution, pass, symbolic role and
exact executable path**; otherwise `interpreter_capture` stays null. That path
match does not prove an unchanged interpreter binary, environment or imports.
The helper interpreter is not evidence of either task or Aware interpreter.

## Freeze U before V

Finish/quiesce U capture, then use separate source/destination coordinates:

```sh
/absolute/helper-python -I -B /absolute/evidence.py freeze \
  /private/evaluation/u /private/evaluation/u-frozen
```

This produces `snapshot.tar.gz`, `inventory.json` and `SHA256SUMS` without editing
input bytes or modes. Ordered archive members have normalized metadata and gzip
mtime; repeat builds under the same interpreter match. The output checksum list
covers the archive and inventory, **not itself**. An existing input checksum file
is carried as evidence, not rewritten. Partial/existing output is never replaced.
Captured roots use their already-existing journal lock; incomplete commands refuse
freeze. Other input writers must be stopped. Symlinks and special files refuse.
The helper compares the source twice to detect observed changes; this is not an
atomic filesystem snapshot, hostile-process control or WORM. Freeze only bounded
evidence trees (the implementation reads bytes into memory), not a large checkout.
The archive is **private raw evidence**, not a sanitized public attachment.
Preserve freeze receipts privately and provide V only its approved probe inputs;
provide a fresh R only approved outcome and durable customer records.

## Null-safe private receipt presentation

```sh
/absolute/helper-python -I -B /absolute/evidence.py receipt /private/actual-result.json
```

This reads saved JSON only, never invokes the product again. Null/non-object
projections remain unknown. Each nested receipt retains its own publication
fields (`operator_ref`, `transaction_mode`, `reference_update`, index state and
receipt refs) without borrowing a sibling/implementation receipt. This projection
is **private**, not a privacy-reviewed export or proof of an enforced refusal.
Full saved receipts remain the evidence; presentation does not replace them.

## Metadata-only allowlisted export

```sh
/absolute/helper-python -I -B /absolute/evidence.py export \
  --private-root /private/evaluation/u /private/review/u-metadata.json
```

Only constructed metadata leaves the private root: typed pass/execution/symbolic
role, normalized observed timestamps, exit code/null, digest/size of raw streams,
argv/journal digests and validated interpreter evidence. Actual streams are
rehashed against the captured receipt before export. Incomplete captures retain
unknown effects. New output only; no overwrite and no output inside the input.
Unknown/ad hoc fields are ignored; invalid selected scalars refuse rather than
being disguised as success.

No raw argv, inline `-c` code, shell programs, patch bodies, cwd, stream text,
SDK envelopes or arbitrary attachments are copied. There is no unsafe
"include everything" switch. Capture IDs become sequential export ordinals.
Digest values refer to the private inputs, **not** byte identity of transformed
artifacts. Metadata-only export deliberately cannot provide an exact sanitized
command or a refusal diagnostic: add those through a separately reviewed report
without exposing executable payloads, customer records or secrets.

This is **not** a complete v2 submission, automatic sanitization certificate or
publication authorization. Review the actual exported bytes and separately
authored report/findings/interactions and validate the assembled v2 submission
with [the existing validator](../v2/validate.py). Keep frozen originals private;
publish corrections at new coordinates. No evaluation acceptance or release
follows from helper success. Existing external archive submissions are unchanged.

## Replay

```sh
/absolute/aware-env/bin/python -I -B -m unittest discover \
  -s protocols/evaluations/tooling -p 'test_*.py' -v
```

Tests use synthetic fixtures and deliberate logger failures. They are helper
proof, not a fresh external customer evaluation or a6 runtime replay.
