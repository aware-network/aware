# Meta Provider Deltas

This package owns the Meta provider-delta implementation.

The old `aware_meta.materialization.provider_delta` compatibility facade has
been retired. Workspace adapters and focused tests should call this package
directly, through `aware_meta.materialization.deltas.service` or the package
entrypoints exposed by `aware_meta.materialization.deltas`. New provider-delta
implementation should land under this package.

## Current Modules

- `constants.py` owns stable provider-delta contract IDs.
- `coercion.py` owns generic payload coercion helpers for mapping, text,
  tuple, and integer normalization.
- `dirty_diff_contracts.py` owns the dirty-entry and semantic-dirty-diff typed
  views plus dirty-entry payload normalization.
- `typed_operation_contracts.py` owns typed operations, typed-operation plans,
  and typed-operation payload normalization.
- `mutation_contracts.py` owns mutation steps, mutation plans, and mutation
  step payload normalization.
- `feature_contracts.py` owns the provider-delta feature-provider contract:
  feature roots expose ontology execution registrations and optional
  source-projection feature-result builders through this shared surface. Source
  projection feature results carry projected `CodeSectionDeltaEntry` values
  plus explicit skipped/blocked evidence, so structural features can report why
  no section delta was emitted without guessing. Feature roots can also expose
  typed-operation dirty-entry planners for feature-specific dirty-entry splits
  such as scalar vs membership updates.
- `feature_registry.py` owns the provider-delta feature registry. It imports
  feature-root providers and exposes registrations to capability facades; it
  must not grow feature-specific behavior.
- `execution_receipt_contracts.py` owns ontology execution, FunctionCall
  capability, OIG commit, head-move-applied, runtime package-index patch, and
  output materialization receipt typed views.
- `change_evidence_contracts.py` owns semantic change reports, preview
  world-change evidence, readable change chains, committed semantic changes,
  semantic commit evidence, and change payload normalization. These contracts
  preserve Meta-owned graph-change meaning without claiming Reactivity event
  dispatch ownership.
- `coverage_matrix.py` owns the code-backed Meta OCG delta coverage matrix.
  It records which semantic subjects/operation families are currently covered
  for semantic change evidence, typed-operation planning, ontology FunctionCall
  execution, Code-owned source projection, language target impact, and Home
  proof evidence. This is the guardrail for choosing the next renderer delta
  without conflating executable ontology deltas with source-projectable code
  segment deltas.
- `ocg_opg_readiness_matrix.py` owns the builder-retirement readiness matrix
  for OCG/OPG construction. It records which semantic capabilities are still
  builder-only versus typed-operation/ontology-FunctionCall/OIG-commit ready,
  including package/root identity, namespace/FQN closure, class/enum/function/
  attribute/relationship contracts, annotation semantics, projection
  declarations, and concrete OPG materialization. This is the guardrail for
  replacing `aware_meta.graph.config.builder` as construction authority without
  confusing renderer/source-projection coverage with graph-authority parity.
- `semantic_scope_closure.py` owns read-only OCG semantic scope/FQN closure
  evidence. It packages namespace paths, import aliases, local class/enum
  symbols, external graph symbols, and optional resolver probes into a typed
  contract so future typed-operation planners can consume Meta-owned scope
  truth without calling builder-local resolver assembly. It does not parse
  source, mutate OIG state, or infer Workspace lane truth. OCG genesis planning
  is the first consumer: it validates closure readiness and class FQN membership
  before emitting typed operations. Broader class/enum/function/relationship
  planners still need committed closure refs before builder-local FQN assembly
  can retire. ClassConfig create/update planning is the first non-genesis
  feature consumer: existing-graph class creates and updates can carry the same
  closure gate through central provider-delta typed-operation planning and block
  before ontology execution when the target class FQN is outside closure
  evidence. EnumConfig create planning now consumes the enum-FQN variant of the
  same gate. FunctionConfig create planning consumes the owner ClassConfig FQN
  through the class gate and resolves the receiver through the owner class
  semantic anchor; scalar FunctionConfig update consumes the same owner-class
  gate before `FunctionConfig.update_config`. RelationshipConfig
  create/update/delete planning now consumes source/target ClassConfig FQN
  closure evidence where available while preserving the existing relationship
  FunctionCall handlers. Enum update, standalone option membership, and
  committed provider-wide closure refs remain blocked until their explicit
  policies/functions are ready.
