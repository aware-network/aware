# Aware Utils

Selected-kernel utility package extracted from `aware-core`. Provides logging helpers, text normalization, Pydantic bootstrap helpers, and strict Aware state-root helpers shared across the Aware codebase.

## Highlights
- Colorized logging helpers with rotating file support
- String and description normalization helpers
- Serialization helpers for transporting invocation payloads
- Strict Aware state-root helpers for services that receive explicit roots

Use `aware-utils` as a dependency when you only need these shared helpers without pulling in the full core package.

Repository root discovery is intentionally not part of this public package.
Remote/runtime code should receive explicit roots, package resources, or
materialized deployment artifacts. Local development and proof source-checkout
resolution lives behind the Workspace-owned
`aware_workspace.source_repo_root.resolve_workspace_source_repo_root` helper.
The retired `aware-root-discovery` / `aware_utils.find_aware_root` compatibility
rail is not public kernel truth.

## Documentation
- Logging reference: `docs/logging.md`
- Usage guide: `docs/USAGE.md`
