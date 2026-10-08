# aware-protocol-sdk

Typed SDK interface for `protocol_sdk.admit_target`.

The caller injects one already selected authority provider. The SDK does not
probe for a filesystem or service, fall back between authority modes, parse
`aware.protocol.toml`, or own Goal, Issue, Specification, or publication
semantics. The filesystem implementation is supplied by
`aware-protocol-fs-adapter`; a later Service/API provider must implement the
same operation meaning and return the same neutral admission contract.

## Governed SPEC setup (source checkpoint)

`protocol_sdk.setup_specification` uses the neutral
`ProtocolSpecificationSetupRequest`, result/effect/error values and
`ProtocolSpecificationSetupClient` provider port. These values are not permits.
The request separately binds exact manifest and Issue byte `sha256:<hex>`
digests, explicit root/directories, Issue reference and caller intent. No actor
string, decoded binding or preview can replace the selected owner's admission.

The optional existing-client composition obtains fresh Issue authority for
preview and apply. Planned results have no consumption evidence; completed
results carry the actual owner's effect, execution and authority-grade evidence.
Refusals retain applied/unknown effects and require fresh observation, not
automatic rollback. Source setup and repository publication are separate.

SDK 0.2.0 is an authored source version, not an installed release receipt.
No service selection, Issue policy, physical writer, SPEC parser or approval
implementation is added to this neutral package.