- `ocg_genesis.py` owns the explicit OCG package genesis
  composition preflight. It composes feature-owned typed operations for package
  creation, root graph creation, package/root attachment, class creation, and
  primitive attribute creation plus OPG root and root-node creation without
  using builder fallback authority. Its preflight proves package, graph, class,
  attribute, OPG, and OPG-node creation through ontology FunctionCall intents.
- `contracts.py` owns the remaining typed internal stage views for Meta
  provider deltas and re-exports stable constants/helpers/stage contracts for
  compatibility. Dirty diff, typed operation, mutation plan, OIG commit,
  head-move-applied, runtime package-index patch, semantic change report,
  semantic commit evidence, output materialization, and final result-envelope stages
  should cross module boundaries through typed views instead of ad hoc
  `dict[str, object]` parsing.
- `pipeline.py` owns the typed internal stage context for provider-delta
  orchestration. `service.py` should use this context to carry preflight,
  planning, execution, and post-commit receipts across the rail instead of
  growing long loose-dict argument threading. Final result and operation-plan
  assembly should consume `MetaProviderDeltaPipelineContext.stage_payloads()`
  so all late-stage receipts come from one normalized context-owned view.
- `service.py` owns provider-delta orchestration plus the rails that have not
  yet been extracted.
- `baseline.py` owns baseline dirty preflight, baseline hydration, baseline ref
  normalization, and committed OIG semantic-object index normalization. The
  production `ObjectInstanceGraph` path is typed and derives baseline
  `source_refs` from committed `ObjectConfigGraphNodeLayout.relative_path`
  relationships; duck-typed OIG traversal is compatibility-only for older
  hydrator payload shapes.
- `dirty_diff.py` owns runtime-delta transform comparison, create/update/noop
  dirty entries, source-ref-backed stale/delete entries, and stale semantic-key
  reporting. Its public payload is normalized through
  `MetaProviderDeltaSemanticDirtyDiff` and `MetaProviderDeltaDirtyEntry` before
  later stages consume it.
- `typed_operations.py` owns typed operation plan construction, explicit Meta
  OCG operation payload previews, blocked typed-operation payloads, and
  semantic change preview projections. It is read-only and does not execute or
  persist changes.
- `capability_matrix.py` owns the provider-delta FunctionCall capability
  matrix. It classifies each typed operation as
  `executable_via_ontology_function`, `blocked_missing_ontology_function`,
  `planner_only`, or `unsupported`, and is the explicit guardrail that prevents
  descriptor-tree planner evidence or raw OIG patch ideas from being treated as
  executable apply.
- `mutation_plan.py` owns typed-operation to mutation-step conversion,
  including attribute receiver resolution, method binding, and descriptor
  resolution. Its public payload is normalized through
  `MetaProviderDeltaMutationPlan` and `MetaProviderDeltaMutationStep` before
  later stages consume it.
- `ontology_execution/` owns typed ontology operation orchestration. Capability
  facades translate registered feature handlers into ordered ontology
  FunctionCall intents, and `ontology_execution/invocation.py` resolves those
  intents against the Meta runtime context/index before invoking
  `MetaGraphRuntime.invoke_function`.
  This is the only provider-delta apply rail for ontology object changes; raw
  OIG/class-instance patching is not allowed. Attribute creates are executable
  only through the owning `ClassConfig`/`FunctionConfig` ontology functions;
  primitive/enum/class `AttributeConfig` updates route through authored
  `AttributeConfig.update_*` ontology functions; collection update and delete
  remain blocked until the ontology declares those public mutation functions.
  Operation planners are registered by `(ontology_subject_kind,
  operation_family)` in `ontology_execution/registry.py`; new semantic subjects
  or operation families should register through a feature root provider instead
  of extending central routing branches.
