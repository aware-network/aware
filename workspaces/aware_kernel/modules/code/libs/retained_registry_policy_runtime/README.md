# Neutral retained registry policy calculation

`calculate_registry_policy(scope, catalog)` implements the deterministic source
calculation for `aware.code.retained-registry-policy.v1`. Inputs are the existing
CodeRetainedScopeProjection and portable CodeSemanticContractCatalog; the result
is the existing input-only RegistryPolicy. Neither inputs nor result confer authority.

Dependencies are only neutral Code module grammar and semantic contract runtime.
No Workspace import, scan, body store, callback, caller grant, rule selection or
service construction exists. The dependency-free contract runtime is unchanged.

The calculation parses every module as v2, matches all authored package rows to
retained membership and manifest locations, retains nonparticipants, rejects
incomplete participants, resolves same-scope registrations, checks each declared
stage's exact catalog profile/provider binding, requires exact package kinds and
manifest basenames, and verifies dependency targets name complete participants.
Existing RegistryPolicy validation rejects conflicting namespace/root assignments.

Registration digests hash the canonical neutral registration table. The policy
scope digest is the complete neutral projection digest. Comment-only module
changes therefore change scope evidence while preserving unchanged grants.

This is isolated portable calculation, not the complete trusted producer entrance.
Host composition must authenticate the original scope adapter and catalog, exact
live selected-provider implementation/configuration, and producer lifecycle; it
must validate scope before and after calculation before retaining
AdmittedRegistryPolicy. Portable executable coordinates are not live executable proof.
Selected-owner semantic name/dependency-constraint convergence remains downstream.

The first policy supports only same-Workspace registrations and all-v2 module
scopes. No repository declarations are migrated. Root lockfile and installed
dependency qualification remain untouched; source tests use explicit Code paths.

## Original grammar host attachment receiving checks

The optional `grammar_role_attachment` module now retains one private attempt
in the original direct-host state. It derives the two original factory-owned
registrations, catalog resolver, declaration issuer and epoch binding there;
callers cannot supply replacement callbacks, a resolver or a detached role host.
Original source/context checks run outside parent exclusion under the existing
synchronous epoch-use obligation. Mutated or retired attempts cannot be revived
by restoring bytes or coordinates.

This is an internal receiving unit, not the public registered-role constructor.
It constructs no producer registration or retained result and enables no factory
execution. Cleanup-only custody is now retained as described below. Tests use
original Code products and original host/epoch mechanics with an explicitly
synthetic source/lifetime owner.
Genuine Workspace application intake, Language producer/result and dependency
admission, async quiescence/cleanup, SDK generation and installation remain
separate proofs. Base imports, exports, metadata and dependencies are unchanged.

## Original async grammar role epoch lifetime

The internal `grammar_role_epoch` support encloses lexical async role work on
the original attachment. Its exact expectations reserve at most two once-only
uses. Original participant hooks begin/start and finish/abandon the obligation;
no parent exclusion spans source callbacks or an `await`. Concurrent and replayed
uses refuse. Cancellation settles only after the enclosed async cleanup ends.

Work quiescence, epoch settlement and exclusion release are distinct evidence.
Failed settlement stays uncertain even after source restoration or forced parent
retirement. Body failures and interruptions keep their original objects, with
finish/release failures chained separately. Crossing the originating task does
not prove quiescence. The attachment retains the evidence after revocation.

This is private lexical lifetime support, not producer/result/dependency
admission, a public constructor, a cleanup ticket or verified resource disposal.
Detached/background work is not supported. The original registered-role owner
must enclose all awaited work when that constructor is implemented. No factory
execution, SDK operation, parser generation or installed capability is enabled.

## Original cleanup custody and detached reads

`grammar_role_cleanup` issues one sealed cleanup-only ticket on the original
attachment before its source validation. `read_grammar_role_cleanup(ticket)`
returns the existing Code-owned portable receipt without source reads, provider
calls, epoch transitions or borrowed-owner cleanup. Only original ticket identity
can select custody; equal receipts, copied attachments/custody and forged tickets
cannot adopt it. Process/thread and retained-journal identity remain checked.

Operation/input correlation is published atomically only after original
validation, final snapshot checks and scalar preparation succeed.
Construction failures retain the original error process-locally and leave those
correlations absent. A synchronous validation failure supplies no separate
settlement receipt, so the snapshot keeps uncertain epoch accounting even when
the tracker is empty. Parent revocation never upgrades running/uncertain evidence.

Snapshots remain `completion=unverified` while the owned attachment is pending;
released epoch evidence alone cannot complete resource cleanup.

## Once-only owned resource disposal

`dispose_grammar_role_cleanup(ticket)` releases the original Code-owned
attachment's execution association by terminal retirement, retaining its custody
and evidence. When the bounded profile source role has acquired its own input
host, registration or retained result, disposal uses their original release ports
in result → registration → host order. It does not close the borrowed host,
participant, catalog, products or source. Original async journal reservation precedes borrowed validation;
lexical lifetime evidence spans acquisition, yielded work and settlement unwind.
Active or unverified work refuses disposal without spending the ticket.

