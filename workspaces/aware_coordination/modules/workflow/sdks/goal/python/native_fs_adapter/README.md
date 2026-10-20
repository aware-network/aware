# Native Goal filesystem adapter

This package supplies the Protocol-admitted Git provider for read-only native
Goal Phase eligibility and direction. Its native constructors require a live
retained resolver capability issued by `aware-protocol-fs-adapter`.

The provider verifies committed Goal and Issue sources under the admitted
roots/templates and delegates Phase decisions to the neutral Goal operational
runtime. It does not authorize approval, pursuit, events, dispatch, or Goal
mutation. The raw-root compatibility class is not a native entrance or
fallback and is not exported from the package root.

The package does not depend on the local Goal SDK, Goal Service, generated
API/DTO, Experience, or ontology packages. Installed-candidate selection is
governed separately from this source wheel.
