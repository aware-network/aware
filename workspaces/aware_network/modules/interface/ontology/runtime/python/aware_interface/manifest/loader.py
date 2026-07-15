"""Interface-owned manifest facade."""

from aware_interface.manifest.app_loader import (
    AwareAppTomlError,
    load_aware_app_toml_spec,
    load_aware_app_toml_spec_from_text,
)
from aware_interface.manifest.app_source_loader import (
    AwareAppSourceError,
    load_aware_app_source_spec_from_text,
    load_aware_app_source_specs,
)
from aware_interface.manifest.interface_loader import (
    AwareInterfaceTomlError,
    load_aware_interface_toml_spec,
    load_aware_interface_toml_spec_from_text,
)
from aware_interface.manifest.pane_loader import (
    AwarePaneTomlError,
    load_aware_pane_toml_spec,
    load_aware_pane_toml_spec_from_text,
)
from aware_interface.manifest.render_component_loader import (
    AwareRenderComponentTomlError,
    load_aware_render_component_toml_spec,
    load_aware_render_component_toml_spec_from_text,
)

__all__ = [
    "AwareAppSourceError",
    "AwareAppTomlError",
    "AwareInterfaceTomlError",
    "AwarePaneTomlError",
    "AwareRenderComponentTomlError",
    "load_aware_app_source_spec_from_text",
    "load_aware_app_source_specs",
    "load_aware_app_toml_spec",
    "load_aware_app_toml_spec_from_text",
    "load_aware_interface_toml_spec",
    "load_aware_interface_toml_spec_from_text",
    "load_aware_pane_toml_spec",
    "load_aware_pane_toml_spec_from_text",
    "load_aware_render_component_toml_spec",
    "load_aware_render_component_toml_spec_from_text",
]
