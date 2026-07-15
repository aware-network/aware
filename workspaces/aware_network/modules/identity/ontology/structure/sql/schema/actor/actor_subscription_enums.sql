-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE subscription_activation_status AS ENUM ('blocked_by_route', 'done', 'ready', 'skipped');

CREATE TYPE subscription_addressing_policy AS ENUM ('any', 'routed_only', 'unrouted_only');

CREATE TYPE subscription_filter_mode AS ENUM ('all_instances', 'owned_instances', 'role_instances', 'specific_instances', 'tagged_instances');

CREATE TYPE subscription_status AS ENUM ('active', 'disabled', 'expired', 'paused');
