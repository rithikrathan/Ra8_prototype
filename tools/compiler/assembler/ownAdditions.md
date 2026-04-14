# Own Additions

Changes made that drastically differ from the original design.

## Register Encoding

Extended from a-h (0-7) to include new registers:

| Register | Index |
|---------|-------|
| a-h | 0-7 |
| SI | 8 |
| DI | 9 |
| RNG | 10 |
| TEMPH | 11 |
| TEMPL | 12 |

Total: 13 registers (fits in 4-bit field).

## Case Insensitivity

All instruction names and register names are now case-insensitive.

## Instruction Formats

New instruction byte layouts derived from pipeline operand formats:

| Type | Format |
|------|--------|
| single reg | `[opcode][R]` |
| two regs | `[opcode][B<<4 \| A]` |
| reg+imm | `[opcode][R][imm]` |
| mem+reg | `[opcode][addrL][addrH][R]` |
| reg+mem | `[opcode][R][addrL][addrH]` |
| sti | `[opcode][addrL][addrH][imm]` (no register) |
| jmp | `[opcode][addrL][addrH]` |
| con/cor/can | `[opcode][mask]` |

## CSV Size Corrections

| Opcode | Old | New |
|--------|-----|-----|
| cmp | 1 | 2 |
| jmp | 1 | 3 |
| ldi | 4 | 3 |
| rs/ls/rr/lr/ars | 1 | 2 |

## Data Handling

- `int8` = 1 byte
- `int16` = 2 bytes (little-endian)
- `str`/`char` = TODO (not implemented, skip)
