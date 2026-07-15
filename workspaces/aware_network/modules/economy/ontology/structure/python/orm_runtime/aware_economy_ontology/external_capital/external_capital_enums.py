from __future__ import annotations

# Standard
from enum import Enum


class ExternalCapitalConversionMode(Enum):
    direct_denomination = "direct_denomination"


class ExternalCapitalProviderStatus(Enum):
    active = "active"
    inactive = "inactive"


class ExternalCapitalRouteStatus(Enum):
    active = "active"
    inactive = "inactive"
