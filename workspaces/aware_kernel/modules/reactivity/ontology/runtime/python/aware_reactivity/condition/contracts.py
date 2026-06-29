from __future__ import annotations

"""
Compatibility shim.

Canonical contract ownership is in reactivity API:
- aware_reactivity_service_dto.reactivity.event_action_binding.EventActionBinding
- aware_reactivity_service_dto.reactivity.event_condition_binding_resolution.EventConditionBindingResolution
"""

from aware_reactivity_service_dto.reactivity.event_action_binding import EventActionBinding
from aware_reactivity_service_dto.reactivity.event_condition_binding_resolution import (
    EventConditionBindingResolution,
)

__all__ = ["EventActionBinding", "EventConditionBindingResolution"]
