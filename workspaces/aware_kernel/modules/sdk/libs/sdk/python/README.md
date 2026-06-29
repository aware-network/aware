# Aware SDK Core

Common public support utilities for generated and hand-authored Aware SDK
packages.

The package is intentionally product-neutral. Product SDK live integration tests
belong under their owning SDK packages and should depend on the transport
adapter that matches the runtime they exercise.

`aware-sdk-core` must not import comms, network DTOs, product SDKs, product
runtimes, or Service runtime implementation helpers.
