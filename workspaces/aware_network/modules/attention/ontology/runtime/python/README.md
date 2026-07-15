# aware-attention

Runtime package for the `attention` module.

Canonical ownership here:

1. local compile/materialization/runtime logic for Attention-owned
   `Layout -> Section -> FocusScope -> Focus + Observable`
2. handler implementation for committed Attention runtime state
3. compiler/runtime rails that the module-owned Attention service package must
   delegate to

This package is not the final shared service boundary.

Long-term contract:

- `workspaces/aware_network/modules/attention/ontology/runtime/python/aware_attention/**` owns the runtime brain
- `workspaces/aware_network/modules/attention/services/attention/**` owns the service adapters that Interface and
  other service consumers call
- Interface Host may mirror section-observable truth temporarily, but that is a
  compatibility rail and not canonical ownership
