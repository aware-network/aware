# Neutral staging creation custody contract

Status: proposed owner contract for review, 2026-10-18. The threat model and
receiving obligations below precede implementation. No new provider profile,
live handle, dependency, syscall adapter or deployment is admitted by this text.

FileSystem must establish creation custody before Interface can write extracted
bytes. Interface consumes that custody rather than inferring it from a path,
an observed inode or a successful mkdir return. The current P2a implementation
does not meet this requirement and remains unaccepted.

## Existing mechanisms and their limits

The original [package contract](../README.md) distinguishes observed currentness
from continuous exclusion. `private_directory.retain_private_directory` retains
an acquired existing private directory. It does not establish who created that
directory. Its live handles and observations must not be relabelled as creation
receipts. The original retained bootstrap, package and tree mechanisms also do
not independently qualify this new staging-creation join.

`cooperative_source` holds actual OS locks against participating writers under
its explicit local cooperating-writer profile. It excludes neither raw OS
mutations nor a process ignoring the lock. It can support serialization inside
a qualified composition, but cannot alone establish the exclusion required
below. No caller assertion that all writers cooperate is sufficient evidence.

The [guarded replacement specification](../../../../docs/specs/filesystem-guarded-replacement/SPEC.md)
describes a stronger managed-volume direction, but its continuous profile is
currently unavailable and its operation is replacement, not directory creation.
Its codecs or signatures cannot be borrowed as an implemented creation backend.

## Concurrency and threat model

The acceptance target is qualified exclusive creation under the original
FileSystem owner. This is a required guarantee, not a newly supported profile.

| Situation | Required behavior |
| --- | --- |
| Multiple admitted operations in the same owner | Real serialization/exclusion covers overlapping namespace effects; separate unaffected roots may progress |
| Cooperating external writers | Original reservations may serialize them, with actual participation and lifetime evidence; a lock does not cover the remaining rows |
| Another ordinary process with the same UID or a leaked writable directory descriptor | Treat it as an unexcluded writer unless an independently qualified enforcement boundary prevents its relevant mutations |
| A raw OS writer renaming/replacing the staging root or ancestors | It must be excluded by the qualified physical boundary or the target must be unsupported before creation; do not silently classify its attack as a permitted profile exception |
| Failure, cancellation or lost return after creation dispatch | Retain possible effects and original custody/uncertainty; do not renew or infer a clean retry |
| Host kernel, privileged administrator or the qualified owner's executable is compromised | Outside the proposed guarantee; executable/policy assumptions and their admission must be explicit |

The boundary must hold from before creation dispatch through custody capture,
all writes and their final verification. If custody is handed between owners,
that handoff must preserve exclusion without an unprotected interval. If the
selected target cannot establish this interval, refuse creation without claiming
a usable staging directory. Existing `0700`, effective UID, advisory locks,
random names, marker files and repeated inode reads do not establish it alone.

A possible backend could use an independently qualified dedicated writer and
controlled backing/exposure policy. Merely choosing a different UID or mount
namespace does not prove exclusion: inherited descriptors, writable aliases,
ancestor rename rights, backing mounts and all relevant writers still need
qualification. This contract does not choose or provision that backend. A
normal same-UID repository parent does not automatically qualify.

The useful local cooperating-writer profile may continue under its existing
claims. It must not be renamed exclusive creation to clear P2a. If a weaker
product acceptance target is ever desired, that is a separate explicit decision;
the two current substitution regressions remain required here.

## Ownership and handoff

FileSystem owns physical admission, reservation, creation, retained identities,
descriptor lifetimes, exclusive bounded writes, rereading and effect/cleanup
evidence. It remains neutral: it knows relative paths, modes, lengths and byte
digests, not App releases, Issues, Views, Actor roles or archive formats.

Interface owns archive/profile validation and exact member interpretation. It
must bind one immutable archive snapshot to the selected descriptor and lower
validated members into the original owner's bounded physical operations. It
must not create/open the destination itself, traverse it with a copied writer,
or reconstruct custody from detached data. Its tar decoder is not a filesystem
authority. The App does neither job.

The next implementation must freeze an exact original-owner entrance and
consumer signature before coding. Conceptually it must provide these operations,
not necessarily these names:

1. Qualify an original namespace/exclusion lifetime against an exact parent,
   target and physical policy, with separately recorded operation authorization.
2. Reserve and create an absent directory, establishing original live custody
   before any application bytes can be written or success is exposed.
