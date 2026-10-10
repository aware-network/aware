# Syntax Highlighting (VS Code / Cursor)

Aware syntax highlighting is currently provided via a TextMate grammar in the VS Code extension:

- `languages/aware/grammar/vscode/aware-language/syntaxes/aware.tmLanguage.json`
- optional theme: `languages/aware/grammar/vscode/aware-language/assets/aware-colors.json`

## Goals

- Reflect canonical keywords (`class`, `edge`, `enum`, `fn`, `ann`, `import`, `mirror`, `projection`, `view`, `augment`, `async`, `program`, `let`, `call`).
- Make *semantic hotspots* obvious even without full LSP:
  - class/edge/enum names
  - type references (including dotted qualification)
  - edge specs (`@EdgeSpec`)
  - function verbs (especially `construct`)
  - annotation verbs + structured args (`load`, `overlay`, `override`)
  - projection membership via `projection { ... }` (replaces legacy `ann ... project ...`)
  - deterministic invocation plans via `program { let/call }`

## Proposed Token Categories

- **Declarations**
  - `class`, `edge`, `enum`, `fn`, `ann`, `import`, `mirror`, `program`
  - `projection` (OPG membership blocks)
  - `view` (projection-scoped view declarations)
- **Program statements**
  - `let` (local binding)
  - `call` (invocation step)
- **Modifiers / verbs**
  - type modifiers: `inline_value`
  - class verb: `augment` (inheritance / extension)
  - function verbs: `construct` (and any future verb identifiers)
  - view kind: `construct`, `instance`; flag: `default`
- **Type references**
  - primitive types: `String`, `Int`, `Bool`, `UUID`, `DateTime`, `Float`, `Bytes`, `Json`
  - parametric types: `Vector(768)`
  - qualified names: `domain.schema.Name`
- **Relationship shaping**
  - cardinality: `unique`, `many`
  - nullability: `?`, collections: `[]`, edge specs: `@EdgeSpec`
- **Annotations**
  - verbs: `load`, `overlay`, `override` (legacy/rejected: `project`)
  - structured args:
    - load: `forward`, `reverse`, `both`, `eager`, `lazy`
    - overlay: `language`, `entity`, `rename`, `wire_name`
    - override: `fk`, `relationship`, `nullable`, `name`

### Legacy (deprecated / rejected): `ann ... project ...`

Projection membership should be authored via `projection { ... }`, but older sources may still contain:
- `ann` verb `project` and args: `name`, `target`, `side`, `is_branchable`

## Palette Direction (Guideline)

Keep the palette calm and low-noise while making structure pop:

- keywords/modifiers: cool (purple/indigo)
- verbs/operations (`augment`, `construct`, `ann` verbs): warm accent (orange/amber)
- type references: neutral but distinct from identifiers (blue/teal)
- literals: subdued (green/gray) to reduce visual dominance

This is intentionally a guideline: the extension should work well with a user’s existing theme even without selecting `aware-colors.json`.

## Follow-ups

- Update `aware.tmLanguage.json` to match canonical keywords (`class` not `type`) and to include annotations/imports/verbs.
- Decide whether to keep existing scope names (e.g. `entity.name.type.aware`) for compatibility or rename to `entity.name.class.aware` and update `aware-colors.json` accordingly.
- Fix tree-sitter grammar gaps that affect highlighting:
  - multi-`::` annotation paths
  - void returns written as `-> { }`
