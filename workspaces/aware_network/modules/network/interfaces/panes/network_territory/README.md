# Network Territory Pane

Control ingress pane for `aware_network.territory.discovery.v1`.

The pane renders Network Service territory truth: nodes, environment advertisements, hosted services, and peer edges. It does not own access gating; Economy/environment access policy is a later service contract layered over the same territory.

The authored render spec uses the compact pane render grammar: root inference,
dot-path node hierarchy, compact state bindings, and renderer-neutral
operational primitives (`field`, `metric`, `list_item`, `section_header`) for
scan-friendly Network evidence.
