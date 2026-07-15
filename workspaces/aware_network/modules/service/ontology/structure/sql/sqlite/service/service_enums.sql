-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

-- enum service_config_code_package_config_cardinality: 'many', 'one'

-- enum service_contract_kind: 'metered', 'one_time', 'subscription'

-- enum service_contract_operation_permit_idempotency_scope: 'none', 'operation_nonce', 'request_hash'

-- enum service_contract_operation_permit_scope: 'contract', 'operation', 'session'

-- enum service_contract_operation_price_source: 'contract_override', 'operation_default'

-- enum service_contract_operation_quota_over_limit_behavior: 'allow_metered', 'deny', 'throttle'

-- enum service_contract_operation_quota_unit: 'artifact', 'byte', 'custom', 'operation', 'request', 'token'

-- enum service_contract_operation_quota_window: 'billing_period', 'day', 'hour', 'minute', 'month', 'none'

-- enum service_contract_status: 'active', 'canceled', 'expired', 'pending', 'suspended'

-- enum service_operation_admission_mode: 'contract_and_permit_required', 'contract_required', 'identity_required', 'metered_settlement_required', 'public_read'

-- enum service_operation_fulfillment_kind: 'actuation', 'coordination', 'view'

-- enum service_operation_receipt_policy: 'committed', 'read_model'

-- enum service_operation_settlement_policy: 'none', 'reserve_and_finalize', 'reserve_before_execute'

-- enum service_operation_status: 'failed', 'queued', 'running', 'skipped', 'succeeded'

-- enum service_plan_cycle: 'annual', 'monthly', 'one_time'

-- enum service_subscription_cycle_status: 'failed', 'paid', 'pending'

-- enum service_subscription_invoice_status: 'open', 'paid', 'uncollectible', 'void'

-- enum service_subscription_status: 'active', 'canceled', 'past_due', 'trial'
