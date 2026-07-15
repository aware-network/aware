# aware-node

Runtime package for the `node` module.

Canonical ownership here:

1. node-owned runtime helpers for hosted composition once `NodePackage` and
   `NodeConfig` exist
2. runtime-side interpretation of committed node package truth before it is
   handed to deploy/supervision adapters
3. a clean node-owned boundary above `modules/network`, which continues to own
   live `NetworkNode` topology/runtime state
4. the canonical runtime service surface for `NodeHostOperation`, which
   `services/node` consumes as a transport/runtime adapter

This package does not replace:

- `modules/network/runtime/**` topology/runtime ownership
- `libs/deploy/**` orchestration ownership
- module-owned service/interface/environment runtime contracts
