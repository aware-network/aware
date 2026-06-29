module.exports = grammar({
    name: 'aware',

    // External token for class-field identity markers.
    // This keeps `key String?` as a normal attribute while still allowing:
    //   identity_email String key
    // where `key` is terminal for that member.
    externals: $ => [
        $.identity_key_marker,
    ],

    // Resolve ambiguity between `ann_path` and the following verb/args.
    conflicts: $ => [
        [$.ann_path],
        // Projection portal edges are intentionally parsed in a class-like form:
        //   TypeRef::relationship TargetProjection
        // This creates a shift/reduce ambiguity with the start of the next projection item
        // (both begin with a qualified name). We allow GLR here to keep the syntax clean.
        [$.projection_edge],
        // `id <ident>(...)` can be either:
        // - class ID declaration (`id_decl`) OR
        // - attribute named `id` with parametric type (`qualified_name(...)`).
        // Keep both parse paths explicit and let adapters/compiler disambiguate by node shape.
        [$.qualified_name, $.id_decl],
        // `member_path` is reused in both annotation selectors (`Type::a.b`) and
        // invocation receivers (`call a.b.c(...)`), where the final `.` can either
        // extend the path or separate receiver/function. Keep both parses explicit.
        [$.member_path],
    ],

    extras: $ => [/\s/],  // Just whitespace

    rules: {
        source_file: $ => repeat(choice(
            $.comment,
            $.import_stmt,
            $.mirror_stmt,
            $.actor_def,
            $.role_def,
            $.action_def,
            $.environment_def,
            $.program_def,
            $.event_def,
            $.projection_def,
            $.experience_def,
            $.experience_profile_scope_def,
            $.graph_def,
            $.binding_def,
            $.api_def,
            $.service_def,
            $.skill_def,
            $.sdk_def,
            $.connector_def,
            $.attention_layout_def,
            $.pane_def,
            $.interface_def,
            $.node_def,
            $.class_def,
            $.edge_def,
            $.fn_def,
            $.enum_def,
            $.ann_def
        )),

        comment: $ => /\/\/[^\n]*/,

        import_stmt: $ => seq(
            'import',
            field('target', $.import_target),
            optional(seq('as', field('alias', $.ident))),
            optional(';')
        ),

        mirror_stmt: $ => seq(
            'mirror',
            field('target', $.qualified_name),
            optional(';')
        ),

        // ---- Programs -------------------------------------------------------
        // Canonical: deterministic invocation plans authored in `.aware`.
        // v0: restricted statement grammar (call/let) to stage invocation plans.
        program_def: $ => seq(
            'program',
            field('name', $.ident),
            optional(seq(
                'impl',
                field('impl', $.qualified_name)
            )),
            optional(field('params', $.program_params)),
            field('body', $.program_block)
        ),

        program_params: $ => seq(
            '(',
            optional(seq(
                $.program_param,
                repeat(seq(',', $.program_param)),
                optional(',')
            )),
            ')'
        ),

        program_param: $ => seq(
            field('name', $.ident),
            field('type', $.type_ref),
            optional(seq(
                '=',
                field('default', $._program_expr)
            ))
        ),

        program_block: $ => seq(
            '{',
            repeat(choice($.comment, $._program_stmt)),
            '}'
        ),

        _program_stmt: $ => choice(
            $.actor_decl_stmt,
            $.port_decl_stmt,
            $.layout_decl_block,
            $.input_stmt,
            $.expect_stmt,
            $.intent_stmt,
            $.let_stmt,
            $.bind_stmt,
            $.call_stmt
        ),

        layout_decl_block: $ => seq(
            choice('layout', 'layouts'),
            '{',
            repeat(choice(
                $.comment,
                $.layout_decl_stmt,
                $.section_decl_stmt,
                $.slot_decl_stmt
            )),
            '}'
        ),

        actor_decl_stmt: $ => seq(
            'actor',
            field('name', $.ident),
            field('actor', $.qualified_name),
            optional(';')
        ),

        port_decl_stmt: $ => seq(
            'port',
            field('name', $.ident),
            field('ref', $.qualified_name),
            optional(field('params', $.port_decl_params)),
            field('body', $.port_decl_block),
            optional(';')
        ),

        port_decl_params: $ => seq(
            '(',
            optional(seq(
                $.port_decl_param,
                repeat(seq(',', $.port_decl_param)),
                optional(',')
            )),
            ')'
        ),

        port_decl_param: $ => seq(
            field('name', $.ident),
            optional(seq(
                '=',
                field('value', $._program_expr)
            ))
        ),

        port_decl_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.port_decl_field_stmt,
                $.port_decl_description_stmt,
                $.port_decl_node_stmt
            )),
            '}'
        ),

        port_decl_description_stmt: $ => seq(
            '"""',
            field('value', /[^"]*/),
            '"""',
            optional(';')
        ),

        port_decl_node_stmt: $ => seq(
            'node',
            field('name', $.ident),
            field('ref', $.ann_path),
            optional(field('params', $.port_decl_params)),
            optional(';')
        ),

        port_decl_field_stmt: $ => seq(
            field('name', $.ident),
            '=',
            field('value', $._program_expr),
            optional(choice(',', ';'))
        ),

        layout_decl_stmt: $ => seq(
            'layout',
            field('args', $.call_args),
            optional(';')
        ),

        section_decl_stmt: $ => seq(
            'section',
            field('args', $.call_args),
            optional(';')
        ),

        slot_decl_stmt: $ => seq(
            'slot',
            field('args', $.call_args),
            optional(';')
        ),

        input_stmt: $ => seq(
            'input',
            field('name', $.ident),
            'from',
            field('source', $.qualified_name),
            optional(seq(
                'default',
                field('default', $._program_expr)
            )),
            optional(';')
        ),

        expect_stmt: $ => seq(
            'expect',
            'event_config',
            field('ref', $._program_expr),
            optional(field('requirement', $.expect_requirement)),
            optional(';')
        ),

        expect_requirement: _ => choice('required', 'optional'),

        intent_stmt: $ => seq(
            'intent',
            'action_config',
            field('action_ref', $._program_expr),
            'on',
            'event_config',
            field('event_ref', $._program_expr),
            optional(';')
        ),

        let_stmt: $ => seq(
            'let',
            field('name', $.ident),
            '=',
            field('value', $._program_expr),
            optional(';')
        ),

        call_stmt: $ => seq(
            optional(field('actor', $.ident)),
            'call',
            optional(field('object', $.qualified_name)),
            field('call', $.program_call),
            optional(';')
        ),

        bind_stmt: $ => seq(
            'bind',
            field('port', $.ident),
            field('view', $.qualified_name),
            optional(';')
        ),

        _program_expr: $ => choice(
            $.program_call,
            $.qualified_name,
            $.literal,
            $.json_object,
            $.json_array
        ),

        program_call: $ => seq(
            field('target', $.qualified_name),
            field('args', $.call_args)
        ),

        // ---- Events --------------------------------------------------------
        // Canonical event declarations authored in `.aware`.
        // Event bindings scope event semantics by projection + class + operation.
        event_def: $ => seq(
            'event',
            field('name', $.ident),
            optional(field('options', $.event_options)),
            '{',
            repeat(choice($.comment, $.event_binding)),
            '}'
        ),

        event_options: $ => repeat1($.event_option),

        event_option: $ => choice(
            seq('name', field('event_name', $.string_literal)),
            seq('renderer', field('renderer_key', $.string_literal)),
            seq('title', field('title', $.string_literal)),
            seq('description', field('description', $.string_literal))
        ),

        event_binding: $ => seq(
            'bind',
            field('projection', $.qualified_name),
            field('type', $.qualified_name),
            field('operation', $.event_operation),
            optional(field('attribute', $.ident)),
            optional(';')
        ),

        event_operation: _ => choice('create', 'update', 'delete'),

        // ---- Actors / Roles -------------------------------------------------
        role_def: $ => seq(
            'role',
            field('name', $.ident),
            '{',
            repeat(choice($.comment, $.role_doc_stmt, $.role_capability_stmt)),
            '}'
        ),

        role_doc_stmt: $ => seq(
            '"""',
            field('value', /[\s\S]*?/),
            '"""',
            optional(';')
        ),

        role_capability_stmt: $ => seq(
            field('target', $.qualified_name),
            optional(';')
        ),

        actor_def: $ => seq(
            'actor',
            field('name', $.ident),
            field('kind', $.qualified_name),
            '{',
            repeat(choice($.comment, $.actor_doc_stmt, $.actor_role_stmt)),
            '}'
        ),

        actor_doc_stmt: $ => seq(
            '"""',
            field('value', /[\s\S]*?/),
            '"""',
            optional(';')
        ),

        actor_role_stmt: $ => seq(
            'role',
            field('role', $.qualified_name),
            optional(';')
        ),

        // ---- Actions / Environments -----------------------------------------
        action_def: $ => seq(
            'action',
            field('name', $.ident),
            optional(field('params', $.program_params)),
            '{',
            repeat(choice($.comment, $.action_doc_stmt, $.action_program_stmt)),
            '}'
        ),

        action_doc_stmt: $ => seq(
            '"""',
            field('value', /[\s\S]*?/),
            '"""',
            optional(';')
        ),

        action_program_stmt: $ => seq(
            'program',
            field('program', $.qualified_name),
            optional(field('args', $.call_args)),
            optional(';')
        ),

        environment_def: $ => seq(
            'environment',
            field('name', $.ident),
            '{',
            repeat(choice($.comment, $.environment_item)),
            '}'
        ),

        environment_item: $ => choice(
            $.environment_actor_stmt,
            $.environment_experience_stmt,
            $.environment_program_stmt,
            $.environment_event_stmt
        ),

        environment_actor_stmt: $ => seq(
            'actor',
            field('actor', $.qualified_name),
            optional(field('body', $.environment_actor_block)),
            optional(';')
        ),

        environment_actor_block: $ => seq(
            '{',
            repeat(choice($.comment, $.environment_actor_doc_stmt, $.environment_actor_role_stmt)),
            '}'
        ),

        environment_actor_doc_stmt: $ => seq(
            '"""',
            field('value', /[\s\S]*?/),
            '"""',
            optional(';')
        ),

        environment_actor_role_stmt: $ => seq(
            'role',
            field('role', $.qualified_name),
            optional(';')
        ),

        environment_experience_stmt: $ => seq(
            'experience',
            field('experience', $.qualified_name),
            optional(';')
        ),

        environment_program_stmt: $ => seq(
            'program',
            field('program_config', $.qualified_name),
            field('program_impl', $.qualified_name),
            optional(';')
        ),

        environment_event_stmt: $ => seq(
            'event',
            field('event', $.qualified_name),
            '{',
            repeat(choice($.comment, $.environment_event_action_stmt)),
            '}'
        ),

        environment_event_action_stmt: $ => seq(
            'action',
            field('action', $.qualified_name),
            optional(field('body', $.environment_event_action_block)),
            optional(';')
        ),

        environment_event_action_block: $ => seq(
            '{',
            repeat(choice($.comment, $.environment_event_action_doc_stmt)),
            '}'
        ),

        environment_event_action_doc_stmt: $ => seq(
            '"""',
            field('value', /[\s\S]*?/),
            '"""',
            optional(';')
        ),

        call_args: $ => seq(
            '(',
            optional(seq(
                $.call_arg,
                repeat(seq(',', $.call_arg)),
                optional(',')
            )),
            ')'
        ),

        call_arg: $ => choice(
            seq(
                field('name', $.ident),
                '=',
                field('value', $._program_expr)
            ),
            field('value', $._program_expr)
        ),

        import_target: $ => choice(
            // Canonical: allow deep dotted imports (e.g., domain.schema.Symbol or package.domain.schema.Symbol)
            seq($.ident, repeat1(seq('.', $.ident))),
            seq($.ident, repeat(seq('.', $.ident)), '.', '*')
        ),

        // ---- Namespaces ------------------------------------------------------
        // Canonical: treat dotted qualification as a single syntactic unit.
        // The resolver is SSOT: it interprets `A.B.C` as domain/schema/class etc by count+context and raises on ambiguity.
        qualified_name: $ => seq($.ident, repeat(seq('.', $.ident))),

        // ----  Types  --------------------------------------------------------
        class_def: $ => seq(
            'class',
            field('name', $.ident),
            optional(field('modifiers', $.class_mods)),  // Class modifiers / attributes
            optional(seq(
                field('verb', $.class_verb),              // Class verb/operator (e.g., augment)
                field('verb_target', $.type_ref)          // Target being augmented (required when verb is present)
            )),
            '{',
            repeat(choice($.comment, $.id_decl, $.attr_def, $.fn_def)),
            '}'
        ),

        id_decl: $ => seq(
            'id',
            field('key', $.ident),
            field('params', $.program_params),
            field('body', $.id_block)
        ),

        id_block: $ => seq(
            '{',
            repeat(choice($.comment, $.id_namespace_stmt, $.id_template_stmt, $.id_let_stmt)),
            '}'
        ),

        id_namespace_stmt: $ => seq(
            'namespace',
            field('namespace', $.ident),
            optional(';')
        ),

        id_template_stmt: $ => seq(
            'template',
            field('template', $.string_literal),
            optional(';')
        ),

        id_let_stmt: $ => seq(
            'let',
            field('name', $.ident),
            '=',
            field('value', $._program_expr),
            optional(';')
        ),

        // Class modifiers (space-separated, canonical)
        class_mods: $ => prec.right(seq(
            ':',
            repeat1($.class_attr)
        )),

        // ---- Attributes ------------------------------------------------------
        attr_def: $ => seq(
            field('name', choice($.ident, alias('id', $.ident))),
            field('type', $.type_ref),
            optional(field('cardinality', choice($.unique_kw, $.many_kw))),
            optional(field('identity_key', $.identity_key_marker)),
            optional(seq(
                '=',
                field('default', $.default_value)  // Allow both literals and identifiers (enum values)
            )),
            optional(';')
        ),

        type_ref: $ => seq(
            choice(
                field('base', $.qualified_name),
                field('parametric', $.parametric_type),
                field('mapping', $.mapping_type)
            ),
            optional(seq('[', ']')),             // list type
            optional('?'),                        // optional/nullable
            optional(seq('@', $.edge_spec_ref))       // explicit edge with optional schema
        ),

        // Edge specification reference - supports optional schema prefix like type_ref
        edge_spec_ref: $ => seq(
            field('edge_name', $.qualified_name)
        ),

        // (no backref in topology grammar)

        // Parametric types like vector(1536)
        parametric_type: $ => seq(
            field('base_type', $.qualified_name),
            '(',
            field('parameters', commaSep1(choice($.number_literal, $.ident))),
            ')'
        ),

        // Mapping types like Dict[String, Int]
        mapping_type: $ => seq(
            'Dict',
            '[',
            field('key', $.type_ref),
            ',',
            field('value', $.type_ref),
            ']'
        ),

        unique_kw: _ => 'unique',
        many_kw: _ => 'many',

        // ----  Edges  --------------------------------------------------------
        edge_def: $ => seq(
            'edge',
            field('name', $.ident),
            optional(field('modifiers', $.edge_mods)),
            '{',
            repeat(choice($.comment, $.attr_def, $.fn_def)),
            '}'
        ),

        // Edge modifiers
        edge_mods: $ => seq(
            ':',
            repeat1($.class_attr)  // Edges use same modifiers as classes
        ),

        // ---- Class/Edge/Enum attributes --------------------------------------
        class_attr: $ => choice(
            'inline_value'
        ),

        // ---- Class verbs / operators ----------------------------------------
        class_verb: _ => 'augment',

        // ----  Functions  ----------------------------------------------------
        fn_def: $ => seq(
            optional('async'),
            'fn',
            field('name', $.ident),
            optional(field('verb', $.ident)),
            field('sig', $.signature),
            optional(field('body', $.block))     // body is optional for now
        ),

        signature: $ => choice(
            prec(2, seq(
                '(',
                optional(seq($.input_attr, repeat(seq(',', $.input_attr)), optional(','))),
                ')',
                '->',
                field('return_clause', $.return_clause)
            )),
            prec(1, seq(
                '(',
                optional(seq($.input_attr, repeat(seq(',', $.input_attr)), optional(','))),
                ')',
                '->'
            )),
            seq(
                '(',
                optional(seq($.input_attr, repeat(seq(',', $.input_attr)), optional(','))),
                ')'
            )
        ),

        return_clause: $ => choice(
            $.type_ref,
            $.return_tuple
        ),

        return_tuple: $ => seq(
            '(',
            commaSep1($.output_attr),
            optional(','),
            ')'
        ),

        output_attr: $ => seq(
            field('name', $.ident),
            field('type', $.type_ref)
        ),

        input_attr: $ => seq(
            field('name', $.ident),
            field('type', $.type_ref),
            optional(field('identity_key', 'key')),
            optional(seq(
                '=',
                field('default', $.default_value)  // Allow both literals and identifiers (enum values)
            ))
        ),

        // ---- Default values ---------------------------------------------------
        // Canonical default values allow scalar literals, enum identifiers, and strict JSON objects/arrays.
        // Strict JSON here means: double-quoted strings, no trailing commas.
        default_value: $ => choice(
            $.literal,
            $.ident,
            $.default_call,
            $.json_object,
            $.json_array
        ),

        // Factory-style defaults (e.g. `now()` for DateTime) are modeled as no-arg calls.
        // This is intentionally constrained to keep the grammar deterministic and defaults
        // round-trippable across materializations.
        default_call: $ => seq(
            field('name', $.ident),
            '(',
            ')'
        ),

        json_value: $ => choice(
            $.json_object,
            $.json_array,
            $.json_string_literal,
            $.json_number_literal,
            // NOTE: numbers in strict JSON literals were previously failing to parse due
            // to a lexer ambiguity with `number_literal`. Accept `number_literal` here
            // so JSON objects/arrays with numbers parse deterministically; semantic
            // strictness is enforced by `json.loads(...)` in the adapters.
            $.number_literal,
            $.json_boolean_literal,
            $.json_null_literal
        ),

        json_object: $ => seq(
            '{',
            optional(seq(
                $.json_pair,
                repeat(seq(',', $.json_pair))
            )),
            '}'
        ),

        json_pair: $ => seq(
            field('key', $.json_string_literal),
            ':',
            field('value', $.json_value)
        ),

        json_array: $ => seq(
            '[',
            optional(seq(
                $.json_value,
                repeat(seq(',', $.json_value))
            )),
            ']'
        ),

        json_string_literal: $ => seq(
            '"',
            repeat(choice(
                $.json_escape_sequence,
                /[^"\\]/
            )),
            '"'
        ),

        json_escape_sequence: _ => token(seq(
            '\\\\',
            choice(
                /["\\\\/bfnrt]/,
                /u[0-9a-fA-F]{4}/
            )
        )),

        json_number_literal: _ => token(/-?(0|[1-9]\\d*)(\\.\\d+)?([eE][+-]?\\d+)?/),

        json_boolean_literal: _ => choice('true', 'false'),

        json_null_literal: _ => 'null',

        // ---- Function body plan statements ---------------------------------
        // v0 contract:
        // - allow structured invocation plans in class function bodies
        // - keep `_any` fallback for backward compatibility while we migrate
        //   free-form bodies to explicit plan statements.
        fn_stmt: $ => choice(
            $.fn_let_stmt,
            $.fn_call_stmt,
            $.fn_construct_stmt,
            $.fn_set_stmt,
            $.fn_require_stmt,
            $.fn_delete_stmt
        ),

        fn_let_stmt: $ => seq(
            'let',
            field('name', $.ident),
            '=',
            field('value', $.fn_stmt_expr),
            optional(';')
        ),

        fn_call_stmt: $ => seq(
            $.fn_call_expr,
            optional(';')
        ),

        fn_construct_stmt: $ => seq(
            $.fn_construct_expr,
            optional(';')
        ),

        fn_set_stmt: $ => seq(
            'set',
            field('target', $.ident),
            '=',
            field('value', $.fn_stmt_expr),
            optional(';')
        ),

        fn_require_stmt: $ => seq(
            'require',
            field('kind', $.ident),
            '(',
            optional(field('operands', $.fn_require_operands)),
            ')',
            optional(field('message', $.fn_require_message)),
            optional(';')
        ),

        fn_require_operands: $ => seq(
            $.fn_stmt_expr,
            repeat(seq(',', $.fn_stmt_expr))
        ),

        fn_require_message: $ => seq(
            'message',
            $.string_literal
        ),

        fn_delete_stmt: $ => seq(
            'delete',
            field('target', 'self'),
            optional(';')
        ),

        fn_stmt_expr: $ => choice(
            $.fn_call_expr,
            $.fn_construct_expr,
            $.program_call,
            $.qualified_name,
            $.literal
        ),

        fn_call_expr: $ => seq(
            'call',
            optional(field('capture', $.ident)),
            field('target', $.fn_invoke_target)
        ),

        fn_construct_expr: $ => seq(
            'construct',
            optional(field('capture', $.ident)),
            field('target', $.fn_invoke_target)
        ),

        fn_invoke_target: $ => choice(
            $.fn_member_invoke,
            $.fn_local_invoke
        ),

        fn_member_invoke: $ => seq(
            field('receiver', $.member_path),
            '.',
            field('function', $.ident),
            field('args', $.call_args)
        ),

        fn_local_invoke: $ => seq(
            field('function', $.ident),
            field('args', $.call_args)
        ),

        block: $ => seq(
            '{',
            repeat(choice($.fn_stmt, $.literal, $.comment, $._any)),
            '}'
        ),

        // ----  Literals for default values ---------------------------------
        literal: $ => choice(
            $.string_literal,
            $.number_literal,
            $.boolean_literal,
            $.null_literal,
            $.triple_string_literal,
            $.dollar_string_literal
        ),

        // Keep multiline raw literals as low-precedence tokens so legacy block `_any`
        // can still absorb function-body docstrings while defaults/expressions remain valid.
        // Triple-quoted and dollar-delimited strings must outrank plain strings so
        // description blocks tokenize as a single literal instead of three adjacent
        // `string_literal` nodes (`""` + `"text"` + `""`).
        triple_string_literal: _ => token(prec(1, seq(
            '"""',
            repeat(choice(/[^"]+/, /"[^"]/, /""[^"]/)),
            '"""'
        ))),
        dollar_string_literal: _ => token(prec(1, seq(
            '$$',
            repeat(choice(/[^$]+/, /\$[^$]/)),
            '$$'
        ))),

        string_literal: _ => token(prec(-1, choice(
            seq('"', /[^"]*/, '"'),
            seq("'", /[^']*/, "'")
        ))),

        number_literal: $ => /[0-9]+(\.[0-9]+)?/,

        boolean_literal: $ => choice('true', 'false'),

        null_literal: $ => 'null',

        // ----  Tokens  -------------------------------------------------------
        ident: _ => /[A-Za-z_][A-Za-z0-9_]*/,

        // Keep compatibility fallback for legacy free-form function body text,
        // but force structured keywords (`let`/`call`/`construct`) to win tokenization.
        _any: $ => choice(token(prec(-1, /[^{}]+/)), $.block),  // naive nested blocks

        // ----  Enums  --------------------------------------------------------
        enum_def: $ => seq(
            'enum',
            field('name', $.ident),
            optional(field('modifiers', $.enum_mods)),  // Enum modifiers
            '{',
            repeat(choice($.comment, $.enum_value_def)),
            '}'
        ),

        // Enum modifiers
        enum_mods: $ => prec.right(seq(
            ':',
            repeat1($.class_attr)  // Enums use same modifiers as classes
        )),

        // Enum value definition
        enum_value_def: $ => seq(
            field('name', $.ident),
            optional(seq(
                '=',
                field('value', $.literal)
            )),
            optional(';')
        ),

        // ----  Projections (OPG)  -------------------------------------------
        projection_def: $ => seq(
            'projection',
            field('name', $.ident),
            optional(field('options', $.projection_options)),
            '{',
            repeat(choice(
                $.comment,
                $.projection_item
            )),
            '}'
        ),

        projection_options: $ => repeat1($.projection_option),

        projection_option: $ => choice(
            seq('name', field('projection_id', $.string_literal)),
            seq('label', field('label', $.string_literal)),
            field('is_branchable', $.branchable_flag)
        ),

        branchable_flag: _ => 'is_branchable',

        projection_item: $ => choice(
            $.projection_edge,
            $.projection_branch,
            $.projection_root,
            $.projection_view_group,
            $.projection_view_def
        ),

        // Root class for a projection.
        // Canonical: exactly one per projection.
        projection_root: $ => seq(
            optional('root'),
            field('type', $.qualified_name),
            optional(';')
        ),

        // Relationship membership (or portal) inside a projection.
        // - No target means membership in the same projection.
        // - A trailing target projection symbol means portal edge to another projection.
        projection_edge: $ => seq(
            field('type', $.qualified_name),
            '::',
            field('member', $.ident),
            optional(field('target', $.projection_target)),
            optional(';')
        ),

        // Branch contract declaration inside a projection.
        // v0: branch name only; config payload is ontology-owned and added in
        // follow-up grammar slices.
        projection_branch: $ => choice(
            seq(
                'branch',
                field('name', $.ident),
                field('body', $.block)
            ),
            seq(
                'branch',
                field('name', $.ident),
                optional(';')
            )
        ),

        projection_target: $ => choice(
            $.qualified_name,
            $.string_literal
        ),

        // ----  Projection Observables (OPGI + ObjectProjectionGraphObservable) ----------
        // Canonical keyword is `observable`.
        // Legacy compatibility aliases `observation` and `view` are accepted
        // during migration.
        projection_observation_kw: _ => choice('observable', 'observation', 'view'),

        view_kind: _ => choice('construct', 'instance'),

        projection_view_group: $ => seq(
            field('keyword', $.projection_observation_kw),
            field('prefix', $.view_path),
            '{',
            repeat(choice(
                $.comment,
                $.projection_view_group,
                $.projection_view_def
            )),
            '}'
        ),

        projection_view_def: $ => seq(
            field('keyword', $.projection_observation_kw),
            field('view_key', $.view_path),
            field('kind', $.view_kind),
            optional('default'),
            field('body', $.block)
        ),

        // ---- Experience Contracts ------------------------------------------
        // Experience is authored as an overlay on top of structural projection
        // contracts. It declares narrative branches and renderer views over
        // projection observables.
        experience_def: $ => seq(
            'experience',
            field('name', $.ident),
            'on',
            field('projection', $.qualified_name),
            '{',
            repeat(choice(
                $.comment,
                $.experience_item
            )),
            '}'
        ),

        experience_item: $ => choice(
            $.experience_branch,
            $.experience_observable_group,
            $.experience_node_def,
            $.experience_surface_def
        ),

        experience_branch: $ => choice(
            seq(
                'branch',
                field('name', $.ident),
                optional('default'),
                field('body', $.block)
            ),
            seq(
                'branch',
                field('name', $.ident),
                optional('default'),
                optional(';')
            )
        ),

        experience_observable_group: $ => seq(
            'observable',
            field('observable', $.view_path),
            '{',
            repeat(choice(
                $.comment,
                $.experience_view_def
            )),
            '}'
        ),

        experience_view_def: $ => seq(
            'view',
            field('view_key', $.view_path),
            optional('default'),
            'state',
            field('state_model', $.ann_path),
            optional(seq(
                'provider',
                field('state_provider', $.ann_path)
            )),
            field('body', $.experience_view_block)
        ),

        experience_view_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.string_literal,
                $.experience_view_action_def
            )),
            '}'
        ),

        experience_view_action_def: $ => seq(
            'action',
            field('action_key', $.ident),
            field('action_kind', $.experience_view_action_kind),
            optional(field('target_ref', $.qualified_name)),
            optional(field('body', $.experience_view_action_block)),
            optional(';')
        ),

        experience_view_action_kind: $ => choice('view', 'sdk', 'api', 'service'),

        experience_view_action_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.experience_view_action_label_stmt,
                $.experience_view_action_receipt_stmt,
                $.experience_view_action_confirmation_stmt,
                $.experience_view_action_optimistic_stmt
            )),
            '}'
        ),

        experience_view_action_label_stmt: $ => seq(
            'label',
            field('label', $.string_literal),
            optional(';')
        ),

        experience_view_action_receipt_stmt: $ => seq(
            'receipt',
            field('policy', $.ident),
            optional(';')
        ),

        experience_view_action_confirmation_stmt: $ => seq(
            'confirmation',
            field('policy', $.ident),
            optional(';')
        ),

        experience_view_action_optimistic_stmt: $ => seq(
            'optimistic',
            field('policy', $.ident),
            optional(';')
        ),

        // ---- Connector / Sensor / Actuator configs -------------------------
        // Authored connector files declare config-level truth only. Runtime
        // connector sessions and concrete sensor/actuator instances are
        // fulfillment receipts, not authored package config.
        connector_def: $ => seq(
            'connector',
            field('connector_key', $.ident),
            field('body', $.connector_block)
        ),

        connector_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal,
                $.connector_item
            )),
            '}'
        ),

        connector_item: $ => choice(
            $.connector_kind_decl,
            $.connector_label_decl,
            $.connector_description_decl,
            $.connector_provider_def,
            $.connector_sensor_def,
            $.connector_actuator_def
        ),

        connector_kind_decl: $ => seq(
            'kind',
            field('kind', $.connector_value),
            optional(';')
        ),

        connector_label_decl: $ => seq(
            'label',
            field('label', $.string_literal),
            optional(';')
        ),

        connector_description_decl: $ => seq(
            'description',
            field('description', $.string_literal),
            optional(';')
        ),

        connector_provider_def: $ => seq(
            'provider',
            field('provider_key', $.ident),
            field('body', $.connector_provider_block)
        ),

        connector_provider_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal,
                $.connector_provider_item
            )),
            '}'
        ),

        connector_provider_item: $ => choice(
            $.connector_kind_decl,
            $.connector_ref_decl,
            $.connector_label_decl,
            $.connector_description_decl
        ),

        connector_sensor_def: $ => seq(
            'sensor',
            field('sensor_key', $.ident),
            field('body', $.connector_sensor_block)
        ),

        connector_sensor_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal,
                $.connector_sensor_item
            )),
            '}'
        ),

        connector_sensor_item: $ => choice(
            $.connector_kind_decl,
            $.connector_source_ref_decl,
            $.connector_payload_schema_ref_decl,
            $.connector_label_decl,
            $.connector_description_decl,
            $.connector_invocation_def
        ),

        connector_actuator_def: $ => seq(
            'actuator',
            field('actuator_key', $.ident),
            field('body', $.connector_actuator_block)
        ),

        connector_actuator_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal,
                $.connector_actuator_item
            )),
            '}'
        ),

        connector_actuator_item: $ => choice(
            $.connector_kind_decl,
            $.connector_target_ref_decl,
            $.connector_payload_schema_ref_decl,
            $.connector_label_decl,
            $.connector_description_decl,
            $.connector_invocation_def
        ),

        connector_ref_decl: $ => seq(
            'ref',
            field('ref', $.connector_value),
            optional(';')
        ),

        connector_source_ref_decl: $ => seq(
            'source_ref',
            field('source_ref', $.connector_value),
            optional(';')
        ),

        connector_target_ref_decl: $ => seq(
            'target_ref',
            field('target_ref', $.connector_value),
            optional(';')
        ),

        connector_payload_schema_ref_decl: $ => seq(
            'payload_schema_ref',
            field('payload_schema_ref', $.connector_value),
            optional(';')
        ),

        connector_invocation_def: $ => seq(
            'invocation',
            field('action_key', $.ident),
            field('action_kind', $.connector_invocation_action_kind),
            field('target_ref', $.qualified_name),
            optional(field('body', $.connector_invocation_block)),
            optional(';')
        ),

        connector_invocation_action_kind: $ => choice('sdk', 'api', 'service'),

        connector_invocation_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.experience_view_action_label_stmt,
                $.experience_view_action_receipt_stmt,
                $.experience_view_action_confirmation_stmt,
                $.experience_view_action_optimistic_stmt
            )),
            '}'
        ),

        connector_value: $ => choice(
            $.qualified_name,
            $.string_literal
        ),

        experience_node_def: $ => seq(
            'node',
            field('node_ref', $.ann_path),
            '{',
            repeat(choice(
                $.comment,
                $.experience_node_identity_def
            )),
            '}'
        ),

        experience_node_identity_def: $ => seq(
            'id',
            field('key_name', $.ident),
            optional(field('body', $.block)),
            optional(';')
        ),

        experience_surface_def: $ => seq(
            'surface',
            field('surface_key', $.qualified_name),
            '{',
            repeat(choice(
                $.comment,
                $.experience_surface_item
            )),
            '}'
        ),

        experience_surface_item: $ => choice(
            $.experience_surface_section_decl,
            $.experience_surface_view_decl,
            $.experience_surface_graph_anchor_decl,
            $.experience_surface_node_anchor_decl,
            $.experience_surface_source_decl
        ),

        experience_surface_section_decl: $ => seq(
            'section',
            field('section_key', $.qualified_name),
            optional(';')
        ),

        experience_surface_view_decl: $ => seq(
            'view',
            field('view_ref', $.qualified_name),
            optional(';')
        ),

        experience_surface_graph_anchor_decl: $ => seq(
            'graph',
            field('graph_identity', $.qualified_name),
            optional(';')
        ),

        experience_surface_node_anchor_decl: $ => seq(
            'node',
            field('node_identity', $.qualified_name),
            optional(';')
        ),

        experience_surface_source_decl: $ => seq(
            'source',
            field('source_surface', $.qualified_name),
            optional(';')
        ),

        // ---- Experience Profile Contracts ---------------------------------
        // Canonical authored environment experience profile truth.
        // This package-owned surface declares profile/process/thread/projection
        // resolution for environment deployment and workspace bundling.
        experience_profile_scope_def: $ => seq(
            'experience',
            field('name', $.ident),
            '{',
            repeat(choice(
                $.comment,
                $.experience_profile_scope_item
            )),
            '}'
        ),

        experience_profile_scope_item: $ => choice(
            $.experience_profile_def
        ),

        experience_profile_def: $ => seq(
            'profile',
            field('key', $.view_path),
            field('body', $.experience_profile_block)
        ),

        experience_profile_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.experience_profile_item
            )),
            '}'
        ),

        experience_profile_item: $ => choice(
            $.experience_profile_title_stmt,
            $.experience_profile_description_stmt,
            $.experience_profile_narrative_stmt,
            $.experience_profile_process_def,
            $.experience_profile_transition_def
        ),

        experience_profile_title_stmt: $ => seq(
            'title',
            field('title', $.string_literal),
            optional(';')
        ),

        experience_profile_description_stmt: $ => seq(
            'description',
            field('description', $.string_literal),
            optional(';')
        ),

        experience_profile_narrative_stmt: $ => seq(
            'narrative',
            field('narrative', $.string_literal),
            optional(';')
        ),

        experience_profile_transition_def: $ => seq(
            'transition',
            field('key', $.view_path),
            field('body', $.experience_profile_transition_block)
        ),

        experience_profile_transition_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.experience_profile_transition_item
            )),
            '}'
        ),

        experience_profile_transition_item: $ => choice(
            $.experience_profile_transition_source_stmt,
            $.experience_profile_transition_trigger_stmt,
            $.experience_profile_transition_target_stmt,
            $.experience_profile_transition_name_stmt,
            $.experience_profile_transition_rationale_stmt,
            $.experience_profile_transition_idempotency_policy_stmt
        ),

        experience_profile_transition_source_stmt: $ => seq(
            'source',
            'projection',
            field('experience', $.view_path),
            'view',
            field('view_key', $.view_path),
            optional(';')
        ),

        experience_profile_transition_trigger_stmt: $ => seq(
            'trigger',
            'event',
            field('event', $.view_path),
            optional(';')
        ),

        experience_profile_transition_target_stmt: $ => seq(
            'target',
            'projection',
            field('experience', $.view_path),
            'binding',
            field('binding_key', $.view_path),
            optional(';')
        ),

        experience_profile_transition_name_stmt: $ => seq(
            'name',
            field('name', $.string_literal),
            optional(';')
        ),

        experience_profile_transition_rationale_stmt: $ => seq(
            'rationale',
            field('rationale', $.string_literal),
            optional(';')
        ),

        experience_profile_transition_idempotency_policy_stmt: $ => seq(
            'idempotency_policy',
            field('idempotency_policy', $.string_literal),
            optional(';')
        ),

        experience_profile_process_def: $ => seq(
            'process',
            field('type', $.view_path),
            field('key', $.view_path),
            optional('default'),
            field('body', $.experience_profile_process_block)
        ),

        experience_profile_process_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.experience_profile_process_item
            )),
            '}'
        ),

        experience_profile_process_item: $ => choice(
            $.experience_profile_process_title_stmt,
            $.experience_profile_process_description_stmt,
            $.experience_profile_process_narrative_stmt,
            $.experience_profile_process_intent_stmt,
            $.experience_profile_process_shape_stmt,
            $.experience_profile_process_position_stmt,
            $.experience_profile_thread_def
        ),

        experience_profile_process_title_stmt: $ => seq(
            'title',
            field('title', $.string_literal),
            optional(';')
        ),

        experience_profile_process_description_stmt: $ => seq(
            'description',
            field('description', $.string_literal),
            optional(';')
        ),

        experience_profile_process_narrative_stmt: $ => seq(
            'narrative',
            field('narrative', $.string_literal),
            optional(';')
        ),

        experience_profile_process_intent_stmt: $ => seq(
            'intent',
            field('intent', $.view_path),
            optional(';')
        ),

        experience_profile_process_shape_stmt: $ => seq(
            'shape',
            field('shape', $.view_path),
            optional(';')
        ),

        experience_profile_process_position_stmt: $ => seq(
            'position',
            field('position', $.number_literal),
            optional(';')
        ),

        experience_profile_thread_def: $ => seq(
            'thread',
            field('key', $.view_path),
            optional('default'),
            field('body', $.experience_profile_thread_block)
        ),

        experience_profile_thread_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.experience_profile_thread_item
            )),
            '}'
        ),

        experience_profile_thread_item: $ => choice(
            $.experience_profile_thread_title_stmt,
            $.experience_profile_thread_description_stmt,
            $.experience_profile_thread_narrative_stmt,
            $.experience_profile_thread_intent_stmt,
            $.experience_profile_thread_workspace_view_stmt,
            $.experience_profile_thread_position_stmt,
            $.experience_profile_thread_state_prompt_template_stmt,
            $.experience_profile_thread_projection_def,
            $.experience_profile_thread_layout_def
        ),

        experience_profile_thread_title_stmt: $ => seq(
            'title',
            field('title', $.string_literal),
            optional(';')
        ),

        experience_profile_thread_description_stmt: $ => seq(
            'description',
            field('description', $.string_literal),
            optional(';')
        ),

        experience_profile_thread_narrative_stmt: $ => seq(
            'narrative',
            field('narrative', $.string_literal),
            optional(';')
        ),

        experience_profile_thread_intent_stmt: $ => seq(
            'intent',
            field('intent', $.view_path),
            optional(';')
        ),

        experience_profile_thread_workspace_view_stmt: $ => seq(
            'workspace_view',
            field('workspace_view', $.view_path),
            optional(';')
        ),

        experience_profile_thread_position_stmt: $ => seq(
            'position',
            field('position', $.number_literal),
            optional(';')
        ),

        experience_profile_thread_state_prompt_template_stmt: $ => seq(
            'state_prompt_template',
            field('state_prompt_template', $.string_literal),
            optional(';')
        ),

        experience_profile_thread_projection_def: $ => seq(
            'projection',
            field('experience', $.view_path),
            optional(seq(
                'view',
                field('view_key', $.view_path)
            )),
            optional('default'),
            optional(';')
        ),

        experience_profile_thread_layout_def: $ => seq(
            'layout',
            field('layout_key', $.view_path),
            optional('default'),
            optional(choice(
                ';',
                field('body', $.experience_profile_thread_layout_block)
            ))
        ),

        experience_profile_thread_layout_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.experience_profile_thread_layout_item
            )),
            '}'
        ),

        experience_profile_thread_layout_item: $ => choice(
            $.experience_profile_thread_layout_section_def
        ),

        experience_profile_thread_layout_section_def: $ => seq(
            'section',
            field('section_key', $.view_path),
            'projection',
            field('experience', $.view_path),
            'view',
            field('view_key', $.view_path),
            optional(seq(
                'binding',
                field('binding_key', $.view_path)
            )),
            optional('default'),
            optional(';')
        ),

        // ---- Experience Graph Contracts ------------------------------------
        // Graph is authored over a ProjectionExperience node identity surface.
        // v0:
        // - exactly one root (validated by compiler)
        // - explicit parent -> child edges using fixed node identities only
        graph_def: $ => seq(
            'graph',
            field('name', $.ident),
            'on',
            field('experience', $.qualified_name),
            '{',
            repeat(choice(
                $.comment,
                $.graph_item
            )),
            '}'
        ),

        graph_item: $ => choice(
            $.graph_root_stmt,
            $.graph_edge_stmt
        ),

        graph_root_stmt: $ => seq(
            'root',
            field('ref', $.graph_node_identity_ref),
            optional(';')
        ),

        graph_edge_stmt: $ => seq(
            'node',
            field('parent', $.graph_node_identity_ref),
            field('child', $.graph_node_identity_ref),
            optional(';')
        ),

        graph_node_identity_ref: $ => seq(
            field('identity', $.ident)
        ),

        // ---- Binding -------------------------------------------------------
        // Meta-owned OCG zoom/interoperability declarations.
        binding_def: $ => seq(
            'binding',
            field('source_graph', $.qualified_name),
            field('target_graph', $.qualified_name),
            '{',
            repeat(choice(
                $.comment,
                $.binding_map_def
            )),
            '}'
        ),

        binding_map_def: $ => choice(
            seq(
                'map',
                field('name', $.ident),
                field('source', $.qualified_name),
                field('target', $.qualified_name),
                field('body', $.binding_map_body)
            ),
            seq(
                'map',
                field('name', $.ident),
                field('source', $.qualified_name),
                field('target', $.qualified_name),
                optional(';')
            )
        ),

        binding_map_body: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal,
                $.binding_map_template_def
            )),
            '}'
        ),

        binding_map_template_def: $ => seq(
            'template',
            field('body', $.binding_map_template_body)
        ),

        binding_map_template_body: $ => seq(
            '{',
            field('value', $.binding_map_template_literal),
            '}'
        ),

        binding_map_template_literal: $ => choice(
            $.string_literal,
            $.triple_string_literal,
            $.dollar_string_literal
        ),

        // ---- API -----------------------------------------------------------
        // API authored files are reference-only link documents over
        // API-package DTO classes, graph-scoped projection mapping, and
        // graph-scoped capability binding.
        api_def: $ => seq(
            'api',
            field('name', $.ident),
            '{',
            repeat(choice(
                $.comment,
                $.api_item
            )),
            '}'
        ),

        api_item: $ => choice(
            $.api_capability_def,
            $.api_graph_def
        ),

        api_capability_def: $ => seq(
            'capability',
            field('capability_name', $.ident),
            field('body', $.api_capability_block)
        ),

        api_capability_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal,
                $.api_capability_item
            )),
            '}'
        ),

        api_capability_item: $ => choice(
            $.api_capability_endpoint_def
        ),

        api_capability_endpoint_def: $ => seq(
            'endpoint',
            field('endpoint_name', $.ident),
            field('request', $.qualified_name),
            choice(
                field('body', $.api_capability_endpoint_block),
                ';'
            )
        ),

        api_capability_endpoint_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal,
                $.api_capability_endpoint_item
            )),
            '}'
        ),

        api_capability_endpoint_item: $ => choice(
            $.api_capability_endpoint_response_def,
            $.api_capability_endpoint_stream_def
        ),

        api_capability_endpoint_response_def: $ => seq(
            'response',
            field('response', $.qualified_name),
            optional(';')
        ),

        api_capability_endpoint_stream_def: $ => seq(
            'stream',
            field('stream_mode', $.ident),
            field('body', $.api_capability_endpoint_stream_block)
        ),

        api_capability_endpoint_stream_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal,
                $.api_capability_endpoint_stream_item
            )),
            '}'
        ),

        api_capability_endpoint_stream_item: $ => choice(
            $.api_capability_endpoint_stream_event_def
        ),

        api_capability_endpoint_stream_event_def: $ => seq(
            'event',
            field('kind', $.ident),
            field('class', $.qualified_name),
            optional(';')
        ),

        api_graph_def: $ => seq(
            'graph',
            field('graph', $.qualified_name),
            '{',
            repeat(choice(
                $.comment,
                $.api_graph_item
            )),
            '}'
        ),

        api_graph_item: $ => choice(
            $.api_graph_projection_def,
            $.api_graph_capability_def
        ),

        api_graph_projection_def: $ => seq(
            'projection',
            field('projection', $.qualified_name),
            optional(choice(
                ';',
                seq(
                    '{',
                    repeat(choice(
                        $.comment,
                        $.api_graph_projection_item
                    )),
                    '}'
                )
            ))
        ),

        api_graph_projection_item: $ => choice(
            $.api_graph_projection_binding_def
        ),

        api_graph_projection_binding_def: $ => seq(
            'binding',
            field('binding', $.qualified_name),
            field('anchor', $.api_projection_anchor),
            optional(';')
        ),

        api_graph_capability_def: $ => seq(
            'capability',
            field('capability_name', $.ident),
            '{',
            repeat(choice(
                $.comment,
                $.api_graph_capability_item
            )),
            '}'
        ),

        api_graph_capability_item: $ => choice(
            $.api_graph_capability_function_def
        ),

        api_graph_capability_function_def: $ => seq(
            'function',
            field('name', $.ident),
            field('target', $.qualified_name),
            optional(';')
        ),

        api_projection_anchor: $ => seq(
            field('parent', $.ident),
            '::',
            field('relationship', $.ident)
        ),

        // ---- Service -------------------------------------------------------
        // Service authored files declare committed config truth over existing
        // API contracts. Runtime receipts and downstream fulfillment rails
        // remain separate adoption phases.
        service_def: $ => seq(
            'service',
            field('name', $.ident),
            '{',
            repeat(choice(
                $.comment,
                $.service_item
            )),
            '}'
        ),

        service_item: $ => choice(
            $.service_api_decl,
            $.service_experience_decl,
            $.service_code_package_config_decl,
            $.service_operation_def,
            $.service_contract_config_def
        ),

        service_api_decl: $ => seq(
            'api',
            field('api', $.qualified_name),
            optional(choice(
                ';',
                field('body', $.service_api_block)
            ))
        ),

        service_experience_decl: $ => seq(
            'experience',
            field('experience', $.qualified_name),
            optional(';')
        ),

        service_code_package_config_decl: $ => seq(
            'package',
            field('slot', $.ident),
            field('body', $.service_code_package_config_block)
        ),

        service_code_package_config_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.service_code_package_config_item
            )),
            '}'
        ),

        service_code_package_config_item: $ => choice(
            $.service_code_package_config_manifest_decl,
            $.service_code_package_config_surface_decl,
            $.service_code_package_config_cardinality_decl,
            $.service_code_package_config_required_decl
        ),

        service_code_package_config_manifest_decl: $ => seq(
            'manifest',
            field('manifest_kind', $.ident),
            optional(';')
        ),

        service_code_package_config_surface_decl: $ => seq(
            'surface',
            field('surface', $.ident),
            optional(';')
        ),

        service_code_package_config_cardinality_decl: $ => seq(
            'cardinality',
            field('cardinality', $.ident),
            optional(';')
        ),

        service_code_package_config_required_decl: $ => seq(
            'required',
            field('required', $.boolean_literal),
            optional(';')
        ),

        service_api_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.service_api_item
            )),
            '}'
        ),

        service_api_item: $ => choice(
            $.service_api_projection_decl
        ),

        service_api_projection_decl: $ => seq(
            'projection',
            field('projection', $.qualified_name),
            optional(';')
        ),

        service_operation_def: $ => seq(
            'operation',
            field('operation_name', $.ident),
            field('body', $.service_operation_block)
        ),

        service_operation_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.service_operation_item
            )),
            '}'
        ),

        service_operation_item: $ => choice(
            $.service_operation_endpoint_def,
            $.service_operation_view_def,
            $.service_operation_role_requirement_def,
            $.service_operation_admission_policy_decl,
            $.service_operation_receipt_policy_decl,
            $.service_operation_settlement_decl,
            $.service_operation_price_def
        ),

        service_operation_endpoint_def: $ => seq(
            'endpoint',
            field('endpoint', $.qualified_name),
            optional(';')
        ),

        service_operation_view_def: $ => seq(
            'view',
            field('view', $.qualified_name),
            optional(choice(
                ';',
                field('body', $.service_operation_view_block)
            ))
        ),

        service_operation_view_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.service_operation_view_item
            )),
            '}'
        ),

        service_operation_view_item: $ => choice(
            $.service_operation_view_provider_decl
        ),

        service_operation_view_provider_decl: $ => seq(
            'provider',
            field('provider_kind', choice($.ident, $.string_literal)),
            optional(';')
        ),

        service_operation_role_requirement_def: $ => seq(
            'role',
            field('role', $.qualified_name),
            optional(choice(
                ';',
                field('body', $.service_role_gate_block)
            ))
        ),

        service_role_gate_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.service_role_gate_item
            )),
            '}'
        ),

        service_role_gate_item: $ => choice(
            $.service_role_access_decl,
            $.service_role_scope_decl,
            $.service_role_class_instance_identity_required_decl,
            $.service_role_assignment_binding_required_decl
        ),

        service_role_access_decl: $ => seq(
            'access',
            field('access_scope', $.ident),
            optional(';')
        ),

        service_role_scope_decl: $ => seq(
            'scope',
            field('scope_kind', $.ident),
            optional(field('scope_ref', choice($.qualified_name, $.string_literal))),
            optional(';')
        ),

        service_role_class_instance_identity_required_decl: $ => seq(
            'class_instance_identity_required',
            field('class_instance_identity_required', $.boolean_literal),
            optional(';')
        ),

        service_role_assignment_binding_required_decl: $ => seq(
            'role_assignment_binding_required',
            field('role_assignment_binding_required', $.boolean_literal),
            optional(';')
        ),

        service_operation_admission_policy_decl: $ => seq(
            'admission',
            field('admission_mode', $.ident),
            optional(';')
        ),

        service_operation_receipt_policy_decl: $ => seq(
            'receipt',
            field('receipt_policy', $.ident),
            optional(';')
        ),

        service_operation_settlement_decl: $ => seq(
            'settlement',
            field('settlement_policy', $.ident),
            optional(';')
        ),

        service_operation_price_def: $ => seq(
            'price',
            field('body', $.service_operation_price_block)
        ),

        service_operation_price_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.service_operation_price_item
            )),
            '}'
        ),

        service_operation_price_item: $ => choice(
            $.service_operation_price_coin_decl,
            $.service_operation_price_type_decl,
            $.service_operation_price_fixed_amount_decl,
            $.service_operation_price_markup_percentage_decl,
            $.service_operation_price_effective_from_decl,
            $.service_operation_price_effective_until_decl,
            $.service_operation_price_policy_def
        ),

        service_operation_price_coin_decl: $ => seq(
            'coin',
            field('coin_symbol', $.ident),
            optional(';')
        ),

        service_operation_price_type_decl: $ => seq(
            'type',
            field('price_type', $.ident),
            optional(';')
        ),

        service_operation_price_fixed_amount_decl: $ => seq(
            'fixed_amount',
            field('fixed_amount', $.number_literal),
            optional(';')
        ),

        service_operation_price_markup_percentage_decl: $ => seq(
            'markup_percentage',
            field('markup_percentage', $.number_literal),
            optional(';')
        ),

        service_operation_price_effective_from_decl: $ => seq(
            'effective_from',
            field('effective_from', $.string_literal),
            optional(';')
        ),

        service_operation_price_effective_until_decl: $ => seq(
            'effective_until',
            field('effective_until', $.string_literal),
            optional(';')
        ),

        service_operation_price_policy_def: $ => seq(
            'policy',
            field('body', $.service_operation_price_policy_block)
        ),

        service_operation_price_policy_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.service_operation_price_policy_item
            )),
            '}'
        ),

        service_operation_price_policy_item: $ => choice(
            $.service_operation_price_policy_fail_closed_decl
        ),

        service_operation_price_policy_fail_closed_decl: $ => seq(
            'fail_closed',
            field('fail_closed', $.boolean_literal),
            optional(';')
        ),

        service_contract_config_def: $ => seq(
            'contract',
            field('name', $.ident),
            field('body', $.service_contract_config_block)
        ),

        service_contract_config_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.service_contract_config_item
            )),
            '}'
        ),

        service_contract_config_item: $ => choice(
            $.service_contract_kind_decl,
            $.service_contract_projection_experience_decl,
            $.service_contract_operation_grant_def,
            $.service_contract_actor_role_grant_def
        ),

        service_contract_kind_decl: $ => seq(
            'kind',
            field('contract_kind', $.ident),
            optional(';')
        ),

        service_contract_projection_experience_decl: $ => seq(
            'projection_experience',
            field('projection_experience', $.qualified_name),
            optional(';')
        ),

        service_contract_operation_grant_def: $ => seq(
            'grant',
            'operation',
            field('operation', $.qualified_name),
            optional(choice(
                ';',
                field('body', $.service_contract_operation_grant_block)
            ))
        ),

        service_contract_operation_grant_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.service_contract_operation_grant_item
            )),
            '}'
        ),

        service_contract_operation_grant_item: $ => choice(
            $.service_role_access_decl
        ),

        service_contract_actor_role_grant_def: $ => seq(
            'grant',
            'actor_role',
            field('role', $.qualified_name),
            optional(choice(
                ';',
                field('body', $.service_role_gate_block)
            ))
        ),

        // ---- Skill ---------------------------------------------------------
        // Skill authored files declare reusable orchestration/config truth over
        // committed API capability endpoints. Runtime execution remains a later
        // service/workspace concern.
        skill_def: $ => seq(
            'skill',
            field('name', $.ident),
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal,
                $.skill_item
            )),
            '}'
        ),

        skill_item: $ => choice(
            $.skill_api_decl,
            $.skill_endpoint_def,
            $.skill_step_def
        ),

        skill_api_decl: $ => seq(
            'api',
            field('api', $.qualified_name),
            optional(';')
        ),

        skill_endpoint_def: $ => seq(
            'endpoint',
            field('endpoint_name', $.ident),
            field('endpoint', $.qualified_name),
            choice(
                field('body', $.skill_endpoint_block),
                optional(';')
            )
        ),

        skill_endpoint_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal
            )),
            '}'
        ),

        skill_step_def: $ => seq(
            'step',
            field('position', $.number_literal),
            field('endpoint_name', $.ident),
            field('body', $.skill_step_block)
        ),

        skill_step_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal
            )),
            '}'
        ),

        // ---- SDK -----------------------------------------------------------
        // SDK authored files declare local operation orchestration over
        // committed API capability endpoints. Generated Python/Dart SDKs and
        // handwritten adapters consume this same operation -> endpoint contract.
        sdk_def: $ => seq(
            'sdk',
            field('name', $.ident),
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal,
                $.sdk_item
            )),
            '}'
        ),

        sdk_item: $ => choice(
            $.sdk_api_decl,
            $.sdk_surface_def,
            $.sdk_operation_def
        ),

        sdk_api_decl: $ => seq(
            'api',
            field('api', $.qualified_name),
            optional(';')
        ),

        sdk_surface_def: $ => seq(
            'surface',
            field('surface_name', $.ident),
            field('body', $.sdk_surface_block)
        ),

        sdk_surface_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal,
                $.sdk_surface_item
            )),
            '}'
        ),

        sdk_surface_item: $ => choice(
            $.sdk_surface_method_def
        ),

        sdk_surface_method_def: $ => seq(
            'method',
            field('method_name', $.ident),
            field('body', $.sdk_surface_method_block)
        ),

        sdk_surface_method_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal,
                $.sdk_surface_method_item
            )),
            '}'
        ),

        sdk_surface_method_item: $ => choice(
            $.sdk_surface_method_operation_decl,
            $.sdk_surface_method_family_decl,
            $.sdk_surface_method_effect_decl,
            $.sdk_surface_method_mutation_scope_decl,
            $.sdk_surface_method_confirmation_policy_decl,
            $.sdk_surface_method_execution_mode_decl,
            $.sdk_surface_method_runtime_binding_kind_decl
        ),

        sdk_surface_method_operation_decl: $ => seq(
            'operation',
            field('operation', $.qualified_name),
            optional(';')
        ),

        sdk_surface_method_family_decl: $ => seq(
            'method_family',
            field('method_family', $.ident),
            optional(';')
        ),

        sdk_surface_method_effect_decl: $ => seq(
            'effect',
            field('effect', $.ident),
            optional(';')
        ),

        sdk_surface_method_mutation_scope_decl: $ => seq(
            'mutation_scope',
            field('mutation_scope', $.ident),
            optional(';')
        ),

        sdk_surface_method_confirmation_policy_decl: $ => seq(
            'confirmation_policy',
            field('confirmation_policy', $.ident),
            optional(';')
        ),

        sdk_surface_method_execution_mode_decl: $ => seq(
            'execution_mode',
            field('execution_mode', $.ident),
            optional(';')
        ),

        sdk_surface_method_runtime_binding_kind_decl: $ => seq(
            'runtime_binding_kind',
            field('runtime_binding_kind', $.ident),
            optional(';')
        ),

        sdk_operation_def: $ => seq(
            'operation',
            field('operation_name', $.ident),
            field('body', $.sdk_operation_block)
        ),

        sdk_operation_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal,
                $.sdk_operation_item
            )),
            '}'
        ),

        sdk_operation_item: $ => choice(
            $.sdk_operation_endpoint_def,
            $.sdk_operation_dependency_def
        ),

        sdk_operation_endpoint_def: $ => seq(
            'endpoint',
            field('endpoint', $.qualified_name),
            optional(';')
        ),

        sdk_operation_dependency_def: $ => seq(
            'operation',
            field('operation', $.qualified_name),
            optional(';')
        ),

        // ---- Attention Topology -------------------------------------------
        attention_layout_def: $ => seq(
            'layout',
            field('layout_name', $.ident),
            optional(field('default_marker', $.default_marker)),
            field('body', $.attention_layout_block)
        ),

        attention_layout_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.attention_layout_item
            )),
            '}'
        ),

        attention_layout_item: $ => choice(
            $.attention_section_def
        ),

        attention_section_def: $ => seq(
            'section',
            field('section_name', $.ident),
            optional(field('body', $.attention_section_block)),
            optional(';')
        ),

        attention_section_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.attention_section_item
            )),
            '}'
        ),

        attention_section_item: $ => choice(
            $.attention_section_title_stmt,
            $.attention_section_description_stmt,
            $.attention_section_order_stmt,
            $.attention_section_flex_stmt,
            $.attention_section_visible_stmt
        ),

        attention_section_title_stmt: $ => seq(
            'title',
            field('title', $.string_literal),
            optional(';')
        ),

        attention_section_description_stmt: $ => seq(
            'description',
            field('description', $.string_literal),
            optional(';')
        ),

        attention_section_order_stmt: $ => seq(
            'order',
            field('order', $.number_literal),
            optional(';')
        ),

        attention_section_flex_stmt: $ => seq(
            'flex',
            field('flex', $.number_literal),
            optional(';')
        ),

        attention_section_visible_stmt: $ => seq(
            choice('visible', 'is_visible'),
            field('is_visible', $.boolean_literal),
            optional(';')
        ),

        // ---- Interface ----------------------------------------------------
        pane_def: $ => seq(
            'pane',
            field('name', $.ident),
            field('body', $.pane_block)
        ),

        pane_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal,
                $.pane_item
            )),
            '}'
        ),

        pane_item: $ => choice(
            $.pane_kind_decl,
            $.pane_view_def,
            $.pane_endpoint_def,
            $.pane_operation_def,
            $.pane_render_def
        ),

        pane_kind_decl: $ => seq(
            'kind',
            field('kind', $.ident),
            optional(';')
        ),

        pane_view_def: $ => seq(
            'view',
            field('view', $.qualified_name),
            optional(field('default_marker', $.default_marker)),
            field('body', $.pane_view_block)
        ),

        pane_view_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.triple_string_literal,
                $.string_literal
            )),
            '}'
        ),

        pane_endpoint_def: $ => seq(
            'endpoint',
            field('endpoint', $.qualified_name),
            optional(';')
        ),

        pane_operation_def: $ => seq(
            'operation',
            field('operation', $.qualified_name),
            optional(';')
        ),

        pane_render_def: $ => seq(
            'render',
            field('name', $.ident),
            field('body', $.pane_render_block)
        ),

        pane_render_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.pane_render_item
            )),
            '}'
        ),

        pane_render_item: $ => choice(
            $.pane_render_view_decl,
            $.pane_render_version_decl,
            $.pane_render_root_decl,
            $.pane_render_require_decl,
            $.pane_render_node_def
        ),

        pane_render_view_decl: $ => seq(
            'view',
            field('view', $.qualified_name),
            optional(';')
        ),

        pane_render_version_decl: $ => seq(
            'version',
            field('version', $.string_literal),
            optional(';')
        ),

        pane_render_root_decl: $ => seq(
            'root',
            field('node', $.qualified_name),
            optional(';')
        ),

        pane_render_require_decl: $ => seq(
            'require',
            field('capability_kind', $.ident),
            field('capability_key', $.qualified_name),
            optional(';')
        ),

        pane_render_node_def: $ => seq(
            'node',
            field('node_key', $.qualified_name),
            field('node_kind', $.ident),
            optional(field('implicit_semantic_role', $.pane_render_compact_semantic_role)),
            repeat($.pane_render_node_option),
            optional(field('body', $.pane_render_node_block)),
            optional(';')
        ),

        pane_render_compact_semantic_role: _ => choice(
            'pane',
            'section',
            'heading',
            'paragraph',
            'metadata',
            'metric',
            'status',
            'input',
            'action',
            'receipt'
        ),

        pane_render_node_option: $ => choice(
            seq('parent', field('parent_node_key', $.qualified_name)),
            seq('order', field('order', $.number_literal)),
            seq('role', field('semantic_role', $.ident)),
            seq('slot', field('slot', $.ident))
        ),

        pane_render_node_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.pane_render_node_item
            )),
            '}'
        ),

        pane_render_node_item: $ => choice(
            $.pane_render_text_stmt,
            $.pane_render_label_stmt,
            $.pane_render_placeholder_stmt,
            $.pane_render_component_stmt,
            $.pane_render_fallback_stmt,
            $.pane_render_state_binding_stmt,
            $.pane_render_action_binding_def,
            $.pane_render_style_stmt
        ),

        pane_render_text_stmt: $ => seq(
            'text',
            field('value', $.string_literal),
            optional(';')
        ),

        pane_render_label_stmt: $ => seq(
            'label',
            field('value', $.string_literal),
            optional(';')
        ),

        pane_render_placeholder_stmt: $ => seq(
            'placeholder',
            field('value', $.string_literal),
            optional(';')
        ),

        pane_render_component_stmt: $ => seq(
            'component',
            field('component_ref', $.qualified_name),
            optional(';')
        ),

        pane_render_fallback_stmt: $ => choice(
            seq(
                'fallback_node_kind',
                field('fallback_node_kind', $.ident),
                optional(';')
            ),
            seq(
                'fallback_text',
                field('fallback_text', $.string_literal),
                optional(';')
            )
        ),

        pane_render_state_binding_stmt: $ => seq(
            'bind',
            field('target_property', $.ident),
            choice(
                seq(
                    'from',
                    field('state_path', $.qualified_name),
                    'attr',
                    field('state_attribute', $.ident),
                    optional(seq(
                        'transform',
                        field('transform', $.ident)
                    ))
                ),
                seq(
                    field('state_path', $.qualified_name),
                    optional(seq(
                        '::',
                        field('state_attribute', $.ident)
                    )),
                    optional(field('transform', $.ident))
                )
            ),
            optional(seq(
                'port',
                field('component_input_port_key', $.ident)
            )),
            optional(seq(
                'fallback',
                field('fallback', $.string_literal)
            )),
            optional(';')
        ),

        pane_render_action_binding_def: $ => seq(
            'action',
            field('event', $.ident),
            field('action_kind', $.pane_render_action_kind),
            field('action', $.qualified_name),
            optional(field('body', $.pane_render_action_block)),
            optional(';')
        ),

        pane_render_action_kind: $ => choice('sdk', 'api', 'view'),

        pane_render_action_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.pane_render_action_item
            )),
            '}'
        ),

        pane_render_action_item: $ => choice(
            $.pane_render_input_binding_stmt,
            $.pane_render_receipt_stmt
        ),

        pane_render_input_binding_stmt: $ => seq(
            'input',
            field('payload_path', $.qualified_name),
            'from',
            field('source', $.qualified_name),
            optional(';')
        ),

        pane_render_receipt_stmt: $ => seq(
            'receipt',
            field('policy', $.ident),
            optional(';')
        ),

        pane_render_style_stmt: $ => seq(
            'style',
            field('token', $.ident),
            optional(seq(
                '=',
                field('value', $.string_literal)
            )),
            optional(';')
        ),

        interface_def: $ => seq(
            'interface',
            field('name', $.ident),
            field('body', $.interface_block)
        ),

        interface_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.interface_item
            )),
            '}'
        ),

        interface_item: $ => choice(
            $.interface_api_decl,
            $.interface_window_def,
            $.interface_pane_def
        ),

        interface_api_decl: $ => seq(
            'api',
            field('api', $.qualified_name),
            optional(';')
        ),

        interface_window_def: $ => seq(
            'window',
            field('window_name', $.ident),
            field('body', $.interface_window_block)
        ),

        interface_window_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.interface_layout_def
            )),
            '}'
        ),

        interface_layout_def: $ => seq(
            'layout',
            field('layout_name', $.ident),
            optional(field('default_marker', $.default_marker)),
            field('body', $.interface_layout_block)
        ),

        interface_layout_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.interface_layout_item
            )),
            '}'
        ),

        interface_layout_item: $ => choice(
            $.interface_layout_section_def
        ),

        interface_layout_section_def: $ => seq(
            'section',
            field('section_name', $.ident),
            optional(';')
        ),

        interface_pane_def: $ => seq(
            'pane',
            field('pane_name', $.ident),
            field('body', $.interface_pane_block)
        ),

        interface_pane_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.interface_pane_item
            )),
            '}'
        ),

        interface_pane_item: $ => choice(
            $.interface_pane_mount_def,
            $.interface_pane_narrative_def
        ),

        interface_pane_mount_def: $ => seq(
            'mount',
            field('view', $.qualified_name),
            field('target', $.qualified_name),
            optional(field('default_marker', $.default_marker)),
            optional(';')
        ),

        interface_pane_narrative_def: $ => seq(
            'narrative',
            field('narrative', $.qualified_name),
            optional(';')
        ),

        // ---- Node ---------------------------------------------------------
        node_def: $ => seq(
            'node',
            field('name', $.ident),
            field('body', $.node_block)
        ),

        node_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.node_item
            )),
            '}'
        ),

        node_item: $ => choice(
            $.node_include_decl,
            $.node_environment_decl,
            $.node_ontology_decl,
            $.node_service_decl,
            $.node_interface_decl
        ),

        node_include_decl: $ => seq(
            'include',
            field('target', $.view_path),
            optional(';')
        ),

        node_environment_decl: $ => seq(
            'environment',
            field('target', $.view_path),
            field('body', $.node_environment_block)
        ),

        node_environment_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.node_environment_item
            )),
            '}'
        ),

        node_environment_item: $ => choice(
            $.node_environment_profile_decl
        ),

        node_environment_profile_decl: $ => seq(
            'profile',
            field('profile', $.view_path),
            'package',
            field('package', $.view_path)
        ),

        node_service_decl: $ => seq(
            'service',
            field('target', $.qualified_name),
            choice(
                field('body', $.node_service_block),
                optional(';')
            )
        ),

        node_service_block: $ => seq(
            '{',
            repeat(choice(
                $.comment,
                $.node_service_item
            )),
            '}'
        ),

        node_service_item: $ => choice(
            $.node_service_code_package_decl
        ),

        node_service_code_package_decl: $ => seq(
            'package',
            field('slot', $.ident),
            field('package', $.view_path),
            optional(';')
        ),

        node_ontology_decl: $ => seq(
            'ontology',
            field('target', $.view_path),
            optional(';')
        ),

        node_interface_decl: $ => seq(
            'interface',
            field('target', $.qualified_name),
            optional(';')
        ),

        // ----  Annotations  --------------------------------------------------
        ann_def: $ => seq(
            'ann',
            field('path', $.ann_path),
            field('verb', $.ident),
            repeat(field('arg', $.ann_arg)),
            optional(';')
        ),

        // Member selection path after '::' (allows dotted segments like "fn.create.outputs")
        member_path: $ => seq($.ident, repeat(seq('.', $.ident))),
        default_marker: _ => 'default',
        view_segment: _ => /[A-Za-z_][A-Za-z0-9_-]*/,
        view_path: $ => seq($.view_segment, repeat(seq('.', $.view_segment))),

        ann_path: $ => seq(
            field('class', $.qualified_name),
            optional(seq('::', field('member', $.member_path)))
        ),

        ann_arg: $ => choice(
            $.ident,
            $.literal
        ),
    }
});

// Helper function for comma-separated lists
function commaSep1(rule) {
    return seq(rule, repeat(seq(',', rule)));
}
