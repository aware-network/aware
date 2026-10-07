# SPEC CLI0.4.1 governed draft preview — local selection

Status: selected locally; independent selection review pending; **not publicly delivered**.
See the [selection record](SELECTION.md). Customer command sequences remain
drafts, not a frozen agent-contract extension. a6 contract1.2.1 and the published
Protocol CLI0.3.1 / SPEC CLI0.2.2 setup/read preview remain unchanged.
This separate composition selects only aware-spec 0.4.1 in a
fresh 26-package environment: SPEC SDK0.3.1, FS SDK adapter0.4.1 and Protocol FS
adapter0.6.1. The governed extra is selected. The original domain owners remain
authoritative; this layout introduces no parser, policy evaluator or writer.

## Install separately after explicit task selection

From this checkout, choose your actual Python3.12 executable and an unused
absolute environment path under an existing private regular parent:

```sh
spec_draft_parent="$(mktemp -d /tmp/aware-spec-draft.XXXXXXXX)"
spec_draft_env="$spec_draft_parent/env"
python3.12 protocols/specification/previews/cli041-draft-v1/install.py \
  --python-executable /usr/bin/python3.12 --venv "$spec_draft_env"
"$spec_draft_env/bin/aware-spec" --help
"$spec_draft_env/bin/aware-spec" create-draft --help
```

The example creates a private temporary parent; if selecting another location,
choose an existing private regular parent and an unused absolute target.
The wrapper checks the exact packet and payload, retains source/notices and
delegates to the unchanged shipped offline install.sh. It rejects existing
files, directories, symlinks and missing/symlink parents. Parent permissions do
not change. consumer-lock.json is an audit inventory, not a pip requirements
file. Linux x86-64 / actual Python3.12 are required; Git is needed for customer
work. After acquisition, no network, development checkout or editable import
is required. Failed installation may leave partial effects and evidence;
automatic rollback and continuous confinement are not promised.

**Never overlay** a6, selected SPEC or any other preview environment. Only
aware-spec is an admitted launcher here: there is no aware-protocol command,
aware command, aware spec wrapper or bootstrap upgrade in this bundle. Use the
[published setup/read entrance](../cli022-reader-v1/README.md) in its own installation for
setup, and the [a6 workflow](../../../agent/quickstart.md) for Issue/repository
operations. Transitive SDKs are owners used by composition, not extra public CLIs.

## Draft inputs and sequence

1. Establish a customer-approved draft outcome, exact Git repository and genuine
   invoking harness execution. Open/claim an In Progress Issue through a6 with
   exact package, scratch and input paths in its scope; do not fabricate authority.
2. Configure the SPEC root with the separately installed setup tooling. Supply
   the explicit Protocol manifest and target SPEC manifest. Required ancestors
   must be admitted and the package absent; no overwrite, import or implicit
   approval is supplied. A draft can be created without an approved iteration.
3. Author terms using installed public types and the canonical snapshot codec.
   [The executable input recipe](packet/instructions/example-draft-input.py)
   emits canonical request bytes; replace its illustrative terms with the
   customer's decision. Save to an explicitly governed input artifact. It does
   not create an approved SPEC, Issue admission or actor-authentication evidence.
4. Preview the exact request through this installation's aware-spec; inspect
   target/scratch paths, proposed effects and the entire result. After explicit
   approval, repeat the exact command with --apply. Never replay an old permit.
5. Read the created draft through this same aware-spec. Retain exact source and
   manifest byte digests. Reading a draft does not accept a Phase or approve it.
6. Publish source changes and close or hand off the Issue separately through a6.
   Draft source publication is not a Git commit or an Issue closeout.

Select SPEC as this environment's exact aware-spec path; REPOSITORY,
PROTOCOL_MANIFEST, SPEC_MANIFEST and SNAPSHOT_JSON are explicit customer
coordinates. Supply ISSUE_REF, genuine execution context, AUTHOR_REF,
AUTHORING_INTENT_REF and CLIENT_INTENT_ID. Use observed ISSUE_DIGEST,
MANIFEST_DIGEST and INPUT_DIGEST as separate sha256:<hex> exact-byte guards.
Protocol's normalized semantic digest is not byte currentness. Declared author
and intent strings are not authenticated action issuance or Issue authority.

