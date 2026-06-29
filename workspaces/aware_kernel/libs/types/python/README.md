# aware-types

`aware-types` is the minimal public type helper package shared by Aware Python
SDK and generated Product A API packages.

It intentionally contains no ontology, runtime, compiler, parser, or service
implementation dependencies. Use it when public models need stable JSON/vector
symbols without depending on the full `aware-code` runtime.

## Install

```bash
pip install aware-types
```

Python 3.12 or newer is required.

## Public Symbols

- `JsonValue`
- `JsonObject`
- `JsonArray`
- `Json`
- `Vector`
- `VectorDim`

`aware_code.types` re-exports these symbols for internal compatibility, but new
public packages should import from `aware_types` directly.
