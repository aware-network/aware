"""Compatibility wrapper for function impl invocation-plan builders.

Canonical builder location:
- `aware_meta.function.impl.builder`
"""

from aware_meta.function.impl.builder import (
    build_function_impl_from_body,
    build_function_invocation_plan_from_body,
    build_function_invocation_plan_from_impl,
)

__all__ = [
    "build_function_impl_from_body",
    "build_function_invocation_plan_from_body",
    "build_function_invocation_plan_from_impl",
]
