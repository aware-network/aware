# aware-code-sdk

`aware-code-sdk` is the consumer-side SDK for Code API DTO truth.

The first local rail is semantic-contract/package-layout resolution for callers
that need Code meaning locally without importing Code runtime or Code service
internals.

Boundary:

- Depends on generated `aware_code_service_dto` DTOs.
- Does not depend on `aware-code`, `aware-code-service`, or
  `aware_code_service_protocol` in package metadata.
- `AwareCodeSdk.local()` is catalog-backed and does not import Code runtime or
  Code service internals.
- Service-backed local execution is composed outside this package by constructing
  `AwareCodeSdk(api_client=...)` with an explicit Code service API client owned
  by the consuming workspace/runtime.
- Exposes a protocol-compatible local Code API client for
  `code.semantic_contract.describe`, `find_manifest_resolution`, `validate`,
  `normalize`,
  `code.package_layout.describe`, and `validate`.
- Exposes a sync manifest-resolution provider for Workspace-style local
  registry/materialization consumers and an async provider for generated API
  clients.
- Returns generated Code DTO response models so Workspace SDK and other
  consumers can use the same contract as remote/service-backed Code API calls.

Example:

```python
from aware_code_sdk import (
    build_local_code_sdk_api_client,
    DescribeCodeSemanticContractRequest,
)

code_api = build_local_code_sdk_api_client()
response = await code_api.code.semantic_contract.describe(
    DescribeCodeSemanticContractRequest(package_name="aware_demo_ontology")
)
```

Use the manifest-resolution provider when a local consumer needs package-owned
manifest descriptor truth without importing Code runtime registries:

```python
from aware_code_sdk import AwareCodeSdk

sdk = AwareCodeSdk.local()
provider = sdk.manifest_resolution_provider()
response = provider.find_manifest_resolution(
    filename="aware.api.toml",
    workspace_manifest_kind="api",
)
```

Use package layout bindings when a caller knows package coordinates locally:

```python
from aware_code_sdk import CodeSdkPackageLayoutBinding, build_local_code_sdk_api_client

code_api = build_local_code_sdk_api_client(
    package_layouts=(
        CodeSdkPackageLayoutBinding(
            package_name="aware_demo_ontology",
            package_root="modules/demo/structure/ontology",
            sources_root="modules/demo/structure/ontology/aware",
            manifest_relative_path="modules/demo/structure/ontology/aware.toml",
        ),
    )
)
```
