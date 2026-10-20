# Neutral Project runtime

`aware-project-runtime` packages the existing six neutral Project contract,
source-codec and initial-state modules. Its only runtime dependency is neutral
Goal Runtime. It has no filesystem provider, command, Service or View dependency.

Imports deliberately retain their original `aware_workflow.project_*` names.
This distribution contributes only those six files to a PEP 420 namespace;
it does not install the broad `aware-workflow` distribution or its initializer.
The broad wheel excludes these same files and depends on their narrow owners.
There is one canonical source and one installed owner per module, not copied
reducers, forwarding classes or duplicate private verifier registries.

Wheel and source-archive inventories are closed and tested. The source archive
includes the original bytes and can rebuild without the monorepo. A manifest
mapping alone is not installed-consumer qualification.

These contracts do not grant publication, membership, eligibility or RUN.
Public commands, a pinned locked installation, release notices and public
activation retain separate qualification gates.
