# End-to-End Minimal Checklist

1. Intent/agreement captured.
2. Module created explicitly (`aware-cli module create`).
3. Ontology + projection + function declarations authored in `.aware`.
4. Compile passes.
5. Quality gates pass (`aware-cli workspace quality-gates --path <target>`).
6. Runtime proof passes.
7. Representation pane registrar/tests pass.
8. Programs replay deterministically from profile symbols.
9. Policy rails materialize capability grants deterministically.
10. Reactivity contracts and activation bindings pass (prefer integrated ACT-REACT binding programs).
11. IPC e2e passes.
12. Evidence logged in issue/feed.
