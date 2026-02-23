package main

import (
	"fmt"
	"strings"
)

// =-=-=-=-=-=-=[DEFINE NECESSARY THINGS]=-=-=-=-=-=-

// flags struct
type Flags uint8

const (
	// [S|-|OV|C|AC|-|P|Z]
	// wait is the flags set to 1 when it is initialised?
	Zero      Flags = 1 << iota // bit 0 == Zero flag
	Parity                      // bit 1
	Halted                      // bit 2
	AuxCarry                    // bit 3
	Carry                       // bit 4
	Overflow                    // bit 5
	reserved2                   // bit 6
	Sign                        // bit 7
)

func HandleFlags(f *Flags, a, b, result byte) {
	*f = 0 // Reset flags to 0 before calculating new state
	if result == 0 {
		*f |= Zero
	} // Zero Flag (Z): Result is 0

	if result&0x80 != 0 {
		*f |= Sign
	} // Sign Flag (S): Bit 7 is set (negative in two's complement)

	if uint16(a)+uint16(b) > 0xFF {
		*f |= Carry
	} // Carry Flag (C): Unsigned overflow (sum > 255)

	if (a&0x0F)+(b&0x0F) > 0x0F {
		*f |= AuxCarry
	} // Auxiliary Carry (AC): Carry from bit 3 to bit 4 (nibble carry)

	p := result
	p ^= p >> 4
	p ^= p >> 2
	p ^= p >> 1
	if (p & 1) == 0 {
		*f |= Parity
	} // Parity Flag (P): Set if the number of set bits is even

	// Logic: If both inputs have the same sign, but the result has a different sign
	if ((a ^ result) & (b ^ result) & 0x80) != 0 {
		*f |= Overflow
	} // Overflow Flag (OV): Signed overflow
}

func (f Flags) GetFlag(index int) bool {
	return (f & (1 << index)) != 0
}

func (f *Flags) SetFlag(index int, value bool) {
	if value {
		*f |= (1 << index)
	} else {
		*f &^= (1 << index)
	}
}

func (s Flags) String() string {
	if s == 0 {
		return "None"
	}

	var names []string

	if s&Zero != 0 {
		names = append(names, "Zero")
	}
	if s&Parity != 0 {
		names = append(names, "Parity")
	}
	if s&Halted != 0 {
		names = append(names, "Halted")
	}
	if s&AuxCarry != 0 {
		names = append(names, "AuxCarry")
	}
	if s&Carry != 0 {
		names = append(names, "Carry")
	}
	if s&Overflow != 0 {
		names = append(names, "Overflow")
	}
	if s&reserved2 != 0 {
		names = append(names, "reserved2")
	}
	if s&Sign != 0 {
		names = append(names, "Sign")
	}

	return strings.Join(names, "|")
}

// =-=-=-=-=-=-=[INITIALIZE]=-=-=-=-=-=-

// OpData holds the decoded operands to avoid map[string]interface{}
type OpData struct {
	A    byte   // Register Index A
	B    byte   // Register Index B
	Res  byte   // Result Register Index
	Imm  byte   // Immediate Value
	Addr uint16 // Address
}

// main processor struct
type Ra8 struct {
	// General purpose registers
	A, B, C, D, E, F, G, H byte `json:"gp_registers"`

	Temph, Templ byte `json:"temp_registers"`

	//NOTE: temph and templ are multiplexers that feed high and low bytes
	//        of pc to databus used in place of registers
	//        edit: me from the future no thise are special registers now that work just like
	//        regular rgisters but cannot be used to perfom ALU operations

	// Special purpose registers
	ProgramCounter   uint16 `json:"program_counter"`
	StackPointer     uint16 `json:"stack_pointer"`
	SourceIndex      uint16 `json:"source_index"`
	DestinationIndex uint16 `json:"destination_index"`
	ReturnRegister   uint16 `json:"return_register"`
	StatusWord       Flags  `json:"status_word"`

	// Memory arrays
	InstructionMemory [0xffff]byte `json:"instruction_memory"`
	DataMemory        [0xffff]byte `json:"data_memory"`

	// Pipeline registers
	InstructionRegister byte `json:"instruction_register"`
	PipelineReg1        byte `json:"pipeline_reg_1"`
	PipelineReg2        byte `json:"pipeline_reg_2"`
	PipelineReg3        byte `json:"pipeline_reg_3"`
	opcode              int  // internal field for decoded opcode
	isHalted            int  // internal field for decoded opcode
	isBranching         int  // internal field for branch instruction flag
	canBranch           int  // internal field for branch instruction flag
}

