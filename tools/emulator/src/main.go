package main

import (
	"flag"
	"fmt"
	"os"
)

func main() {
	trace := flag.Bool("trace", false, "verbose per-step output")
	dumpState := flag.Bool("dump-state", false, "dump register state at end")
	dumpMem := flag.Bool("dump-mem", false, "dump data memory at end")
	dataFile := flag.String("data", "", "data binary file to load into data memory")
	maxSteps := flag.Int("max-steps", 100000, "max execution steps")
	flag.Parse()

	args := flag.Args()
	if len(args) < 1 {
		fmt.Fprintf(os.Stderr, "Usage: %s [--trace] [--data file.bin] <program.bin>\n", os.Args[0])
		os.Exit(1)
	}

	cpu := NewCPU()
	cpu.trace = *trace
	cpu.maxSteps = *maxSteps

	if err := cpu.LoadProgram(args[0]); err != nil {
		fmt.Fprintf(os.Stderr, "Error loading program: %v\n", err)
		os.Exit(1)
	}

	if *dataFile != "" {
		if err := cpu.LoadData(*dataFile); err != nil {
			fmt.Fprintf(os.Stderr, "Error loading data: %v\n", err)
			os.Exit(1)
		}
	}

	cpu.Run()

	if cpu.halted {
		fmt.Println("Execution halted successfully.")
	} else if cpu.stepCount >= cpu.maxSteps {
		fmt.Printf("Execution stopped at max steps (%d).\n", cpu.maxSteps)
	}

	if *dumpState {
		fmt.Println("\n=== REGISTER STATE ===")
		fmt.Printf("A=%02x B=%02x C=%02x D=%02x\n", cpu.regs[0], cpu.regs[1], cpu.regs[2], cpu.regs[3])
		fmt.Printf("E=%02x F=%02x G=%02x H=%02x\n", cpu.regs[4], cpu.regs[5], cpu.regs[6], cpu.regs[7])
		fmt.Printf("Templ=%02x Temph=%02x RNG=%02x\n", cpu.regs[8], cpu.regs[9], cpu.regs[10])
		fmt.Printf("PC=%04x SP=%04x SI=%04x DI=%04x\n", cpu.pc, cpu.sp, cpu.si, cpu.di)
		fmt.Printf("Flags=[%s] (%02x)\n", flagStr(cpu.flags), cpu.flags)
		fmt.Printf("Halted=%v Steps=%d\n", cpu.halted, cpu.stepCount)
	}

	if *dumpMem {
		fmt.Println("\n=== DATA MEMORY (first 256 bytes) ===")
		for i := 0; i < 256; i += 16 {
			fmt.Printf("%04x: ", i)
			for j := 0; j < 16; j++ {
				fmt.Printf("%02x ", cpu.dataMem[i+j])
			}
			fmt.Println()
		}
	}
}
