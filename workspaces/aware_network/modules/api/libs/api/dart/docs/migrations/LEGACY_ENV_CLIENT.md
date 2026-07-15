# Legacy Env Client Migration

Migration tracker for removing the legacy env-client + resolver stack
and routing all invocation through DTO-only clients.

**Canonical Target**
- Use `AwareApiClient.invokeFunction()` with explicit IDs from capability discovery.
- No name-based function resolution inside this package.
- No OPG/constructor inference outside DTO context; callers provide IDs.

**Source Inventory (Legacy)**
- `OLD/aware_interface_api_dart/service/env_client/**`
- `libs/session/dart/lib/session/environment_capability_resolver_provider.dart`
- `libs/session/dart/lib/session/environment_opg_resolver_provider.dart`
- `OLD/aware_interface_api_dart/domain/util/fqn_resolver.dart`

**Canonical Gaps (Must Remove/Replace)**
- Name-based function resolution is non-canonical and couples to legacy models.
- OPG inference logic belongs to runtime/node, not the client.
- Function invocation models depend on `aware_models` types.

**Phase Plan**
- [x] Replace legacy invocation requests with DTO-native request models.
- [x] Route all invoke paths through `environment_dto_client` (or `AwareApiClient`).
- [ ] Delete resolver utilities after consumers move to ID-based calls.
- [x] Move `env_client` package to `OLD/aware_interface_api_dart/service/env_client` and update imports.

**Dependencies / Open Questions**
- Confirm how clients obtain OPG/projection hashes from node capabilities.
- Decide if any thin helper remains for mapping human-readable names (outside API).
