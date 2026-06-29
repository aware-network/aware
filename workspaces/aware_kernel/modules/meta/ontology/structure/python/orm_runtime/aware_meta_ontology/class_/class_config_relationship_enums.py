from __future__ import annotations

# Standard
from enum import Enum


class ClassConfigRelationshipAttributeRole(Enum):
    auxiliary = "auxiliary"
    foreign_key = "foreign_key"
    reference = "reference"


class ClassConfigRelationshipDirection(Enum):
    forward = "forward"
    reverse = "reverse"


class ClassConfigRelationshipIdentityRail(Enum):
    containment = "containment"
    reference = "reference"


class ClassConfigRelationshipReifiedRole(Enum):
    source_to_association = "source_to_association"
    association_to_target = "association_to_target"


class ClassConfigRelationshipSideLoadingStrategy(Enum):
    eager = "eager"
    lazy = "lazy"


class ClassConfigRelationshipType(Enum):
    many_to_many = "many_to_many"
    many_to_one = "many_to_one"
    one_to_many = "one_to_many"
    one_to_one = "one_to_one"