// some kind of constructor or something that initializes it
func NewRa8() Ra8 {
	return Ra8{
		StackPointer: 0xFFFF, // Stack starts at top of memory
	}
}

// =-=-=-=-=-=-=[EXECUTION CYCLE]=-=-=-=-=-=-

// NOTE: in this single step method, the fetch decode and execute cycle programs here do not implement
// their movement in the pipeline, as ILP is only necessary when implementing in
// hardware and im lazy to implement in the emulator, its useless anyways
func (p *Ra8) Step() int {
	//composition of a single execution cycle
	// Fixed syntax: Check if Halted bit is NOT set
	if p.StatusWord&Halted == 0 {
		p.Fetch()
		p.Decode()
		p.Execute()
		return 0 // Running
	} else {
		return 1 // satus code to check if the processor halted
	}
}

// make sure you do the ProgramCounter increment
func (p *Ra8) Fetch() {
	p.InstructionRegister = p.InstructionMemory[p.ProgramCounter]
	p.ProgramCounter += 1
}

func (p *Ra8) Decode() {
	// 11000000 - mask to get the number of immediate bytes
	// 00000001 - mask to check if the instruction is a branching type
	// 00111110 - mask get the opcode

	numImm := p.InstructionRegister & 0b11000000            // Extract bits 7-6
	p.opcode = int(p.InstructionRegister & 0b00011111)      // Extract bits 5-1 (OPCODE)
	p.isBranching = int(p.InstructionRegister & 0b00100000) // see if its a branching instruction (Fixed mask to bit 5)

	//TODO: refactor this hardcoded thing if you want to
	switch numImm >> 6 { // Shifted to match 0, 1, 2, 3 cases
	case 0:
		// do nothing

	case 1:
		p.PipelineReg1 = p.InstructionMemory[p.ProgramCounter]
		p.ProgramCounter++

	case 2:
		p.PipelineReg1 = p.InstructionMemory[p.ProgramCounter]
		p.PipelineReg2 = p.InstructionMemory[p.ProgramCounter+1]
		p.ProgramCounter += 2

	case 3:
		p.PipelineReg1 = p.InstructionMemory[p.ProgramCounter]
		p.PipelineReg2 = p.InstructionMemory[p.ProgramCounter+1]
		p.PipelineReg3 = p.InstructionMemory[p.ProgramCounter+2]
		p.ProgramCounter += 3

	default:
		// Shifted mask handles this, but keep print just in case
		fmt.Println("owned by skill issue; invalid number of immediate bytes")
	}
}

// TODO: make a proper instruction set table and proceed
//  instructions that i skipped from implementing:
// 		neg, lin, sin, lnr{instructions to load index register using a register pair}
//      str, ldr??

