-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE class_selection_mode AS ENUM ('all_classes', 'base_class', 'specific_class');

CREATE TYPE condition_logic_strategy AS ENUM ('all', 'any', 'none', 'sequence');

CREATE TYPE condition_operator AS ENUM ('changed', 'contains', 'create', 'decreased', 'ends_with', 'equals', 'exists', 'greater_or_equal', 'greater_than', 'in', 'increased', 'is_not_null', 'is_null', 'less_or_equal', 'less_than', 'matches_regex', 'not_changed', 'not_contains', 'not_equals', 'not_exists', 'not_in', 'starts_with');

CREATE TYPE enum_match_mode AS ENUM ('all_of', 'any_of', 'none_of');

CREATE TYPE relationship_eval_mode AS ENUM ('all_match', 'any_match', 'count_equals', 'count_greater', 'count_less', 'exists', 'none_match', 'not_exists');
