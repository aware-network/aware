# Aware Issue Runtime

`aware-issue-runtime` is Coordination/Issue's generated-free structured read
core. It parses canonical and legacy Issue Markdown text into immutable,
versioned projections while preserving the raw source, unknown sections, exact
append-only sequence, and explicit temporal provenance.

The pure parser/projection operations perform no filesystem IO. The package
imports no generated ontology/API DTO, SDK, service, Pydantic, graph/ORM,
provider, transport, or materialization implementation. Workspace owns source
observation and confined reads for those operations.

Version 0.3.0 removes the retained `aware_issue_runtime.local_json_state`
compatibility module. Its original implementation now belongs to
`aware_file_system.local_json_state` in FileSystem `>=0.3.1,<0.4.0`; both the
SDK compatibility cache and Service backend import that owner directly. The
old module has no forwarding shim. This is a breaking import migration, not a
change to storage bytes or operational decisions. Core neither ships nor
depends on the storage mechanism. Consumers requiring persistence declare the
FileSystem dependency themselves. Source separation does not prove a built or
installed consumer closure.

Version 0.2.0 removes the projection participant and its seven Service exports.
They now belong to `aware_issue_local_service_runtime` in the separate
`aware-issue-local-service-runtime>=0.1.1,<0.2.0` distribution. No compatibility
shim or optional dependency restores them in core. The neutral read-projection
schema remains here. Existing parse/projection/source-import operations and
their operational rules are unchanged; SDK and FS adapter migration and
consumer installation are separately qualified.
