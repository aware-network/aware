# Neutral Code module manifest contract

Owns the complete existing aware.module.toml immutable model and bytes grammar.
`parse_module_manifest(body, source_label="<bytes>")` performs no filesystem reads.
`source_label` changes diagnostics only. The legacy Code loader reads once and delegates.

The strict canonical full-meaning JSON codec includes every model field and default,
rejects missing/extra/duplicate fields, wrong types and noncanonical wire. It preserves
legacy normalization and boolean-aware behavior; it does not invent new source rules.
The codec proves structural meaning, not source grammar admission or membership.

Manifests without a syntax declaration retain the original models and wires.
The base parser/root imports no Workspace, Language, ORM, generated DTO or semantic owner.
Installed/module-package qualification remains pending exact module declaration handoff
and dependency resolution; the shared uv.lock is untouched.

## Version 2

The same parser accepts isolated `aware = 2` sources under the accepted extension
contract. AwareModuleSpecV2 preserves the base membership view and adds immutable
package_declarations in matching order. The common codec dispatches to the exact
v2 full-meaning discriminator; explicit v2 encode/decode functions are also public.
Tags and registration tables are declarations, not admissions. Namespace/root
issuance requires original Workspace evidence. Repository v2 manifests remain held
until Workspace version admission and positive issuers are ready.

## Authored syntax requirements

The original parser accepts the frozen optional
`[[packages]].semantic_contract.syntax` table in V1, V2 and V3 manifests. It has
exactly integer `version = 1`, an ordered unique `contributions` array of
canonical package-relative `.syntax.json` paths and an `anchors` array.
Each anchor retains its complete consumer contract reference, role, rule name,
ordered field path and exact boolean required/top-level flags.

An explicit owned `AwareModulePackageSemanticContractSyntaxSpec` represents
present syntax. Absence returns the original exact base model, without a new
nullable field or wire key. Other subclasses and explicit null syntax refuse.
Full-meaning encoding revalidates the bounded declaration and preserves authored
order. `syntax_declaration_digest` hashes the complete lowered table under
`aware.code.grammar-syntax-declaration.v1`; this is not its TOML source hash.

These are authored requirements, not admitted sources or parser capabilities.
Paths are relative to the declaring provider package; parsing does not resolve
them or read files. Anchors reference rule/field names; they do not define rules
or establish that an assembled parser supports them. Original provider/consumer
matching, contribution-source correspondence, parser assembly and SDK composition
remain separate qualified joins. Package dependencies and metadata are unchanged.

## Registered grammar profile source interpretation

`parse_registered_grammar_profile(body, profile_key=...)` uses the original
profile parser and full-meaning codec. The new grammar path requires an exact
integer format, an explicit matching profile key, `registered_contracts`, active
status and required active providers. It preserves the complete original value,
including package key and authored provider order. Unsupported modes refuse;
legacy dynamic/default parsing remains unchanged. The receiving ceiling is 256
providers; excess refuses before complete-value encoding, never by truncation.

`parse_grammar_provider_module(body, package_id=..., provider_key=...)` uses the
original module parser/codec and returns the complete module and selected package.
The exact package must contain a matching `aware.semantic_provider` declaration
with authored syntax. Other packages, provider labels or missing syntax do not
provide a fallback. V1/V2/V3 declarations retain all unrelated fields and authored
syntax order. `GrammarProfileSourceError.reason` identifies new selection refusals;
original parser/codec exceptions propagate without diagnostic reconstruction.

Both functions accept bounded exact bytes and explicit exact selectors, with no
source IO, dynamic provider imports or new dependencies. The 8 MiB per-call ceiling
does not replace or enlarge Workspace's aggregate context budget. These functions
interpret supplied data; they do not authenticate source or choose an occurrence.
A coherent replacement source can pass. Original composition must supply the
qualified Workspace occurrence, full registered provider/consumer contracts and
contribution/scanner sources, then invoke Language's original reconstruction
helper inside registered execution. These parser helpers are not that completed
composition, generated SDK exposure, parser capability or installed readiness.

## Grammar factory and catalog construction

The optional `grammar_factory` source module defines the two accepted
zero-argument factory targets:
`construct_grammar_profile_selection_product` and
`construct_grammar_syntax_binding_product`. Explicit import requires Semantic;
the base parser/root does not import this module or gain dependencies.
Metadata, extras, entrypoint enrollment and installed qualification remain held.

Each factory creates a fresh original Code runtime/provider and complete
six/seven-contract body-codec inventory. It returns the exact original factory
product with bound input/executable methods, canonical implementation and
no-options configuration bodies. Import/construction performs no source IO,
factory admission, provider execution or catalog/host admission.

The original Code issuer alone registers these products. The retained catalog
producer reads and revalidates that original contribution, preserving its
complete operational profile, binding and actual executable object. It returns
one entry/planner; the existing composer adds it alongside original root stages.
A catalog input is not an admitted catalog or command lifetime. The original
product owner additionally rejects runtime/provider/bound-method/body substitutions
against its captured registration, even when declarations or bytes match.

