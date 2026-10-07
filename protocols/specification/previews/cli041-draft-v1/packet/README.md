# Aware filesystem SPEC draft creation: internal review candidate

Linux x86_64, Python 3.12, filesystem authority. This packet is not a public
selection, frozen customer contract or upgrade to a6. Keep source and notices
together. Only aware-spec 0.4.1 is exposed. The governed extra is selected.
Issue/repository and SPEC setup tooling stay in their separate installations;
never overlay environments or replace customer AGENTS.md. No aware spec wrapper.

## Install in a fresh separate environment

Verify outer SHA256SUMS. Expand payload/specification-cli041-completion-v1.tar.gz
under a fresh private parent; its root is
aware-specification-cli041-completion-internal-v1. Verify the inner SHA256SUMS,
then change into that root. Use the shipped `install.sh`, not an invented pip
requirements filename. `consumer-lock.json` is not a pip requirements file.
Choose your own absolute unused environment path; preserve parent permissions:

```sh
set -eu
spec_review_env="/absolute/path/to/new-spec-review-venv"
test ! -e "$spec_review_env"
test ! -L "$spec_review_env"
PYTHON_BIN=/usr/bin/python3.12 sh ./install.sh "$spec_review_env"
```

If Python 3.12 is elsewhere, select its verified absolute executable. Existing
files, directories and symlinks must stop before installation. The installer
installs offline from the exact 26-wheel closure; no editable checkout or service.

## Explicit customer inputs, preview, apply, read

Select a customer Git repository, approved draft-writing outcome, exact current
Issue and invoking genuine harness execution. Use existing Issue tooling, not
manual authority edits, to open/claim an In Progress Issue with the admitted
SPEC root and scratch descendants in scope. Configure the SPEC root through
the separately installed setup tooling. The target package must not exist and
required ancestors must already be admitted; no overwrite or implicit approval.

Author meaning with the installed public types and canonical snapshot codec.
instructions/example-draft-input.py is an executable illustrative recipe; replace
its terms with the customer's decision. It emits request bytes, not an approved
SPEC or iteration. Save those bytes to an explicitly selected, governed input
artifact. Do not hand-write generated Markdown to bypass create-draft, invent
receipt digests or treat the example labels as actor authentication.

Set SPEC to this installation's exact aware-spec command, REPOSITORY to the
customer root, PROTOCOL_MANIFEST and SPEC_MANIFEST to explicit selected paths,
and SNAPSHOT_JSON to the canonical request artifact. Retain ISSUE_REF and the
fresh Issue byte digest, manifest byte digest and input byte digest as separate
sha256:<hex> values. Protocol's normalized semantic digest is not byte currentness.
AUTHOR_REF and AUTHORING_INTENT_REF are declared terms, not Issue write authority;
CLIENT_INTENT_ID identifies this attempt, not durable replay authorization.

```sh
"$SPEC" create-draft --repository-root "$REPOSITORY"   --protocol-manifest "$PROTOCOL_MANIFEST" --spec-manifest "$SPEC_MANIFEST"   --snapshot-json "$SNAPSHOT_JSON" --author-ref "$AUTHOR_REF"   --authoring-intent-ref "$AUTHORING_INTENT_REF" --client-intent-id "$CLIENT_INTENT_ID"   --issue-ref "$ISSUE_REF" --expected-issue-sha256 "$ISSUE_DIGEST"   --expected-manifest-sha256 "$MANIFEST_DIGEST" --expected-input-sha256 "$INPUT_DIGEST"
```

Default preview is non-authorizing. Inspect the exact rendered paths and effects.
After explicit customer approval, repeat that exact command with --apply.
The real Issue admission authorizes this single source publication; neither the
preview nor a JSON result is a reusable permit. A fresh observe command can read
the created package. Source publication is not a Git commit or Issue closeout;
publish and close separately through the Issue/repository owners.

Exit0 requires consumer_completion_verified=true after original whole-context
cleanup. Protocol completed alone is insufficient. Exit2 can retain a known
published package, applied/unknown effects, cleanup diagnostics or scratch residue.
Preserve those receipts; never blindly retry known publication, invent rollback,
delete evidence or upgrade historical unknown receipts through later observation.

## Source, notice and capability boundaries

source/workspaces contains only selected neutral wheel sources, projected package
metadata and exact legal inputs. SOURCE-INDEX.json correlates originals, projections
and 98 wheel matches (95 supplier-audited plus three command-runtime files).
Build recipes are inspectable provenance, not a universal
checkout-free rebuild promise. NOTICE-BINDINGS.json binds inherited legal texts to
this exact candidate. All upstream wheel bytes and source-derived jsonschema
remain unchanged; its benchmark subtree is excluded. The schema BSD selection
attaches the complete upstream alternative license file. Binary component lists
are conservative notice accounts, not an exact linkage/toolchain claim.

The inner manifest's draft_authoring and installed_acceptance nonclaims are
construction-time records. Only the bounded installed completion acceptance for
this exact payload supersedes them; it does not admit other capabilities. No
approved iteration, Phase acceptance, durable iteration-to-Issue writer, Goal,
dispatch, Service/API, ontology/ORM or Experience authority is supplied.
Currentness is observed state; every-write detection, continuous confinement and
authenticated action issuance remain unsupported. Synthetic installed fixtures
do not establish unassisted onboarding or external U/V/R.

Notice sufficiency, public-content acceptance, instruction freeze, public layout,
selection, evaluation and publication require their separate reviewed decisions.
