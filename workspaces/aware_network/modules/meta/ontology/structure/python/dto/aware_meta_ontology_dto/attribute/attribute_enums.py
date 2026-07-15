from __future__ import annotations

# Standard
from enum import Enum


class AttributeCollectionType(Enum):
    list = "list"
    set = "set"
    single = "single"


class AttributeRelationshipRole(Enum):
    auxiliary = "auxiliary"
    foreign_key = "foreign_key"
    reference = "reference"
