package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: ./main <program>_inst.txt [data_file]")
		os.Exit(1)
	}

	emulator := NewRa8()

	instFile := os.Args[1]
	dataFile := ""

	if len(os.Args) >= 3 {
		dataFile = os.Args[2]
	}

	if instFile != "" {
		err := loadInstructionFile(emulator.InstructionMemory[:], instFile)
		if err != nil {
			fmt.Printf("Error loading instruction file: %v\n", err)
			os.Exit(1)
		}
	}

	if dataFile != "" {
		err := loadDataFile(emulator.DataMemory[:], dataFile)
		if err != nil {
			fmt.Printf("Error loading data file: %v\n", err)
			os.Exit(1)
		}
	}

	fmt.Println("=== Starting Execution ===")

	step := 0
	maxSteps := 50
	oldPC := emulator.ProgramCounter
	for emulator.isHalted == 0 && step < maxSteps {
		ir := emulator.InstructionMemory[emulator.ProgramCounter]
		opcode := int(ir & 0x3F)
		immBytes := (ir >> 6) & 0x3
		var immInfo string
		if immBytes > 0 {
			immStr := ""
			for i := uint16(1); i <= uint16(immBytes); i++ {
				if i > 1 {
					immStr += " "
				}
				immStr += fmt.Sprintf("%02X", emulator.InstructionMemory[emulator.ProgramCounter+i])
			}
			immInfo = fmt.Sprintf(" imm=[%s]", immStr)
		} else {
			immInfo = ""
		}

		// Print what the decode will extract
		var decodeInfo string
		switch opcode {
		case 27: // LDI: PipelineReg1 = (dest << 4) | src, PipelineReg2 = imm
			pr1 := emulator.InstructionMemory[emulator.ProgramCounter+1]
			immVal := emulator.InstructionMemory[emulator.ProgramCounter+2]
			destField := (pr1 >> 4) & 0x0F
			decodeInfo = fmt.Sprintf(" LDI: r%d = %02X", destField, immVal)
		case 2: // ADD: PipelineReg1 = (srcB << 4) | srcA, PipelineReg2 = dest
			pr1 := emulator.InstructionMemory[emulator.ProgramCounter+1]
			pr2 := emulator.InstructionMemory[emulator.ProgramCounter+2]
			srcAField := pr1 & 0x0F
			srcBField := (pr1 >> 4) & 0x0F
			resField := pr2 & 0x0F
			srcA_val := emulator.GetRegVal(byte(srcAField))
			srcB_val := emulator.GetRegVal(byte(srcBField))
			decodeInfo = fmt.Sprintf(" ADD: r%d = r%d(%02X) + r%d(%02X) -> r%d", resField, srcAField, srcA_val, srcBField, srcB_val, resField)
		case 3: // ADI: PipelineReg1 = (dest << 4) | src, PipelineReg2 = imm
			pr1 := emulator.InstructionMemory[emulator.ProgramCounter+1]
			immVal := emulator.InstructionMemory[emulator.ProgramCounter+2]
			srcField := pr1 & 0x0F
			destField := (pr1 >> 4) & 0x0F
			src_val := emulator.GetRegVal(byte(srcField))
			decodeInfo = fmt.Sprintf(" ADI: r%d = r%d(%02X) + %02X -> r%d", destField, srcField, src_val, immVal, destField)
		case 6: // SUI: PipelineReg1 = (dest << 4) | src, PipelineReg2 = imm
			pr1 := emulator.InstructionMemory[emulator.ProgramCounter+1]
			immVal := emulator.InstructionMemory[emulator.ProgramCounter+2]
			srcField := pr1 & 0x0F
			destField := (pr1 >> 4) & 0x0F
			src_val := emulator.GetRegVal(byte(srcField))
			decodeInfo = fmt.Sprintf(" SUI: r%d = r%d(%02X) - %02X -> r%d", destField, srcField, src_val, immVal, destField)
		default:
			decodeInfo = ""
		}

		emulator.Step()
		step++
		if emulator.ProgramCounter != oldPC || emulator.isHalted == 1 {
			fmt.Printf("Step %d: PC=0x%04X IR=0x%02X opcode=%d%s%s -> PC=0x%04X | A=%02X B=%02X C=%02X D=%02X E=%02X F=%02X G=%02X H=%02X Flags=%v\n",
				step, oldPC, ir, opcode, immInfo, decodeInfo, emulator.ProgramCounter,
				emulator.A, emulator.B, emulator.C, emulator.D,
				emulator.E, emulator.F, emulator.G, emulator.H, emulator.StatusWord)
		}
		oldPC = emulator.ProgramCounter
	}

	fmt.Println("=== Execution Halted ===")
	printFinalState(emulator)
}

func loadInstructionFile(memory []byte, filename string) error {
	data, err := os.ReadFile(filename)
	if err != nil {
		return err
	}

	lines := strings.Split(string(data), "\n")
	addr := 0
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		line = strings.TrimPrefix(line, "0x")
		line = strings.TrimPrefix(line, "0X")
		val, err := strconv.ParseInt(line, 16, 64)
		if err != nil {
			fmt.Printf("Warning: could not parse line: %s\n", line)
			continue
		}

		if addr >= len(memory) {
			break
		}
		memory[addr] = byte(val)
		addr++
	}

	fmt.Printf("Loaded %d bytes into instruction memory\n", addr)
	return nil
}

func loadDataFile(memory []byte, filename string) error {
	data, err := os.ReadFile(filename)
	if err != nil {
		return err
	}

	lines := strings.Split(string(data), "\n")
	addr := 0
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		line = strings.TrimPrefix(line, "0x")
		val, err := strconv.ParseInt(line, 16, 64)
		if err != nil {
			continue
		}

		if addr >= len(memory) {
			break
		}
		memory[addr] = byte(val)
		addr++
	}

	fmt.Printf("Loaded %d bytes into data memory\n", addr)
	return nil
}

func printFinalState(p *Ra8) {
	fmt.Println("\n=== Register State ===")
	fmt.Printf("PC: 0x%04X\n", p.ProgramCounter)
	fmt.Printf("A: 0x%02X (%d)\n", p.A, p.A)
	fmt.Printf("B: 0x%02X (%d)\n", p.B, p.B)
	fmt.Printf("C: 0x%02X (%d)\n", p.C, p.C)
	fmt.Printf("D: 0x%02X (%d)\n", p.D, p.D)
	fmt.Printf("E: 0x%02X (%d)\n", p.E, p.E)
	fmt.Printf("F: 0x%02X (%d)\n", p.F, p.F)
	fmt.Printf("G: 0x%02X (%d)\n", p.G, p.G)
	fmt.Printf("H: 0x%02X (%d)\n", p.H, p.H)
	fmt.Printf("SP: 0x%04X\n", p.StackPointer)
	fmt.Printf("Flags: %v\n", p.StatusWord)
}