```sh
"$SPEC" create-draft --repository-root "$REPOSITORY" \
  --protocol-manifest "$PROTOCOL_MANIFEST" --spec-manifest "$SPEC_MANIFEST" \
  --snapshot-json "$SNAPSHOT_JSON" --author-ref "$AUTHOR_REF" \
  --authoring-intent-ref "$AUTHORING_INTENT_REF" --client-intent-id "$CLIENT_INTENT_ID" \
  --issue-ref "$ISSUE_REF" --expected-issue-sha256 "$ISSUE_DIGEST" \
  --expected-manifest-sha256 "$MANIFEST_DIGEST" --expected-input-sha256 "$INPUT_DIGEST"
```

After explicit approval, repeat the complete request above with --apply. Only
after inspecting that publication outcome, use the fresh read below; preview
alone creates no package to observe. A late refusal can still have published
bytes, so preserve its evidence instead of automatically retrying.

```sh
"$SPEC" observe --repository-root "$REPOSITORY" \
  --protocol-manifest "$PROTOCOL_MANIFEST" --spec-manifest "$SPEC_MANIFEST"
```

Preview is default and non-authorizing; apply requires explicit --apply and fresh
original Issue admission. Exit0 requires consumer_completion_verified=true after
original whole-context completion. Late exit2 may retain a known published
package, applied/unknown effects, cleanup failures or scratch residue. Preserve
the receipts: **never automatically retry known publication**, delete evidence,
invent rollback or upgrade historical unknown results through later observation.

Supported scope: governed draft creation, strict observation and existing
iteration identity. No approved iteration authoring, SPEC approval/import,
Phase acceptance, durable iteration-to-Issue writer, Goal, dispatch, Service/API,
generated API/DTO, ontology/ORM or Experience authority is supplied. Currentness
is observed state; every-write detection and continuous confinement are
unsupported. Synthetic installed proofs do not establish unassisted customer
onboarding or external U/V/R. Contract1.3.0 remains unallocated.

## Exact software, source and notices

- [Accepted packet](distribution/aware-specification-cli041-source-notice-review-v1.tar.gz): SHA-256 `b78a45f66ef89ea081d61cd77a37be9d5ccebbfe10b2df60fa577fab53ad0934`.
- Unchanged payload SHA-256 `a5dc83d12a79487dbf345481c82b7c6ba894ead77047b5c4e49557a2f7e2aa30`.
- [Delivery map](delivery.json): all 446 packet members and remapped tree hashes.
- [Neutral sources](../../../../workspaces/previews/specification-cli041-draft-v1/README.md): 146 exact source/legal
  files; no new workspace revision or editable operational rail.
- [Source index](packet/SOURCE-INDEX.json), [notice bindings](packet/NOTICE-BINDINGS.json),
  [historical packet instructions](packet/README.md).
- [Evaluation protocol](../../../evaluations/README.md).

Outer extraction root: aware-specification-cli041-source-notice-review-v1.
Inner root: aware-specification-cli041-completion-internal-v1. These are retained
artifact names, not semantic protocol versions or a different authority mode.
Original packet-relative indexes/checksums remain unchanged: verify them against
the unchanged extracted distribution, not the remapped source tree. Use
delivery.json for public tree paths. Build recipes are provenance, not a general
checkout-independent wheel-rebuild promise. Historical internal/unaccepted
nonclaims stay historical; the exact completion and bounded content acceptances
do not rewrite them or admit wider operations.

All 43 in-wheel legal copies and 236 inherited notice files remain exact. MIT
package and selected BSD schema terms remain separate; the whole upstream
alternative-license text is retained. Native-component lists are conservative,
not exact binary-linkage/toolchain evidence or a legal warranty. The retained
/home/aware scan occurrence is a hash-bound --tmpfs mount point in a historical
build recipe, not a private checkout coordinate; raw finding/exit2 remain intact.
This page is an unfrozen instruction proposal. The existing customer AGENTS.md,
a6, selected setup/read preview and prior source snapshots remain unchanged.
Layout acceptance, actual integration, selection, instruction freeze, external
evaluation and public delivery require separate decisions. No push is authorized.
