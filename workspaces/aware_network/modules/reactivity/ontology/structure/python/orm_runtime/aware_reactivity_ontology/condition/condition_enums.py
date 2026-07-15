from __future__ import annotations

# Standard
from enum import Enum


class ClassSelectionMode(Enum):
    all_classes = "all_classes"
    base_class = "base_class"
    specific_class = "specific_class"


class ConditionLogicStrategy(Enum):
    all = "all"
    any = "any"
    none = "none"
    sequence = "sequence"


class ConditionOperator(Enum):
    changed = "changed"
    create = "create"
    contains = "contains"
    decreased = "decreased"
    ends_with = "ends_with"
    equals = "equals"
    exists = "exists"
    greater_or_equal = "greater_or_equal"
    greater_than = "greater_than"
    in_ = "in"
    increased = "increased"
    is_not_null = "is_not_null"
    is_null = "is_null"
    less_or_equal = "less_or_equal"
    less_than = "less_than"
    matches_regex = "matches_regex"
    not_changed = "not_changed"
    not_contains = "not_contains"
    not_equals = "not_equals"
    not_exists = "not_exists"
    not_in = "not_in"
    starts_with = "starts_with"


class EnumMatchMode(Enum):
    all_of = "all_of"
    any_of = "any_of"
    none_of = "none_of"


class RelationshipEvalMode(Enum):
    all_match = "all_match"
    any_match = "any_match"
    count_equals = "count_equals"
    count_greater = "count_greater"
    count_less = "count_less"
    exists = "exists"
    none_match = "none_match"
    not_exists = "not_exists"
