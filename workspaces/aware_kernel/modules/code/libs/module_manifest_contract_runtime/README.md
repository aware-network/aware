# Neutral Code module manifest contract

Owns the complete existing aware.module.toml immutable model and bytes grammar.
`parse_module_manifest(body, source_label="<bytes>")` performs no filesystem reads.
`source_label` changes diagnostics only. The legacy Code loader reads once and delegates.

The strict canonical full-meaning JSON codec includes every model field and default,
rejects missing/extra/duplicate fields, wrong types and noncanonical wire. It preserves
legacy normalization and boolean-aware behavior; it does not invent new source rules.
The codec proves structural meaning, not source grammar admission or membership.

Manifests without a syntax declaration retain the original models and wires.
No Workspace, Language, ORM, generated DTO or semantic-owner imports.
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
