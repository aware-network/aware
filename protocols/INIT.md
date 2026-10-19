# Init summary streams and explicit decisions

Issue CLI **0.8.4** instructions are frozen locally pending independent review;
public delivery is not yet authorized. Use this reviewed checkout and its
whole-envelope installer, not the delivered predecessor's acquisition path.
Instruction pins grant no operation authority. Both reviews and original guards
remain; carrying an Issue observation does not freeze previewed source bytes.

Historical freezes remain unchanged.
Use the one [whole-envelope installation](../README.md) and your genuine harness
identity. Keep the [public contributor checkout](../AGENTS.md) separate from
the explicitly selected customer target. No service, Issue admission or
Workspace apply authority follows from installing or configuring tooling.

Parallel activation is outside this delivery. No activation qualification or
inclusion follows from this instruction freeze.

## Read init summaries and preserve full receipts

Init keeps its default JSON output. Select `--format summary` explicitly for
human-readable answers: **What happened**, **What changed**,
**What remains uncertain**, **What next (guidance, not authority)** and
**Where is full evidence**. The full `aware.agent.init.v1` JSON is emitted on
**stderr in the same invocation**, while the summary is on stdout. Explicit
`--format json` retains the same transport as default JSON: full JSON on
stdout. Stderr is not an error-only channel when summary format is selected.

Choose the customer repository explicitly; do not initialize the acquired
public source checkout. For an absent intended target, preview first:

```bash
: "${aware_repo_root:?Set the absolute intended customer repository}"
"$AWARE" init --repo-root "$aware_repo_root" --create-repository --format summary
```

Stop and review that preview and its complete JSON before making a separate
creation decision. A new-repository preview has no effects, verified completion
or admitted Protocol plan; it reports prospective Protocol inputs. Creation
requires explicit intent. Only after accepting that request, invoke:

```bash
"$AWARE" init --repo-root "$aware_repo_root" --create-repository --apply --format summary
```

Do not blindly execute both blocks as an unattended sequence. Apply obtains
fresh Protocol admission after Workspace preparation; a preview is not a
reusable admission. Both original owner receipts remain available in full.
An existing repository or missing explicit creation intent has its own original
owner outcome; do not infer creation from presentation alone.

If retaining command output, capture both streams during the original invocation
to distinct, newly chosen files. Do not repeat a mutating command to obtain
JSON or a better summary. Full output may describe known effects, partial
publication, refused work or original cleanup uncertainty. Summary omission
does not erase that evidence and does not restore authority.

Output failure returns **3**, or preserves **130** for an existing interruption.
Either may coexist with already completed owner effects. The surviving stream
still carries available evidence; the process does not redispatch either owner.
Do not retry merely because a stream was lost. Stop and inspect retained
evidence before any separately supported recovery decision. The source-qualified
and installed closed-pipe checks do not imply a saved receipt exists when no
capture or durable reference was returned.


After successful initialization read the target's `AGENTS.md` and
`aware.protocol.toml`, then follow [the first-Issue guide](issues/FIRST-ISSUE.md).
Workspace setup remains a separate [two-review operation](workspace/REVIEWED-SETUP.md).
Keep [complete terms, source and notices](../releases/canonical-reference-fs-v1/README.md)
with the installation. Wider capability and release acceptance remain separate.
