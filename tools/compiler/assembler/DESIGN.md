# Assembler Design Document

## Overview

Two-pass assembler that converts Ra8 assembly to machine code (text and binary formats).

## Data Flow

```
.asm file
    ↓
Lexer (lexer.l) → Token stream
    ↓
Parser (parser.y) → AST
    ↓
First Pass → Symbol table (label → address)
    ↓
Second Pass → Machine code generation
    ↓
Output: *_inst.txt, *_data.txt (and _inst.bin, _data.bin in future)
```

---

## AST Structure

### Node Types

```c
typedef enum {
    root,           // root node
    section,        // [__data__] or [__inst__]
    instruction,    // opcode + operands
    labelDef,       // $labelname:
    labelRef,       // $labelname
    reg,            // register operand (a-h, SI, DI, RNG, TEMPH, TEMPL)
    literal,        // immediate value (NUM, BIN, HEX)
    identifier,     // variable name
    dataDeclaration // data section entry
} nodeType;
```

### Node Layout

| Node Type | Key Fields | Children |
|-----------|-----------|----------|
| `root` | — | section nodes |
| `section` | `as.section.name` ("data"/"inst") | lines/data declarations |
| `instruction` | `as.instruction.opcode` | operands (reg, literal, labelRef) |
| `labelDef` | `as.label.name` | — |
| `labelRef` | `as.label.name` | — |
| `reg` | `as.reg.name` | — |
| `literal` | `as.literal.intValue` | — |
| `identifier` | `as.identifier.name` | — |
| `dataDeclaration` | `as.dataDeclaration.type` | identifier, literal |

---

## Symbol Table

Hash table mapping label names to addresses.

```c
struct hashMap {
    char *key;      // label name
    int value;       // address (in bytes)
    UT_hash_handle hh;
};
```

---

## Instruction Set

Loaded from `data/instructionSet.csv` / `.json`.

### Register Encoding (4-bit field, 0-12)

| Register | Index |
|---------|-------|
| a | 0 |
| b | 1 |
| c | 2 |
| d | 3 |
| e | 4 |
| f | 5 |
| g | 6 |
| h | 7 |
| SI | 8 |
| DI | 9 |
| RNG | 10 |
| TEMPH | 11 |
| TEMPL | 12 |

### Instruction Formats

| Type | Example | Size | Byte Layout |
|------|---------|------|-------------|
| no operand | `nope`, `hlt` | 1 | `[opcode]` |
| single reg | `not a` | 2 | `[opcode][R]` |
| two regs | `cmp a, b`, `mv c, a` | 2 | `[opcode][B<<4 \| A]` |
| reg+imm | `adi a, a, 1`, `ldi a, 10` | 3 | `[opcode][R][imm]` |
| reg+mem | `ld b, 0x50` | 4 | `[opcode][R][addrL][addrH]` |
| mem+reg | `st 0x50, a` | 4 | `[opcode][addrL][addrH][R]` |
| sti | `sti 0x50, 10` | 4 | `[opcode][addrL][addrH][imm]` |
| jmp | `jmp $label` | 3 | `[opcode][addrL][addrH]` |
| con/cor/can | `con 1` | 2 | `[opcode][mask]` |

### Operand Detection Logic

```
instruction operand count:
    0 → no operand
    1 → 
        reg → single reg
        literal → "future additions" warning (lin/sin/etc)
    2 →
        reg, reg → two regs
        literal, reg → ??? (error or future)
        reg, literal → reg+imm
        reg, labelRef → ??? (error or future)
        labelRef, reg → reg+mem
    3 → ??? (currently not used)
```

---

## Pass Architecture

### First Pass

**Purpose:** Build symbol table, calculate addresses.

**Algorithm:**
```
address = 0
for each node in AST:
    switch node.type:
        case labelDef:
            put(node.as.label.name, address)
        case instruction:
            size = lookupSize(node.as.instruction.opcode)
            address += size
        case dataDeclaration:
            size = (type == int8) ? 1 : 2
            address += size
```

### Second Pass

**Purpose:** Generate machine code.

**Algorithm:**
```
for each node in AST:
    switch node.type:
        case instruction:
            emit(lookupMachineCode(opcode))
            for each operand:
                emitEncodedOperand(operand)
        case dataDeclaration:
            emitDataValue(value, type)
```

---

## Output Format

### Text Output (*_inst.txt, *_data.txt)

One byte per line as decimal (0-255):

```
28    ; LDI A, 10
0     ; register A
10    ; immediate 10
26    ; MV C, A
3     ; register C << 4 | A
...
```

### Binary Output (future)

Raw bytes written with `fwrite()`.

---

## File Naming

| Input | Outputs |
|-------|---------|
| `program.asm` | `program_inst.txt`, `program_data.txt` |
| `test.asm` | `test_inst.txt`, `test_data.txt` |

---

## Error Handling

| Condition | Action |
|-----------|--------|
| No `$START:` label | Print warning: "Warning: No $START label defined" |
| Undefined label reference | Error: "Undefined label: xyz" |
| lin/sin instruction | Warning: "lin/sin: Future addition, not implemented" |
| String/char data type | Skip with TODO comment in code |

---

## Changes from Original Design

### Registers
- Added TEMPH (11), TEMPL (12) registers
- Total: 13 registers (0-12, fits in 4 bits)

### Case Insensitivity
- Lexer: `is_instruction()` case-insensitive matching
- Parser: `isValid()` case-insensitive matching
- Register names: case-insensitive

### Instruction Sizes (CSV corrections)

| Opcode | Old Size | New Size |
|--------|----------|----------|
| cmp | 1 | 2 |
| jmp | 1 | 3 |
| ldi | 4 | 3 |
| rs/ls/rr/lr/ars | 1 | 2 |

### Instruction Formats
- Single reg: `[opcode][R]` (2 bytes, not 1)
- Two regs: `[opcode][B<<4 | A]` (register in nibbles)
- reg+imm: `[opcode][R][imm]` (3 bytes)
- mem+reg: `[opcode][addrL][addrH][R]` (4 bytes)
- reg+mem: `[opcode][R][addrL][addrH]` (4 bytes)
- sti: `[opcode][addrL][addrH][imm]` (4 bytes, no register)
- jmp: `[opcode][addrL][addrH]` (3 bytes)
- con/cor/can: `[opcode][mask]` (2 bytes)

### Data Handling
- `int8` = 1 byte
- `int16` = 2 bytes (little-endian)
- `str`/`char` = TODO (skip, add comment in code)

### Output
- Separate inst and data files
- Inst file: `_inst.txt`
- Data file: `_data.txt`

---

## Implementation Order

1. `Makefile` — build system
2. `data/instructionSet.csv` — update sizes
3. `data/instructionSet.json` — update sizes
4. `lexer.l` — case insensitive, register expansion, fix register check
5. `parser.y` — case insensitive instruction checking
6. `assembler.c`:
   - Register encode function
   - JSON/CSV loader
   - `getNextNode()` implementation
   - `firstPass()`
   - `secondPass()`
   - `exportTxt()`
   - Start label warning
   - lin/sin future additions message
7. `ownAdditions.md` — document drastic changes only
