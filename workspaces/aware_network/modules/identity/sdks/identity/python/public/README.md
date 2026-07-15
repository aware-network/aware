# aware-identity-sdk

Handwritten SDK facade over the generated
`aware_identity_service_api` client.

Primary entrypoints:

- `IdentitySdkClient`
- `IdentityAdmissionProfile`
- `IdentityAdmission`
- `IdentityGateSnapshot`

Credential setup is exposed through `IdentitySdkClient.setup_credential_profile`.
Credential readiness is exposed through
`IdentitySdkClient.check_credential_readiness`. These helpers create or reuse
Identity-owned credential metadata, attach external secret-material references,
and return resolver readiness receipts without carrying raw secret values.

## Install

```bash
pip install aware-identity-sdk
```

## Public Boundary

- Wraps the generated Identity API client only.
- Accepts a generated `AwareIdentityServiceApiClient` or a
  protocol-compatible test double.
- Builds Identity admission requests for human and agent identities using
  `identity.signup_via_profile.signup_via_profile`.
- Builds actor-role assignment, unassignment, and resolution requests over the
  generated Identity role endpoints.
- Builds actor subscription ensure and resolve requests over generated Identity
  ActorSubscription endpoints. Reactivity owns the event-condition scope ids and
  action-intent resolution; this SDK only forwards Identity-owned subscription
  eligibility/willingness records.
- Builds root and child Identity session requests over generated Identity
  session endpoints. Public callers pass `parent_session_id`; the Identity
  service owns any stable-id scope key derivation.
- Builds credential profile setup and readiness-check requests over generated
  Identity credential endpoints.
- Produces SDK-local admission receipts and gate snapshots for consumers that
  need to reason about Identity + Actor readiness.
- Owns the public credential/API-key rail for Identity and Organization
  consumers through generated Identity API endpoints.
- Credential profiles store provider-neutral metadata, grants, readiness
  receipts, usage receipts, and secret material references only.
- Raw token strings, API keys, passwords, one-time credentials, and private
  secret material are never stored in ontology commits or SDK receipts.
- Does not import Service internals, service protocol internals, local graph
  gateways, runtime indexes, or full `aware-code`.
- Does not export local monorepo admission helpers. Use
  `aware-identity-sdk-local` for local dogfood admission.
- Does not create AgentProcessThread records or route Identity calls into Agent
  service APIs; Agent execution and process threads are Agent-owned.
- Does not treat execution/session tokens as the public Identity credential
  model. Those tokens stay bound to execution context.

## Example

```python
from aware_api import AwareApiEndpointInvoker
from aware_identity_service_api import AwareIdentityServiceApiClient
from aware_identity_sdk import IdentityAdmissionProfile, IdentitySdkClient

api = AwareIdentityServiceApiClient(AwareApiEndpointInvoker(transport))
sdk = IdentitySdkClient(api)

admission = await sdk.admit_human(
    public_key="public-key",
    profile=IdentityAdmissionProfile(
        display_name="Luis",
        public_handle="luis",
        full_name="Luis",
        country_code="US",
        language_code="en",
    ),
)
```

```python
root = await sdk.start_session(
    session_config_id=environment_session_config_id,
    key="environment-main",
)

child = await sdk.start_child_session(
    parent_session_id=root.session.session_id,
    session_config_id=experience_session_config_id,
    key="aware-conversations",
)
```

```python
subscription = await sdk.ensure_actor_subscription(
    actor_id=agent_actor_id,
    event_config_condition_config_scope_id=conversation_message_scope_id,
    name="conversation.message.created",
    action_type="agent.turn.execute",
    priority=50,
)
```