Once reserved, disposal cannot replay. Repeated disposal/read returns the exact
terminal immutable receipt. Failed/invalid release remains unknown, even if the
attachment retired; restoration cannot upgrade it. Terminal snapshot failure
retains original errors and confirmed release independently, but refuses further
disposal/read rather than reconstructing a missing terminal receipt.

Quiescent work permits attachment release even when settlement is uncertain.
Verified cleanup requires all currently owned resources released and original
obligations settled; it does not mean the operation succeeded. Confirmed child
and attachment releases remain independent of uncertain child cleanup or epoch
settlement. Full two-stage admission, constructor failure delivery and installed
SDK consumption remain separate.

## Bounded original profile source-role execution

`grammar_profile_role` privately composes the first profile-selection source role
from the original captured Code host, both stage expectations and an explicit
profile selector. It does not accept a caller-created catalog, source reader,
producer or role host. The selector chooses authored data; it grants no authority.
The original Module operand/profile helpers interpret the original input through
Semantic's registered producer execution and retained-result ports.

Owned-resource custody is reserved before construction callbacks. Construction
and execution retain known original resources separately from invalid returns
and uncertain effects. Reentrant disposal refuses during construction or lexical
execution. Failed attempts retire permanently; restoring sources cannot revive
them. Only the identical original retained result can be released.

Host ownership requires the original class, allocator and initializer entrance
before invocation and again before ownership is assigned. A substituted factory
cannot donate another role's same-type host. Each original child disposal must
return `None` before its release is confirmed. Raw return presence/value remains
process-local; invalid returns leave that child unknown, even if a later parent
close succeeds. Explicit result release follows the same rule and cannot retry.

This internal first-stage cut does not implement the frozen complete two-stage
constructor or mount a public SDK operation. Its tests use explicit fixture
source/lifetime/catalog inputs with genuine Code registrations and result ports.
Genuine Workspace intake, syntax/contribution/dependency admission, canonical SDK
generation, native qualification and installed delivery remain separate.

## Original staged syntax registration

`grammar_syntax_role` extends the original profile-role host with a joined syntax
registration and Semantic role join before profile execution. It accepts only
the original sealed profile role; it does not create a second host or accept
caller catalogs, callbacks, detached predecessors or observed contribution bodies.

The caller's predecessor must be the original retained profile result. Semantic's
join slot deliberately holds its own detached body copy; that copy is checked
through the original slot/registration/expectation, not treated as another grant.
The receiver verifies the complete authored profile under the original async use.
For selected authored contributions it delegates the original Language
reconstruction and canonical V1 payload codec through Module's shared source
correspondence algorithm. An additive Code-owned output descriptor supplies the
outer coordinate; it does not claim a standalone Language producer registration.
The registered Code executor retains a genuine syntax-binding result. Dependencies
between selected contributions in the same original package occurrence now use
that existing whole-source admission: complete target version/digest, source
selection, namespace and cycle checks remain mandatory. The grouped successor
also interprets complete selected contributions across qualified occurrences,
requiring an oriented direct grouped edge and exact target version/digest.
The registered producer selects grouped interpretation before execution when
its original operands span multiple occurrences; failed local execution never
triggers fallback. Portable edges alone still supply no target admission.
This does not issue a materialized dependency-product grant.
The explicit data helper `reconstruct_grammar_local_dependency_binding` grants no
source authority. The older dependency-free reconstruction entrance continues
refusing nonempty inventories; no implicit fallback or wire change exists.
The local helper still refuses cross-occurrence targets. The additive
`reconstruct_grammar_group_dependency_binding` is also data-only: it does not
authenticate Workspace source owners, mint grants or assemble a parser.

Owned cleanup releases a retained syntax result before the original join and
syntax registration, then the profile result, profile registration and shared
owned host. Partial acquisitions and
invalid returns stay unknown; parent closure cannot upgrade them. A consumed
executor join without a separate release confirmation remains unknown after
failure. Borrowed source/catalog/host/participant lifetimes are not closed.

On a successful normal executor return, original retained-result validation and
the captured original consumed join record confirm the result and join
independently. Empty registries are not completion evidence. If final epoch
settlement fails after a result was retained, that known result survives while
whole-context cleanup stays unverified. Fixtures exercise genuine Code ports
with explicit synthetic source/catalog/lifetime parents. Selected cross-occurrence
interpretation passes under those fixture parents; genuine Workspace intake is
separately replayed, not joined to authored Language contributions in that proof.
Their end-to-end join, parser assembly, canonical SDK generation and installed
delivery remain separate.

