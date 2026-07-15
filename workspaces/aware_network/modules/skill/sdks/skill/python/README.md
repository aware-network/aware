# aware-skill-sdk

Handwritten SDK facade over the generated `aware_skill_service_api` client.

Primary entrypoints:

- `SkillSdkClient`
- `SkillPackageSelection`
- `SkillApiPackageSelection`
- `SkillStepInput`
- `SkillInvocation`
- `SkillSdkOperationRunner`
- `SkillSdkOperationRunRequest`
- `SkillSdkOperationRunReceipt`
- `SkillSdkOperationTarget`

## Install

```bash
pip install aware-skill-sdk
```

## Public Boundary

- Wraps the generated Skill API client only.
- Accepts a generated `AwareSkillServiceApiClient` or a protocol-compatible
  test double.
- Builds `SkillInvokeRequest` DTOs for `skill.invoke.invoke`.
- Carries committed SkillPackage and ApiPackage refs only.
- Carries actor-provided step payloads as API-call request payloads.
- Returns SDK-local invocation receipts over the generated
  `SkillInvokeResponse`.
- Provides `SkillSdkOperationRunner` as the SDK-first local-effect bridge for
  canonical skill steps that target declared SDK operations. It dispatches
  through `aware.sdk_operation_catalog.v0` providers and records a Skill SDK
  receipt over the SDK operation handler result.
- Accepts `SkillSdkOperationTarget` to bind an SDK operation run to package and
  catalog coordinates. Installed provider discovery is bootstrap fulfillment;
  the target DTO is the path toward WorkspaceRevision/Hub-resolved
  `sdk.operation_catalog.json` artifacts.
- Does not import Skill runtime modules, Skill service internals, service
  protocol packages, local graph gateways, or runtime indexes.
- Does not execute repository `SKILL.md` files. Markdown skills are
  transitional documentation/import material; executable skills should move
  toward committed SkillPackage truth and SDK operation targets.

## SDK Operation Runner

Use this for local SDK effects that must stay inside the public SDK boundary,
for example Workspace materialization/apply operations that need local checkout
access:

```python
from aware_skill_sdk import (
    SkillSdkOperationRunRequest,
    SkillSdkOperationRunner,
    SkillSdkOperationTarget,
)

runner = SkillSdkOperationRunner(include_builtin_providers=False)
receipt = await runner.run(
    SkillSdkOperationRunRequest(
        target=SkillSdkOperationTarget(
            sdk_package_name="workspace-sdk",
            sdk_name="workspace_sdk",
            operation_ref="workspace_sdk.load_status",
        ),
        request_payload={"workspace_root": "/path/to/workspace"},
    )
)
```

This is the bridge toward canonical SkillPackage execution with SDK operation
targets. The runner uses explicit SDK operation catalogs, not method reflection.
Installed SDKs should publish catalog entry points; `extra_provider_refs` is only
for source-checkout bootstrapping and focused tests.

Receipts include the resolved SDK package/catalog provider, operation ref,
effect policy, target coordinates, and result digest. When SDK catalog artifacts
are resolved from WorkspaceRevision/Hub, callers should pass
`catalog_hash_sha256` and `sdk_package_revision_id` on the target.

## Example

```python
from uuid import UUID

from aware_api import AwareApiEndpointInvoker
from aware_skill_service_api import AwareSkillServiceApiClient
from aware_skill_sdk import (
    SkillApiPackageSelection,
    SkillPackageSelection,
    SkillSdkClient,
    SkillStepInput,
)

api = AwareSkillServiceApiClient(AwareApiEndpointInvoker(transport))
sdk = SkillSdkClient(api)

invocation = await sdk.invoke_skill(
    skill_package=SkillPackageSelection(
        package_name="home-door-skill",
        semantic_object_instance_graph_commit_id=UUID("00000000-0000-0000-0000-000000000001"),
    ),
    api_packages=[
        SkillApiPackageSelection(
            package_name="home-api",
            semantic_object_instance_graph_commit_id=UUID("00000000-0000-0000-0000-000000000002"),
        )
    ],
    skill_config_id=UUID("00000000-0000-0000-0000-000000000003"),
    run_key="door-open-001",
    step_inputs=[
        SkillStepInput(
            skill_config_step_id=UUID("00000000-0000-0000-0000-000000000004"),
            request_payload={"target": "front_door"},
        )
    ],
)
```
