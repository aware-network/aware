from __future__ import annotations

# Standard
from enum import Enum


class ObjectConfigGraphAnnotationKind(Enum):
    load = "load"
    overlay = "overlay"
    override = "override"
    project = "project"
    discriminate = "discriminate"
    oneof = "oneof"
    identity = "identity"
    reference = "reference"
    index = "index"
    storage = "storage"