The genuine receiving probes use original Workspace selected-source/group
issuers, original Code fixed products and SDK's actual source factory/catalog.
They do not supply a fixture catalog or profile result. The initial SDK graph-product
nomination roundtripped through Code's profile V2, then refused at the grammar
receiver's explicit format-1 gate. The accepted receiving amendment now permits
only one exact active/required V2 graph product: authored package, registration,
six-part occurrence and complete profile ref/version/digest must correspond to
the original complete catalog. Both direct interpretation entrances recheck it.
The genuine source proof now retains the profile and Language-derived syntax
results and verifies normal close while preserving the borrowed host.
A real SDK stage pair still supplies two complete
profiles for `aware_sdk`; the original receiver refuses ambiguity rather than
choosing one by key. V2 stage-pair and multiple-product grammar modes remain
refused. The existing V1 grammar, result wires and lifecycle owners are unchanged.
Source mutation retires the admitted attempt; restoring bytes cannot renew it.
Failed receiving retains unavailable-join/unknown-cleanup evidence rather than
inventing success. This is disposable source-bootstrap qualification, not a
public constructor, native assembly or installed SDK capability. Stage-pair
selection cannot silently filter or pick the first registered profile.

## Original Workspace command source attachment proof

The grammar pair now has product-bound planner configurations. Its two retained
planner objects no longer advertise the same implementation/configuration pair:
the canonical v2 configuration binds the complete original product binding and
profile. Workspace's original planner-owner collision guard remains unchanged.
No shared planner cache or copied owner is introduced; graph-targeting refusal
and original product retirement still apply.

The integration tests construct the original Workspace command, paired catalog,
Code host, repository observations, retained selection results and grouped
expectations, then exercise the unchanged grammar attachment/cleanup ports.
Original source mutation/restoration, expectation copies, foreign command parents
and source entrance substitutions refuse. Bootstrap coordinates and the small
source selector remain explicit test inputs, not installed application authority.
This is original command/source attachment—not cross-occurrence target execution,
the complete public grammar constructor, parser assembly or SDK installation.

## Optional public registered grammar composition

The optional `grammar_role_composition` surface supplies the owner-issued
`CodeGrammarRoleHost` view and these ports:

```python
with compose_registered_grammar_source_roles(
    code_host=original_code_host,
    profile_expected=original_profile_expectation,
    syntax_expected=original_syntax_expectation,
    profile_key=request.profile_key,
) as roles:
    previous = await execute_grammar_profile_selection(roles)
    result = await execute_grammar_syntax_binding(roles, predecessor=previous)
    validate_grammar_role_result(roles, result=result)
    # Context exit disposes owned resources through the original cleanup ticket.
```

All four constructor arguments are required keyword-only values. The selector
is forwarded unchanged and validated before attachment effects; no default,
normalization, inference, alias or fallback exists. The host and expectations
must already belong to the original admitted Code/Workspace execution. The
request shown is illustrative; no SDK operation is mounted by this source unit.

The view is retained on the original attachment, not a second registry or
detached owner. Profile/syntax construction and execution, retained results and
once-only disposal delegate to the original owners. Explicit result validation
and release accept only original pending results. Base package imports, metadata,
dependencies, advertisements and resolution locks remain unchanged.

Failure evidence is delivered when the composed operation exits its context.
Ordinary delivery retains the original primary first, cleanup errors in original
attempt order and one portable-evidence marker last. Interruptions preserve the
same primary control-flow exception, with cleanup/evidence as its cause. The
marker retains the prior causal slots, original cleanup ticket and unvalidated
return presence/value process-locally. Snapshot/cleanup observation failure
cannot replace the primary or invent verified resource evidence. A caller that
catches a leaf error inside the context controls that exception's propagation;
original retirement/uncertainty is not undone by that catch.

These are source proofs, including genuine Workspace intake under disclosed
disposable bootstrap inputs. They do not prove canonical SDK generation,
native parser assembly, installation or public materialization. Borrowed Code,
Workspace, catalog, product and epoch owners are never disposed by this view.

## Original planning and target source integration proof

The source integration tests compose original Environment root stages and both
grammar products under one original Workspace command and paired catalog.
That stage-backed composition installs the original Code planning/authority and
dependency validators; the product-only source attachment above does not.
Original retained planning inputs yield Workspace inventory and target handles,
and Code's already-installed target origin supplies retained registration and
typed manifest-contract correspondence. Registered root-stage completion uses
the same host/catalog; it does not execute a grammar product or its target.
Two original retained selection results and the admitted inventory/target pair
also reach the existing grouped source/declaration context with an authenticated
cross-occurrence edge. A disclosed raw test selector supplies those selections;
foreign inventory, a different edge owner and an unauthored selector refuse
before interpretation.

Foreign or same-type reconstructed handles, operation substitutions and target
mutation/restoration refuse. Command closure retires retained target reads and
inventory use. The disposable repository and factory/bootstrap inputs remain
test inputs, not installed provenance. No target/group coordinate is upgraded
to a syntax dependency grant: cross-occurrence grammar interpretation, parser
assembly, canonical SDK and installed/public delivery remain separate.
