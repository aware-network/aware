# Workspace A1 reviewed setup

The original Workspace SDK, neutral runtime, FileSystem and Issue owners provide
the [two-review repository-manifest workflow](REVIEWED-SETUP.md) through
`aware workspace review`. Init supplies configuration, not admission or apply
authority. Review physical scope before scope binding; separately review final
files before apply. Full evidence and original uncertainty remain available.

Software for this bounded flow was published at
[`42a6740e29bb39ec9d332a63d52cb59540655ccd`](https://github.com/aware-network/aware/blob/42a6740e29bb39ec9d332a63d52cb59540655ccd/protocols/workspace/README.md).
[Status and review provenance](../../releases/canonical-reviewed-workflow-fs-v1/PUBLIC-STATUS.md)
remain separate from operation authority. The [previous manual guide](FIRST-SETUP.md)
remains carried; it does not qualify broader operations for this successor.
Read [the full filesystem workflow](../WORKFLOW.md) and
[coherence rules](../COHERENCE.md). Package selection stays with the authored
`portable_protocols` profile. No A2, tree completion, materialization, Service
or object capability is admitted by package or script presence.
