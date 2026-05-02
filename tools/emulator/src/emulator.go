package main

import (
	"fmt"
	"os"
)

type CPU struct {
	regs       [13]byte
	pc         uint16
	sp         uint16
	si         uint16
	di         uint16
	flags      byte
	halted     bool
	canBranch  bool
	instMem    []byte
	dataMem    []byte
	trace      bool
	stepCount  int
	maxSteps   int
}

func NewCPU() *CPU {
	return &CPU{
		sp:        0xFFFF,
		canBranch: true,
		dataMem:   make([]byte, 65536),
	}
}

func (c *CPU) LoadProgram(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	c.instMem = data
	return nil
}

func (c *CPU) LoadData(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	for i, b := range data {
		c.dataMem[i] = b
	}
	return nil
}

func (c *CPU) Run() {
	for !c.halted && c.stepCount < c.maxSteps {
		c.step()
	}
}

func (c *CPU) step() {
	if c.halted {
		return
	}

	pc := c.pc
	opcode := c.instMem[pc]
	c.pc++

	if c.trace {
		fmt.Printf("[%04d] PC=%04x %-5s", c.stepCount+1, pc, opcodeName(opcode))
	}

	c.execute(opcode)
	c.stepCount++

	if c.trace {
		fmt.Printf("  A=%02x B=%02x C=%02x D=%02x E=%02x F=%02x G=%02x H=%02x",
			c.regs[0], c.regs[1], c.regs[2], c.regs[3],
			c.regs[4], c.regs[5], c.regs[6], c.regs[7])
		fmt.Printf("  SP=%04x SI=%04x DI=%04x PC=%04x", c.sp, c.si, c.di, c.pc)
		fmt.Printf("  Flags=[%s] (%02x)\n", flagStr(c.flags), c.flags)
	}
}

func (c *CPU) fetchByte() byte {
	b := c.instMem[c.pc]
	c.pc++
	return b
}

func (c *CPU) fetchWord() uint16 {
	hi := uint16(c.fetchByte())
	lo := uint16(c.fetchByte())
	return (hi << 8) | lo
}

func (c *CPU) reg(i byte) byte {
	if i < 13 {
		return c.regs[i]
	}
	return 0
}

func opcodeName(o byte) string {
	names := [44]string{
		"nop", "hlt", "add", "adi", "addc", "sub", "sui", "subb",
		"and", "ani", "or", "ori", "not", "xor", "xri", "xnr",
		"xni", "iin", "din", "cmp", "rs", "ls", "rr", "lr",
		"ars", "mv", "ld", "ldi", "st", "sti", "lin", "sin",
		"rin", "rpc", "rsp", "con", "cor", "can", "jmp", "set",
		"lsx", "ldx", "ssx", "sdx",
	}
	if o < 44 {
		return names[o]
	}
	return fmt.Sprintf("?%02x", o)
}

func regName(i byte) string {
	names := []string{
		"A", "B", "C", "D", "E", "F", "G", "H",
		"SI", "DI", "RNG", "SP", "PC",
	}
	if i < 13 {
		return names[i]
	}
	return "?"
}

func flagStr(f byte) string {
	s := ""
	if f&0x01 != 0 {
		s += "Z"
	}
	if f&0x02 != 0 {
		s += "P"
	}
	if f&0x04 != 0 {
		s += "H"
	}
	if f&0x08 != 0 {
		s += "AC"
	}
	if f&0x10 != 0 {
		s += "C"
	}
	if f&0x20 != 0 {
		s += "OV"
	}
	if f&0x80 != 0 {
		s += "S"
	}
	if s == "" {
		return "-"
	}
	return s
}

