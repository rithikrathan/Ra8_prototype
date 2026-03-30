# Assembler Parser Implementation - Feedback

## Pipeline Overview

```
.asm file → Flex (lexer.l) → Bison (parser.y) → AST → assembler binary
```

Two tools generate C code that gets compiled together:
- Flex generates `lex.yy.c` - the tokenizer/lexer
- Bison generates `parser.tab.c` and `parser.tab.h` - the parser

Final compilation: `gcc assembler.c lex.yy.c parser.tab.c ast.c -o assembler`

---

## Problem 1: Lexer/Parser Communication

**Problem:** When Flex returns a token, it doesn't carry semantic data. Tokens like `INST "LDI"` or `REG "B"` need to pass their text value to the parser so the AST node can store the opcode or register name.

**Solution:** Used `yylval` - a union declared in `parser.tab.h` that Bison generates. The union is defined in the parser:

```c
%union {
    int num;       // for NUM, BIN, HEX tokens
    char *str;     // for INST, REG, LABELDEF, etc.
    astNode *node; // for non-terminal types
}
```

Flex rules set `yylval.str` or `yylval.num` before returning the token. The parser receives this through `$1` in grammar actions.

---

## Problem 2: Token Redefinition

**Problem:** Both `lexer.l` and `assembler.c` had identical `#define` statements for token IDs (ERROR, INST, REG, etc.). This creates conflicts when bison generates `parser.tab.h` which redefines these tokens.

**Solution:** Removed all token defines from `lexer.l` and `assembler.c`. Now they only include `parser.tab.h` which has the canonical token definitions from Bison. The lexer includes `parser.tab.h` in its header section.

---

## Problem 3: Function Name Mismatch

**Problem:** `ast.h` declared `addChild()` but `ast.c` defined `addchild()`. The parser includes `ast.h` and calls `addchild()`. Compilation fails with implicit declaration or type mismatch errors.

**Solution:** Changed `ast.h` to match - `void addchild(astNode *parent, astNode *child);`

---

## Problem 4: Grammar Conflict with Labels

**Problem:** Initial grammar had:

```
instruction:
    LABELDEF INST operands
    | LABELDEF INST
    | INST operands
    | INST
    | LABELDEF
```

Bison reported shift/reduce conflicts on `LABELDEF INST`. The parser couldn't decide whether to reduce `LABELDEF` as a standalone instruction or shift to combine it with `INST`.

**Solution:** Split into two rules:
- `inst_line` - handles `LABELDEF INST` combinations and standalone `INST`
- Removed standalone `LABELDEF` from instruction rules

Now `LABELDEF INST operands` and `LABELDEF INST` are the only ways to match a labeled instruction. Bison resolves the ambiguity correctly.

---

## Problem 5: String Value in Data Section

**Problem:** Test file had `str LDI = thissho...`. The lexer correctly tokenizes `LDI` as `IDENTIFIER` (not `INST`) because we're in data section. But the parser expected `data_value` to be NUM, BIN, HEX, or STRING_LITERAL - not IDENTIFIER.

**Solution:** Added IDENTIFIER as a valid `data_value`:

```c
data_value:
    NUM { $$ = createNode(literal); }
    | BIN { $$ = createNode(literal); }
    | HEX { $$ = createNode(literal); }
    | STRING_LITERAL { $$ = createNode(literal); }
    | IDENTIFIER { $$ = createNode(literal); free($1); }
    ;
```

---

## Problem 6: Comma Tokenization

**Problem:** Flex rule `[,\t\n ]+` was eating commas along with whitespace. The parser expected a `','` token between operands but never received it.

**Solution:** Moved comma to its own rule before the whitespace rule:

```c
"," { return ','; }
[ \t\n]+ { }
```

Order matters in Flex - first matching rule wins.

---

## Problem 7: Hex Tokenization

**Problem:** `0x50` was not being tokenized. Looking at the debug output, it simply vanished between tokens.

**Root cause:** Flex was rebuilding `lex.yy.c` but the old binary wasn't linking against the new file. Make wasn't detecting that the source (lexer.l) hadn't changed but the generated file had been deleted.

**Solution:** Explicitly ran `flex lexer.l` and `gcc` commands rather than relying on make dependencies for testing.

---

## Problem 8: Data Section State Tracking

**Problem:** The lexer needed to distinguish between instructions and identifiers in the data section. `str LDI = ...` should tokenize `LDI` as IDENTIFIER, not INST, even though `LDI` is a valid instruction name.

**Solution:** Added `inDataSection` global variable in the lexer. Set to 1 when `[__data__]` is matched, 0 when `[__inst__]` or `end` is matched. The identifier rule checks this:

```c
if (is_instruction(yytext)) {
    if (inDataSection) {
        return IDENTIFIER; // instructions are just identifiers in data section
    }
    return INST;
}
```

---

## How the Grammar Works

### Non-terminal Types

All AST-building non-terminals return `astNode*` through `%type <node>`:

```yacc
%type <node> program sections section data_section inst_section
%type <node> data_declarations data_declaration data_value
%type <node> instructions inst_line operand operands
```

### Node Building Pattern

Each rule builds a node and adds children. Example - data declaration:

```c
data_declaration:
    DATA_TYPE IDENTIFIER EQUALS data_value {
        $$ = createNode(dataDeclaration, str, $2, $4);
        free($2); // IDENTIFIER was strdup'd, now owned by node
    }
```

