from __future__ import annotations

# Standard
from enum import Enum


class InterfaceOs(Enum):
    android = "android"
    ios = "ios"
    linux = "linux"
    macos = "macos"
    web = "web"
    windows = "windows"


class InterfaceSessionState(Enum):
    active = "active"
    inactive = "inactive"
