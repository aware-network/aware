-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE memory_working_event_meaning (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  memory_working_event_frame_id UUID UNIQUE,
  -- ATTRIBUTES
  meaning_text TEXT NOT NULL,
  provider_reference TEXT,
  resolved_at TIMESTAMPTZ NOT NULL,
  resolver_status TEXT NOT NULL,
  resolver_endpoint_ref TEXT NOT NULL,
  resolver_discriminant TEXT NOT NULL,
  resolver_program_impl_instruction_intent_id UUID NOT NULL,
  resolver_action_config_id UUID NOT NULL,
  resolver_api_capability_endpoint_id UUID NOT NULL,
  resolver_api_call_id UUID NOT NULL,
  resolver_api_call_key UUID NOT NULL,
  resolver_request_model_id UUID NOT NULL,
  resolver_api_call_outcome_id UUID NOT NULL,
  resolver_response_model_id UUID NOT NULL,
  resolver_response_class_config_id UUID NOT NULL,
  resolver_service_operation_id UUID NOT NULL,
  resolver_service_operation_config_id UUID NOT NULL,
  resolver_service_operation_commit_id UUID NOT NULL,
  resolver_service_operation_head_commit_id UUID NOT NULL,
  resolver_service_operation_branch_id UUID NOT NULL,
  resolver_service_operation_projection_hash TEXT NOT NULL,
  resolver_api_call_outcome_commit_id UUID NOT NULL,
  resolver_api_call_outcome_head_commit_id UUID NOT NULL,
  resolver_api_call_outcome_branch_id UUID NOT NULL,
  resolver_api_call_outcome_projection_hash TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, resolver_api_call_outcome_id),
  FOREIGN KEY (branch_id, projection_hash, memory_working_event_frame_id) REFERENCES memory_working_event_frame(branch_id, projection_hash, id)
);
