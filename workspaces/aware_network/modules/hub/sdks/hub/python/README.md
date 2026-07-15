# aware-hub-sdk

Handwritten SDK facade over `aware_hub_service_api`.

Primary entrypoints:

- `AwareHubSdk`
- `HubCodePackageClient`
- `HubDeploymentArtifactClient`

Contract:

- Wraps the generated Hub Api Client only
- Does not import Service internals
- wraps generated Hub Api Client methods
- calls `hub.code_package.search`, `describe`, `resolve`, and `download`
- returns normalized CodePackage descriptors and receipts
- resolves deployment artifact locks through `hub.deployment_artifact.resolve`
- deployment artifact resolution returns public payload locks only; it does not
  download, hydrate, render, or launch a Node
- does not import Hub service internals, service protocol handlers, local host
  helpers, or authority indexes
- `download` returns an artifact-lock receipt; it does not write files
