# Grammar Development Notes

## Modifiers vs verbs
- **Type modifiers** (`: inline_value`) remain colon-prefixed lists that annotate structural traits of a type.
  - Canonical rule: **branchability is projection-scoped**, not a type modifier (see `projection ... is_branchable`).
- **Class verbs** are appended after the optional attribute list without a colon. Today we only support the `augment` verb, e.g.:
  ```aware
  class TerminalEnv augment Terminal {
      fn attach(host TerminalHost) -> Terminal { }
  }
  ```
  Verbs represent behavioral overlays. The grammar accepts them directly after the modifiers token so they read like actions applied to the base type.

- When adding new verbs, keep them out of the colon list so Aware Type Modifiers continue to describe structural traits only.

### Augmentation topology
- A regular `class Foo { … }` definition represents a canonical node in the graph: it owns attributes and functions.
- An `augment` class declares a base relationship (inheritance-style) to another class:
  - `class Child augment Parent { ... }`
  - Meta models this by setting `ClassConfig.parent_class_id = Parent.id`.
- Augment classes may define additional attributes/functions; downstream materializers decide how inheritance/extension is expressed per target language.

## Function verbs & constructors
- Function declarations now accept an optional verb token that trails the function name and precedes the parameter list:
  ```aware
  fn spawn construct(name String) -> Widget { ... }
  fn get_profile read(public_key String) -> Profile { ... }
  ```
- Language adapters (see `AwareFunctionAdapter`) expose the verb through `get_verb`, and `FunctionConfigBuilder` stores it on `FunctionConfig.verb`. The canonical graph treats verbs as immutable metadata—no additional attributes or relationships are emitted.
- The `construct` verb has special meaning today: the canonical builder records the verb on the `FunctionConfig`, and the `ClassConfigFunctionConfig` link stores `is_constructor`. Renderers/materializers look at the link (never the function alone) to decide whether to emit constructor semantics (e.g., Python adds `@classmethod` + `cls` when the link is marked).
- The canonical meta layer validates verbs against the allowlist (`construct`, `read`) so runtime policies can be enforced deterministically.
- Additional verbs should follow the same pipeline: grammar → adapter → builder → graph. Avoid putting verbs inside the colon-prefixed attribute list so structural capabilities and behavioural verbs stay disjoint.

## Function signatures & tuple returns
- Signatures continue to use positional parameters, but the return clause now accepts either a single `type_ref` or a tuple literal:
  ```aware
  fn list() -> (count Int, terminals Terminal[]) { }
  ```
- The parser emits a `return_clause` node so adapters can capture either the raw type or the tuple. When a tuple is present the Type Descriptor adapter produces a `TypeNodeKind.TUPLE` with ordered elements.
- Tuple entries are canonicalized as named output attributes (`name Type`); builders propagate names + positions to OUTPUT attribute configs so renderers/materializers can expose structured payloads.
- Single-value returns keep the historical behaviour—no code changes required—so existing functions stay binary-compatible.

## Regenerating the parser

From repo root:
```bash
python3 languages/_build/build_grammars.py --language=aware --abi=14
```