- `descriptor_tree.py` owns descriptor-tree execution contracts, executor
  preflight checks, descriptor-tree operation payloads, append-ready changes,
  and execution draft construction. It is still read-only and does not commit
  OIG changes.
- `head_move.py` owns Workspace provider-delta head-move request payload
  construction, shared head-move plan normalization, and operation-plan
  enrichment with head-move status/reason/count.
- `execution.py` owns execute-flag preflight, durable OIG execution input
  normalization, OIG commit receipts, operation execution detail payloads, and
  head-move-applied receipts. Applied receipts are derived from successful
  ontology FunctionCall runtime commit receipts. Package-index mutation is
  intentionally separate and belongs after `execute_flag_commit_applied` plus
  `head_move_applied_receipt_ready`.
- `index_patch.py` owns post-commit `MetaRuntimePackageIndexPatch`
  construction and receipt emission. It applies central package-index updates
  only after durable provider-delta OIG commit plus ready head-move refs; dry
  runs and planner-only paths return blocked receipts and never mutate the
  index.
- `change_evidence.py` owns semantic change report construction and committed
  semantic-change evidence from committed typed operations plus head refs.
  Its public payloads are normalized through
  `MetaProviderDeltaSemanticChangeReport`,
  `MetaProviderDeltaSemanticWorldChange`,
  `MetaProviderDeltaReadableSemanticChangeChain`,
  `MetaProviderDeltaSemanticCommitEvidence`, and
  `MetaProviderDeltaCommittedSemanticChange`. It produces read-only Meta
  change evidence; Reactivity event dispatch is a higher-layer consumer concern
  and is not represented by placeholder fields here.
- `source_projection.py` owns the Meta compatibility facade into the Code-owned
  `source_projection` capability. It maps typed Meta semantic change reports
  to generated Code API `CodeSourceProjectionRequest` DTOs, packages
  explicit provider-produced source-projection feature results as
  `CodeSourceProjectionResult(delta_set=CodeSectionDeltaSet)` evidence, and
  delegates feature-specific section-delta creation/skipped evidence through
  `feature_registry.py`. It does not execute source-projection algorithms,
  apply files, own Code resolution, or infer source edits from semantic
  summaries.
  FunctionImpl is currently the only feature allowed to emit concrete
  `CodeSectionDeltaEntry` values. Structural features must return explicit
  feature-owned `source_projection_skipped` policy evidence until their
  renderer segment policies are declared.
  The next source-projection contract gate is Code-owned section/segment
  authority: feature providers may reference built-in or custom
  `CodeSectionRef.section_type` values, but Code Service must validate the
  section and segment before `CodePackageDelta` resolution. If Code does not
  expose a durable segment, the feature must emit blocked evidence rather than
  a guessed byte replacement.
- `target_impact.py` owns provider-delta language target impact planning. It
  consumes typed operation evidence and selects/skips language materialization
  targets before renderer execution, with conservative render-all fallback for
  missing, blocked, mixed, or unsupported operation sets. Workspace and Code do
  not infer these target policies.
- `result.py` owns final provider-delta result envelopes, fallback results,
  baseline-context-missing results, commit-ref compatibility payloads, and
  request-detail evidence. Public result payloads are normalized through
  `MetaProviderDeltaResultEnvelope`, `MetaProviderDeltaResultDetails`,
  `MetaProviderDeltaCommitRefContract`, and
  `MetaProviderDeltaBundlePackageRef` before returning so Workspace/SDK/status
  consumers can rely on typed readiness/fallback evidence while the JSON shape
  stays stable. `service.py` passes resolved rail receipts/plans into this
  module and stays orchestration-focused.

## Extraction Order

1. Continue moving stage boundaries into `contracts.py` typed views before
   adding new operation families. Dirty diff, typed operation, mutation plan,
   receipt, semantic change evidence, and final result envelope boundaries now
   have typed views; dirty diff, typed operation, mutation, execution receipt,
   and change evidence contracts are now focused modules.
2. Continue moving `service.py` stage threading into `pipeline.py` until the
   service reads as ordered orchestration instead of manual payload plumbing.
