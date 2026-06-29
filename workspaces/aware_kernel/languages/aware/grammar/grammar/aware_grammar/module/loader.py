"""Compatibility facade for Code-owned `aware.module.toml` loading."""

from aware_code.module_manifest.loader import (
    AwareModuleTomlError,
    load_aware_module_spec,
)

__all__ = [
    "AwareModuleTomlError",
    "load_aware_module_spec",
]