The planner first revalidates its original catalog and supplied fields, then
refuses unsupported graph targeting; it never returns empty demands as success.
Demand/target-intent codecs admit no value or write permission. Products remain
limited to `code`, `ontology` and `sdk` roots and `resolve_grammar_profile`.

**Execution is not activated.** Input closure, direct execute and ordinary
derive all refuse until the original source-role attachment is implemented.
Implementation bodies name the frozen interpretation entrances. The separate
profile and syntax helpers below supply data correspondence; original host
invocation remains unfinished. Policy host attachment,
Language contribution execution, cleanup/epoch joins and canonical SDK follow
under separate source scopes, not a new preparation gate. No public grammar,
materialization or installed readiness follows from construction.

## Authored profile interpretation and result correspondence

Explicit optional import of `grammar_profile_composition` provides
`produce_grammar_profile_selection` and
`validate_grammar_profile_selection_result`. The receiving constructor supplies
the exact ordinary input, selection, complete interpretation profile, original
Code catalog resolver and explicit provider occurrences in authored order.
These are verification inputs, not a new public authority constructor.

The helper checks both supplied declaration/group contexts, selection and shared
budget before parsing. Original profile/module parsers preserve full authored
values. All authored providers must correspond to the complete registered
profile, exact selected occurrences, enclosing module/package manifests and
original catalog bindings. No label-based occurrence fallback or provider
filtering occurs. The runtime profile supplies its own ref, version, contracts
and graph; these are not inferred from a selector or TOML format. The original
profile codec supplies the canonical output body.

Full catalog reads and input correspondence checks bracket production. Returned
profile validation checks the exact body/coordinate and reconstructs complete
correspondence afresh. Original failures and interruptions propagate without
retry or diagnostic reconstruction. A self-consistent copied input/body can
still pass these data checks; only original registered execution authenticates
Workspace source/currentness and nominal retained result ownership.

The helpers perform no source IO, native assembly, provider invocation, host
attachment, admission or release. Both factory execution ports still refuse.
The focused source proof uses portable Workspace input and catalog-parent
fixtures; it is not positive production grammar execution. Original-host/epoch
cleanup, SDK composition and installed proof remain
later units. Base imports, dependencies, metadata and installed selection are
unchanged.

## Syntax contribution and result correspondence

The frozen `grammar_profile_composition.produce_grammar_source_binding` entrance
accepts the complete joined input, exact selection, original catalog resolver,
explicit provider occurrences and occurrence/path/observed-body rows. Its
validator reconstructs complete data correspondence. The auxiliary
`grammar_syntax_composition` module directly reexports those same function
objects; it owns no implementation or cache.

The profile predecessor keeps its complete original coordinate and canonical
body. Each provider's original declaration selects its own contribution paths.
Code projects all six Language source fields from the original occurrence and
source coordinates. Language's original helper reconstructs the authored payload
and scanner account; Code compares the complete canonical observed body and
preserves its supplied coordinate. Full provider/consumer refs, namespace
uniqueness, dependency version/digest and grouped cross-occurrence provenance
are checked. An ordinary edge alone does not authenticate contribution selection
or dependency admission. Code's namespace check does not replace Language's
assembly validation or dependency-first grammar traversal.

Code's original V2 body codec produces the provider/contribution bijections,
anchors and complete profile reference. The shared 8 MiB receiving budget also
charges selection, predecessor and observed bodies. Rechecks refuse changed
source/predecessor/result data and retired catalogs. Original failures and
interruptions propagate without retry. Anchor requirements do not prove parser
capabilities, and this helper builds no assembly request or fake generator.

These are detached data checks. A copied, relabelled observed coordinate can
pass while proving no nominal production or retention. Original Policy must
authenticate joined registrations, observed result ownership, source/currentness
and admitted dependency evidence. Factory execution remains refused. Syntax
invocation imports the selected Language suppliers explicitly; lazy imports
are not installed-neutrality evidence. Metadata/optional-dependency enrollment
and fresh installed qualification remain pending, with no Source SDK/Service,
Objects, ORM or generated dependency added by this cut.

## Explicit grammar source operands

The optional `grammar_source_operands.derive_grammar_source_operands` helper
derives a complete selection, qualified provider-occurrence tuple and original
catalog profile from an explicit request profile key and the supplied grouped
input. It reuses the original profile/module parsers, Code context codecs and
full profile-correspondence implementation. Ambiguous profile scopes, packages,
occurrences or complete catalog profiles refuse; no priority, first match,
default selector, dynamic import or availability fallback chooses a winner.

The result is detached data, not a registration or source/retention capability.
Original Policy must still authenticate the original host, request association,
producer/results and dependency admission before and after execution. The
registered-executor test uses the real Code owner ports with explicit fixture
source/producer authority; it does not qualify the production constructor.
Factory execution, async quiescence/cleanup, SDK generation and installed
delivery remain separate. Metadata, base exports and dependencies are unchanged.
