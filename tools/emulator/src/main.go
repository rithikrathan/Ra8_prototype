package main

import (
	"fmt"
)

func main() {
	// Initialize the RA8 processor with default values
	processor := NewRa8()

	// Print the contents of the RA8 struct
	fmt.Println("=== RA8 Processor State ===")
	fmt.Printf("General Purpose Registers:\n")
	fmt.Printf("  A: 0x%02X, B: 0x%02X, C: 0x%02X, D: 0x%02X\n",
		processor.A, processor.B, processor.C, processor.D)
	fmt.Printf("  E: 0x%02X, F: 0x%02X, G: 0x%02X, H: 0x%02X\n",
		processor.E, processor.F, processor.G, processor.H)

	fmt.Printf("\nSpecial Purpose Registers:\n")
	fmt.Printf("  Program Counter: 0x%04X\n", processor.ProgramCounter)
	fmt.Printf("  Stack Pointer:   0x%04X\n", processor.StackPointer)
	fmt.Printf("  Source Index:    0x%04X\n", processor.SourceIndex)
	fmt.Printf("  Dest Index:      0x%04X\n", processor.DestinationIndex)
	fmt.Printf("  Return Register: 0x%04X\n", processor.ReturnRegister)
	fmt.Printf("  Status Word:     %s\n", processor.StatusWord)

	fmt.Printf("\nPipeline Registers:\n")
	fmt.Printf("  Instruction Reg: 0x%02X\n", processor.InstructionRegister)
	fmt.Printf("  Pipeline Reg 1:  0x%02X\n", processor.PipelineReg1)
	fmt.Printf("  Pipeline Reg 2:  0x%02X\n", processor.PipelineReg2)
	fmt.Printf("  Pipeline Reg 3:  0x%02X\n", processor.PipelineReg3)

	fmt.Printf("\nMemory:\n")
	fmt.Printf("  Instruction Memory: %d bytes (first 16 shown)\n", len(processor.InstructionMemory))
	for i := 0; i < 16 && i < len(processor.InstructionMemory); i++ {
		if i%8 == 0 {
			fmt.Printf("    ")
		}
		fmt.Printf("%02X ", processor.InstructionMemory[i])
		if i%8 == 7 {
			fmt.Printf("\n")
		}
	}

	fmt.Printf("  Data Memory: %d bytes (first 16 shown)\n", len(processor.DataMemory))
	for i := 0; i < 16 && i < len(processor.DataMemory); i++ {
		if i%8 == 0 {
			fmt.Printf("    ")
		}
		fmt.Printf("%02X ", processor.DataMemory[i])
		if i%8 == 7 {
			fmt.Printf("\n")
		}
	}
}
