# Aware Code Package Delta Contract

`aware-code-package-delta-contract` is the dependency-free portable output
contract for package-relative Code mutations. It carries deterministic
create/update/delete bodies and producer provenance. It does not apply files,
select a Workspace, interpret domain meaning, or claim canonical graph
authority.

The public `aware.code.package-delta.v1` vocabulary is:

- optional language: absent for language-neutral manifest/metadata output, or
  `aware`, `dart`, `python`, or `sql`;
- path role: `authored_source`, `generated_code`, `generated_manifest`, or
  `generated_metadata`;
- package-relative normalized POSIX paths;
- content-bound before/after lifecycle and one complete output-root digest.

The sibling `aware.code.package-output-state.v1` value is the compact prior
output coordinate required for successor rendering. It carries only exact
path hashes, sizes, language/role metadata, producer identity and a complete
state digest—never generated file bodies, filesystem currentness or Workspace
authority. `derive_code_package_output_state(...)` deterministically advances
that portable state through one admitted delta; it does not claim that any
filesystem or Workspace head was advanced.

SDK, API, Ontology, and later providers emit this same contract through the
Code-neutral semantic runtime. They must not define domain-specific delta
types. Workspace transports and publishes the body without interpreting its
provider meaning; FileSystem may later apply an explicitly admitted body to a
selected checkout.

`v1` was hard-cut to this complete vocabulary before module registration. The
earlier Python/generated-code-only implementation was an unregistered
Workflow Issue proof subset and is not retained as a compatibility rail.

Local application or Workspace publication is operational evidence only.
Neither elevates this value to OCG/OIG history.
