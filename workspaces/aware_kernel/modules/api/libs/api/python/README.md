# aware-api-client

`aware-api-client` is the transport-neutral Python substrate for generated
Aware API clients. It loads generated API invocation artifacts, resolves
endpoint references, normalizes request payloads, delegates transport to the
caller, and decodes typed Pydantic responses.

## Installation

```bash
pip install aware-api-client
```

Python 3.12 or newer is required.

## Public Boundary

- Generated API packages publish invocation and interface artifacts.
- `aware-api-client` loads those artifacts and prepares typed endpoint calls.
- Your application supplies the transport that sends the invocation to the
  runtime it trusts.
- Routing, deployment, service selection, workspace truth, and settlement stay
  outside this package.

The stable generated-client dependency is `AwareApiEndpointInvoker`.

## Invoke An Endpoint

```python
from aware_api.invocation import load_api_invocation_manifest_file
from aware_api.invoker import (
    ApiEndpointInvocation,
    ApiEndpointResponse,
    ApiEndpointTransport,
    AwareApiEndpointInvoker,
)


class MyTransport(ApiEndpointTransport):
    async def invoke(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointResponse:
        # Send invocation.endpoint_ref and invocation.request_payload through
        # your runtime transport, then return the response envelope.
        return ApiEndpointResponse(
            status="succeeded",
            response_payload={"ok": True},
        )


manifest = load_api_invocation_manifest_file("runtime/api.invocation_manifest.json")
invoker = AwareApiEndpointInvoker(MyTransport())

response = await invoker.invoke_api_endpoint(
    manifest=manifest,
    api_name="home_devices",
    capability_name="lock_door",
    endpoint_name="lock_door",
    request_payload={"door_id": "front"},
)
```

Generated clients should accept an `AwareApiEndpointInvoker` or an
`ApiEndpointTransport`. Each generated method can then resolve the endpoint from
the manifest, pass a Pydantic request model or mapping, and return the decoded
response model.

## Load Interface Specs

Use `aware_api.interface` when a client needs to inspect generated API surface
metadata before invocation.

```python
from aware_api.interface import load_api_interface_spec_file


loaded = load_api_interface_spec_file("runtime/api.interface_spec.json")
endpoint = loaded.index.require_endpoint_by_discriminant(
    "home_devices.lock_door.lock_door"
)
print(endpoint.endpoint.request.class_ref)
```

## Transport Contract

`ApiEndpointTransport` owns one method:

```python
async def invoke(
    invocation: ApiEndpointInvocation,
    *,
    timeout_s: float | None = None,
) -> ApiEndpointResponse:
    ...
```

The invocation envelope contains:

- `endpoint_ref`: stable endpoint reference from the generated manifest.
- `discriminant`: generated endpoint discriminant.
- `request_payload`: JSON object payload after request normalization.

The response envelope contains:

- `status`: `succeeded`, `failed`, or `pending`.
- `response_payload`: decoded by the invoker when a response model is declared.
- `error`: failure text when the transport reports a failed request.

## Streaming Endpoints

For streaming endpoints, implement `ApiEndpointStreamTransport` and use
`stream_api_endpoint(...)`.

```python
async for event in invoker.stream_api_endpoint(
    manifest=manifest,
    discriminant="home_devices.lock_door.events",
    request_payload={"door_id": "front"},
):
    print(event)
```

## Package Contents

- `aware_api.invocation`: generated invocation manifest loading and indexing.
- `aware_api.interface`: generated interface spec loading and indexing.
- `aware_api.invoker`: transport-neutral endpoint invocation helpers.

This package deliberately does not provide a Node client, Environment router,
FunctionCall model, NetworkOperation builder, or service-selection logic.
Those belong to generated API packages and caller-owned transports.

## Release Notes

The default package intentionally keeps dependencies small. Generated API
packages should depend on this package when they need a shared Python invocation
substrate.
