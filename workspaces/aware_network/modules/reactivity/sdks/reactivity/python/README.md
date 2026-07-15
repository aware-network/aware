# aware-reactivity-sdk

Python Reactivity SDK facade over the generated
`aware_reactivity_service_api` client.

The SDK keeps Reactivity actor-first and Agent-independent:

- Identity owns `ActorSubscription` truth.
- Reactivity owns semantic bridge events and action lifecycle correlation.
- Agent SDK may later provide an operator context, but it is not a dependency
  of this package.

This package only builds typed Product A request DTOs, calls generated
Reactivity API methods, returns generated response/model objects, and raises a
local SDK error when the generated response rejects the operation.