3. Consume validated bounded member writes through that live custody, rejecting
   foreign, copied, decoded, cross-process/thread/generation, retired or released
   handles. Verification and final rereading use the same owner.
4. Return original observations and effect/cleanup evidence; end custody without
   granting cleanup over unproven ownership or transferring a raw descriptor as
   a public capability.

Detached metadata can describe parent/child identity, policy generation,
operation reference, creation state, durability and resource disposition. It
cannot issue a handle or qualify exclusion. Do not add a public constructor,
caller `exclusive=true`, arbitrary authenticity callback or supplied integer fd
as a shortcut. Transport and future remote binding require their own original
owner composition, not serialization of process-local handles.

Current acquired-directory retention may receive a proven creation result if
the original owner can transfer custody without reopening an unbound name and
without losing the exclusion lifetime. It cannot manufacture the missing proof.

## Effects and failure semantics

Record the creation attempt before dispatch. A missing/exceptional return after
dispatch remains uncertain even when no usable handle returned. Keep original
known identities and any owned resources separately from unproven path occupants.
Do not reopen a path to claim the occupant as the operation's created object.

Before dispatch, an observed existing target can refuse with no effects from
this operation. After dispatch, no-effects status requires original positive
evidence of no effect, not absence of a Python success flag. Preserve a known
created directory when acquisition, synchronization or publication later fails.
Unknown acquisition/close/creation outcomes remain unknown on subsequent calls.

No automatic retry, rmdir, recursive deletion, adoption, rename-back or rollback
is authorized by failure. Resource release is once-only and limited to genuine
retained custody; ambiguous cleanup must remain in the original ledger. Physical
staging success is not installation, activation, source authority or release
publication. Limits and resource fit must cover the actual proposed backend,
not only the current archive parser or observer.

## Required qualification matrix

| Control | Evidence required before P2a acceptance |
| --- | --- |
| Positive creation and extraction | Genuine qualified namespace/exclusion, original creation-bound handle, exact bounded writes, complete reread and once-only resource release |
| Replace at creation-return boundary | Original control perturbs that boundary; refuse or preserve genuine retained custody with zero bytes written into the substituted foreign directory |
| Replace at first-open boundary | Same non-adoption result; later acceptance of the substituted inode must not pass |
| Unqualified ordinary parent | Refuse before creation, with no hidden setup, service launch or claim that a cooperative lock is sufficient |
| Real raw writer through a process/descriptor alias | Qualify actual enforcement on the real backend; a mocked boolean or successful unit-only profile is insufficient |
| Interrupted creation after dispatch | Preserve unknown/applied effects, owned-resource disposition and residue without retry or unproven cleanup |
| Unknown acquisition or release return | Preserve uncertainty and single-use state; no second acquisition/close as recovery |
| Forged/detached/copied/foreign handle | Refuse before writes and preserve legitimate owner's lifetime |
| Root/ancestor/exclusion generation changes | Refuse before later writes; do not infer a new creation from another observation |
| Remote/public lifecycle isolation | No App/Release selector or authority is inferred from local filesystem evidence |

The two existing Interface regressions stay ordinary tests. Porting the join
may move the physical seam, but must preserve each injected boundary and its
foreign-directory assertion. Tests must show that the perturbation actually
ran, or that the unsupported target was refused before any creation; bypassing
a monkeypatch because an implementation stopped calling that name is not proof.
A blanket refusal implementation does not satisfy the positive creation row.

Source-only unit/negative controls can proceed independently, but do not qualify
an unavailable backend. Both substitution controls and positive original-owner
custody must pass before accepting the Interface staging join. A native canary,
privileged setup or deployment needs separate explicit effect authority.

## Implementation boundaries and parallel progress

The next source scope must name the owning FileSystem implementation and tests,
Interface receiver and tests, authored dependency declarations and actual
resolution roots if a dependency is needed. Follow original package registration,
projection and lock procedures; an editable import is not installed support.
Do not add a second package selector or bypass package projection to wire it.

Do not change the acquired-directory/cooperative-source guarantees globally or
import Interface formats into FileSystem. A provider gap holds only its receiving
creation/extraction effect. App/Panes, Agent View, manual-reread preparation,
Protocol delivery, immutable App artifact preparation and Release planning
continue independently. ONE Development App, local public and prepared remote
profiles, remains the product direction. Neither profile gets staging or
installed-readiness claims from this contract.
