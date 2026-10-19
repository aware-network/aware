# Aware open-source policy

## Project default

Aware-authored source, documentation, schemas, templates, and generated project
artifacts are licensed under Apache License 2.0 (`Apache-2.0`) unless a more
specific notice applies. The current rights holder is Luis Lechuga Ruiz. Aware
is a project name and is not represented here as a registered legal entity.

The root `LICENSE` supplies the license text. `NOTICE` supplies Aware
attribution. `THIRD_PARTY_NOTICES.md` records known upstream boundaries.

## Repository ownership

`aware.repo.toml` owns the release-level licensing contract. Every licensing
field is required and must point to a declared `repository_files` target. A
RepositoryRevision is distributable only when it includes those files and all
selected WorkspaceRevision license/provenance evidence.

Workspace manifests own workspace scope and package composition. They do not
override repository distribution policy. A repository aggregates selected
WorkspaceRevisions and repository-owned overlays; it does not silently acquire
copyright ownership of their contents.

## Third-party source

Upstream-owned source keeps its upstream copyright, license, and notices.
Apache-2.0 is the Aware default, not a claim that all files were authored by
Aware. Copyleft components must be excluded from an Apache-only release profile
unless that profile explicitly satisfies the copyleft license.

## Provenance gate

A public release profile must fail closed when a selected artifact lacks:

- an SPDX license expression;
- source and version identity;
- required copyright and attribution notices; or
- a reproducible build receipt, checksum-backed acquisition receipt, or an
  explicit source-only exclusion.

The repository being publicly visible is not itself a release receipt.