func (p *Ra8) Execute() {
	// Switch is cleaner than if-else chain
	switch p.opcode {
	// CONTROL INSTRUCTIONS
	case 0:
		// NOPE instruction

	case 1:
		// HALT instruction
		p.isHalted = 1
		p.StatusWord |= Halted

	// ARITHMETIC INSTRUCTIONS
	case 2:
		// ADD instruction
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := a_val + b_val
		p.SetRegVal(operands.Res, result)
		HandleFlags(&p.StatusWord, a_val, b_val, result)

	case 3:
		// ADI instruction
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		result := a_val + imm_val
		p.SetRegVal(operands.Res, result)
		HandleFlags(&p.StatusWord, a_val, imm_val, result)

	case 4:
		// ADC instruction
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := a_val + b_val + 1
		p.SetRegVal(operands.Res, result)
		HandleFlags(&p.StatusWord, a_val, b_val, result)

	case 5:
		// SUB instruction
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := a_val - b_val
		p.SetRegVal(operands.Res, result)
		HandleFlags(&p.StatusWord, a_val, b_val, result)

	case 6:
		// SUI instruction
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		result := a_val - imm_val
		p.SetRegVal(operands.Res, result)
		HandleFlags(&p.StatusWord, a_val, imm_val, result)

	case 7:
		// SBB instruction
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := a_val - b_val - 1
		p.SetRegVal(operands.Res, result)
		HandleFlags(&p.StatusWord, a_val, b_val, result)

		// NOTE: should I instead use subroutines for mul and div instructions??? idk
	case 8:
		// MUL instruction
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := (uint16(a_val) * uint16(b_val)) & 0x00ff
		p.SetRegVal(operands.Res, byte(result))
		HandleFlags(&p.StatusWord, a_val, b_val, byte(result))

	case 9:
		// MUH instruction
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := (uint16(a_val) * uint16(b_val)) & 0xff00
		p.SetRegVal(operands.Res, byte(result>>8))
		HandleFlags(&p.StatusWord, a_val, b_val, byte(result>>8))

	case 10:
		// MIL instruction
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		result := (uint16(a_val) * uint16(imm_val)) & 0x00ff
		p.SetRegVal(operands.Res, byte(result))
		HandleFlags(&p.StatusWord, a_val, imm_val, byte(result))

	case 11:
		// MIH instruction
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		result := (uint16(a_val) * uint16(imm_val)) & 0xff
		p.SetRegVal(operands.Res, byte(result))
		HandleFlags(&p.StatusWord, a_val, imm_val, byte(result))

	case 12:
		// DIV instruction
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		if b_val != 0 {
			result := (a_val / b_val) & 0xff
			p.SetRegVal(operands.Res, result)
			HandleFlags(&p.StatusWord, a_val, b_val, result)
		}

	case 13:
		// DII instruction
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		if imm_val != 0 {
			result := (uint16(a_val) / uint16(imm_val)) & 0xff00
			p.SetRegVal(operands.Res, byte(result>>8))
			HandleFlags(&p.StatusWord, a_val, imm_val, byte(result>>8))
		}

	case 14:
		// REM instruction
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		if b_val != 0 {
			result := (a_val % b_val) & 0xff
			p.SetRegVal(operands.Res, result)
			HandleFlags(&p.StatusWord, a_val, b_val, result)
		}

	case 15:
		// REI instruction
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		if imm_val != 0 {
			result := (a_val % imm_val) & 0xff
			p.SetRegVal(operands.Res, result)
			HandleFlags(&p.StatusWord, a_val, imm_val, result)
		}
		// NEG instruction here

	// LOGICAL INSTRUCTIONS
	case 16:
		// AND instruction
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := a_val & b_val
		p.SetRegVal(operands.Res, result)

	case 17:
		// ANI instruction
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		result := a_val & imm_val
		p.SetRegVal(operands.Res, result)

	case 18:
		// OR instruction
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := a_val | b_val
		p.SetRegVal(operands.Res, result)

	case 19:
		// ORI instruction
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		result := a_val | imm_val
		p.SetRegVal(operands.Res, result)

	case 20:
		// NOT instruction
		operands := p.getOperands(3)
		a_val := p.GetRegVal(operands.A)
		result := ^a_val
		p.SetRegVal(operands.Res, result)

	case 21:
		// NOI instruction
		operands := p.getOperands(4)
		imm_val := operands.Imm
		result := ^imm_val
		p.SetRegVal(operands.Res, result)

	case 22:
		// XOR instruction
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := a_val ^ b_val
		p.SetRegVal(operands.Res, result)

	case 23:
		// XRI instruction
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		result := a_val ^ imm_val
		p.SetRegVal(operands.Res, result)

	// BITWISE INSTRUCTIONS
	case 24:
		// RS instruction
		operands := p.getOperands(3)
		a_val := p.GetRegVal(operands.A)
		result := a_val >> 1
		p.SetRegVal(operands.Res, result)

	case 25:
		// LS instruction
		operands := p.getOperands(3)
		a_val := p.GetRegVal(operands.A)
		result := a_val << 1
		p.SetRegVal(operands.Res, result)

	case 26:
		// RR instruction
		operands := p.getOperands(3)
		a_val := p.GetRegVal(operands.A)
		result := ((a_val >> 1) | (a_val << 7)) & 0xff
		p.SetRegVal(operands.Res, result)

	case 27:
		// LR instruction
		operands := p.getOperands(3)
		a_val := p.GetRegVal(operands.A)
		result := ((a_val << 1) | (a_val >> 7)) & 0xff
		p.SetRegVal(operands.Res, result)

	case 28:
		// ARS instruction
		operands := p.getOperands(3)
		a_val := p.GetRegVal(operands.A)
		msb := a_val & 0x80
		lower7bits := a_val & 0x7f
		val := (lower7bits >> 1) & 0x7f
		result := msb | val
		p.SetRegVal(operands.Res, result)

	// MEM INSTRUCTIONS
	case 29:
		// MV instruction A <= B
		operands := p.getOperands(5)
		p.SetRegVal(operands.B, p.GetRegVal(operands.A))

	case 30:
		// LD instruction A <= Value in memory location
		operands := p.getOperands(6)
		p.SetRegVal(operands.A, p.DataMemory[operands.Addr])

	case 31:
		// LDI instruction A <= Immediate value
		operands := p.getOperands(2)
		p.SetRegVal(operands.Res, operands.Imm)

	case 32:
		// ST instruction: memory location <= Value in register A
		operands := p.getOperands(7)
		p.DataMemory[operands.Addr] = p.GetRegVal(operands.A)

	case 33:
		// STI instruction: memory location <= Immediate value
		operands := p.getOperands(7)
		p.DataMemory[operands.Addr] = operands.Imm

	case 34:
		// IIN  instruction: increment index
		operands := p.getOperands(8)
		switch operands.A {
		case 1:
			p.SourceIndex++
		case 2:
			p.DestinationIndex++
		}

	case 35:
		// DIN  instruction: memory location <= Immediate value
		operands := p.getOperands(8)
		switch operands.A {
		case 1:
			p.SourceIndex--
		case 2:
			p.DestinationIndex--
		}

	// BRANCHING INSTRUCTIONS
	// condition check
	case 36:
		// CON  instruction: basic Branch if, condition check
		operands := p.getOperands(8)
		if p.StatusWord.GetFlag(int(operands.A)) {
			p.canBranch = 1
		}

	case 37:
		// COR  instruction: Branch if any, condition check
		operands := p.getOperands(8)
		if (byte(p.StatusWord) & operands.A) == operands.A {
			p.canBranch = 1
		}

	case 38:
		// CAN  instruction: Branch if all, condition check
		operands := p.getOperands(8)
		if (byte(p.StatusWord) & operands.A) == operands.A {
			p.canBranch = 1
		}

	// branching
	case 39:
		// JMP  instruction: jump to addr, condition check
		operands := p.getOperands(8)
		if p.canBranch == 0 {
			p.ProgramCounter = operand.addr
		}

	// STACK OPERATIONS
	case 40:
		// PUSH  instruction: Branch if all, condition check
		operands := p.getOperands(8)
		p.Stack_Push(p.GetRegVal(operands.A))

	case 41:
		// POP  instruction: Branch if all, condition check
		p.SetRegVal(p.Stack_Pop())

	default:
		// xx instruction
		fmt.Println("Owned by skill issue, invalid opcode bro")
	}
}

