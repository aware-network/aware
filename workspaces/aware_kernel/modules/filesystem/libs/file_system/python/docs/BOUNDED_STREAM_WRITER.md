# Original bounded temporary stream writer

This source cut extends the original `confined_mutation` temporary-file writer.
It does not create a staging root or provide a public descriptor-taking API.
P2a remains held; creation exclusion, worker authentication, nested traversal
and full postimage verification remain separate joins.

## Private owner entrance

`_write_temporary_stream_steps(parent_descriptor, name, chunks, size_bytes,
content_digest, mode, maximum_chunk_bytes=65536, maximum_chunks=4096,
_io=os, _path="")` is an internal generator consumed by the original writer
driver/ledger. Arguments are keyword-only. The original owner must already
hold the parent descriptor and physical operation authorization. Interface
must not invoke this helper or supply a raw descriptor or arbitrary IO adapter.
The `_io` and step machinery are the existing FileSystem owner's integration
seam, not external callbacks or backend qualification.

Metadata validation occurs before scratch acquisition. The leaf is canonical
and flat, the declared length is at most 256 MiB and fits the selected bounded
chunk count, the digest is exact lowercase SHA256, and final file modes match
the plan's 0444/0555/0600/0644/0700/0755 set. Limits may be narrowed, not raised.
The helper consumes exact nonempty byte chunks, never a joined whole body.
Empty files have no chunks and the known empty digest. An oversize chunk,
excess chunk count or length overflow refuses before writing that chunk;
short streams and hash mismatch refuse before final mode/sync.

Both whole-body and streaming inputs use one original scratch lifecycle.
Streaming creates the absent leaf with no-follow/exclusive flags and temporary
0600 permissions (subject to umask), writes through `_write_confined_bytes`,
then applies the exact final mode and synchronizes. Temporary permissions are
not substituted into the plan digest. The owner closes the acquired descriptor
once through its original IO ledger. Existing whole-body traces are unchanged.

This primitive does not publish, rename, unlink or roll back any scratch. On
failure or interruption, partial bytes may remain; the containing owner must
retain original acquisition/effect/cleanup evidence and must not replay an
uncertain operation. A failed close is not retried. The primitive does not issue
standalone effect receipts or claim that input hashes prove stored postimages.
The higher owner must reread bytes/modes and finish directory synchronization.

## Receiving obligations

The future worker must feed an authenticated, plan-bound member stream through
original creation custody and descriptor traversal. Transport must not execute
caller-supplied Python iterators in a privileged worker: this private helper's
iterator is supplied by trusted owner code over bounded received bytes. The
iterator's blocking/time budget and lifetime belong to that owner. No transport,
worker or privileged setup is supplied here.

Candidate chunk/byte ceilings do not enlarge the retained sequence or tree
writer's existing limits. Joining those writers requires separate original-owner
changes and resource accounting. Unit tests on a temporary ordinary directory
qualify this primitive only, not same-UID exclusion or the stronger
[creation custody contract](STAGING_CREATION_CUSTODY.md). ONE APP remains.
