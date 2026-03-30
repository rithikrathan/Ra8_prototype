# AST Parsing Algorithm for Ra8 Assembler

## Overview

Two-pass approach:
1. **Pass 1 (Parse)**: Lex tokens → Build AST (no validation)
2. **Pass 2 (Validate)**: Walk AST → Check semantics, resolve labels

---

## Data Structure: Dynamic Child Arrays

Since `instruction` and `section` nodes store variable-length child arrays, `addChild` uses a growth pattern:

```c
typedef struct {
    astNode **children;    // dynamic array
    size_t count;          // current count
    size_t capacity;       // allocated size
} ChildArray;
```

**Growth algorithm**:
```
if (count >= capacity):
    capacity = max(capacity * 2, 4);  // start at 4, double on overflow
    children = realloc(children, capacity * sizeof(astNode*));
children[count++] = child;
```

---

## Pass 1: Lex + Parse + Build AST

### Algorithm

```
root = createNode(root)

currentParent = root
tokenStack = empty

while (token = yylex()) != EOF:
    switch (token):
        case DATASEGMENTSTART:
            section = createNode(section, ".data")
            addChild(root, section)
            currentParent = section
            break

        case INSTSEGMENTSTART:
            section = createNode(section, ".text")
            addChild(root, section)
            currentParent = section
            break

        case END:
            currentParent = root
            break

        case DATA_TYPE:
            node = createNode(dataDeclaration)
            node.as.dataDeclaration.type = parseDataType(yytext)
            push(tokenStack, node)
            break

        case IDENTIFIER:
            if (expecting name in data):
                tokenStack.top.dataDeclaration.identifier = strdup(yytext)
            else if (expecting instruction operand):
                operand = createNode(labelRef/reg/literal)
                addChild(currentInstruction, operand)
            break

        case INST:
            instr = createNode(instruction)
            instr.as.instruction.opcode = strdup(yytext)
            addChild(currentParent, instr)
            currentInstruction = instr
            break

        case REG:
            reg = createNode(reg)
            reg.as.reg.name = strdup(yytext)
            addChild(currentInstruction, reg)
            break

        case LITERAL (NUM/HEX/BIN):
            lit = createNode(literal)
            lit.as.literal.value = parseValue(yytext, tokenType)
            addChild(currentInstruction, lit)
            break

        case LABELDEF:
            label = createNode(labelDef)
            label.as.label.name = strdup(cleanup(yytext))
            addChild(currentParent, label)
            break

        case LABELREF:
            ref = createNode(labelRef)
            ref.as.label.name = strdup(cleanup(yytext))
            addChild(currentInstruction, ref)
            break
```

### Key Rules
- Track `currentParent` to know where to attach nodes
- Instructions become children of current section
- Operands become children of current instruction
- Return `currentParent` to `root` on `END`

---

## Pass 2: Semantic Validation

### Algorithm

```
validate(node):
    switch (node.type):
        case root:
            for each child:
                validate(child)
            break

        case section:
            if (node.name not in [".data", ".text", ".rodata"]):
                error("Unknown section: " + node.name)
            for each child:
                validate(child)
            break

        case instruction:
            if (node.opcode not in OPCODES):
                error("Unknown opcode: " + node.opcode)
            if (operandCount != OPCODE_ARITY[node.opcode]):
                error("Wrong operand count for " + node.opcode)
            for each operand:
                validate(operand)
            break

        case dataDeclaration:
            if (node.type not in [int8, int16, chr, str]):
                error("Unknown data type")
            if (node.valueNode == NULL):
                error("Data variable missing value")
            validate(node.valueNode)
            break

        case reg:
            if (node.name not in VALID_REGISTERS):
                error("Invalid register: " + node.name)
            break

        case literal:
            if (value out of allowed range):
                error("Literal out of range")
            break

        case labelDef:
            if (node.name in definedLabels):
                error("Duplicate label: " + node.name)
            add to definedLabels
            break

        case labelRef:
            // Mark for later resolution
            add to unresolvedRefs
            break
```

### Label Resolution (after initial pass)

```
for each ref in unresolvedRefs:
    if (ref.name in definedLabels):
        ref.resolved = true
        ref.target = definedLabels[ref.name]
    else:
        error("Undefined label: " + ref.name)
```

---

## Helper Functions

### addChild(parent, child)

```
addChild(parent, child):
    switch (parent.type):
        case instruction:
            growAndAppend(parent.as.instruction.operands, 
                          parent.as.instruction.operandCount,
                          child)
            break
        case section:
            growAndAppend(parent.as.section.valueNode,
                          parent.as.section.statement_count,
                          child)
            break
        case dataDeclaration:
            parent.as.dataDeclaration.valueNode = child
            break
        default:
            // Nodes like literal, reg, label don't have children
            break
```

### createNode(type, ...)

```
createNode(type, ...):
    node = malloc(sizeof(astNode))
    node.type = type
    va_start(args, type)
    switch (type):
        case instruction:
            node.as.instruction.opcode = va_arg(args, char*)
            node.as.instruction.operands = NULL
            node.as.instruction.operandCount = 0
            break
        case section:
            node.as.section.name = va_arg(args, char*)
            node.as.section.valueNode = NULL
            node.as.section.statement_count = 0
            break
        case label:
            node.as.label.name = va_arg(args, char*)
            break
        // ... etc
    va_end(args)
    return node
```

---

## Error Handling Strategy

1. **Collect all errors** before stopping (don't halt on first error)
2. **Track line numbers** in each node for meaningful error messages
3. **Error structure**:
   ```c
   typedef struct {
       int line;
       char *message;
       nodeType context;
   } SyntaxError;
   ```

---

## Memory Management

- All strings from lexer: `strdup()` to own the memory
- Tree deletion: recursive `freeNode(node)` that frees children first
- On parse error: can discard entire tree safely

---

## Summary: Two-Pass Flow

```
Source Code
    │
    ▼
┌─────────┐
│  Lexer  │  (yylex() - tokenizes)
└────┬────┘
     │ tokens
     ▼
┌─────────┐
│ Parser  │  (Pass 1: Build AST)
└────┬────┘
     │ AST
     ▼
┌──────────────┐
│   Validator  │  (Pass 2: Semantic checks)
└────┬─────────┘
     │ errors or success
     ▼
 Binary Output / Error Report
```
