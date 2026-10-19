# Bounded original file postimage verification

This private original-owner read primitive verifies one observed regular-file
postimage without retaining its body. It does not issue custody or seal a
namespace. P2a remains held.

## Private entrance and result

`_verify_confined_file_postimage(parent_descriptor, leaf, expected_identity,
size_bytes, content_digest, mode, maximum_chunk_bytes=65536,
maximum_read_calls=4097)` is keyword-only in original `confined_mutation`.
The parent is borrowed from original owner custody and is not closed here.
The identity tuple must originate from that owner's actual creation; the tuple
itself is a comparison, never evidence that creation or exclusion occurred.
Interface must not invoke this descriptor-taking helper or reconstruct custody
from its result. The future worker remains responsible for authentic inputs.

Validation precedes IO. Leaf names are flat canonical POSIX paths, metadata
uses exact types, final modes match the plan's 0444/0555/0600/0644/0700/0755,
and length is at most 256 MiB. Positive read limits may narrow the fixed ceilings,
not enlarge them. Declared length must fit within the selected call budget,
including a final EOF probe. Empty files require the known empty digest.

The original read ledger opens no-follow/nonblocking, retains acquisition before
dispatch and attempts release once. The opened inode must match the expected
device/inode, be regular, single-linked and owned by the unchanged effective
UID, and have the exact declared length and final permission bits. Reads are
bounded by both chunk size and call count. Length/hash, before/after descriptor
metadata and final no-follow leaf correspondence must all match.

Success is `_FilePostimageVerification(observation, cleanup)` with a detached
`_FilePostimageObservation` containing leaf, identity, length, digest, mode and
read-call count. Grade is `observed_state`. It contains no body or handle.
Success requires confirmed cleanup. Failures use `_FilePostimageError` with
code, failed stage, original primary cause, any completed observation and
original cleanup evidence. Interrupted acquisition/release remains unknown;
failure never reopens, reissues, deletes or retries a spent descriptor.

The new and existing bounded readers use one factored original cleanup-settlement
routine. Existing whole-body read behavior is conserved. A source test on a
temporary ordinary directory does not qualify creation exclusion or namespace
confinement.

## Remaining worker obligations

The worker must hold original namespace exclusion and bind this reread to the
same creation, plan, member sequence and authenticated operation lifetime.
It must settle directory durability, verify full membership and modes, and
retire its write rights before reporting a genuinely sealed stage. A successful
individual observed reread cannot perform those transitions. Raw same-UID
writers and root/ancestor changes remain outside this primitive's protection;
the caller must not label it a live seal. No accounts, services, mounts, setup
authority, transport or installation are supplied here. ONE APP remains.
