#include "tree_sitter/parser.h"

#include <stdbool.h>
#include <wctype.h>

enum TokenType {
  IDENTITY_KEY_MARKER,
};

void *tree_sitter_aware_external_scanner_create(void) { return NULL; }
void tree_sitter_aware_external_scanner_destroy(void *payload) {}
void tree_sitter_aware_external_scanner_reset(void *payload) {}
unsigned tree_sitter_aware_external_scanner_serialize(void *payload, char *buffer) { return 0; }
void tree_sitter_aware_external_scanner_deserialize(void *payload, const char *buffer, unsigned length) {}

static inline void advance(TSLexer *lexer) { lexer->advance(lexer, false); }
static inline void skip(TSLexer *lexer) { lexer->advance(lexer, true); }

static bool is_ident_char(int32_t ch) {
  return ch == '_' || iswalnum(ch);
}

static bool scan_identity_key_marker(TSLexer *lexer) {
  // Skip horizontal spacing before token.
  while (lexer->lookahead == ' ' || lexer->lookahead == '\t' || lexer->lookahead == '\r') {
    skip(lexer);
  }

  if (lexer->lookahead != 'k') {
    return false;
  }
  advance(lexer);
  if (lexer->lookahead != 'e') {
    return false;
  }
  advance(lexer);
  if (lexer->lookahead != 'y') {
    return false;
  }
  advance(lexer);

  // Require a word boundary after "key".
  if (is_ident_char(lexer->lookahead)) {
    return false;
  }

  // Token text is exactly "key" (exclude trailing spaces/comments).
  lexer->mark_end(lexer);

  // Terminal contexts for an identity marker:
  // - end-of-line / EOF
  // - explicit ';'
  // - end of class body '}'
  // - inline default assignment '=' (e.g. `field Type key = "x"`)
  // - start of trailing line comment '//'
  if (lexer->lookahead == '\n' ||
      lexer->lookahead == ';' ||
      lexer->lookahead == '=' ||
      lexer->lookahead == '}' ||
      lexer->lookahead == '\0') {
    return true;
  }
  if (lexer->lookahead == '/') {
    advance(lexer);
    return lexer->lookahead == '/';
  }

  // Allow horizontal whitespace before terminal/comment.
  while (lexer->lookahead == ' ' || lexer->lookahead == '\t' || lexer->lookahead == '\r') {
    skip(lexer);
  }

  if (lexer->lookahead == '\n' ||
      lexer->lookahead == ';' ||
      lexer->lookahead == '=' ||
      lexer->lookahead == '}' ||
      lexer->lookahead == '\0') {
    return true;
  }
  if (lexer->lookahead == '/') {
    advance(lexer);
    return lexer->lookahead == '/';
  }

  return false;
}

bool tree_sitter_aware_external_scanner_scan(void *payload, TSLexer *lexer, const bool *valid_symbols) {
  if (valid_symbols[IDENTITY_KEY_MARKER]) {
    return scan_identity_key_marker(lexer);
  }
  return false;
}
