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
- Opcode 0-39 + operands; no bit-encoding (old emu wrong: numImm=byte&0b11000000)
- 2-reg pack: PACK_REGS(a,b)=(b<<4)|(a&0xF)
- HIGH_BYTE(x)=(x>>8)&0xFF, LOW_BYTE(x)=x&0xFF

### Inst sizes (assembler.c emitCode)
nop(0)=1,hlt(1)=1,add(2)=2,adi(3)=3,addc(4)=2,sub(5)=2,sui(6)=3,subb(7)=2,and(8)=2,ani(9)=3,or(10)=2,ori(11)=3,not(12)=2,xor(13)=2,xri(14)=3,xnr(15)=2,xni(16)=3,iin(17)=2,din(18)=2,cmp(19)=2,rs(20)=2,ls(21)=2,rr(22)=2,lr(23)=2,ars(24)=2,mv(25)=2,ld(26)=4,ldi(27)=4,st(28)=4,sti(29)=4,lin(30)=4,sin(31)=4,rin(32)=2,rpc(33)=2,rsp(34)=2,con(35)=2,cor(36)=2,can(37)=2,jmp(38)=3,set(39)=2

### Operand encoding
- add/addc/sub/subb/and/or/xor/xnr/rs/ls/rr/lr/ars: [opcode, regB<<4|regA] (no regRes byte, JSON says 3 bytes wrong)
- adi/sui/ani/ori/xri/xni: [opcode, regA<<4|regRes, imm8]
- not: [opcode, regA<<4|regRes]
- iin/din: [opcode, regIndex] (1=SI,2=DI)
- cmp: [opcode, regB<<4|regA]
- mv/rin/rpc/rsp: [opcode, regB<<4|regA]
- ld: [opcode, reg, addr_hi, addr_lo]
- ldi: [opcode, imm8, addr_hi, addr_lo]
- st: [opcode, reg, addr_hi, addr_lo]
- sti: [opcode, imm8, addr_hi, addr_lo]
- lin/sin: [opcode, reg, addr_hi, addr_lo]
- con/cor/can/set: [opcode, flag_bit_or_mask]
- jmp: [opcode, addr_hi, addr_lo]

## canBranch Logic
- Init TRUE (unconditional)
- CON flagBit: StatusWord has bit → true else false
- COR mask: (StatusWord & mask) !=0 → true
- CAN mask: (StatusWord & mask) == mask → true (all bits match)
- JMP addr: if canBranch → PC=addr; always reset canBranch=true after

## Asm Notes
- Two-pass: collectLabels()+resolvePass() first, emitCode() second
- AST mutation: identifier/labelRef → literal post-resolution
- Flag macros: Z=0x01,P=0x02,H=0x04,AC=0x08,C=0x10,OV=0x20,S=0x80; combos: CZ=0x11,ZP=0x03,CZP=0x13 etc.

## Emu Design
- Single-step fetch-decode-execute, no pipelining
- Lookup table: opcode → operand count, read bytes from inst mem
- Reg file: 13-byte array 0-10; PC/SP/SI/DI as uint16
- Safety: max step count to prevent infinite loops
- CLI: ./main <program.bin> [--data data.bin] [--trace] [--max-steps N]

## File Structure
- tools/compiler/assembler/: C assembler (flex/bison)
- tools/emulator/: Go emulator
- tools/emulator/src/emulator.go: old buggy emu, incompatible format
- tools/emulator/src/main.go: old CLI
- tools/compiler/assembler/data/instructionSet.json: opcode defs
- tools/compiler/assembler/helperScripts/csv2json.py: CSV→JSON converter

## JSON vs Asm Size Mismatch
JSON size includes opcode byte. Asm uses hardcoded getInstSize()/emitCode(), not JSON. Wrong JSON entries:
- cmp=1→2, sti=2→4, lin=2→4, sin=2→4, jmp=1→3, 3-op ALU=3→2, rin/rpc/rsp=3→2
