# Complete a first useful task with Aware

Issue CLI **0.8.4**, with Agent **0.2.0a14**, was published at `813ab2e82f7ff0fa24403c6889bf82e2c8b121fb`.
Acquire that exact revision and retain its complete source/notice envelope.
This alignment changes current wording and pins, not software or operation authority.
Both reviews and original guards remain required. Additional publication of this
wording alignment requires independent review and separate authorization.

Consumer guidance for delivered Issue CLI 0.8.4 with Agent 0.2.0a14.
Earlier trial evidence remains version-bound; this is not a new evaluation or
authorization for a customer run.

Aware helps agents coordinate bounded repository work and leave evidence another
execution can review and lawfully continue. **The first useful outcome is a
customer change that works, not an Issue, Specification or manifest by itself.**
The agent implements and tests the change; Aware supplies coordination and
governed operations, not application correctness or a sandbox.

## Choose the outcome before the commands

Start with **Issue → optional SPEC → bounded work → verification → publication
and closeout**. No Project, Goal, service or object infrastructure is required.
A Specification draft helps when shared intent needs a durable description;
it is not a compulsory detour for a small repair.

The customer chooses a real, small deliverable and its acceptance checks. For a
first trial, a read-only JSON checker is a suitable example: a local command
accepts one input file, reports whether it contains valid JSON, returns a
documented nonzero result for malformed input or an unreadable file, and never
modifies that input. Include automated tests, usage documentation and observed
input-byte preservation. A generated repository manifest does not satisfy this
outcome. Another small customer-approved bug fix or tool is equally valid.

Before work, the customer brief must name:

- The intended result and observable acceptance checks, including task-specific
  error cases; any exact output names must be separate, unambiguous fields.
- The absolute customer repository and whether creating it is authorized.
  This first-use profile prefers a new target; adoption into an existing
  governed repository requires compatibility review, not overwritten guidance.
- The allowed source/test/document paths, baseline or absent-target state, and
  unrelated files or modes that must survive. The Issue record and any required
  configuration/publication effects must also be explicitly scoped.
- Whether local publication/closeout is authorized and the explicit local Git
  author to use. Remote push, deployment and distribution are separate effects.

Clear task direction is sufficient authorization within its bounds; ask only
about a missing target, material ambiguity or additional effect. Read the target's
instructions before mutation. Do not infer a task, scope or authority from a
transcript, cached selection or the fact that a command is available.

Earlier evaluated guidance `379cd5dcbe26c256be82c760b73fc100fdfc0fc6` ran against Agent a11 at `faed3f46668a3ec111d8fbf4cf1d5a287d5e1b89`. These remain distinct guidance/software coordinates, not a new evaluation of CLI 0.8.4. Read [current supported use](../releases/canonical-issue084-fs-v1/PUBLIC-STATUS.md) for exact evidence and limits; historical checkpoints are not live availability.

## Follow one installed consumer rail

