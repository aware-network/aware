# Deliver a read only JSON checker

Illustrative customer brief; select it explicitly or supply your own task. This is not an implementation or an evaluated customer success.

Deliver a standard-library Python JSON checker for a teammate, with tests, usage documentation, an Issue-governed local commit and evidence-based closeout.

## Acceptance

- Run src/jsoncheck.py with exactly one file argument. Read UTF-8 JSON. Accept every JSON value, including scalar values; reject NaN and Infinity.
- Print exactly one JSON object with the sole boolean member valid. Valid input exits 0; malformed JSON, invalid UTF-8 or an unreadable file exits 2 with valid=false.
- Create meaningful standard-library tests and document how a teammate runs the checker and tests.
- Use the installed Aware tooling for Issue lifecycle and scoped local publication. Preserve all existing scaffold files and customer-note.txt. No manual authority-record edits, remote push or seed commit.
- For first publication you may include the tooling-created scaffold and the exact Issue document in your scope, alongside the three approved source paths. Acceptance boxes need not be changed. Record actual verification and publication evidence.

Read [the first useful task](../FIRST-USEFUL-TASK.md). Choose the customer target, approved paths and local author explicitly. SPEC and manifest setup are optional unless your task needs them.

## Scope and local closeout

Use the complete [implementation branch](../issues/FIRST-ISSUE.md#implementation-branch-for-a-tested-json-checker), not the preserved draft-only example. Obtain the actual Issue record path from its read projection. For a first publication, the qualified six-path scope is that Issue record, `AGENTS.md`, `aware.protocol.toml`, `README.md`, `src/jsoncheck.py` and `tests/test_jsoncheck.py`. This includes selected init-created scaffold, not arbitrary existing files. The unchanged init-created `docs/issues/PROTOCOL.md` may remain untracked outside this scope; preserve it. Preserve an unrelated customer note outside scope and publication. A repository with those known untracked files is not claimed clean.

Observe the current Issue, bind the approved paths, observe again and start progress through the original operations. After implementation and tests, explicitly observe the Issue byte guard and select only those exact paths for the original `aware issue publish-close`. Supply the approved local Git author, resolution, verification evidence and explicit intent. Dry-run, review the source/diff and test result, then separately apply with that same reviewed Issue guard and request. The dry-run does not pin earlier HEAD/work-file bytes for apply; apply prepares afresh. Stop if reviewed input changed or admission refuses. Keep both publication and closeout receipts; they are non-atomic. Do not republish to recover spent closeout authority. See [publication](../repository/README.md) and installed leaf help for exact syntax.
