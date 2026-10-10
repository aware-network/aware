# Stage 1 - Runtime (FunctionCall -> Commit)

Goal: implement behavior only in runtime handler `impl` sections and prove it with module proof tests.

Minimal references:

- `docs/aware/grammar/README.md`
- `docs/rules/SOFTWARE/1-runtime.md`
- `docs/rules/SOFTWARE/assets/minimal-references/end-to-end-checklist.md`

Rules:

- Generated runtime code is read-only.
- Implement logic only in handler `impl` sections.
- No cross-object mutation from one handler call.

Done criteria:

- Runtime tests pass.
- Module proof passes.
