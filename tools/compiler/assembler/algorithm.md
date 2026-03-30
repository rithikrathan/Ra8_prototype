# AST Data Structure & Tree Construction - Theory

## The astNode Struct

Think of `astNode` as a box that can hold different types of data inside it.

```
astNode
├── type          ← tells you WHAT is stored inside
└── as            ← union: the actual data
```

The `type` field is a "tag" that tells you which part of the union is valid.

---

## Understanding the Union

The union `as` can hold ONE of these at a time:

```
as can be:
├── instruction  (opcode + operands array)
├── label        (just a name string)
├── reg          (just a name string)
├── dataDeclaration (type + identifier + value)
└── section      (name + statements array)
```

**Key insight**: You MUST check `node->type` before accessing `node->as.xxx`. If you access the wrong union member, you get garbage.

Example thought process:
```
if (node->type == instruction) {
    // NOW it's safe to read node->as.instruction.opcode
}
```

---

## Creating Nodes

### The Problem

Different node types need different data:
- `instruction` needs: opcode string
- `section` needs: name string
- `label` needs: name string
- `reg` needs: name string
- `literal` needs: value number
- `dataDeclaration` needs: type + identifier + value

### The Solution: Variadic Arguments (varargs)

`createNode(type, ...)` uses the type to know how many additional arguments to read:

```
node = createNode(instruction, "MOV");    // 1 extra arg: opcode
node = createNode(section, ".data");      // 1 extra arg: name
node = createNode(literal, 42);           // 1 extra arg: value
```

Inside `createNode`, you use `va_start`, `va_arg`, `va_end` to pull out the arguments based on the type.

---

## Memory Allocation

When you create a node:

```
node = malloc(sizeof(astNode));  // allocate the struct itself
// ... set up the union members ...
```

For dynamic arrays inside (like operands in instruction), you start with NULL and grow as needed:

```
node->as.instruction.operands = NULL;       // start empty
node->as.instruction.operandCount = 0;
```

---

## Tree Structure

Your AST forms a tree:

```
root (type=root)
├── section (".data")
│   ├── dataDeclaration (myVar)
│   │   └── literal (42)
│   └── dataDeclaration (msg)
│       └── literal ("hello")
│
└── section (".text")
    ├── labelDef ("start")
    ├── instruction ("MOV")
    │   ├── reg ("r0")
    │   └── literal (10)
    └── instruction ("ADD")
        ├── reg ("r1")
        ├── reg ("r0")
        └── labelRef ("start")
```

**Rules for your assembler:**
- Root is always created first
- Sections are direct children of root
- Instructions are children of sections
- Operands are children of instructions
- Labels at same level as instructions (in section)
- Data values are children of data declarations

---

## How addChild Works

`addChild(parent, child)` attaches a node to another.

The implementation depends on WHAT the parent can hold:

```
if parent.type == instruction:
    // instruction holds an array of operands
    // append child to that array

if parent.type == section:
    // section holds an array of statements
    // append child to that array

if parent.type == dataDeclaration:
    // dataDeclaration holds a single value node
    // set that field directly

otherwise:
    // node type doesn't support children
    // either error or ignore
```

---

## Dynamic Array Growth (for operands/statements)

Arrays in C are fixed size. To simulate dynamic arrays:

```
start:   capacity = 0, count = 0, array = NULL

when adding:
    if count == capacity:
        capacity = max(capacity * 2, 4)   // double, minimum 4
        array = realloc(array, capacity * sizeof(ptr))
    
    array[count] = newItem
    count++
```

Why double? Amortized O(1) per insertion. Growing by 1 would be O(n) overall.

---

## Tracking Where to Attach (Parser State)

The parser needs to know "what is the current parent?"

```
currentParent = root    // start at root

on DATASEGMENTSTART:
    section = createNode(section, ".data")
    addChild(currentParent, section)
    currentParent = section    // now children go into this section

on END:
    currentParent = root       // go back up

on instruction:
    instr = createNode(instruction, opcode)
    addChild(currentParent, instr)
    currentParent = instr      // now operands go into this instruction

on operand (reg/literal/labelRef):
    operand = createNode(...)
    addChild(currentParent, operand)    // parent is the instruction
    // don't change currentParent - next operand still goes to same instruction
```

---

## Two Passes Explained

### Pass 1: Build the tree (no validation)
- Lex token by token
- Create nodes
- Attach to parent
- Don't check if registers are valid, labels exist, etc.
- Goal: just construct the data structure

### Pass 2: Validate the tree
- Walk the tree recursively
- Check each node's data makes sense
- Collect errors but keep going
- Resolve label references

This separation keeps each pass simple.

---

## Summary of Data Flow

```
Source Code
    |
    v
Lexer (yylex)
    |
    | tokens (type + text)
    v
Parser (createNode + addChild)
    |
    | AST (tree of nodes)
    v
Validator (walk tree + check rules)
    |
    | errors or valid
    v
Codegen (walk tree + emit bytes)
```
