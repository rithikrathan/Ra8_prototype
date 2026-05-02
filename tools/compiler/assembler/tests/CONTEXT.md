# Ra8 Assembler & Emulator - Session Context
## Date: 2026-05-02

## Project Structure
```
tools/compiler/assembler/
├── assembler.c          # C assembler (flex/bison parser)
├── ast.c / ast.h        # AST node helpers
├── cJSON.c / cJSON.h    # JSON parser for instruction set
├── lexer.l              # Flex lexer
├── parser.y             # Bison parser
├── makefile             # Build: make / make test / make run / make clean
├── test.asm             # Simple 5+3=8 add test
├── test_vars.asm        # Variable declaration test
├── uthash.h             # Hash table library
├── data/
│   ├── instructionSet.csv
│   ├── instructionSet.json
│   └── opcode           # Generated opcode data
├── tests/
│   ├── test_basic.py      # 20 tests (arithmetic, bitwise, control flow)
│   ├── test_extended.py   # 10 tests (sort, popcount, reverse, etc.)
│   └── test_block.py      # 8 tests (memcpy, memset, memcmp, etc.)
└── testScripts/           # Old test scripts (may need updating)
    ├── 01_hello_world.asm ... 12_invalid_identifier.asm
    └── run_all.sh
```

## Build & Run
- `make` — build assembler
- `make run` — assemble test.asm
- `make test` — run all 38 tests
- `make clean` — remove generated files

## Register Set
A(0), B(1), C(2), D(3), E(4), F(5), G(6), H(7), SI(8), DI(9), RNG(10), SP(11), PC(12), templ(13), temph(14)

## Key Semantics (IMPORTANT)
- **CMP X, Y** computes Y-X (not X-Y). Sign flag = Y<X, Zero flag = Y==X
- **RIN regA, regB, target** → SI/DI = regA | (regB << 8). Target: 1/SI or 2/DI
- **LIN regSI/DI, addr16** → SI/DI = addr
- **IIN/DIN regIdx** → SI++/DI++ or SI--/DI--
- **LSX/SSX** = load/store via SI indirect; **LDX/SDX** = via DI indirect
- **AND/OR/XOR regRes, regA, regB** — 2-byte encoding: (regA,regB) then regRes
- **NOT regRes, regA** — 2-byte encoding: (regA, regRes)
- **LDI regA, imm** — regA = imm
- **ST addr, reg** — dataMem[addr] = reg
- **CAN mask** — jump if (flags & mask) == mask; **COR mask** — jump if (flags & mask) != 0
- **Data segment** starts at memory offset 0. First user variable = offset 0.
- **RIN high-byte register** must NOT be reused for loop counter — RIN overwrites it!
- **8-bit wrap** on underflow (e.g., SUB 12-18 = 250)

## Available Instructions
NOPE, HLT, ADD, ADI, ADDC, SUB, SUI, SUBB, AND, ANI, OR, ORI, NOT, XOR, XRI, XNR, XNI, IIN, DIN, CMP, RS, LS, RR, LR, ARS, MV, LD, LDI, ST, STI, LIN, SIN, RIN, RPC, RSP, CON, COR, CAN, JMP, SET, LSX, LDX, SSX, SDX

## Test Suite Status
- 38 tests total, all passing
- Tests use assembler + emulator pipeline, verify memory results
- Emulator binary: tools/emulator/main (Go, built separately)

## Pending/TODO
- testScripts/ files may need updating to match current syntax
- emulator binary needs to be built separately (cd emulator && go build)
