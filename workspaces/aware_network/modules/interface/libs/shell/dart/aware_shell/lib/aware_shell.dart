/// Aware Shell — Flutter renderer binding for Interface Host packages.
///
/// Single barrel for generated interface packages and the app entry. Exports
/// the runtime model, Riverpod providers, and shell widgets that mount what the
/// Interface Host returns.
library;

// API surface re-exports — consumers of aware_shell can rely on this single
// barrel for the host-state DTOs and SDK transport that the shell exposes.
// Mirrors the original aware_interface barrel so generated interface packages
// and tests do not need to add direct aware_interface_service_api /
// aware_interface_sdk imports.
export 'package:aware_interface_service_api/aware_interface_service_api.dart';
export 'package:aware_interface_sdk/aware_interface_sdk.dart';

export 'src/runtime/interface_package_runtime.dart';
export 'src/runtime/interface_host_view_state_cache.dart';
export 'src/runtime/interface_host_view_state_cache_store_factory.dart';
export 'src/runtime/interface_renderer_capabilities.dart';
export 'src/runtime/interface_view_state_decoder_registry.dart';
export 'src/render_spec/pane_render_spec.dart';
export 'src/render_spec/pane_render_spec_renderer.dart';
export 'src/render_spec/render_component_registry.dart';
export 'src/shell/environment_navigator_rail.dart';
export 'src/shell/shell_section.dart';
export 'src/shell/shell_resolved_pane.dart';
export 'src/shell/shell_scaffold.dart';
export 'src/shell/runtime_shell.dart';
export 'src/shell/host_runtime_shell.dart';
export 'src/providers/host_state_provider.dart';
export 'src/providers/package_runtime_provider.dart';
export 'src/providers/pane_api_scope.dart';