// =-=-=-=-=-=-=[HELPERS]=-=-=-=-=-=-
// INFO: getOperands
// Legend:
//   Reg A  = Source Register A
//   Reg B  = Source Register B
//   Reg Res= Destination Register (Result)
//   Imm8   = 8-bit Immediate Value
//   Addr16 = 16-bit Memory Address
// Types: there is a way to reduce these types, but im gonna make this easy for me ok
//   type 1 => Reg A, Reg B, Reg Res   (Three Registers)
//   type 2 => Reg A, Reg Res, Imm8    (Two Registers + Immediate)
//   type 3 => Reg A, Reg Res          (Two Registers - Src/Dest)
//   type 4 => Imm8                    (One Immediate - stored in Imm)
//   type 5 => Reg A, Reg B            (Two Registers - Src/Src)
//   type 6 => Reg A, Addr16           (One Register + Address)
//   type 7 => Imm8, Addr16            (One Immediate + Address)
//   type 8 => Reg A                   (Single Register / Special Reg)
//   type 9 => Addr16                  (Single Address - Jumps/Calls)

func (p *Ra8) getOperands(instructionType int) OpData {
	var result OpData

	switch instructionType {
	case 1:
		// opcode xx ------
		// pipeline reg 1: a4 b4
		// pipeline reg 2: ---- res4
		result.A = p.PipelineReg1 & 0x07
		result.B = (p.PipelineReg1 >> 4) & 0x07
		result.Res = p.PipelineReg2 & 0x07

	case 2:
		// opcode xx ------
		// pipeline reg 1: res4 a4
		// pipeline reg 2: immediate8
		result.A = p.PipelineReg1 & 0x07
		result.Res = (p.PipelineReg1 >> 4) & 0x07
		result.Imm = p.PipelineReg2

	case 3:
		// opcode xx ------
		// pipeline reg 1: res4 a4
		result.A = p.PipelineReg1 & 0x07
		result.Res = (p.PipelineReg1 >> 4) & 0x07

	case 4:
		// opcode xx ------
		// pipeline reg 1: immediate8
		result.Imm = p.PipelineReg1

	case 5:
		// opcode xx ------
		// pipeline reg 1: a4 b4
		result.A = p.PipelineReg1 & 0x07
		result.B = (p.PipelineReg1 >> 4) & 0x07

	case 6:
		// opcode xx ------
		// pipeline reg 1: ---- a4
		// pipeline reg 2: Addr high byte
		// pipeline reg 3: Addr low byte
		result.A = p.PipelineReg1 & 0x07
		result.Addr = (uint16(p.PipelineReg2) << 8) | uint16(p.PipelineReg3)

	case 7:
		// opcode xx ------
		// pipeline reg 1: immediate8
		// pipeline reg 2: Addr high byte
		// pipeline reg 3: Addr low byte
		result.A = p.PipelineReg1
		result.Addr = (uint16(p.PipelineReg2) << 8) | uint16(p.PipelineReg3)

	case 8:
		// opcode xx ------
		// pipeline reg 1: ---- srA4 sprcial register index??? idk bro
		result.A = p.PipelineReg1 & 0x07

	case 9:
		// opcode xx ------
		// pipeline reg 1: Addr high byte
		// pipeline reg 2: Addr low byte
		result.Addr = (uint16(p.PipelineReg1) << 8) | uint16(p.PipelineReg2)
	default:
		fmt.Println("Owned by skill issue")
	}

	return result
}

// get pointerss to register
func (p *Ra8) regPointer() []*byte {
	return []*byte{
		&p.A, &p.B, &p.C, &p.D,
		&p.E, &p.F, &p.G, &p.H,
	}
}

// Get register value by index
func (p *Ra8) GetRegVal(index byte) byte {
	idx := int(index)
	if idx < 0 || idx > 7 {
		panic("Owned by skill issue, Invalid register index")
	}
	return *p.regPointer()[idx]
}

// Set register value by index
func (p *Ra8) SetRegVal(index byte, value byte) {
	idx := int(index)
	if idx < 0 || idx > 7 {
		panic("Owned by skill issue, Invalid register index")
	}
	*p.regPointer()[idx] = value
}

func (p *Ra8) Stack_Push(val byte) {
	p.StackPointer--
	if p.StackPointer >= 0xFFFF {
		panic("Owned by skill issue, Stack Overflow or Invalid Address!")
	}
	p.DataMemory[p.StackPointer] = val
}

func (p *Ra8) Stack_Pop() byte {
	if p.StackPointer >= 0xFFFF {
		panic("Owned by skill issue, Underflow! Cannot pop from empty stack.")
	}
	val := p.DataMemory[p.StackPointer]
	p.StackPointer++
	return val
}
