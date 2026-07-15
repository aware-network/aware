# Experience SDK

Python facade for Experience service API operations.

Use this SDK when a consumer needs Experience-owned behavior without importing
Experience runtime internals or talking directly to Environment, Attention, or
Reactivity for Experience semantics. The main consumers are Interface service
and Environment service orchestration.

The SDK accepts generated request DTOs and also provides keyword helpers that
build the DTOs before invoking the generated Experience API client.

```python
from aware_experience_sdk import build_experience_sdk_client

sdk = build_experience_sdk_client(api_client)
```

## What Experience Owns

Experience is the facade for these public capabilities:

- Thread layout intent: `resolve_thread_layout_intent(...)`
- Personal layout transition: `request_personal_layout_transition(...)`
- Environment profiles: `upsert_environment_profile(...)`,
  `provision_environment_profile(...)`,
  `apply_environment_profile_programs(...)`
- Section graph bindings: `get_section_graph_binding_catalog(...)`,
  `get_section_graph_binding_state(...)`,
  `activate_section_graph_binding(...)`,
  `watch_section_graph_bindings(...)`
- View event transitions: `apply_view_event_transition(...)`
- View action provenance: `record_view_invocation_action(...)`
- Session handoff and feature health: `ensure_session_handoff(...)`,
  `get_session_handoff_status(...)`
- Local ServiceHost dogfood helpers from `aware_experience_sdk.local_host`

Experience does not replace Attention. Attention owns committed focus state.
Experience resolves the meaning of that state for a projection experience:

```text
Attention:  Section -> FocusScope -> Observable + Branch
Experience: ProjectionExperience + Section + Observable -> SectionView -> ViewInstance
```

The Interface surface should render Experience `section_view` evidence and use
Experience methods for view actions/transitions instead of deriving view state
from section keys or focus-scope ids.

## Interface Consumer Flow

A typical Interface lane should use this sequence:

1. Admit the actor into the Environment first through Environment SDK/service.
   The canonical `EnvironmentActorAdmissionReceipt` is admission-only evidence
   for Experience. It is not navigation/attention state and carries no
   process/thread/branch/projection scope.

2. Join an Environment session through Environment SDK/service. The canonical
   `EnvironmentSessionJoinReceipt` is collaboration evidence and carries the
   parent Identity Session/member evidence. It is still not navigation or
   Attention state.

3. Admit the actor for the Experience-specific ActorConfig/RoleConfig contract
   through Experience SDK/service. Environment membership is parent context; the
   Experience actor admission receipt is the Experience authorization evidence.

4. Start or refresh the Experience session feature by passing the Environment
   admission, Environment session join, Experience actor admission, and the
   explicit Experience child Identity `SessionConfig` id. Keep navigation and
   Attention out of Environment admission evidence:

   ```python
   await sdk.ensure_session_handoff(
       session_scope={
           "namespace": "interface",
           "experience_name": "aware_control_identity",
           "environment_id": environment_id,
           "environment_session_id": environment_session_id,
           "actor_id": actor_id,
           "window_key": "main",
           "section_key": "identity_admission",
       },
       actor_context={
           "status": "ready",
           "kind": "human_identity",
           "source": "interface_environment_session",
           "actor_id": actor_id,
       },
       environment_admission=environment_receipt,
       environment_session_join=environment_session_join,
       experience_actor_admission=experience_actor_receipt,
       experience_identity_session_config_id=experience_session_config_id,
       feature={
           "feature_key": "reactivity_transition_dispatch",
           "reason": "interface_experience_lens",
       },
       idempotency_key="interface-experience-session:main",
   )
   ```

   Experience session handoff fails closed without accepted Environment
   admission, accepted Environment session join Identity evidence, accepted
   Experience actor admission role bindings, and an explicit child
   `SessionConfig` id. If the caller uses Environment or Experience SDK wrapper
   receipts, Experience SDK extracts their canonical DTO receipts before
   building the request.

5. Read the section graph binding state:

   ```python
   state_response = await sdk.get_section_graph_binding_state(
       experience_name="aware_control_identity",
       binding_key="identity_admission",
   )
   state = state_response.state
   section_view = state.section_view
   ```

