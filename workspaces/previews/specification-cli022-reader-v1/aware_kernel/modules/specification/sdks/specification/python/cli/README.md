# Specification CLI

Thin source-stage `aware-spec` 0.2.2 read-only entrance; no service probing or fallback.

- `observe --repository-root PATH --spec-manifest RELATIVE_MANIFEST`.
- Repeat `--spec-manifest` in exact UTF-8-byte order for all explicit roots.
- `iteration-identity` adds the exact `--iteration-ref`.
- `--protocol-manifest` defaults to `aware.protocol.toml` within the explicit
  repository; `--expected-manifest-sha256` checks its exact observed byte digest.
- Repository roots may be relative to the invocation directory. Relative
  Protocol manifests remain repository-relative and are resolved once by the
  Protocol issuer; absolute manifest paths pass through unchanged.
- `--expected-source-digest` separately checks the SPEC owner's source closure.

Example source-stage form (not a consumer installation instruction):

```text
aware-spec observe --repository-root /customer/repo \
  --spec-manifest contracts/example/aware.spec.toml
```

The command freshly issues Protocol selection, constructs the real guarded SPEC
provider and reads through the public SDK. It revalidates before printing and
closes its owned provider and selection on every exit. Typed Protocol refusals
do not become SPEC approval or fabricated source observations. Output is portable
evidence with `retained_capability_exported=false`; a later execution must admit
its own sources again.

The mandatory dependencies select public SDK `>=0.2.0,<0.3.0`,
`aware-specification-fs-sdk-adapter[protocol]>=0.3.0,<0.4.0` and the existing
neutral `aware-command-runtime>=0.1.1,<0.2.0`. The adapter's Protocol reader extra
selects `aware-protocol-fs-adapter>=0.3.0,<0.6.0`; this CLI does not select the
adapter's `governed` extra or Protocol's `draft` extra. Adapter 0.3.0 source
adoption is independently accepted; the exact successor installation and
predecessor/successor command parity remain separately qualified by Bundle.
Do not modify or substitute historical CLI 0.2.1 wheels, overlay environments,
or infer a neutral dependency closure from internal workspace metadata.
No Protocol or command-runtime edge enters the neutral public SDK/runtime or
source-value contract.

`aware_specification_cli.read_commands.register_read_commands(registry)` registers
exactly `observe`, then `iteration-identity`, with no IO or provider admission.
The standalone entrypoint dispatches through Kernel's existing neutral registry.
Both projections reference `SPECIFICATION_OBSERVE_OPERATION_REF`; identity adds
the existing neutral resolver, not a second SDK operation. Registration labels
and invocation context are not authority. Duplicate registration refuses; no
writer registration, `aware spec` alias or automatic environment combination.
Rejecting `create-draft` never retries through `compatibility_main`, even when
the historical diagnostic writer or optional governed dependencies are present.

Help now describes those two reads through the generic registry. Command arguments,
JSON result/refusal streams, explicit exit codes and owner cleanup remain unchanged;
the help-only wording change does not imply installed predecessor/successor parity.

This is an explicit pre-1.0 CLI source-interface change. Raw `--source-base`/
`--root` and `create-draft` are not consumer commands, and failure never retries
through them. `compatibility_main` retains historical maintainer diagnostics
as a library function only; it is not registered as a console entrypoint.

## Historical compatibility input

The input is the existing runtime's canonical snapshot wire containing exactly
one complete definition, no iterations, and the accepted semantic profile.
Use the typed neutral runtime codec to produce it; compatibility diagnostics do not guess
semantic meaning or reinterpret legacy Markdown. The primitive creates an absent draft,
not an approved execution plan. Parent directories must already exist.

Output includes authority mode/grade, source/snapshot digests and semantic
iteration identity. JSON is portable evidence, not the retained SDK capability.
No approval, iteration writer, Issue binding, Git publication or readiness
authority is exposed. Source tests do not admit this command in public a6;
customer-input ergonomics and governed writing must be integrated by Protocol.
