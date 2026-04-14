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
	// General purpose registers (indices 0-7)
	A, B, C, D, E, F, G, H byte `json:"gp_registers"`

	// Special registers (indices 8-12)
	Si    byte `json:"si"`  // Source Index (8)
	Di    byte `json:"di"`  // Destination Index (9)
	Rng   byte `json:"rng"` // Random number (10)
	Temph byte `json:"th"`  // Temp High (11)
	Templ byte `json:"tl"`  // Temp Low (12)

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
func NewRa8() *Ra8 {
	return &Ra8{
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
	numImm := p.InstructionRegister & 0b11000000
	p.opcode = int(p.InstructionRegister & 0b00111111)
	p.isBranching = int(p.InstructionRegister & 0b00100000)

	switch numImm >> 6 {
	case 0:
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
	}
}

// TODO: make a proper instruction set table and proceed
//  instructions that i skipped from implementing:
// 		neg, lin, sin, lnr{instructions to load index register using a register pair}
//      str, ldr??

func (p *Ra8) Execute() {
	switch p.opcode {
	case 0:
		// NOPE instruction - no operation

	case 1:
		// HLT instruction
		p.isHalted = 1
		p.StatusWord |= Halted

	case 2:
		// ADD instruction (3 registers: dest = srcA + srcB)
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := a_val + b_val
		p.SetRegVal(operands.Res, result)
		HandleFlags(&p.StatusWord, a_val, b_val, result)

	case 3:
		// ADI instruction (2 registers + immediate: dest = src + imm)
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		result := a_val + imm_val
		p.SetRegVal(operands.Res, result)
		HandleFlags(&p.StatusWord, a_val, imm_val, result)

	case 4:
		// ADDC instruction (add with carry)
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		carry := byte(0)
		if p.StatusWord.GetFlag(4) {
			carry = 1
		}
		result := a_val + b_val + carry
		p.SetRegVal(operands.Res, result)
		HandleFlags(&p.StatusWord, a_val, b_val, result)

	case 5:
		// SUB instruction (dest = srcA - srcB)
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := a_val - b_val
		p.SetRegVal(operands.Res, result)
		HandleFlags(&p.StatusWord, a_val, b_val, result)

	case 6:
		// SUI instruction (dest = src - immediate)
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		result := a_val - imm_val
		p.SetRegVal(operands.Res, result)
		HandleFlags(&p.StatusWord, a_val, imm_val, result)

	case 7:
		// SUBB instruction (subtract with borrow)
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		borrow := byte(0)
		if p.StatusWord.GetFlag(4) {
			borrow = 1
		}
		result := a_val - b_val - borrow
		p.SetRegVal(operands.Res, result)
		HandleFlags(&p.StatusWord, a_val, b_val, result)

	case 8:
		// AND instruction (dest = srcA & srcB)
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := a_val & b_val
		p.SetRegVal(operands.Res, result)

	case 9:
		// ANI instruction (dest = src & immediate)
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		result := a_val & imm_val
		p.SetRegVal(operands.Res, result)

	case 10:
		// OR instruction (dest = srcA | srcB)
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := a_val | b_val
		p.SetRegVal(operands.Res, result)

	case 11:
		// ORI instruction (dest = src | immediate)
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		result := a_val | imm_val
		p.SetRegVal(operands.Res, result)

	case 12:
		// NOT instruction (dest = ~src) - 2-byte: opcode + (dest << 4 | src)
		operands := p.getOperands(5)
		a_val := p.GetRegVal(operands.A)
		result := ^a_val
		p.SetRegVal(operands.B, result)

	case 13:
		// XOR instruction (dest = srcA ^ srcB)
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := a_val ^ b_val
		p.SetRegVal(operands.Res, result)

	case 14:
		// XRI instruction (dest = src ^ immediate)
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		result := a_val ^ imm_val
		p.SetRegVal(operands.Res, result)

	case 15:
		// XNR (XNOR) instruction (dest = ~(srcA ^ srcB))
		operands := p.getOperands(1)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := ^(a_val ^ b_val)
		p.SetRegVal(operands.Res, result)

	case 16:
		// XNI instruction (dest = ~(src ^ immediate))
		operands := p.getOperands(2)
		a_val := p.GetRegVal(operands.A)
		imm_val := operands.Imm
		result := ^(a_val ^ imm_val)
		p.SetRegVal(operands.Res, result)

	case 17:
		// IIN instruction (increment index)
		operands := p.getOperands(8)
		if operands.A == 1 {
			p.SourceIndex++
		} else if operands.A == 2 {
			p.DestinationIndex++
		}

	case 18:
		// DIN instruction (decrement index)
		operands := p.getOperands(8)
		if operands.A == 1 {
			p.SourceIndex--
		} else if operands.A == 2 {
			p.DestinationIndex--
		}

	case 19:
		// CMP instruction (compare: set flags based on srcA - srcB)
		operands := p.getOperands(5)
		a_val := p.GetRegVal(operands.A)
		b_val := p.GetRegVal(operands.B)
		result := a_val - b_val
		HandleFlags(&p.StatusWord, a_val, b_val, result)

	case 20:
		// RS instruction (right shift: dest = src >> 1)
		operands := p.getOperands(5)
		a_val := p.GetRegVal(operands.A)
		result := a_val >> 1
		p.SetRegVal(operands.B, result)

	case 21:
		// LS instruction (left shift: dest = src << 1)
		operands := p.getOperands(5)
		a_val := p.GetRegVal(operands.A)
		result := a_val << 1
		p.SetRegVal(operands.B, result)

	case 22:
		// RR instruction (rotate right)
		operands := p.getOperands(5)
		a_val := p.GetRegVal(operands.A)
		result := ((a_val >> 1) | (a_val << 7)) & 0xff
		p.SetRegVal(operands.B, result)

	case 23:
		// LR instruction (rotate left)
		operands := p.getOperands(5)
		a_val := p.GetRegVal(operands.A)
		result := ((a_val << 1) | (a_val >> 7)) & 0xff
		p.SetRegVal(operands.B, result)

	case 24:
		// ARS instruction (arithmetic right shift - preserve sign bit)
		operands := p.getOperands(5)
		a_val := p.GetRegVal(operands.A)
		msb := a_val & 0x80
		result := msb | (a_val >> 1)
		p.SetRegVal(operands.B, result)

	case 25:
		// MV instruction (A <= B)
		operands := p.getOperands(5)
		p.SetRegVal(operands.B, p.GetRegVal(operands.A))

	case 26:
		// LD instruction (A <= memory[address])
		operands := p.getOperands(6)
		p.SetRegVal(operands.A, p.DataMemory[operands.Addr])

	case 27:
		// LDI instruction (reg <= immediate) - assembler encodes as (dest << 4) | dest
		// So PipelineReg1 = dest register index
		dest := p.PipelineReg1 & 0x0F
		p.SetRegVal(dest, p.PipelineReg2)

	case 28:
		// ST instruction (memory[address] <= A)
		operands := p.getOperands(6)
		p.DataMemory[operands.Addr] = p.GetRegVal(operands.A)

	case 29:
		// STI instruction (memory[address] <= immediate)
		operands := p.getOperands(7)
		p.DataMemory[operands.Addr] = operands.Imm

	case 30:
		// LIN instruction (load index register from reg pair)
		operands := p.getOperands(8)
		if operands.A == 1 {
			p.SourceIndex = (uint16(p.G) << 8) | uint16(p.H)
		} else if operands.A == 2 {
			p.DestinationIndex = (uint16(p.G) << 8) | uint16(p.H)
		}

	case 31:
		// SIN instruction (store index register to reg pair)
		operands := p.getOperands(8)
		if operands.A == 1 {
			p.G = byte(p.SourceIndex >> 8)
			p.H = byte(p.SourceIndex & 0xFF)
		} else if operands.A == 2 {
			p.G = byte(p.DestinationIndex >> 8)
			p.H = byte(p.DestinationIndex & 0xFF)
		}

	case 32:
		// RIN instruction (load index reg from reg pair - 3 registers)
		operands := p.getOperands(1)
		if operands.B == 1 {
			p.SourceIndex = (uint16(p.G) << 8) | uint16(p.H)
		} else if operands.B == 2 {
			p.DestinationIndex = (uint16(p.G) << 8) | uint16(p.H)
		}

	case 33:
		// RPC instruction (register pair to PC)
		operands := p.getOperands(5)
		if operands.B == 1 {
			p.ProgramCounter = (uint16(p.G) << 8) | uint16(p.H)
		} else if operands.B == 2 {
			p.ProgramCounter = p.ReturnRegister
		}

	case 34:
		// RSP instruction (register pair to SP)
		operands := p.getOperands(5)
		if operands.B == 1 {
			p.StackPointer = (uint16(p.G) << 8) | uint16(p.H)
		} else if operands.B == 2 {
			p.StackPointer = 0xFFFF
		}

	case 35:
		// CON - condition check with mask
		// CON 0 = unconditional (always branch)
		// CON <mask> = branch if ALL flags in mask are set
		operands := p.getOperands(8)
		if operands.A == 0 || (byte(p.StatusWord)&operands.A) == operands.A {
			p.canBranch = 1
		}

	case 36:
		// COR instruction (check if any flag in mask is set)
		operands := p.getOperands(8)
		if (byte(p.StatusWord) & operands.A) != 0 {
			p.canBranch = 1
		}

	case 37:
		// CAN instruction (check if all flags in mask are set)
		operands := p.getOperands(8)
		if (byte(p.StatusWord) & operands.A) == operands.A {
			p.canBranch = 1
		}

	case 38:
		// JMP instruction (jump to address if canBranch is set)
		operands := p.getOperands(9)
		if p.canBranch == 1 {
			p.ProgramCounter = operands.Addr
		}

	case 39:
		// SET instruction (set flag)
		operands := p.getOperands(8)
		p.StatusWord.SetFlag(int(operands.A), true)

	default:
		fmt.Printf("Unknown opcode: %d\n", p.opcode)
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
		// 3-register: PipelineReg1 = (srcA << 4) | srcB, PipelineReg2 = result
		result.A = p.PipelineReg1 & 0x0F
		result.B = (p.PipelineReg1 >> 4) & 0x0F
		result.Res = p.PipelineReg2 & 0x0F

	case 2:
		// 2-register + immediate: PipelineReg1 = (result << 4) | source, PipelineReg2 = imm
		result.A = p.PipelineReg1 & 0x0F
		result.Res = (p.PipelineReg1 >> 4) & 0x0F
		result.Imm = p.PipelineReg2

	case 3:
		// 2-register (single operand): PipelineReg1 = (result << 4) | source
		result.A = p.PipelineReg1 & 0x0F
		result.Res = (p.PipelineReg1 >> 4) & 0x0F

	case 4:
		// immediate only: PipelineReg1 = immediate
		result.Imm = p.PipelineReg1

	case 5:
		// 2-register move: PipelineReg1 = (dest << 4) | src
		result.A = p.PipelineReg1 & 0x0F
		result.B = (p.PipelineReg1 >> 4) & 0x0F

	case 6:
		// register + address (LD/ST): PipelineReg1 = reg, PipelineReg2/3 = address (little-endian)
		result.A = p.PipelineReg1 & 0x0F
		result.Addr = (uint16(p.PipelineReg3) << 8) | uint16(p.PipelineReg2)

	case 7:
		// immediate + address (STI): PipelineReg1 = imm, PipelineReg2/3 = address (little-endian)
		result.A = p.PipelineReg1
		result.Addr = (uint16(p.PipelineReg3) << 8) | uint16(p.PipelineReg2)

	case 8:
		// single register for stack/branch ops
		result.A = p.PipelineReg1 & 0x0F

	case 9:
		// address only for jumps (JMP): PipelineReg1/2 = address (little-endian)
		result.Addr = (uint16(p.PipelineReg2) << 8) | uint16(p.PipelineReg1)
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
		&p.Si, &p.Di, &p.Rng, &p.Temph, &p.Templ,
	}
}

// Get register value by index
func (p *Ra8) GetRegVal(index byte) byte {
	idx := int(index)
	if idx < 0 || idx > 12 {
		panic("Owned by skill issue, Invalid register index")
	}
	return *p.regPointer()[idx]
}

// Set register value by index
func (p *Ra8) SetRegVal(index byte, value byte) {
	idx := int(index)
	if idx < 0 || idx > 12 {
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