6. Render `section_view.view_ref` and its declared actions:

   ```python
   for action in section_view.actions:
       render_action(
           key=action.action_key,
           label=action.label,
           target=action.target_ref,
       )
   ```

7. When the user invokes an action, run the configured target operation through
   the appropriate API or SDK lane, then record the concrete view-scoped action
   provenance:

   ```python
   action = section_view.actions[0]
   api_call_receipt = await identity_sdk.admit_identity(...)

   action_receipt = await sdk.record_view_invocation_action(
       experience_name="aware_control_identity",
       projection_experience_view_instance_id=(
           section_view.projection_experience_view_instance_id
       ),
       view_invocation_action_config_id=(
           action.view_invocation_action_config_id
       ),
       invocation_key=invocation_key,
       actor_id=actor_id,
       api_call_id=api_call_receipt.api_call_id,
       request_ref="interface.identity_admission.submit",
       receipt_ref="api_call.identity.admit",
       status="succeeded",
   )
   ```

8. If the action/event should move focus, apply the Experience view-event
   transition:

   ```python
   transition = await sdk.apply_view_event_transition(
       experience_name="aware_control_identity",
       profile_key="os.default",
       transition_key="identity_admission.actor_home",
       source_view_ref=section_view.view_ref,
       event_type="identity.admitted",
       action_type="experience.focus.actor_home",
   )
   next_state = transition.state
   ```

9. Refresh or watch the bindings the Interface is rendering:

   ```python
   snapshot = await sdk.watch_section_graph_bindings(
       experience_name="aware_control_identity",
       binding_keys=["identity_admission", "actor_home"],
   )
   ```

The invariant is that view actions are scoped by the concrete
`projection_experience_view_instance_id`, not by global view config. A transition
from one section-bound view instance must not transition every view of the same
kind.

## View Action Provenance

`section_view.actions` contains `ExperienceViewInvocationActionDescriptor`
objects. These descriptors are configuration evidence:

- `view_invocation_action_config_id`: view-level action config
- `experience_invocation_action_config_id`: generic invocation action config
- `api_capability_endpoint_id`: configured API target, when present
- `sdk_operation_id`: configured SDK target, when present

`record_view_invocation_action(...)` records the actual invocation instance.
The response carries an `ExperienceViewInvocationActionReceipt` with:

- `experience_invocation_action_id`: generic invocation instance
- `projection_experience_view_invocation_action_id`: view-instance provenance
- `api_call_id` or `sdk_operation_call_id`: concrete target call evidence
- `object_instance_graph_commit_id` / `commit_id`: commit evidence when known

This gives consumers one common provenance rail:

```text
ViewInstance -> ViewActionConfig -> ExperienceInvocationAction
ExperienceInvocationAction -> API call or SDK operation call -> Commit -> Event
```

The helper can also accept the generated DTO directly:

```python
from aware_experience_sdk import RecordExperienceViewInvocationActionRequest

await sdk.record_view_invocation_action(
    RecordExperienceViewInvocationActionRequest(
        experience_name="aware_control_identity",
        projection_experience_view_instance_id=view_instance_id,
        view_invocation_action_config_id=action_config_id,
        invocation_key=invocation_key,
        status="pending",
    )
)
```

## Environment Consumer Flow

Environment service callers should use the Experience facade for
Experience-owned environment profile behavior:

```python
await sdk.upsert_environment_profile(
    environment_id=environment_id,
    experience_name="aware_control_identity",
    profile={
        "key": "os.default",
        "events": [
            {
                "event_config_ref": "identity.admitted",
                "actions": [
                    {"action_config_ref": "experience.focus.actor_home"},
                ],
            },
        ],
    },
)

await sdk.provision_environment_profile(
    environment_id=environment_id,
    profile_key="os.default",
    topology_seed_key="identity.default",
)

await sdk.apply_environment_profile_programs(
    environment_id=environment_id,
    profile_key="os.default",
    phase="bootstrap",
)
```

Experience owns profile installation and topology activation. Environment stores
only explicit mount pointers and routing context for installed profiles; callers
must not use Environment API/SDK surfaces to provision Experience profiles.

## Layout and Section Binding