func setFlags(result byte, a byte, b byte, carryOut bool) byte {
	f := byte(0) &^ 0x1F
	f &^= 0x80
	if result == 0 {
		f |= 0x01
	}
	p := result
	parity := 0
	for p != 0 {
		if p&1 != 0 {
			parity++
		}
		p >>= 1
	}
	if parity%2 == 0 {
		f |= 0x02
	}
	if result&0x80 != 0 {
		f |= 0x80
	}
	if carryOut {
		f |= 0x10
	}
	au := uint16(a) & 0xF
	bu := uint16(b) & 0xF
	if au+bu > 0xF {
		f |= 0x08
	}
	sa := int8(a)
	sb := int8(b)
	sr := int8(result)
	if (sa >= 0 && sb >= 0 && sr < 0) || (sa < 0 && sb < 0 && sr >= 0) {
		f |= 0x20
	}
	return f
}

func (c *CPU) execute(opcode byte) {
	switch opcode {
	case 0:
		// nop

	case 1:
		c.halted = true
		c.flags |= 0x04

	case 2: // add regRes, regA, regB  => [opcode, (regB<<4)|regA, regRes]
		b := c.fetchByte()
		regB := (b >> 4) & 0x0F
		regA := b & 0x0F
		regRes := c.fetchByte()
		a := c.reg(regA)
		bv := c.reg(regB)
		result := a + bv
		carry := uint16(a)+uint16(bv) > 0xFF
		if c.trace {
			fmt.Printf("    %s+%s=%s -> %s(0x%02x)", regName(regA), regName(regB), regName(regRes), regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, bv, carry)

	case 3: // adi regRes, regA, imm  => [opcode, PACK(regRes,regA), imm]
		b := c.fetchByte()
		regA := (b >> 4) & 0x0F
		regRes := b & 0x0F
		imm := c.fetchByte()
		a := c.reg(regA)
		result := a + imm
		carry := uint16(a)+uint16(imm) > 0xFF
		if c.trace {
			fmt.Printf("    %s+0x%02x -> %s(0x%02x)", regName(regA), imm, regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, imm, carry)

	case 4: // addc regRes, regA, regB  => regRes = regA + regB + carry
		b := c.fetchByte()
		regB := (b >> 4) & 0x0F
		regA := b & 0x0F
		regRes := c.fetchByte()
		a := c.reg(regA)
		bv := c.reg(regB)
		carryBit := byte(0)
		if c.flags&0x10 != 0 {
			carryBit = 1
		}
		sum := uint16(a) + uint16(bv) + uint16(carryBit)
		result := byte(sum)
		carry := sum > 0xFF
		if c.trace {
			fmt.Printf("    %s+%s+carry=%s -> %s(0x%02x)", regName(regA), regName(regB), regName(regRes), regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, bv, carry)

	case 5: // sub regRes, regA, regB  => regRes = regA - regB
		b := c.fetchByte()
		regB := (b >> 4) & 0x0F
		regA := b & 0x0F
		regRes := c.fetchByte()
		a := c.reg(regA)
		bv := c.reg(regB)
		result := a - bv
		carry := a < bv
		if c.trace {
			fmt.Printf("    %s-%s=%s -> %s(0x%02x)", regName(regA), regName(regB), regName(regRes), regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, bv, carry)

	case 6: // sui regRes, regA, imm  => regRes = regA - imm
		b := c.fetchByte()
		regA := (b >> 4) & 0x0F
		regRes := b & 0x0F
		imm := c.fetchByte()
		a := c.reg(regA)
		result := a - imm
		carry := a < imm
		if c.trace {
			fmt.Printf("    %s-0x%02x -> %s(0x%02x)", regName(regA), imm, regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, imm, carry)

	case 7: // subb regRes, regA, regB  => regRes = regA - regB - borrow
		b := c.fetchByte()
		regB := (b >> 4) & 0x0F
		regA := b & 0x0F
		regRes := c.fetchByte()
		a := c.reg(regA)
		bv := c.reg(regB)
		borrow := byte(0)
		if c.flags&0x10 != 0 {
			borrow = 1
		}
		diff := uint16(a) - uint16(bv) - uint16(borrow)
		result := byte(diff)
		carry := a < bv+borrow
		if c.trace {
			fmt.Printf("    %s-%s-borrow=%s -> %s(0x%02x)", regName(regA), regName(regB), regName(regRes), regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, bv, carry)

	case 8: // and regRes, regA, regB
		b := c.fetchByte()
		regB := (b >> 4) & 0x0F
		regA := b & 0x0F
		regRes := c.fetchByte()
		a := c.reg(regA)
		bv := c.reg(regB)
		result := a & bv
		if c.trace {
			fmt.Printf("    %s&%s -> %s(0x%02x)", regName(regA), regName(regB), regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, bv, false)

	case 9: // ani regRes, regA, imm
		b := c.fetchByte()
		regA := (b >> 4) & 0x0F
		regRes := b & 0x0F
		imm := c.fetchByte()
		a := c.reg(regA)
		result := a & imm
		if c.trace {
			fmt.Printf("    %s&0x%02x -> %s(0x%02x)", regName(regA), imm, regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, imm, false)

	case 10: // or regRes, regA, regB
		b := c.fetchByte()
		regB := (b >> 4) & 0x0F
		regA := b & 0x0F
		regRes := c.fetchByte()
		a := c.reg(regA)
		bv := c.reg(regB)
		result := a | bv
		if c.trace {
			fmt.Printf("    %s|%s -> %s(0x%02x)", regName(regA), regName(regB), regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, bv, false)

	case 11: // ori regRes, regA, imm
		b := c.fetchByte()
		regA := (b >> 4) & 0x0F
		regRes := b & 0x0F
		imm := c.fetchByte()
		a := c.reg(regA)
		result := a | imm
		if c.trace {
			fmt.Printf("    %s|0x%02x -> %s(0x%02x)", regName(regA), imm, regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, imm, false)

	case 12: // not regRes, regA
		b := c.fetchByte()
		regA := (b >> 4) & 0x0F
		regRes := b & 0x0F
		a := c.reg(regA)
		result := ^a
		if c.trace {
			fmt.Printf("    ~%s -> %s(0x%02x)", regName(regA), regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, 0, false)

	case 13: // xor regRes, regA, regB
		b := c.fetchByte()
		regB := (b >> 4) & 0x0F
		regA := b & 0x0F
		regRes := c.fetchByte()
		a := c.reg(regA)
		bv := c.reg(regB)
		result := a ^ bv
		if c.trace {
			fmt.Printf("    %s^%s -> %s(0x%02x)", regName(regA), regName(regB), regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, bv, false)

	case 14: // xri regRes, regA, imm
		b := c.fetchByte()
		regA := (b >> 4) & 0x0F
		regRes := b & 0x0F
		imm := c.fetchByte()
		a := c.reg(regA)
		result := a ^ imm
		if c.trace {
			fmt.Printf("    %s^0x%02x -> %s(0x%02x)", regName(regA), imm, regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, imm, false)

	case 15: // xnr regRes, regA, regB  => ~(A ^ B)
		b := c.fetchByte()
		regB := (b >> 4) & 0x0F
		regA := b & 0x0F
		regRes := c.fetchByte()
		a := c.reg(regA)
		bv := c.reg(regB)
		result := ^(a ^ bv)
		if c.trace {
			fmt.Printf("    ~(%s^%s) -> %s(0x%02x)", regName(regA), regName(regB), regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, bv, false)

	case 16: // xni regRes, regA, imm  => ~(A ^ imm)
		b := c.fetchByte()
		regA := (b >> 4) & 0x0F
		regRes := b & 0x0F
		imm := c.fetchByte()
		a := c.reg(regA)
		result := ^(a ^ imm)
		if c.trace {
			fmt.Printf("    ~(%s^0x%02x) -> %s(0x%02x)", regName(regA), imm, regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, imm, false)

	case 17: // iin regIndex  => SI++ or DI++
		regIdx := c.fetchByte()
		if regIdx == 1 || regIdx == 8 {
			c.si++
			if c.trace {
				fmt.Printf("    SI++ -> %04x", c.si)
			}
		} else if regIdx == 2 || regIdx == 9 {
			c.di++
			if c.trace {
				fmt.Printf("    DI++ -> %04x", c.di)
			}
		}

	case 18: // din regIndex  => SI-- or DI--
		regIdx := c.fetchByte()
		if regIdx == 1 || regIdx == 8 {
			c.si--
			if c.trace {
				fmt.Printf("    SI-- -> %04x", c.si)
			}
		} else if regIdx == 2 || regIdx == 9 {
			c.di--
			if c.trace {
				fmt.Printf("    DI-- -> %04x", c.di)
			}
		}

	case 19: // cmp regA, regB  => flags from regA - regB
		b := c.fetchByte()
		regA := (b >> 4) & 0x0F
		regB := b & 0x0F
		a := c.reg(regA)
		bv := c.reg(regB)
		result := a - bv
		carry := a < bv
		if c.trace {
			fmt.Printf("    %s(0x%02x)-%s(0x%02x) -> flags", regName(regA), a, regName(regB), bv)
		}
		c.flags = setFlags(result, a, bv, carry)

	case 20: // rs regRes, regA, regB  => regRes = regA >> regB
		b := c.fetchByte()
		regB := (b >> 4) & 0x0F
		regA := b & 0x0F
		regRes := c.fetchByte()
		a := c.reg(regA)
		bv := c.reg(regB)
		result := a >> bv
		if c.trace {
			fmt.Printf("    %s>>%s -> %s(0x%02x)", regName(regA), regName(regB), regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, bv, false)

	case 21: // ls regRes, regA, regB  => regRes = regA << regB
		b := c.fetchByte()
		regB := (b >> 4) & 0x0F
		regA := b & 0x0F
		regRes := c.fetchByte()
		a := c.reg(regA)
		bv := c.reg(regB)
		result := a << bv
		if c.trace {
			fmt.Printf("    %s<<%s -> %s(0x%02x)", regName(regA), regName(regB), regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, bv, false)

	case 22: // rr regRes, regA, regB  => regRes = rotate_right(regA, regB)
		b := c.fetchByte()
		regB := (b >> 4) & 0x0F
		regA := b & 0x0F
		regRes := c.fetchByte()
		a := c.reg(regA)
		bv := c.reg(regB) & 0x07
		if bv == 0 {
			bv = 8
		}
		result := (a >> bv) | (a << (8 - bv))
		if c.trace {
			fmt.Printf("    rotR(%s,%s) -> %s(0x%02x)", regName(regA), regName(regB), regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, bv, false)

	case 23: // lr regRes, regA, regB  => regRes = rotate_left(regA, regB)
		b := c.fetchByte()
		regB := (b >> 4) & 0x0F
		regA := b & 0x0F
		regRes := c.fetchByte()
		a := c.reg(regA)
		bv := c.reg(regB) & 0x07
		if bv == 0 {
			bv = 8
		}
		result := (a << bv) | (a >> (8 - bv))
		if c.trace {
			fmt.Printf("    rotL(%s,%s) -> %s(0x%02x)", regName(regA), regName(regB), regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, bv, false)

	case 24: // ars regRes, regA, regB  => arithmetic right shift
		b := c.fetchByte()
		regB := (b >> 4) & 0x0F
		regA := b & 0x0F
		regRes := c.fetchByte()
		a := c.reg(regA)
		bv := c.reg(regB)
		if bv >= 8 {
			bv = 7
		}
		msb := a & 0x80
		result := (a >> bv) | (0xFF << (8 - bv))
		if msb == 0 {
			result &^= (0xFF << (8 - bv))
		}
		if c.trace {
			fmt.Printf("    arithR(%s,%s) -> %s(0x%02x)", regName(regA), regName(regB), regName(regRes), result)
		}
		c.regs[regRes] = result
		c.flags = setFlags(result, a, bv, false)

	case 25: // mv regA, regB  => regB = regA
		b := c.fetchByte()
		regA := (b >> 4) & 0x0F
		regB := b & 0x0F
		val := c.reg(regA)
		if c.trace {
			fmt.Printf("    %s(0x%02x) -> %s", regName(regA), val, regName(regB))
		}
		c.regs[regB] = val

	case 26: // ld regA, addr16  => regA = dataMem[addr]
		regA := c.fetchByte()
		addr := c.fetchWord()
		val := c.dataMem[addr]
		if c.trace {
			fmt.Printf("    [0x%04x]=0x%02x -> %s", addr, val, regName(regA))
		}
		c.regs[regA] = val

	case 27: // ldi regA, imm  => regA = imm
		regA := c.fetchByte()
		imm := c.fetchByte()
		if c.trace {
			fmt.Printf("    0x%02x -> %s", imm, regName(regA))
		}
		c.regs[regA] = imm

	case 28: // st addr16, reg  => dataMem[addr] = reg
		reg := c.fetchByte()
		addr := c.fetchWord()
		val := c.reg(reg)
		if c.trace {
			fmt.Printf("    %s(0x%02x) -> [0x%04x]", regName(reg), val, addr)
		}
		c.dataMem[addr] = val

	case 29: // sti addr16, imm  => dataMem[addr] = imm
		addr := c.fetchWord()
		imm := c.fetchByte()
		if c.trace {
			fmt.Printf("    0x%02x -> [0x%04x]", imm, addr)
		}
		c.dataMem[addr] = imm

	case 30: // lin regSI/DI, addr16  => SI/DI = addr
		regIdx := c.fetchByte()
		addr := c.fetchWord()
		if regIdx == 1 || regIdx == 8 {
			c.si = addr
			if c.trace {
				fmt.Printf("    addr=0x%04x -> SI", addr)
			}
		} else if regIdx == 2 || regIdx == 9 {
			c.di = addr
			if c.trace {
				fmt.Printf("    addr=0x%04x -> DI", addr)
			}
		}

	case 31: // sin regSI/DI, addr16  => dataMem[addr] = dataMem[SI/DI]
		regIdx := c.fetchByte()
		addr := c.fetchWord()
		var src uint16
		if regIdx == 1 || regIdx == 8 {
			src = c.si
		} else if regIdx == 2 || regIdx == 9 {
			src = c.di
		}
		val := c.dataMem[src]
		c.dataMem[addr] = val
		if c.trace {
			fmt.Printf("    dataMem[SI/DI=0x%04x]=0x%02x -> [0x%04x]", src, val, addr)
		}

	case 32: // rin regA, regB, targetIdx  => SI/DI = regA | (regB << 8)
		b := c.fetchByte()
		regA := (b >> 4) & 0x0F
		regB := b & 0x0F
		targetIdx := c.fetchByte()
		val := uint16(c.reg(regA)) | (uint16(c.reg(regB)) << 8)
		if targetIdx == 1 || targetIdx == 8 {
			c.si = val
			if c.trace {
				fmt.Printf("    %s|%s<<8 -> SI=%04x", regName(regA), regName(regB), c.si)
			}
		} else if targetIdx == 2 || targetIdx == 9 {
			c.di = val
			if c.trace {
				fmt.Printf("    %s|%s<<8 -> DI=%04x", regName(regA), regName(regB), c.di)
			}
		}

	case 33: // rpc regA, regB  => PC = regA | (regB << 8)
		b := c.fetchByte()
		regA := (b >> 4) & 0x0F
		regB := b & 0x0F
		c.pc = uint16(c.reg(regA)) | (uint16(c.reg(regB)) << 8)
		if c.trace {
			fmt.Printf("    %s|%s<<8 -> PC=%04x", regName(regA), regName(regB), c.pc)
		}

	case 34: // rsp regA, regB  => SP = regA | (regB << 8)
		b := c.fetchByte()
		regA := (b >> 4) & 0x0F
		regB := b & 0x0F
		c.sp = uint16(c.reg(regA)) | (uint16(c.reg(regB)) << 8)
		if c.trace {
			fmt.Printf("    %s|%s<<8 -> SP=%04x", regName(regA), regName(regB), c.sp)
		}

	case 35: // con flagBit  => canBranch = (flagBit==0) || (flags & (1<<flagBit))
		flagBit := c.fetchByte()
		if flagBit == 0 {
			c.canBranch = true
		} else {
			c.canBranch = (c.flags & (1 << flagBit)) != 0
		}
		if c.trace {
			if flagBit == 0 {
				fmt.Printf("    always -> canBranch=%v", c.canBranch)
			} else {
				fmt.Printf("    flagBit=%d, flags=0x%02x -> canBranch=%v", flagBit, c.flags, c.canBranch)
			}
		}

	case 36: // cor flagMask  => canBranch = (flags & mask) != 0
		mask := c.fetchByte()
		c.canBranch = (c.flags & mask) != 0
		if c.trace {
			fmt.Printf("    mask=0x%02x, flags=0x%02x -> canBranch=%v", mask, c.flags, c.canBranch)
		}

	case 37: // can flagMask  => canBranch = (flags & mask) == mask
		mask := c.fetchByte()
		c.canBranch = (c.flags & mask) == mask
		if c.trace {
			fmt.Printf("    mask=0x%02x, flags=0x%02x -> canBranch=%v", mask, c.flags, c.canBranch)
		}

	case 38: // jmp addr16  => if canBranch { PC = addr }; canBranch = true
		addr := c.fetchWord()
		wasBranch := c.canBranch
		if c.canBranch {
			c.pc = addr
		}
		c.canBranch = true
		if c.trace {
			if wasBranch {
				fmt.Printf("    addr=0x%04x -> JUMPED", addr)
			} else {
				fmt.Printf("    addr=0x%04x -> SKIPPED", addr)
			}
		}

	case 39: // set flagMask  => flags |= mask
		mask := c.fetchByte()
		c.flags |= mask
		if c.trace {
			fmt.Printf("    flags|=0x%02x -> flags=0x%02x", mask, c.flags)
		}

	case 40: // lsx regA  => regA = dataMem[SI]
		regA := c.fetchByte()
		val := c.dataMem[c.si]
		if c.trace {
			fmt.Printf("    dataMem[SI=0x%04x]=0x%02x -> %s", c.si, val, regName(regA))
		}
		c.regs[regA] = val

	case 41: // ldx regA  => regA = dataMem[DI]
		regA := c.fetchByte()
		val := c.dataMem[c.di]
		if c.trace {
			fmt.Printf("    dataMem[DI=0x%04x]=0x%02x -> %s", c.di, val, regName(regA))
		}
		c.regs[regA] = val

	case 42: // ssx regA  => dataMem[SI] = regA
		regA := c.fetchByte()
		val := c.reg(regA)
		if c.trace {
			fmt.Printf("    %s(0x%02x) -> dataMem[SI=0x%04x]", regName(regA), val, c.si)
		}
		c.dataMem[c.si] = val

	case 43: // sdx regA  => dataMem[DI] = regA
		regA := c.fetchByte()
		val := c.reg(regA)
		if c.trace {
			fmt.Printf("    %s(0x%02x) -> dataMem[DI=0x%04x]", regName(regA), val, c.di)
		}
		c.dataMem[c.di] = val

	default:
		if c.trace {
			fmt.Printf("    UNKNOWN OPCODE 0x%02x", opcode)
		}
	}
}