The `$2` is a `char*` from `yylval.str`. We pass it to `createNode()` which stores it, then free the duplicate.

### List Accumulation

Rules like `sections`, `data_declarations`, `instructions` accumulate children:

```c
sections:
    %empty { $$ = NULL; }
    | sections section {
        if ($1 == NULL) {
            $$ = $2;
        } else {
            addchild($1, $2);
            $$ = $1;
        }
    }
    ;
```

First match creates the node, subsequent matches add to it. The `if ($1 == NULL)` pattern handles the initial case.

### Operand Transfer

Instructions receive operands through an intermediate node that accumulates them, then transfers ownership:

```c
| INST operands {
    astNode *instNode = createNode(instruction, $1);
    if ($2 != NULL) {
        for (size_t i = 0; i < $2->childCount; i++) {
            addchild(instNode, $2->children[i]);
        }
        free($2->children);
        free($2);
    }
    $$ = instNode;
    free($1);
}
```

The `operands` rule builds a temporary node. We transfer its children to the instruction node and free the container. This avoids recursive `addchild` in the operand rule.

---

## AST Node Structure

```c
typedef struct astNode {
  nodeType type;                    // root, section, instruction, etc.
  struct astNode **children;        // dynamic array of child pointers
  size_t childCount;                // number of children
  size_t childCapacity;             // allocated capacity
  union {
    struct { char *opcode; astNode **operands; size_t operandCount; } instruction;
    struct { char *name; } label;
    struct { char *name; } reg;
    struct { dataType type; char *identifier; astNode *valueNode; } dataDeclaration;
    struct { char *name; } section;
  } as;
} astNode;
```

The union holds type-specific data. `children` is for structural children (section contains declarations, instruction contains operands as children).

---

## Current State

The parser successfully builds an AST tree with DOT format output for visualization.

Missing pieces:
- Semantic analysis (resolving label references)
- Code generation from AST

---

## Problem 9: Literal Node Missing Value

**Problem:** Literal nodes were being created without storing the actual value. The `createNode(literal)` call didn't pass any value, so when printing the AST, literals showed no value.

**Solution:** Added `value` field to literal struct in the union:

```c
struct {
  char *value;
  int intValue;
} literal;
```

Updated `createNode` to accept and store the value:

```c
case literal:
  node->as.literal.value = va_arg(args, char *);
  node->as.literal.intValue = va_arg(args, int);
  break;
```

---

## Problem 10: yytext Not Available in Parser

**Problem:** For NUM, BIN, HEX tokens, the parser needed both the string representation (for display) and the integer value. But `$1` in bison gives the token's semantic value (int), not the matched text (string).

**Solution:** Declared `extern char *yytext;` in the parser and used `strdup(yytext)` to get the string value:

```c
NUM { $$ = createNode(literal, strdup(yytext), $1); }
```

---

## Problem 11: Labels as Siblings vs Parents

**Problem:** Initially, labels and instructions were structured as parent-child (label containing its following instruction). The user wanted labels to be siblings of instructions, just leaf nodes like mnemonics.

**Solution:** Rewrote the grammar:

```yacc
line:
    LABELDEF { $$ = createNode(labelDef, $1); }
    | INST operands { ... }
    | INST { ... }
    ;

lines:
    %empty { $$ = NULL; }
    | lines line { if ($1 == NULL) $$ = $2; else addchild($1, $2); $$ = $1; }
    ;
```

Now labels and instructions are both children of the instruction section (or children of the accumulated list).

---

## Problem 12: Data Type String to Enum Conversion

**Problem:** DATA_TYPE token carries the type name as a string ("int8", "char", etc.) but `createNode(dataDeclaration)` expected a `dataType` enum.

**Solution:** Added `parse_data_type()` helper function:

```c
dataType parse_data_type(const char *s) {
    if (strcmp(s, "int8") == 0) return int8;
    if (strcmp(s, "int16") == 0) return int16;
    if (strcmp(s, "chr") == 0) return chr;
    if (strcmp(s, "str") == 0) return str;
    if (strcmp(s, "bool") == 0) return boolean;
    if (strcmp(s, "char") == 0) return chr;
    return str;
}
```

---

## AST Output Format

The assembler outputs DOT format for graphviz rendering:

```
{
  "nodes": [
  0 [label="root" shape=box];
  1 [label="section\ndata" shape=box];
  2 [label="dataDeclaration\nhello" shape=box];
  3 [label="literal\n23" shape=box];
  2 -> 3;
  ...
```

Visualization:
```bash
# Text tree
make visualize
# or
.venv/bin/python visualize_ast.py test.asm --text

# DOT format
make visualize-dot
# or
.venv/bin/python visualize_ast.py test.asm -f dot
```

---

## AST Structure

```
root
├── section (data)
│   └── dataDeclaration (hello)
│       └── literal (23)
└── section (inst)
    ├── labelDef ($START:)
    │   └── instruction (LDI)
    │       ├── reg (B)
    │       └── literal (0)
    ├── labelDef ($LOOP:)
    └── instruction (JMP)
        └── labelRef ($START)
```

Labels are leaf nodes (just like reg/literal), not containers. Instructions are their siblings in the instruction section.
