# Protocol — Hub Attention Layout Iterations

Status: draft
Owner: `codex-019c2411-ab35-7821-974a-249a299a9451`

This package follows:

- `docs/specs/PROTOCOL.md`
- `experiences/aware-hub/docs/specs/PROTOCOL.md`

## Goal

Deliver hub attention-layout consumption in signed, issue-backed loops without bypassing attention ownership.

## Required Iteration Location

- `phases/<phase_order>-<phase_slug>/iterations/<iter_order>-<YYYY-MM-DD>-<iter_slug>/README.md`

## Required Sections

Each iteration artifact must include:

- `Goal`
- `Scope In`
- `Scope Out`
- `Expected Deltas`
- `Proofs (commands)`
- `Exit Checks`
- `Roadblock Rules`
- `Sign-Off`

## Lock

Stop and mark `Roadblock` if an iteration:

- introduces a second navigation rail outside focus/attention commit materialization
- assumes attention compiler/runtime behavior that is not locked in attention-owned specs
