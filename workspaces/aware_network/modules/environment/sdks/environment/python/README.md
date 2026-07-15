# aware-environment-sdk

Handwritten SDK facade over the generated
`aware_environment_service_api` client.

Primary entrypoint:

- `EnvironmentActorAdmissionClient`
- `EnvironmentGraphClient`
- `EnvironmentReadinessClient`

## Install

```bash
pip install aware-environment-sdk
```

## Public Boundary

- Wraps the generated Environment API client only.
- Accepts a generated `AwareEnvironmentServiceApiClient` or a protocol-compatible
  test double.
- Resolves runtime function targets through
  `environment.runtime_ref.resolve_runtime_refs`.
- Invokes graph functions through `environment.function_call.invoke_function`.
- Configures service API dependency routes and ensures Environment readiness
  through `environment.service_routes.configure_service_api_dependency_routes`
  and `environment.ready.ensure_ready`.
- Admits actors to a concrete Environment/Profile through
  `environment.actor_admission.admit_actor`; Environment owns the admission
  scope and Identity owns concrete role truth.
- Starts/joins Environment sessions through `environment.session.*`; Environment
  returns linked Identity Session evidence and does not own canonical members.
- Returns normalized client-side receipts.
- Does not import Service internals, service protocol internals, local graph
  gateways, runtime indexes, full `aware-code`, or Experience service internals.
- Does not install, provision, or select Experience profiles. Use the Experience
  SDK/service for profile installation and Experience-owned topology activation.

## Example

```python
from aware_api import AwareApiEndpointInvoker
from aware_environment_service_api import AwareEnvironmentServiceApiClient
from aware_environment_sdk import EnvironmentGraphClient, EnvironmentGraphContext

api = AwareEnvironmentServiceApiClient(AwareApiEndpointInvoker(transport))
client = EnvironmentGraphClient(
    api_client=api,
    context=EnvironmentGraphContext(environment_id=...),
)
```

Actor admission:

```python
from aware_environment_sdk import (
    EnvironmentActorAdmissionClient,
    EnvironmentActorAdmissionContext,
)

admission = EnvironmentActorAdmissionClient(
    api_client=api,
    context=EnvironmentActorAdmissionContext(
        actor_id=actor_id,
        environment_id=environment_id,
    ),
)
receipt = await admission.admit_actor(
    environment_profile_id=environment_profile_id,
    actor_config_id=actor_config_id,
    class_instance_identity_id=class_instance_identity_id,
    requested_role_config_names=["aware.environment.member"],
    reason="join shared environment",
)
```

Environment session:

```python
from aware_environment_sdk import EnvironmentSessionClient, EnvironmentSessionContext

sessions = EnvironmentSessionClient(
    api_client=api,
    context=EnvironmentSessionContext(
        actor_id=actor_id,
        environment_id=environment_id,
    ),
)
started = await sessions.start_session(
    environment_profile_id=environment_profile_id,
    environment_session_config_id=environment_session_config_id,
    admission_receipt=receipt,
    session_key="shared-work",
)
identity_session = started.join_receipt.identity_evidence.identity_session
```

Readiness and route import:

```python
from aware_environment_sdk import EnvironmentReadinessClient, EnvironmentReadinessContext

readiness = EnvironmentReadinessClient(
    api_client=api,
    context=EnvironmentReadinessContext(environment_id=...),
)
await readiness.configure_service_api_dependency_routes(route_payloads)
receipt = await readiness.ensure_ready()
lane = await readiness.get_lane_head(
    branch_id=receipt.branch_id,
    projection_hash=receipt.projection_hash,
)
commit = await readiness.get_object_instance_graph_commit(
    receipt.object_instance_graph_commit_id,
)
```
