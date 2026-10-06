# aware-command-runtime

`aware-command-runtime` is the small shared command composition substrate for
Aware SDK CLIs.

It is intentionally separate from `aware-cli`. `aware-cli` remains the internal
operator rail today. SDK packages can use this package to register command
surfaces and compose public/local launchers without making public packages know
about local packages.

Current pattern:

```python
from aware_command_runtime import AwareCommandRegistry, run_cli


def register_public_commands(registry: AwareCommandRegistry) -> None:
    registry.register_command(
        name="status",
        help="Show public status.",
        configure_parser=lambda parser: parser.add_argument("--json", action="store_true"),
        handle=lambda invocation: 0,
        source="aware-example-sdk.public",
        operation_ref="aware-example-sdk.status",
        projection_ref="aware-example-sdk.cli.status",
    )


def register_local_commands(registry: AwareCommandRegistry) -> None:
    registry.register_command(
        name="service",
        help="Manage local service transport.",
        configure_parser=lambda parser: None,
        handle=lambda invocation: 0,
        source="aware-example-sdk.local",
    )


def main(argv=None) -> int:
    registry = AwareCommandRegistry()
    register_public_commands(registry)
    register_local_commands(registry)
    return run_cli(registry, argv=argv, prog="aware-example")
```

Long term, generated SDK CLI projection materialization should generate the same
registry calls from `.aware` SDK surface truth.

## Neutral supplier boundary

Version 0.1.1 changes packaging/legal metadata, not the runtime API or behavior.
The wheel has no runtime dependencies and no command entrypoints of its own.
It carries the complete Apache-2.0 text and a scoped NOTICE. Test and build
tools are separate inputs, not consumer dependencies.

The registry dispatches only explicitly registered callbacks. It does not
discover a repository, load `.env`, select providers, authenticate actors,
validate SDK bindings or authorize domain operations. `operation_ref`,
`projection_ref` and `context` are supplied labels/data, not authority.
Duplicate names refuse by default; replacement requires explicit `replace=True`.
Parser configuration is eager for every registered command; optional registrars
must keep heavy/domain imports in their selected handlers. No lazy-family API
or generated SDK projection is admitted by this qualification.

Supplier qualification does not select or upgrade any consumer CLI. Protocol's
read-only `admit` pilot and internal developer compatibility adoption have their
own scopes and installed parity gates. Existing workspace registration stays
unchanged; shared generated manifests, locks and environments are not rewritten
by this package correction.
