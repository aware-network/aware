# aware_shell

Flutter shell consumer of `aware_interface_sdk`. Owns the runtime model, Riverpod
providers, and widgets that mount Interface Host packages and render resolved
panes.

## Layering

```text
generated interface package (e.g. aware_control_interface)
       │  depends on
       ▼
aware_shell                      (this package)
       │  depends on
       ▼
aware_interface_sdk              (sdks/interface/dart/aware_interface_sdk)
       │  wraps
       ▼
aware_interface_service_api       (apis/interface/dart/aware_interface_service_api)
       │  speaks to
       ▼
services/interface (Interface Host)
```

`aware_interface_control` is only a source-local transport adapter behind
`aware_interface_sdk` while the local Interface Host socket/websocket bridge is
being replaced by the canonical Interface service API rail. Product Flutter code
and `aware_shell` must not import `aware_interface_control`, `aware_session`, or
Node SDK/API packages directly.

Other-language SDKs mirror `aware_interface_sdk` only. `aware_shell` is the
Flutter-specific renderer binding; future Swift/Kotlin SDKs will add their own
sibling renderer packages over the same SDK core.

## Public surface

Single barrel: `package:aware_shell/aware_shell.dart`. Exports the shell
runtime model, providers, and widgets generated interface packages and the app
entry need.
