# Issue: Correct a5 feedback and prepare separate a6 documentation candidate

- Slug: agent-a5-feedback-a6-candidate-v0
- Tag: fb/2026-10-05/agent-a5-feedback-a6-candidate-v0
- Status: In Progress
- Owner: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Priority: P1
- Goal: TBD
- Captured: 2026-10-05
- Recorder: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Source: Customer-directed work through aware issue open

## Ownership Scope
- `docs/issues/2026/10/05/fb-2026-10-05-agent-a5-feedback-a6-candidate-v0.md`
- `protocols/agent/A6-CANDIDATE.md`
- `protocols/agent/distribution/aware-agent-fs-0.1.0a6-linux_x86_64-py312.tar.gz`
- `protocols/agent/feedback-a6-candidate-binding.json`
- `protocols/agent/release-a6-candidate.json`
- `protocols/agent/source-provenance.json`
- `protocols/agent/test_a6_bundle.py`
- `protocols/agent/test_bundle.py`
- `protocols/agent/test_installed_a5_usability.py`
- `protocols/agent/test_installed_bootstrap.py`
- `protocols/agent/test_installed_feedback.py`
- `protocols/contracts/agent-fs/v1.2.1/AGENTS.md.in`
- `protocols/contracts/agent-fs/v1.2.1/contract.json`
- `protocols/contracts/agent-fs/v1.2.1/docs/agents/README.md`
- `protocols/contracts/agent-fs/v1.2.1/docs/agents/operational-work.md`
- `protocols/contracts/agent-fs/v1.2.1/docs/agents/repository-change.md`
- `protocols/contracts/agent-fs/v1.2.1/docs/agents/verification-and-handoff.md`
- `protocols/contracts/agent-fs/v1.2.1/docs/alignment/CURRENT.md`
- `protocols/contracts/agent-fs/v1.2.1/docs/alignment/PROTOCOL.md`
- `protocols/contracts/agent-fs/v1.2.1/docs/alignment/README.md`
- `protocols/contracts/agent-fs/v1.2.1/docs/issues/PROTOCOL.md`
- `protocols/evaluations/README.md`
- `protocols/publication/prepare_feedback_a6.py`
- `protocols/publication/source-layout.json`
- `protocols/publication/test_feedback_a6.py`
- `protocols/publication/test_source_layout.py`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/main.py`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/AGENTS.md.in`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/contract.json`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/agents/README.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/agents/operational-work.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/agents/repository-change.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/agents/verification-and-handoff.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/alignment/CURRENT.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/alignment/PROTOCOL.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/alignment/README.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/issues/PROTOCOL.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/pyproject.toml`



## Problem
1. Pinned a5 client evaluation 984d99987b1fe1ff629f954e51cfbeeaeab2da12 reports inconsistent contract labels, ambiguous status/acceptance interpretation, and missing task-test interpreter evidence.




## Goal
1. Correct F-009 in contract 1.2.1; clarify F-010/F-011 and evaluator F-012; prepare separately versioned a6 candidate without new domain behavior, SPEC work, promotion or push.




## Acceptance Checklist
- [ ] Installed contract and scaffold labels consistently advertise 1.2.1; a5 bytes and live selection remain unchanged.
- [ ] Status and acceptance explanations preserve actual SDK semantics; evaluator instructions distinguish installed and task-test interpreters.
- [ ] Exact a6 candidate proves expected one-wheel change and fresh offline checkout-hidden installed checks; hold independent review and publication.




## Updates (append-only)
- Ensured through `issue_sdk.ensure_issue_snapshot`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Applied `issue_sdk.start_issue_progress`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Revalidated immutable client evaluation 984d99987b1fe1ff629f954e51cfbeeaeab2da12 (20 artifacts/108 interactions/12 findings). Reproduced F-009; prepared contract 1.2.1 and client 0.1.0a6 without domain changes or live selection migration. Six feedback regressions, ten source-layout tests and eighteen a5 archive accounting tests pass. First layout attempt failed an outdated README-count assertion; corrected it to separate admitted amendments from historical link-only edits. New installed tests await exact candidate. Candidate build via unchanged scoped builder in separate committed-source checkout is admitted; promotion/push/SPEC excluded. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
