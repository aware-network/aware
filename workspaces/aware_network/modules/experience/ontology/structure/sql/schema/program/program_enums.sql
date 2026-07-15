-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE program_attribute_type AS ENUM ('input', 'output');

CREATE TYPE program_branch_binding_mode AS ENUM ('create', 'reference');

CREATE TYPE program_run_status AS ENUM ('pending', 'running', 'terminal');

CREATE TYPE program_slot_on_bind AS ENUM ('if_empty', 'replace', 'sticky');

CREATE TYPE program_turn_decision_reason AS ENUM ('awaiting_external_signal', 'continue_current_turn', 'input_instruction_requires_runtime_unlock', 'instruction_failed', 'invoke_budget_reached', 'plan_exhausted', 'turn_time_budget_reached');

CREATE TYPE program_turn_transition AS ENUM ('stay_in_turn', 'switch_turn_continue_run', 'switch_turn_wait_signal', 'terminal_program_run');
