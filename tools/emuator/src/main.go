package main

import (
	"fmt"
	"strings"
)

// =-=-=-=-=-=-=[DEFINE NECESSARY THINGS]=-=-=-=-=-=-

// processor struct
type Processor struct {
	// General purpose registers
	A, B, C, D, E, F, G, H byte `json:"registers"`

	// Special purpose registers
	ProgramCounter   uint  `json:"program_counter"`
	StackPointer     uint  `json:"stack_pointer"`
	SourceIndex      uint  `json:"source_index"`
	DestinationIndex uint  `json:"destination_index"`
	ReturnRegister   uint  `json:"return_register"`
	StatusWord       Flags `json:"status_word"`

	// Memory arrays
	InstructionMemory [0xffff]byte `json:"instruction_memory"`
	DataMemory        [0xffff]byte `json:"data_memory"`

	// Pipeline registers
	PipelineReg1 byte `json:"pipeline_reg_1"`
	PipelineReg2 byte `json:"pipeline_reg_2"`
	PipelineReg3 byte `json:"pipeline_reg_3"`
}

// flags struct
type Flags uint8

const (
	// [S|-|OV|C|AC|-|P|Z]
	Zero Flags = 1 << iota // bit 0 == Zero flag
	Parity
	reserved1
	AuxCarry
	Carry
	Overflow
	reserved2
	Sign
)

type State uint

const (
	FetchInstructions State = iota
	FetchImmediates
	DecodeAndExecute
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
	if s&reserved1 != 0 {
		names = append(names, "reserved1")
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

//=-=-=-=-=-=-=[INITIALIZE]=-=-=-=-=-=-

// =-=-=-=-=-=-=[MAIN LOGIC]=-=-=-=-=-=-
func main() {
}
