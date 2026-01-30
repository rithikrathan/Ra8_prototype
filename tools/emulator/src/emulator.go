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

	if ((a ^ result) & (b ^ result) & 0x80) != 0 {
		// Logic: If both inputs have the same sign, but the result has a different sign
		*f |= Overflow
	} // Overflow Flag (OV): Signed overflow

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
// main processor struct
type Ra8 struct {
	// General purpose registers
	A, B, C, D, E, F, G, H byte `json:"gp_registers"`

	temph, templ byte `json:"temp_registers"`

	//NOTE: temph and templ are multiplexers that feed high and low bytes
	//		of pc to databus used in place of registers

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
	isBranching         int  // internal field for branch instruction flag
}

// some kind of constructor or something that initializes it
func NewRa8() Ra8 {
	return Ra8{
		StackPointer: 0xFFFF, // Stack starts at top of memory
	}
}

// =-=-=-=-=-=-=[EXECUTION CYCLE]=-=-=-=-=-=-

// NOTE: in this single step method, the fetch decode and execute cycle programs here do not implement
// their movement in the pipeline as ILP is only necessary when implementing in
// hardware and im lazy to implement in the emulator, its useless anyways
func (p *Ra8) Step() int {
	//composition of a single execution cycle
	if !p.StatusWord[Halted] {
		p.Fetch()
		p.Decode()
		p.Execute()
	} else {
		return 1 // satus code to check if the processor halted
	}
}

func (p *Ra8) Fetch() {
	p.InstructionRegister = p.InstructionMemory[p.ProgramCounter]
	p.ProgramCounter++
}

func (p *Ra8) Decode() {

	// 11000000 - mask to get the number of immediate bytes
	// 00000001 - mask to check if the instruction is a branching type
	// 00111110 - mask get the opcode

	numImm := p.InstructionRegister & 0b11000000       // Extract bits 7-6 (Number of immediate bytes following this opcode)
	p.opcode = int(p.InstructionRegister & 0b00111110) // Extract bits 5-1 (OPCODE)

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

	return

}

// TODO: make a proper instruction set table and proceed
func (p *Ra8) Execute() {
	if p.opcode == 0 {
		// NOPE instruction
	} else if p.opcode == 1 {
		// HALT instruction
		p.StatusWord[Halted] = 1
	} else if p.opcode == 2 {
		// ADD instruction
	} else if p.opcode == 3 {
		// ADI instruction
	} else if p.opcode == 4 {
		// ADC instruction
	} else if p.opcode == 5 {
		// xx instruction
	}

}

// =-=-=-=-=-=-=[HELPERS]=-=-=-=-=-=-

// Initialize helper maps for Ra8
func (p *Ra8) registerPointers() []*byte {
	return []*byte{
		&p.A, &p.B, &p.C, &p.D,
		&p.E, &p.F, &p.G, &p.H,
	}
}

// Get register Name by index like what the fuck do you think these do bro
func (p *Ra8) GetRegisterName(index int) string {
	names := []string{"A", "B", "C", "D", "E", "F", "G", "H"}
	if index < 0 || index > 7 {
		panic("owned by skill issue, invalid register index")
	}
	return names[index]
}

// Get register value by index
func (p *Ra8) GetRegisterValue(index int) byte {
	if index < 0 || index > 7 {
		panic("invalid register index")
	}
	return *p.registerPointers()[index]
}

// Set register value by index
func (p *Ra8) SetRegisterValue(index int, value byte) {
	if index < 0 || index > 7 {
		panic("invalid register index")
	}
	*p.registerPointers()[index] = value
}

// =-=-=-=-=-=-=[AI GENERATED]=-=-=-=-=-=-

// getOperands() reads and displays pipeline register values based on format type
func (p *Ra8) getOperands(formatType string) {
	switch formatType {
	case "immediate data":
		fmt.Printf("Immediate Data: 0x%02X\n", p.PipelineReg1)

	case "register type":
		regIndex := p.PipelineReg1 & 0x07
		regValue := p.GetRegisterValue(regIndex)
		regName := p.GetRegisterName(regIndex)

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

// =-=-=-=-=-=-=[EVEN MORE AI GENERATED]=-=-=-=-=-=-
// Initialize helper maps for Ra8
// func (p *Ra8) registerPointers() []*byte {
// 	return []*byte{
// 		&p.A, &p.B, &p.C, &p.D,
// 		&p.E, &p.F, &p.G, &p.H,
// 	}
// }
// Map register names to index
// func (p *Ra8) registerNameToIndex() map[string]int {
// 	return map[string]int{
// 		"A": 0, "B": 1, "C": 2, "D": 3,
// 		"E": 4, "F": 5, "G": 6, "H": 7,
// 	}
// }

// Get register value by name
// func (p *Ra8) GetRegisterValueByName(name string) (byte, error) {
// 	idxMap := p.registerNameToIndex()
// 	index, ok := idxMap[name]
// 	if !ok {
// 		return 0, fmt.Errorf("invalid register name: %s", name)
// 	}
// 	return p.GetRegisterValue(index), nil
// }

// Set register value by name
// func (p *Ra8) SetRegisterValueByName(name string, value byte) error {
// 	idxMap := p.registerNameToIndex()
// 	index, ok := idxMap[name]
// 	if !ok {
// 		return fmt.Errorf("invalid register name: %s", name)
// 	}
// 	p.SetRegisterValue(index, value)
// 	return nil
// }
