# aware-api (Dart)

High-level Dart client for invoking Aware API endpoints over caller-supplied
transport. This package owns generic endpoint invocation helpers only; typed
service clients and DTOs live under `apis/*`.

Direction:

- `workspaces/aware_kernel/modules/api/apis/api` owns authored API contracts, runtime truth, and API endpoint DTOs.
- `workspaces/aware_kernel/modules/api/libs/api` owns the cross-language consumer rail: transport helpers today, and loader/index/client surfaces over API-owned artifacts as the long-term direction.
- `workspaces/aware_kernel/modules/api/libs/api/dart` is therefore downstream of `apis/*`, not a second owner of API schema or runtime semantics.

## Status

Early scaffolding stage. APIs are unstable until the first release.

## Current functionality

- `AwareApiClient.fetchCapabilities()` returns the generic Environment capability response payload.
- `AwareApiClient.invokeFunction()` sends a generic Environment function-call payload and yields `FunctionCallResult`.
- `AwareApiClient.invokeFunctionByName()` resolves function ids from capabilities and returns `FunctionCallResult`.
- `AwareApiClient.invokeApiEndpoint()` / `streamApiEndpoint()` provide shared endpoint helpers over generic `ApiEndpointInvocation` / `ApiEndpointResponse` transport types.
- `AwareFileOpsClient` supports compatibility `uploadFile` / `downloadFile`
  over the mounted HTTP data-plane. Storage owns the implementation; product
  renderers should resolve media through `storage-service-api` / Storage SDK
  before fetching bytes.
- Convenience request models exist for generated function callers (`FunctionInvocationRequest`).

### Context

`AwareApiConfig` accepts an `AwareApiContext` (environment/process/thread/branch/actor) so requests can be scoped to the correct Environment lane. Use `client.setContext()` to update at runtime.
