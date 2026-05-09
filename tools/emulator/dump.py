#!/usr/bin/env python3
"""Ra8 CPU Emulator - dumps all registers, memory, and execution info."""

import sys
import struct


class CPU:
    def __init__(self):
        self.regs = [0] * 13
        self.pc = 0
        self.sp = 0xFFFF
        self.si = 0
        self.di = 0
        self.flags = 0
        self.halted = False
        self.can_branch = True
        self.inst_mem = b""
        self.data_mem = bytearray(65536)
        self.step_count = 0
        self.max_steps = 100000

    REG_NAMES = ["A", "B", "C", "D", "E", "F", "G", "H", "Templ", "Temph", "RNG", "SP", "PC"]
    FLAG_BITS = {7: "S", 5: "OV", 4: "C", 3: "AC", 2: "H", 1: "P", 0: "Z"}
    OPCODES = {
        0: "nop", 1: "hlt", 2: "add", 3: "adi", 4: "addc", 5: "sub", 6: "sui",
        7: "subb", 8: "and", 9: "ani", 10: "or", 11: "ori", 12: "not", 13: "xor",
        14: "xri", 15: "xnr", 16: "xni", 17: "iin", 18: "din", 19: "cmp",
        20: "rs", 21: "ls", 22: "rr", 23: "lr", 24: "ars", 25: "mv", 26: "ld",
        27: "ldi", 28: "st", 29: "sti", 30: "lin", 31: "sin", 32: "rin",
        33: "rpc", 34: "rsp", 35: "con", 36: "cor", 37: "can", 38: "jmp",
        39: "set", 40: "lsx", 41: "ldx", 42: "ssx", 43: "sdx",
    }

    def load_program(self, path):
        with open(path, "rb") as f:
            self.inst_mem = f.read()

    def load_data(self, path):
        with open(path, "rb") as f:
            data = f.read()
            for i, b in enumerate(data):
                self.data_mem[i] = b

    def fetch_byte(self):
        b = self.inst_mem[self.pc]
        self.pc += 1
        return b

    def fetch_word(self):
        hi = self.fetch_byte()
        lo = self.fetch_byte()
        return (hi << 8) | lo

    def reg(self, i):
        return self.regs[i] if i < 13 else 0

    def set_flags(self, result, a, b, carry_out=False):
        f = 0
        if result == 0:
            f |= 0x01
        parity = bin(result).count("1")
        if parity % 2 == 0:
            f |= 0x02
        if result & 0x80:
            f |= 0x80
        if carry_out:
            f |= 0x10
        if (a & 0xF) + (b & 0xF) > 0xF:
            f |= 0x08
        sa, sb, sr = int8(a), int8(b), int8(result)
        if (sa >= 0 and sb >= 0 and sr < 0) or (sa < 0 and sb < 0 and sr >= 0):
            f |= 0x20
        return f

    def run(self):
        while not self.halted and self.step_count < self.max_steps:
            self.step()

    def step(self):
        if self.halted:
            return
        pc = self.pc
        opcode = self.inst_mem[pc]
        self.pc += 1
        self.execute(opcode)
        self.step_count += 1

    def execute(self, opcode):
        if opcode == 1:
            self.halted = True
            self.flags |= 0x04
        elif opcode == 2:
            b = self.fetch_byte(); regB = (b >> 4) & 0x0F; regA = b & 0x0F
            regRes = self.fetch_byte()
            a = self.reg(regA); bv = self.reg(regB)
            result = (a + bv) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, bv, uint16(a)+uint16(bv) > 0xFF)
        elif opcode == 3:
            b = self.fetch_byte(); regA = (b >> 4) & 0x0F; regRes = b & 0x0F
            imm = self.fetch_byte()
            a = self.reg(regA)
            result = (a + imm) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, imm, uint16(a)+uint16(imm) > 0xFF)
        elif opcode == 4:
            b = self.fetch_byte(); regB = (b >> 4) & 0x0F; regA = b & 0x0F
            regRes = self.fetch_byte()
            a = self.reg(regA); bv = self.reg(regB)
            carry = 1 if self.flags & 0x10 else 0
            result = (a + bv + carry) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, bv, uint16(a)+uint16(bv)+carry > 0xFF)
        elif opcode == 5:
            b = self.fetch_byte(); regB = (b >> 4) & 0x0F; regA = b & 0x0F
            regRes = self.fetch_byte()
            a = self.reg(regA); bv = self.reg(regB)
            result = (a - bv) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, bv, a < bv)
        elif opcode == 6:
            b = self.fetch_byte(); regA = (b >> 4) & 0x0F; regRes = b & 0x0F
            imm = self.fetch_byte()
            a = self.reg(regA)
            result = (a - imm) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, imm, a < imm)
        elif opcode == 7:
            b = self.fetch_byte(); regB = (b >> 4) & 0x0F; regA = b & 0x0F
            regRes = self.fetch_byte()
            a = self.reg(regA); bv = self.reg(regB)
            borrow = 1 if self.flags & 0x10 else 0
            result = (a - bv - borrow) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, bv, a < bv + borrow)
        elif opcode == 8:
            b = self.fetch_byte(); regB = (b >> 4) & 0x0F; regA = b & 0x0F
            regRes = self.fetch_byte()
            a = self.reg(regA); bv = self.reg(regB)
            result = (a & bv) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, bv)
        elif opcode == 9:
            b = self.fetch_byte(); regA = (b >> 4) & 0x0F; regRes = b & 0x0F
            imm = self.fetch_byte()
            a = self.reg(regA)
            result = (a & imm) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, imm)
        elif opcode == 10:
            b = self.fetch_byte(); regB = (b >> 4) & 0x0F; regA = b & 0x0F
            regRes = self.fetch_byte()
            a = self.reg(regA); bv = self.reg(regB)
            result = (a | bv) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, bv)
        elif opcode == 11:
            b = self.fetch_byte(); regA = (b >> 4) & 0x0F; regRes = b & 0x0F
            imm = self.fetch_byte()
            a = self.reg(regA)
            result = (a | imm) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, imm)
        elif opcode == 12:
            b = self.fetch_byte(); regA = (b >> 4) & 0x0F; regRes = b & 0x0F
            a = self.reg(regA)
            result = (~a) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, 0)
        elif opcode == 13:
            b = self.fetch_byte(); regB = (b >> 4) & 0x0F; regA = b & 0x0F
            regRes = self.fetch_byte()
            a = self.reg(regA); bv = self.reg(regB)
            result = (a ^ bv) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, bv)
        elif opcode == 14:
            b = self.fetch_byte(); regA = (b >> 4) & 0x0F; regRes = b & 0x0F
            imm = self.fetch_byte()
            a = self.reg(regA)
            result = (a ^ imm) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, imm)
        elif opcode == 15:
            b = self.fetch_byte(); regB = (b >> 4) & 0x0F; regA = b & 0x0F
            regRes = self.fetch_byte()
            a = self.reg(regA); bv = self.reg(regB)
            result = (~(a ^ bv)) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, bv)
        elif opcode == 16:
            b = self.fetch_byte(); regA = (b >> 4) & 0x0F; regRes = b & 0x0F
            imm = self.fetch_byte()
            a = self.reg(regA)
            result = (~(a ^ imm)) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, imm)
        elif opcode == 17:
            regIdx = self.fetch_byte()
            if regIdx in (1, 8): self.si += 1
            elif regIdx in (2, 9): self.di += 1
        elif opcode == 18:
            regIdx = self.fetch_byte()
            if regIdx in (1, 8): self.si -= 1
            elif regIdx in (2, 9): self.di -= 1
        elif opcode == 19:
            b = self.fetch_byte(); regA = (b >> 4) & 0x0F; regB = b & 0x0F
            a = self.reg(regA); bv = self.reg(regB)
            result = (a - bv) & 0xFF
            self.flags = self.set_flags(result, a, bv, a < bv)
        elif opcode == 20:
            b = self.fetch_byte(); regB = (b >> 4) & 0x0F; regA = b & 0x0F
            regRes = self.fetch_byte()
            a = self.reg(regA); bv = self.reg(regB)
            result = (a >> bv) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, bv)
        elif opcode == 21:
            b = self.fetch_byte(); regB = (b >> 4) & 0x0F; regA = b & 0x0F
            regRes = self.fetch_byte()
            a = self.reg(regA); bv = self.reg(regB)
            result = (a << bv) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, bv)
        elif opcode == 22:
            b = self.fetch_byte(); regB = (b >> 4) & 0x0F; regA = b & 0x0F
            regRes = self.fetch_byte()
            a = self.reg(regA); bv = self.reg(regB) & 0x07
            if bv == 0: bv = 8
            result = ((a >> bv) | (a << (8 - bv))) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, bv)
        elif opcode == 23:
            b = self.fetch_byte(); regB = (b >> 4) & 0x0F; regA = b & 0x0F
            regRes = self.fetch_byte()
            a = self.reg(regA); bv = self.reg(regB) & 0x07
            if bv == 0: bv = 8
            result = ((a << bv) | (a >> (8 - bv))) & 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, bv)
        elif opcode == 24:
            b = self.fetch_byte(); regB = (b >> 4) & 0x0F; regA = b & 0x0F
            regRes = self.fetch_byte()
            a = self.reg(regA); bv = self.reg(regB)
            if bv >= 8: bv = 7
            result = (a >> bv) | (0xFF << (8 - bv))
            if a & 0x80 == 0: result &= ~(0xFF << (8 - bv))
            result &= 0xFF
            self.regs[regRes] = result
            self.flags = self.set_flags(result, a, bv)
        elif opcode == 25:
            b = self.fetch_byte(); regA = (b >> 4) & 0x0F; regB = b & 0x0F
            self.regs[regB] = self.reg(regA)
        elif opcode == 26:
            regA = self.fetch_byte(); addr = self.fetch_word()
            self.regs[regA] = self.data_mem[addr]
        elif opcode == 27:
            regA = self.fetch_byte(); imm = self.fetch_byte()
            self.regs[regA] = imm
        elif opcode == 28:
            reg = self.fetch_byte(); addr = self.fetch_word()
            self.data_mem[addr] = self.reg(reg)
        elif opcode == 29:
            addr = self.fetch_word(); imm = self.fetch_byte()
            self.data_mem[addr] = imm
        elif opcode == 30:
            regIdx = self.fetch_byte(); addr = self.fetch_word()
            if regIdx in (1, 8): self.si = addr
            elif regIdx in (2, 9): self.di = addr
        elif opcode == 31:
            regIdx = self.fetch_byte(); addr = self.fetch_word()
            src = self.si if regIdx in (1, 8) else self.di
            self.data_mem[addr] = self.data_mem[src]
        elif opcode == 32:
            b = self.fetch_byte(); regA = (b >> 4) & 0x0F; regB = b & 0x0F
            targetIdx = self.fetch_byte()
            val = self.reg(regA) | (self.reg(regB) << 8)
            if targetIdx in (1, 8): self.si = val & 0xFFFF
            elif targetIdx in (2, 9): self.di = val & 0xFFFF
        elif opcode == 33:
            b = self.fetch_byte(); regA = (b >> 4) & 0x0F; regB = b & 0x0F
            self.pc = self.reg(regA) | (self.reg(regB) << 8)
        elif opcode == 34:
            b = self.fetch_byte(); regA = (b >> 4) & 0x0F; regB = b & 0x0F
            self.sp = self.reg(regA) | (self.reg(regB) << 8)
        elif opcode == 35:
            flagBit = self.fetch_byte()
            self.can_branch = flagBit == 0 or bool(self.flags & (1 << flagBit))
        elif opcode == 36:
            mask = self.fetch_byte()
            self.can_branch = bool(self.flags & mask)
        elif opcode == 37:
            mask = self.fetch_byte()
            self.can_branch = (self.flags & mask) == mask
        elif opcode == 38:
            addr = self.fetch_word()
            if self.can_branch: self.pc = addr
            self.can_branch = True
        elif opcode == 39:
            mask = self.fetch_byte()
            self.flags |= mask
        elif opcode == 40:
            regA = self.fetch_byte()
            self.regs[regA] = self.data_mem[self.si]
        elif opcode == 41:
            regA = self.fetch_byte()
            self.regs[regA] = self.data_mem[self.di]
        elif opcode == 42:
            regA = self.fetch_byte()
            self.data_mem[self.si] = self.reg(regA)
        elif opcode == 43:
            regA = self.fetch_byte()
            self.data_mem[self.di] = self.reg(regA)

    def flag_str(self):
        parts = [self.FLAG_BITS[bit] for bit in sorted(self.FLAG_BITS.keys()) if self.flags & (1 << bit)]
        return " ".join(parts) if parts else "-"

    def dump_data_only(self):
        print("=" * 70)
        print("DATA MEMORY (non-zero regions)")
        print("=" * 70)
        nonzero = []
        for i in range(0, len(self.data_mem), 16):
            row = self.data_mem[i:i+16]
            if any(b != 0 for b in row):
                nonzero.append((i, row))
        if not nonzero:
            print("  (all zeros)")
        else:
            for addr, row in nonzero:
                hex_str = " ".join(f"{b:02x}" for b in row)
                ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
                print(f"  {addr:04x}: {hex_str:<48s}  |{ascii_str}|")
        print()
        print("=" * 70)

    def dump(self, trace=False):
        if trace:
            print("=" * 70)
            print("TRACE (per-step execution)")
            print("=" * 70)
            saved_halted = self.halted
            self.halted = False
            self.pc = 0
            self.sp = 0xFFFF
            self.si = 0
            self.di = 0
            self.flags = 0
            self.regs = [0] * 13
            self.data_mem = bytearray(65536)
            self.step_count = 0
            self.can_branch = True
            while not self.halted and self.step_count < self.max_steps:
                pc = self.pc
                opcode = self.inst_mem[pc]
                self.pc += 1
                name = self.OPCODES.get(opcode, f"?{opcode:02x}")
                print(f"  [{self.step_count+1:04d}] PC={pc:04x} {name:<5s}", end="")
                self.execute(opcode)
                print(f"  Flags=[{self.flag_str()}]")
                self.step_count += 1
            self.halted = saved_halted
            print()

        print("=" * 70)
        print("GENERAL PURPOSE REGISTERS (8-bit)")
        print("=" * 70)
        names_8bit = self.REG_NAMES[:11]
        for i in range(0, len(names_8bit), 4):
            row = names_8bit[i:i+4]
            vals = [f"{self.regs[i+j]:02x}" for j in range(4) if i+j < len(names_8bit)]
            labels = [f"{n}={v}" for n, v in zip(row, vals)]
            print("  " + "  ".join(f"{l:<10s}" for l in labels))
        print(f"  {'Flags':<10s}= {self.flags:02x}  [{self.flag_str()}]")

        print()
        print("=" * 70)
        print("POINTER REGISTERS (16-bit)")
        print("=" * 70)
        print(f"  PC = {self.pc:04x}    SP = {self.sp:04x}    SI = {self.si:04x}    DI = {self.di:04x}")

        print()
        print("=" * 70)
        print("EXECUTION STATUS")
        print("=" * 70)
        status = "HALTED" if self.halted else "MAX STEPS REACHED" if self.step_count >= self.max_steps else "UNKNOWN"
        print(f"  Status   : {status}")
        print(f"  Steps    : {self.step_count}")
        print(f"  Prog Size: {len(self.inst_mem)} bytes")

        print()
        print("=" * 70)
        print("INSTRUCTION MEMORY (program)")
        print("=" * 70)
        for i in range(0, len(self.inst_mem), 16):
            chunk = self.inst_mem[i:i+16]
            hex_str = " ".join(f"{b:02x}" for b in chunk)
            print(f"  {i:04x}: {hex_str}")

        print()
        print("=" * 70)
        print("DATA MEMORY (non-zero regions)")
        print("=" * 70)
        nonzero = []
        for i in range(0, len(self.data_mem), 16):
            row = self.data_mem[i:i+16]
            if any(b != 0 for b in row):
                nonzero.append((i, row))

        if not nonzero:
            print("  (all zeros)")
        else:
            for addr, row in nonzero:
                hex_str = " ".join(f"{b:02x}" for b in row)
                ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
                print(f"  {addr:04x}: {hex_str:<48s}  |{ascii_str}|")

        print()
        print("=" * 70)


def uint16(v):
    return v & 0xFFFF


def int8(v):
    return v - 256 if v >= 128 else v


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <program.bin> [--data data.bin] [--trace]")
        sys.exit(1)

    prog = sys.argv[1]
    data_file = None
    trace = False
    data_only = False

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--data" and i + 1 < len(sys.argv):
            data_file = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--trace":
            trace = True
            i += 1
        elif sys.argv[i] == "--data-only":
            data_only = True
            i += 1
        else:
            i += 1

    cpu = CPU()
    cpu.load_program(prog)
    if data_file:
        cpu.load_data(data_file)
    cpu.run()
    if data_only:
        cpu.dump_data_only()
    else:
        cpu.dump(trace=trace)


if __name__ == "__main__":
    main()
