-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE service_config_code_package_config_cardinality AS ENUM ('many', 'one');

CREATE TYPE service_contract_kind AS ENUM ('metered', 'one_time', 'subscription');

CREATE TYPE service_contract_operation_permit_idempotency_scope AS ENUM ('none', 'operation_nonce', 'request_hash');

CREATE TYPE service_contract_operation_permit_scope AS ENUM ('contract', 'operation', 'session');

CREATE TYPE service_contract_operation_price_source AS ENUM ('contract_override', 'operation_default');

CREATE TYPE service_contract_operation_quota_over_limit_behavior AS ENUM ('allow_metered', 'deny', 'throttle');

CREATE TYPE service_contract_operation_quota_unit AS ENUM ('artifact', 'byte', 'custom', 'operation', 'request', 'token');

CREATE TYPE service_contract_operation_quota_window AS ENUM ('billing_period', 'day', 'hour', 'minute', 'month', 'none');

CREATE TYPE service_contract_status AS ENUM ('active', 'canceled', 'expired', 'pending', 'suspended');

CREATE TYPE service_operation_admission_mode AS ENUM ('contract_and_permit_required', 'contract_required', 'identity_required', 'metered_settlement_required', 'public_read');

CREATE TYPE service_operation_fulfillment_kind AS ENUM ('actuation', 'coordination', 'view');

CREATE TYPE service_operation_receipt_policy AS ENUM ('committed', 'read_model');

CREATE TYPE service_operation_settlement_policy AS ENUM ('none', 'reserve_and_finalize', 'reserve_before_execute');

CREATE TYPE service_operation_status AS ENUM ('failed', 'queued', 'running', 'skipped', 'succeeded');

CREATE TYPE service_plan_cycle AS ENUM ('annual', 'monthly', 'one_time');

CREATE TYPE service_subscription_cycle_status AS ENUM ('failed', 'paid', 'pending');

CREATE TYPE service_subscription_invoice_status AS ENUM ('open', 'paid', 'uncollectible', 'void');

CREATE TYPE service_subscription_status AS ENUM ('active', 'canceled', 'past_due', 'trial');