3. Code-owned source projection: Meta provider-delta change reports feed Code
   API `source_projection` request DTOs, provider-produced entries are packaged
   as `CodeSourceProjectionResult` evidence, and resolution stays behind Code
   Service.
4. Consumer integration: Workspace/product-facing change evidence consumers
   should consume these typed Meta change reports instead of raw provider-local
   payload parsing. Reactivity event envelopes are a higher-layer projection,
   not part of the Meta provider-delta contract.
5. Extract operation-plan and stage-specific contracts only after each
   boundary has enough stable semantics to stand alone without becoming a
   generic junk drawer. Dirty diff, typed-operation, mutation, and execution
   receipt contracts are now focused modules.

Feature behavior should live under the feature root that already owns the
semantic builders. `materialization/deltas` is the contracts/orchestration
surface, not a second structural root. Current feature-root providers:

- `aware_meta.graph.package.deltas` owns ObjectConfigGraphPackage
  provider-delta behavior. It now exposes feature-owned typed-operation
  constructors for package create and package/root attach; ontology execution
  handlers are intentionally still absent, so capability preflight blocks on
  missing package/root FunctionCall handlers instead of falling back to the
  builder.
- `aware_meta.graph.config.deltas` owns ObjectConfigGraph provider-delta
  behavior. It now exposes the feature-owned root graph create typed-operation
  constructor for `ObjectConfigGraph.build`; ontology execution remains blocked
  until the graph-root FunctionCall handler and hash/layout recompute policy are
  implemented.
- `aware_meta.function.impl.deltas` owns FunctionImpl provider-delta behavior:
  ontology FunctionCall planning and FunctionImpl CodeSectionDeltaEntry
  source-projection evidence. The older `materialization/deltas` handler and
  source-projection functions remain compatibility facades.
- `aware_meta.class_.config.deltas` owns ClassConfig provider-delta behavior:
  ClassConfig create/update ontology FunctionCall planning through
  `ObjectConfigGraph.create_node`, `ObjectConfigGraphNode.create_class`, and
  `ClassConfig.update_config`, plus explicit source-projection skipped policy
  evidence. The older `materialization/deltas` class handler module remains a
  compatibility facade.
- `aware_meta.enum.config.deltas` owns EnumConfig create provider-delta
  behavior: enum dirty entries normalize through feature-owned typed-operation
  planning, consume enum-FQN semantic scope closure evidence, and plan
  ontology FunctionCalls through `ObjectConfigGraph.create_node` plus
  `ObjectConfigGraphNode.create_enum`. Enum update and standalone option
  membership stay blocked until explicit ontology functions exist.
- `aware_meta.function.config.deltas` owns FunctionConfig provider-delta
  behavior: FunctionConfig create and scalar update dirty entries normalize
  through feature-owned typed-operation planning, consume owner ClassConfig
  FQN semantic scope closure evidence, and plan ontology FunctionCalls through
  `ClassConfig.create_function_config` and `FunctionConfig.update_config`.
  Class/function membership updates remain a separate edge planner through
  `ClassConfigFunctionConfig.update_config`.
- `aware_meta.class_.config.relationship.deltas` owns RelationshipConfig
  provider-delta behavior: relationship create/update/delete ontology
  FunctionCall planning through `ClassConfig.create_relationship`,
  `ClassConfig.remove_relationship_config`, and
  `ClassConfigRelationship.update_config`, plus explicit source-projection
  skipped policy evidence. The older `materialization/deltas` relationship
  handler module remains a compatibility facade.
- `aware_meta.attribute.config.deltas` owns AttributeConfig provider-delta
  behavior: scalar/membership typed-operation split planning plus AttributeConfig
  and attribute-membership ontology FunctionCall planning, plus explicit
  source-projection skipped policy evidence for scalar and membership updates.
  Primitive AttributeConfig type updates emit concrete Code-owned
  `CodeSectionDeltaEntry(replace_segment)` evidence for the attribute `type`
  segment when source refs, section identity, and renderable primitive type
  descriptor text are available. Renderable primitive default-value updates emit
  concrete Code-owned replacement evidence for `attribute.default_value`;
  unsupported default render/delete cases block instead of guessing. Attribute
  source-projection entries carry segment-level before hashes only; Code owns
  byte-range and file-level source hash resolution.
  The older `materialization/deltas` typed-operation planner and ontology
  handler modules remain compatibility facades.
