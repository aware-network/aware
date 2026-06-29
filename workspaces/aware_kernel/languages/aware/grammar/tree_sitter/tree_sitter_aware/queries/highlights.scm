; keywords
"type"             @keyword
"edge"             @keyword
"fn"               @keyword
"program"          @keyword
"projection"       @keyword
"api"              @keyword
"interface"        @keyword
"environment"      @keyword
"node"             @keyword
"service"          @keyword
"skill"            @keyword
"operation"        @keyword
"endpoint"         @keyword
"surface"          @keyword
"method"           @keyword
"method_family"    @keyword
"effect"           @keyword
"mutation_scope"   @keyword
"confirmation_policy" @keyword
"execution_mode"   @keyword
"runtime_binding_kind" @keyword
"step"             @keyword
"contract"         @keyword
"layout"           @keyword
"layouts"          @keyword
"port"             @keyword
"bind"             @keyword
"branch"           @keyword
"section"          @keyword
"slot"             @keyword
"id"               @keyword
"namespace"        @keyword
"template"         @keyword
"input"            @keyword
"expect"           @keyword
"intent"           @keyword
"from"             @keyword
"default"          @keyword
"required"         @keyword
"optional"         @keyword
"on"               @keyword
"let"              @keyword
"call"             @keyword
"unique"           @keyword

; punctuation
"{" "}" "[" "]" ";" "@" "->" @punctuation.delimiter

; identifiers
(ident)            @variable
(field_def
  name: (ident)    @property)

; primitive-looking types in upper-case → builtin
(type_ref
  base: (ident) @type.builtin
  (#match? @type.builtin "^[A-Z][A-Za-z0-9_]*$"))
