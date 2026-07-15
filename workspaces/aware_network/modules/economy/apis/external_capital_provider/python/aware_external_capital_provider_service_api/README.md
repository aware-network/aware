# aware_external_capital_provider_service_api

Generated API client package.

Generated action-target API for provider-owned wallet-funding session actuators.

## Install

```bash
pip install aware-external-capital-provider-service-api
```

## Public Boundary

- Use this package from SDKs, tools, agents, and service consumers
  that need a public caller boundary over `aware-api-client`.
- Generated clients accept `aware_api.invoker.AwareApiEndpointInvoker`.
- Endpoint refs and DTOs are generated API contract surfaces.
- This package does not deploy, provision, or host a Service.
- This package does not expose or depend on Service internals,
  service protocol internals, local graph gateways, runtime
  indexes, or full `aware-code`.
- This is not the public `aware hub ...` product rail.

## Example

```python
from aware_api import AwareApiEndpointInvoker
from aware_external_capital_provider_service_api import AwareExternalCapitalProviderServiceApiClient

api = AwareExternalCapitalProviderServiceApiClient(AwareApiEndpointInvoker(...))
```
