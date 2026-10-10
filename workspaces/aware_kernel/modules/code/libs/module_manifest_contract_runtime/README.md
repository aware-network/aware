# Neutral Code module manifest contract

Owns the complete existing aware.module.toml immutable model and bytes grammar.
`parse_module_manifest(body, source_label="<bytes>")` performs no filesystem reads.
`source_label` changes diagnostics only. The legacy Code loader reads once and delegates.

The strict canonical full-meaning JSON codec includes every model field and default,
rejects missing/extra/duplicate fields, wrong types and noncanonical wire. It preserves
legacy normalization and boolean-aware behavior; it does not invent new source rules.
The codec proves structural meaning, not source grammar admission or membership.

V1 has no new declaration fields. No Workspace, ORM, generated DTO or semantic-owner imports.
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