Use `resolve_thread_layout_intent(...)` when the caller has semantic intent and
needs Experience to resolve the target layout evidence:

```python
resolution = await sdk.resolve_thread_layout_intent(
    intent_key="aware.workspace.identity_admission",
    experience_name="aware_control_identity",
    profile_key="os.default",
    environment_id=environment_id,
)
```

Use section graph binding helpers when the caller already knows the binding key:

```python
catalog = await sdk.get_section_graph_binding_catalog(
    experience_name="aware_control_identity",
    binding_keys=["identity_admission", "actor_home"],
)

active = await sdk.activate_section_graph_binding(
    experience_name="aware_control_identity",
    binding_key="actor_home",
    rationale="identity admitted",
    focus_scope_title="Actor home",
)
```

`activate_section_graph_binding(...)` delegates lawful focus activation through
Experience. Consumers should not mutate Attention directly for Experience view
transitions.

## Session Feature Status

Experience owns session feature lifecycle. Consumers start a feature through
`ensure_session_handoff(...)` and observe lifecycle/health through
`get_session_handoff_status(...)`.

Runtime session handoff requires typed admission/session evidence. Actor context
alone is insufficient; Interface should pass Environment admission through
`environment_admission`, Environment session join evidence through
`environment_session_join`, Experience actor admission through
`experience_actor_admission`, and the child Identity SessionConfig through
`experience_identity_session_config_id` instead of hiding any of them in generic
`evidence`.

```python
status = await sdk.get_session_handoff_status(
    session_scope={
        "experience_name": "aware_control_identity",
        "profile_key": "os.default",
        "actor_id": actor_id,
    },
    feature_key="reactivity_transition_dispatch",
    lease_key="interface-experience-session:main",
    include_health=True,
)
```

The status response returns actor admission, child Identity Session evidence,
feature leases, worker status, and feature-specific health payloads without
exposing runtime supervisor classes.

## Local ServiceHost Dogfood

For local dogfood, consumers should attach to a local ServiceHost IPC socket
through the SDK instead of importing Experience runtime modules directly:

```python
from aware_experience_sdk.local_host import (
    build_local_experience_sdk_client,
    install_local_experience_service_api_dependency_routes,
    resolve_local_experience_service_host_config,
)

config = resolve_local_experience_service_host_config(
    socket_path="/tmp/aware-experience-interface-local/service/aware-service-host.sock",
    runtime_manifest_path=".aware/environment/runtime/environment.manifest.json",
    reference_experience_toml_paths=(
        "workspaces/aware_network/modules/interface/experiences/aware_control/aware.experience.toml",
    ),
)

await install_local_experience_service_api_dependency_routes(
    config=config,
)

sdk = build_local_experience_sdk_client(
    config=config,
)

catalog = await sdk.get_section_graph_binding_catalog(
    experience_name="aware_conversations",
    binding_keys=["conversations.active"],
)
```

The helper builds:

- `LocalServiceHostAwareApiClient`
- generated `AwareExperienceServiceApiClient`
- public `ExperienceSdkClient`
- Service runtime-owned dependency routes for local Attention/Reactivity
  providers, installed through ServiceHost host-control
- ServiceHost reference Experience TOMLs, materialized by ServiceHost into
  committed Experience reference branches before the SDK hydrates contracts

Process lifecycle remains owned by Node/ServiceHost. During the direct local
Interface dogfood phase, prepare the host with the full service set.
`--service-toml` replaces defaults, so list every required service explicitly:

```bash
uv run aware-cli node interface-local prepare \
  --run-dir /tmp/aware-experience-interface-local \
  --service-toml services/identity/aware.service.toml \
  --service-toml services/hub/aware.service.toml \
  --service-toml workspaces/aware_workspace/services/workspace/aware.service.toml \
  --service-toml services/attention/aware.service.toml \
  --service-toml workspaces/aware_kernel/modules/reactivity/services/reactivity/aware.service.toml \
  --service-toml workspaces/aware_network/modules/experience/services/experience/aware.service.toml \
  --json
```

After the Node/Interface local readiness rail is healthy, use the same service
list with `aware-cli node interface-local up ...` and attach the Experience SDK
to the generated ServiceHost socket under `<run-dir>/service/`.
