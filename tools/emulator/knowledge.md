# Ra8 Knowledge

## Arch
- 13 regs: A=0,B=1,C=2,D=3,E=4,F=5,G=6,H=7,Templ=8,Temph=9,RNG=10
- Templ/Temph: PC bytes (Templ=low,Temph=high), no ALU, addr bus collective
- 16-bit special: PC,SP(start 0xFFFF),SI,DI,ReturnRegister
- 64KB inst mem, 64KB data mem
- Flags: Z(b0),P(b1),Halted(b2),AC(b3),C(b4),OV(b5),reserved(b6),S(b7)
- HandleFlags: reset all; Z=result==0; S=bit7 set; C=unsigned overflow>0xFF; AC=nibble carry; P=even parity; OV=signed overflow

## Asm Binary Format
- Output: program.bin (raw inst bytes), dataSegment.txt (data hex)
- Opcode 0-43 + operand bytes in sequence; no bit-encoding
- PACK_REGS(a,b) = (b<<4) | (a&0xF)
- HIGH_BYTE(x)=(x>>8)&0xFF, LOW_BYTE(x)=x&0xFF
- Registers A-H are single-char tokens. SI,DI,RNG,SP,PC,templ,temph are also REG tokens.

### Inst sizes (getInstSize in assembler.c)
nop(0)=1,hlt(1)=1,add(2)=3,adi(3)=3,addc(4)=3,sub(5)=3,sui(6)=3,subb(7)=3,and(8)=3,ani(9)=3,or(10)=3,ori(11)=3,not(12)=2,xor(13)=3,xri(14)=3,xnr(15)=3,xni(16)=3,iin(17)=2,din(18)=2,cmp(19)=2,rs(20)=3,ls(21)=3,rr(22)=3,lr(23)=3,ars(24)=3,mv(25)=2,ld(26)=4,ldi(27)=3,st(28)=4,sti(29)=4,lin(30)=4,sin(31)=4,rin(32)=3,rpc(33)=2,rsp(34)=2,con(35)=2,cor(36)=2,can(37)=2,jmp(38)=3,set(39)=2,lsx(40)=2,ldx(41)=2,ssx(42)=2,sdx(43)=2

### Operand encoding
- add/addc/sub/subb/and/or/xor/xnr/rs/ls/rr/lr/ars (3 bytes): `[opcode, (regB<<4)|regA, regRes]` — `regRes = regA OP regB`
- adi/sui/ani/ori/xri/xni (3 bytes): `[opcode, PACK_REGS(regRes, regA), imm8]` — `regRes = regA OP imm`
- not (2 bytes): `[opcode, PACK_REGS(regRes, regA)]` — `regRes = ~regA`
- iin/din (2 bytes): `[opcode, regIndex]` — regIndex: 1 or 8=SI, 2 or 9=DI
- cmp (2 bytes): `[opcode, PACK_REGS(regB, regA)]` — sets flags from `regA - regB`
- mv/rpc/rsp (2 bytes): `[opcode, PACK_REGS(regB, regA)]`
- rin (3 bytes): `[opcode, PACK_REGS(regB, regA), targetIdx]` — SI/DI = regA | (regB<<8), targetIdx: 1/8=SI, 2/9=DI
- ld (4 bytes): `[opcode, reg, addr_hi, addr_lo]` — `reg = dataMem[addr]`
- ldi (3 bytes): `[opcode, regA, imm8]` — `regs[regA] = imm`
- st (4 bytes): `[opcode, reg, addr_hi, addr_lo]` — `dataMem[addr] = reg`
- sti (4 bytes): `[opcode, addr_hi, addr_lo, imm8]` — `dataMem[addr] = imm`
- lin (4 bytes): `[opcode, regSI/DI, addr_hi, addr_lo]` — `SI/DI = addr`
- sin (4 bytes): `[opcode, regSI/DI, addr_hi, addr_lo]` — `dataMem[addr] = dataMem[SI/DI]`
- lsx (2 bytes): `[opcode, regA]` — `regA = dataMem[SI]`
- ldx (2 bytes): `[opcode, regA]` — `regA = dataMem[DI]`
- ssx (2 bytes): `[opcode, regA]` — `dataMem[SI] = regA`
- sdx (2 bytes): `[opcode, regA]` — `dataMem[DI] = regA`
- con/cor/can/set (2 bytes): `[opcode, flag_bit_or_mask]`
- jmp (3 bytes): `[opcode, addr_hi, addr_lo]` — conditional on canBranch

## canBranch Logic
- Init TRUE (unconditional JMP)
- CON flagBit: if flagBit==0 → true; else (flags & (1<<flagBit)) != 0 → true, else false
- COR mask: (flags & mask) != 0 → true (any flag match)
- CAN mask: (flags & mask) == mask → true (all flags must match)
- JMP addr: if canBranch → PC=addr; always reset canBranch=true after

## Asm Notes
- Two-pass: collectLabels()+resolvePass() first, emitCode() second
- AST mutation: identifier/labelRef → literal post-resolution
- Lexer recognizes SI,DI,RNG,SP,PC,templ,temph as REG tokens (not just A-H)
- `getLiteralValue` doesn't handle 0x hex or 0b binary strings — use decimal
- Flag macros: Z=0x01,P=0x02,H=0x04,AC=0x08,C=0x10,OV=0x20,S=0x80; combos: CZ=0x11,ZP=0x03,CZP=0x13 etc.

## Emu Design
- Single-step fetch-decode-execute, no pipelining
- Emulator reads operand bytes per instruction in execute() switch
- Reg file: 13-byte array 0-10; PC/SP/SI/DI as uint16
- Safety: max step count to prevent infinite loops
- CLI: ./main <program.bin> [--data data.bin] [--trace] [--dump-state] [--max-steps N]

## File Structure
- tools/compiler/assembler/: C assembler (flex/bison)
- tools/emulator/: Go emulator
- tools/compiler/assembler/data/instructionSet.json: opcode lookup for getMachineCode()

## Indirect Addressing Summary
- Only SI and DI can be used as indirect pointers
- `lsx`/`ldx` load from dataMem[SI]/dataMem[DI] into a register
- `ssx`/`sdx` store register to dataMem[SI]/dataMem[DI]
- `iin`/`din` increment/decrement SI or DI
- `lin` loads a 16-bit address into SI/DI
- `rin` loads a register pair into SI or DI (3rd operand selects target)