- `aware_meta.function.config.deltas` owns FunctionConfig provider-delta
  behavior: FunctionConfig create planning through the owner `ClassConfig`,
  scalar/membership update split planning, FunctionConfig and
  class/function-membership ontology FunctionCall planning, plus explicit
  source-projection skipped policy evidence for create/scalar/membership paths.
  FunctionConfig `description` updates emit concrete Code-owned replacement
  evidence for `function.description_comment`, and renderable signature-shape
  updates emit concrete replacement evidence for `function.signature`.
  Unsupported signature shapes block instead of guessing. FunctionConfig
  source-projection entries carry segment-level before hashes only; Code owns
  byte-range and file-level source hash resolution.
  The older `materialization/deltas` typed-operation planner and ontology
  handler modules remain compatibility facades.

The next production slice should migrate feature behavior one feature at a
time through the feature-provider contract. FunctionImpl, ClassConfig,
EnumConfig create, RelationshipConfig, AttributeConfig, and FunctionConfig are
now feature-root providers.

Internal provider-delta consumers should import feature-root modules or the
shared feature registry directly. Older `materialization/deltas` handler and
typed-operation planner modules are compatibility facades for external callers
and transition tests only; they should not be used as the ownership source for
new Meta runtime behavior.

## Coverage Matrix

`coverage_matrix.py` is intentionally cross-feature because it is a contract
and planning surface, not feature behavior. It tracks the current production
truth:

- source projection is concrete for FunctionImpl body, AttributeConfig
  primitive type/default value, and FunctionConfig description/signature shape;
- class, relationship, membership, and generic structural updates emit
  semantic change evidence and ontology FunctionCalls but still report explicit
  source-projection policy gaps;
- FunctionConfig and FunctionConfig membership currently render all language
  targets until impact planning splits description-only updates from signature
  or runtime-affecting updates;
- Home latest-baseline proof coverage is recorded separately from module-test
  coverage so a green unit slice cannot be mistaken for product dogfood.

The former P0 source-projection gaps are now ready through Code-owned segment
capabilities:

- `attribute.update.default_value` -> `attribute.default_value`
- `function.update.signature_shape` -> `function.signature`

`ocg_opg_readiness_matrix.py` is the companion graph-authority matrix. It asks a
different question: can Meta model the OCG/OPG by typed operations and ontology
FunctionCalls without rebuilding the package through
`aware_meta.graph.config.builder`?

Current truth:

- `provider_delta_production_ready` is intentionally separate from
  `builder_retirement_status`: a capability can execute and commit through
  provider deltas while still being partial for full builder retirement;
- no full OCG/OPG capability is marked `builder_retirement_ready` yet, because
  namespace/FQN closure, derived semantics, and full projection/runtime parity
  still block complete builder removal;
- OCG package/root/class/primitive-attribute genesis now has explicit
  typed-operation planning, ontology FunctionCall execution, OIG commit,
  package-index, and proof coverage;
- OPG root/root-node genesis now has the same provider-delta production-ready
  execution coverage, while authored projection declarations and full runtime
  materialization remain separate blockers;
- class create/update, attribute contract deltas, and FunctionImpl graph
  mutations are real typed-operation/OIG-commit rails, but they are still
  partial from a builder-retirement perspective because namespace closure,
  full package closure, and/or parent feature genesis remain builder-owned;
- enum update/options, FunctionConfig invocation-plan deltas, inheritance/
  augment chains, annotation semantics, projection declarations, OPG edge/
  constructor/relationship materialization, and OIG derivation remain P0
  blockers for full OCG/OPG parity;
- renderer/source/generated materialization evidence is downstream and must not
  be treated as graph construction readiness.
