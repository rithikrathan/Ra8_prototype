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
	Zero Flags = 1 << iota // bit 0 == Zero flag
	Parity
	Halted
	AuxCarry
	Carry
	Overflow
	reserved2
	Sign
)

func HandleFlags(f *Flags, a, b, result byte) {
	// Reset flags to 0 before calculating new state
	*f = 0

	// Zero Flag (Z): Result is 0
	if result == 0 {
		*f |= Zero
	}

	// Sign Flag (S): Bit 7 is set (negative in two's complement)
	if result&0x80 != 0 {
		*f |= Sign
	}

	// Carry Flag (C): Unsigned overflow (sum > 255)
	if uint16(a)+uint16(b) > 0xFF {
		*f |= Carry
	}

	// Auxiliary Carry (AC): Carry from bit 3 to bit 4 (nibble carry)
	if (a&0x0F)+(b&0x0F) > 0x0F {
		*f |= AuxCarry
	}

	// Parity Flag (P): Set if the number of set bits is even
	p := result
	p ^= p >> 4
	p ^= p >> 2
	p ^= p >> 1
	if (p & 1) == 0 {
		*f |= Parity
	}

	// Overflow Flag (OV): Signed overflow
	// Logic: If both inputs have the same sign, but the result has a different sign
	if ((a ^ result) & (b ^ result) & 0x80) != 0 {
		*f |= Overflow
	}
}

unc (s Flags) String() string {
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
// main processor struct
type Ra8 struct {
	// General purpose registers
	A, B, C, D, E, F, G, H byte `json:"registers"`

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
}

// NewRa8 creates a new Ra8 processor with default values
func NewRa8() Ra8 {
	return Ra8{
		StackPointer: 0xFFFF, // Stack starts at top of memory
	}
}

func (p *Ra8) Step() {
}

func (p *Ra8) Fetch() byte {
	instruction := p.InstructionMemory[p.ProgramCounter]
	p.ProgramCounter++
	return instruction
}

func (p *Ra8) Decode() {
	// 11000000 - mask to get the number of immediate bytes
	// 00000001 - mask to check if the instruction is a branching type
	// 00111110 - mask get the opcode
	numImm := (p.InstructionRegister >> 6) & 0x03       // Extract bits 7-6
	p.opcode = int((p.InstructionRegister >> 1) & 0x1F) // Extract bits 5-1

	//TODO: refactor this hardcoded thing if you want to
	switch numImm {
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
		println("owned by skill issue; invalid number of immediate bytes")

	}

	// isBranching := b & 0x01   // Extract bit 0

	return

}

func (p *Ra8) Execute() {
}

// =-=-=-=-=-=-=[AI GENERATED]=-=-=-=-=-=-

// GetRegisterValue returns the value of a register by index (0=A, 1=B, 2=C, etc.)
func (p *Ra8) GetRegisterValue(regIndex byte) byte {
	switch regIndex {
	case 0:
		return p.A
	case 1:
		return p.B
	case 2:
		return p.C
	case 3:
		return p.D
	case 4:
		return p.E
	case 5:
		return p.F
	case 6:
		return p.G
	case 7:
		return p.H
	default:
		println("owned by skill issue; invalid Register selection")
		return 0
	}
}

// GetRegisterName returns the name of a register by index
func (p *Ra8) GetRegisterName(regIndex byte) string {
	switch regIndex {
	case 0:
		return "A"
	case 1:
		return "B"
	case 2:
		return "C"
	case 3:
		return "D"
	case 4:
		return "E"
	case 5:
		return "F"
	case 6:
		return "G"
	case 7:
		return "H"
	default:
		println("owned by skill issue; invalid register index")
		return "INVALID"
	}
}

// ReadPipelineRegisters reads and displays pipeline register values based on format type
func (p *Ra8) ReadPipelineRegisters(formatType string) {
	switch formatType {
	case "immediate data":
		fmt.Printf("Immediate Data: 0x%02X\n", p.PipelineReg1)

	case "register type":
		regIndex := p.PipelineReg1 & 0x07
		regValue := p.GetRegisterValue(regIndex)
		regName := p.GetRegisterName(regIndex)
		fmt.Printf("Register (AAA=%d): %s = 0x%02X\n", regIndex, regName, regValue)

	case "immediate16 type":
		value := uint16(p.PipelineReg1) | (uint16(p.PipelineReg2) << 8)
		fmt.Printf("Immediate16: 0x%04X\n", value)

	case "address type":
		address := uint16(p.PipelineReg1) | (uint16(p.PipelineReg2) << 8)
		fmt.Printf("Address: 0x%04X\n", address)

	case "register,register types":
		regAIndex := p.PipelineReg1 & 0x07
		regBIndex := (p.PipelineReg1 >> 4) & 0x07
		regAValue := p.GetRegisterValue(regAIndex)
		regBValue := p.GetRegisterValue(regBIndex)
		regAName := p.GetRegisterName(regAIndex)
		regBName := p.GetRegisterName(regBIndex)
		fmt.Printf("Register A (AAA=%d): %s = 0x%02X, Register B (BBB=%d): %s = 0x%02X\n",
			regAIndex, regAName, regAValue, regBIndex, regBName, regBValue)

	case "register,immediate data types":
		regIndex := (p.PipelineReg1 >> 4) & 0x07
		regValue := p.GetRegisterValue(regIndex)
		regName := p.GetRegisterName(regIndex)
		immediate := p.PipelineReg2
		fmt.Printf("Register (RRR=%d): %s = 0x%02X, Immediate: 0x%02X\n", regIndex, regName, regValue, immediate)

	case "address,register types":
		address := uint16(p.PipelineReg1) | (uint16(p.PipelineReg2) << 8)
		regIndex := p.PipelineReg3 & 0x0F
		regValue := p.GetRegisterValue(regIndex)
		regName := p.GetRegisterName(regIndex)
		fmt.Printf("Address: 0x%04X, Register (AAAA=%d): %s = 0x%02X\n", address, regIndex, regName, regValue)

	default:
		fmt.Printf("Unknown format type: %s\n", formatType)
	}
}
