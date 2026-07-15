"""Compatibility wrapper for function config builders.

Canonical builder location:
- `aware_meta.function.config.builder`
"""

from aware_meta.function.config.builder import (
    build_attribute_configs_from_function_attributes,
    build_function_config_from_code,
)

__all__ = [
    "build_attribute_configs_from_function_attributes",
    "build_function_config_from_code",
]
