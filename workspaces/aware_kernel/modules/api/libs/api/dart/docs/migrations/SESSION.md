# Session Migration

Root Session was retired on 2026-06-20. Do not recreate `libs/session`,
`aware_session`, or a replacement Session API/service.

**Canonical owners**

- Identity owns identity sessions, actor membership, credentials, and identity
  presentation data.
- Environment owns admitted environment session operations, readiness,
  descriptors, lane/head reads, and invocation/session APIs.
- Network/Node and Economy own login, membership, checkout, provisioning, and
  node discovery DTO operations.
- Interface host/runtime owns local pane/window, focus, layout, active-lane,
  and update-hub state.
- Comms and generated API/SDK packages own typed transport/client surfaces.

**Guardrail**

New code must not import `package:aware_session/`, declare `aware_session:`, or
reference `libs/session/dart` outside historical docs.