Use the [pinned public acquisition and installation instructions](https://github.com/aware-network/aware/blob/08a598fdeb8f960bf30fb8e85229e820286e67be/README.md)
and [complete distribution terms](https://github.com/aware-network/aware/blob/08a598fdeb8f960bf30fb8e85229e820286e67be/releases/canonical-a14-fs-v1/README.md).
This release requires Linux x86-64, Git and Python 3.12. Retain the whole
source/notice envelope. Six detached-wheel legal gaps remain unresolved;
detached wheels, stripped bundles and registry delivery are not accepted.

Acquire the exact revision, not a moving `main`. Verify installation provenance
before reusing an environment: Agent version alone is insufficient. A retained
installation must match the selected payload and complete source/notice envelope.
The installer refuses an existing destination; do not overlay or reinstall into
it. Use the original installed command, not imports from a development checkout.

Pinned product pages retain historical checkpoint wording. Read the current
[starting instructions](../README.md) and
[status](../releases/canonical-issue084-fs-v1/PUBLIC-STATUS.md).
Historical freezes are not rewritten or renewed admissions.

The public source checkout's contributor `AGENTS.md` and a6 command selection
govern contributions there, not the customer target. Likewise, aware-dev's
`aware-cli` is not the public consumer command. Never copy a contributor bootstrap
into a customer repository or replace an existing selected command implicitly.

## Make the useful change

1. Read the [coherence rules](https://github.com/aware-network/aware/blob/08a598fdeb8f960bf30fb8e85229e820286e67be/protocols/COHERENCE.md).
   Use exactly one genuine supported harness identity. Declared actors and
   receipts do not authenticate every action or provide filesystem isolation.
2. Follow [initialization](https://github.com/aware-network/aware/blob/813ab2e82f7ff0fa24403c6889bf82e2c8b121fb/protocols/INIT.md).
   Inspect preview, then separately choose apply. Capture both original streams:
   summary mode keeps full JSON on stderr in the same invocation. Init supplies
   configuration, not Issue admission, scope approval or apply authority. It
   creates no seed commit or remote and starts no service.
3. Use the complete [implementation branch](issues/FIRST-ISSUE.md#implementation-branch-for-a-tested-json-checker) for the selected JSON checker, or separately admit your own task's exact paths. The draft branch remains available for draft-only work. Observe owner, exact scope and `in_progress` through the original Issue owner before editing; no translation from a draft objective is needed.
4. Add a SPEC draft only if selected for this task, using the original
   [setup, typed input, target-fit and explicit preview/apply workflow](https://github.com/aware-network/aware/blob/08a598fdeb8f960bf30fb8e85229e820286e67be/protocols/WORKFLOW.md).
   Choose that before the affected design work; a draft does not approve an
   implementation. Repository-manifest setup is also optional unless the task
   needs it. If used, preserve [both review decisions](https://github.com/aware-network/aware/blob/08a598fdeb8f960bf30fb8e85229e820286e67be/protocols/workspace/REVIEWED-SETUP.md):
   complete physical scope first, final-file apply second. Setup is not Package/A2
   acceptance or application implementation.
5. Implement and test the customer change with its approved engineering tools.
   Record actual editor/test effects honestly; do not label provider-native
   edits as Workspace mutation receipts. Use the target's instructions and
   admitted boundaries. Missing write authority is a stop, not permission to
   invent a file-writing command or bypass repository governance.
6. Check the actual deliverable against the customer's acceptance tests, inspect
   source changes and verify unrelated bytes/modes. A zero tooling exit, valid
   receipt or closed Issue does not establish that the application works.
7. If authorized, use the original [publication and closeout owners](https://github.com/aware-network/aware/blob/08a598fdeb8f960bf30fb8e85229e820286e67be/protocols/repository/README.md):
   dry-run exact admitted paths, review, then apply the identical publication
   request. Publication and closeout are distinct, non-atomic effects. Retain
   commit, CAS/index and closure evidence separately. Without that authorization,
   report verified but unpublished work, not completed publication.

Use existing pinned instructions and installed help for syntax; this contract
adds no commands, package selector, writer or authority. Agent **0.2.0a12**
supports both the original inline `--reference` JSON and explicit
`--reference-from-stdin` input for Workspace review. Optional historical
`show --focus` views help inspect scope or files; they grant no current-use
authority. Follow [reference navigation](workspace/REFERENCE-NAVIGATION.md)
for exact syntax, input limits and original-result pairing: scope consumes the
original prepare result; apply consumes the original second-preview result.
Keep the separate scope and final-file review decisions. These Workspace
helpers do not automate Issue guard extraction, publication or closeout, and
are not prerequisites for an Issue-only implementation task. Keep reviewed
guards unchanged; staleness requires a new explicit observation and review,
never automatic guard refresh or mutation retry.

## Stop without hiding what happened

Keep original references and reviewed guards unchanged. A stale request requires
a new explicit observation and review, never automatic refresh or mutation retry.
Missing configuration, unsupported commands and conflicting instructions require
an explicit disposition; do not guess, manufacture authority or borrow identities.

Clean stale refusals can exit 2. Genuine retention/output incompleteness can exit
3, and interruption remains 130. Those exits do not erase known effects. Original
release uncertainty remains unknown even if later client cleanup completes.
Preserve full surviving evidence; a missing reference stays missing. Historical
reads do not renew approval or transfer live admission. Never repeat a mutation
or republish merely to recover output or spent closeout authority.

A replacement execution needs lawful transfer/admission and its own current
reviews. Planned recovery is a separate scenario, not permission to resume from
a transcript or reuse predecessor process-local authority.

## Show the value and its limits

The [evidence map](EVIDENCE-MAP.json) binds the shipped product and exact public
[U](https://github.com/aware-network/aware-client-evaluations/blob/33b3916f1a0d81c9662b03f54fac4a4f6afaefd8/evaluations/2026/10/18/workspace-faed3f-unassisted/evaluation.md),
[V](https://github.com/aware-network/aware-client-evaluations/blob/33b3916f1a0d81c9662b03f54fac4a4f6afaefd8/evaluations/2026/10/18/workspace-faed3f-guided-v-sanitization1/evaluation.md)
and [R](https://github.com/aware-network/aware-client-evaluations/blob/33b3916f1a0d81c9662b03f54fac4a4f6afaefd8/evaluations/2026/10/18/workspace-faed3f-planned-r-correction1/evaluation.md)
reports. U completed manifest setup with coordinator-prepared installation,
not customer code or publication. Guided V exercised parser consent and stale
refusals; spent reuse preserved measured state with exit-3 incompleteness.
Planned R established lawful continuation and scope/sentinel preservation, but
an ambiguous brief prevents exact intended-name conformance. Shared filesystem
visibility was disclosed; these are not isolated swarm or crash-recovery proofs.

These observations support bounded coordination and clearer immediate decisions.
They do not measure faster work, reduced Human intervention, broad onboarding,
customer application correctness or full coherence. A later coordinator-selected useful-work U reported code and local closeout; its [current evidence and limits](../releases/canonical-issue084-fs-v1/PUBLIC-STATUS.md) are separate from that earlier U/V/R. The next task trial should be genuinely customer-selected and compatibility-reviewed for an existing repository.

For that run, report the exact customer outcome; test commands/results and actual
interpreter; source scope and preservation; publication/closeout state; blockers,
Human hints and product retries; manual reference extractions; and evidence-reading
effort in defined units. Keep product calls, shell batches and document reads
separate. Record installation as fresh or provenance-verified reuse, not both.
Elapsed time is descriptive; productivity comparisons need matched tasks and
baselines. Keep cost and unobserved measures unknown.

Use the existing [evaluation capture and v2 submission procedure](https://github.com/aware-network/aware/blob/08a598fdeb8f960bf30fb8e85229e820286e67be/protocols/evaluations/README.md).
Freeze U before separate guided V or planned R; hints end its unassisted segment.
Sanitize exported evidence, retain private receipts, and admit exact archive
coordinates separately. Earlier frozen evaluations remain unchanged. This
contract supplies no evaluator runner, hidden answer key or automatic pass.

Project/Goal direction, language and Meta-first materialization, Object execution,
services and activation remain parallel, separately qualified extensions. They
must preserve the same owners and evidence meanings, not become today's barrier
to a useful Issue-first task.
