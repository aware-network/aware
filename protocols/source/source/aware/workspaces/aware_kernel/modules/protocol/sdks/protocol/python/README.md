# aware-protocol-sdk

Typed SDK interface for `protocol_sdk.admit_target`.

The caller injects one already selected authority provider. The SDK does not
probe for a filesystem or service, fall back between authority modes, parse
`aware.protocol.toml`, or own Goal, Issue, Specification, or publication
semantics. The filesystem implementation is supplied by
`aware-protocol-fs-adapter`; a later Service/API provider must implement the
same operation meaning and return the same neutral admission contract.
