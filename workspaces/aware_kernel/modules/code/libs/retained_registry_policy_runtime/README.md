# Neutral retained registry policy calculation

`calculate_registry_policy(scope, catalog)` implements the deterministic source
calculation for `aware.code.retained-registry-policy.v1`. Inputs are the existing
CodeRetainedScopeProjection and portable CodeSemanticContractCatalog; the result
is the existing input-only RegistryPolicy. Neither inputs nor result confer authority.

Dependencies are only neutral Code module grammar and semantic contract runtime.
No Workspace import, scan, body store, callback, caller grant, rule selection or
service construction exists. The dependency-free contract runtime is unchanged.

The calculation parses every module as v2, matches all authored package rows to
retained membership and manifest locations, retains nonparticipants, rejects
incomplete participants, resolves same-scope registrations, checks each declared
stage's exact catalog profile/provider binding, requires exact package kinds and
manifest basenames, and verifies dependency targets name complete participants.
Existing RegistryPolicy validation rejects conflicting namespace/root assignments.

Registration digests hash the canonical neutral registration table. The policy
scope digest is the complete neutral projection digest. Comment-only module
changes therefore change scope evidence while preserving unchanged grants.

This is isolated portable calculation, not the complete trusted producer entrance.
Host composition must authenticate the original scope adapter and catalog, exact
live selected-provider implementation/configuration, and producer lifecycle; it
must validate scope before and after calculation before retaining
AdmittedRegistryPolicy. Portable executable coordinates are not live executable proof.
Selected-owner semantic name/dependency-constraint convergence remains downstream.

The first policy supports only same-Workspace registrations and all-v2 module
scopes. No repository declarations are migrated. Root lockfile and installed
dependency qualification remain untouched; source tests use explicit Code paths.
