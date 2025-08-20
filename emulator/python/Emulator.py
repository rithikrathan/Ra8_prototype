class usefulMethods:
    def isValidInput(self, maxSize, *inputs):
        return all(v < maxSize for v in inputs)


class InstrMem(usefulMethods):
    def __init__(self, size=0xffff):
        self.instr = [0] * size

    def store(self, addr, value):
        if self.isValidInput(0xffff, addr):
            self.instr[addr] = value
        else:
            print(f"Invalid input,{addr} max value is {len(self.instr)}")

    def load(self, addr):
        if self.isValidInput(0xffff, addr):
            return self.instr[addr]
        else:
            print(f"Invalid input,{addr} max value is {len(self.instr)}")

    def initializeMemory(self, file, wordSize=1):
        with open(file, "rb") as f:
            addr = 0
            while byte := f.read(wordSize):
                self.store(addr, int.from_bytes(byte, 'little'))
                addr += 1


class DataMem(usefulMethods):
    def __init__(self, size=0xffff):
        self.data = [0] * size

    def store(self, addr, value):
        if self.isValidInput(0xffff, addr):
            self.data[addr] = value
        else:
            print(f"Invalid input,{addr} max value is {len(self.data)}")

    def load(self, addr):
        if self.isValidInput(0xffff, addr):
            return self.data[addr]
        else:
            print(f"Invalid input,{addr} max value is {len(self.data)}")

    def initializeMemory(self, file, wordSize=1):
        with open(file, "rb") as f:
            addr = 0
            while byte := f.read(wordSize):
                self.store(addr, int.from_bytes(byte, 'little'))
                addr += 1


class Stack(usefulMethods):
    def __init__(self, dataMemory: DataMem) -> None:
        self.dataMemory = dataMemory
        self.stackPointer = 0xffff

    def push(self, value):
        self.stackPointer -= 1
        self.dataMemory.store(self.stackPointer, value)

    def pop(self):
        data = self.dataMemory.load(self.stackPointer)
        self.dataMemory.store(self.stackPointer, 0x0000)
        self.stackPointer += 1
        return data

    def topElement(self):
        if self.stackPointer < 0xffff:
            data = self.dataMemory.load(self.stackPointer)
        else:
            data = -1
        return data

    def top2Element(self):
        if self.stackPointer < 0xffff:
            data = self.dataMemory.load(self.stackPointer + 1)
        else:
            data = -1
        return data


class generalPurposeRegisterFile(usefulMethods):
    def __init__(self) -> None:
        self.registers = [0] * 8

    def read(self, regA, regB):
        if self.isValidInput(8, regA, regB):
            return (self.registers[regA], self.registers[regB])
        else:
            print("Register index out of range")

    def write(self, regW, value):
        if self.isValidInput(8, regW):
            self.registers[regW] = value
        else:
            print("Register index regW out of range")


class Ra8_MPU(usefulMethods):
    def __init__(self) -> None:
        self._halted = False
        self._clockPulse = False

        self.proramCounter = 0xffff

        self.pipelineRegisters = [0, 0, 0]

        self.flags = {
            "sign": False,
            "overFlow": False,
            "carry": False,
            "auxillaryCarry": False,
            "equal": False,
            "greaterThan": False,
            "parity": False,
            "zero": False
        }

        self.dataMemory = DataMem()
        self.instructionMemory = InstrMem()
        self.stack = Stack(self.dataMemory)
        self.registers = generalPurposeRegisterFile()

    def setFlag(self, flag):
        self.flags[flag] = True

    def resetFlags(self):
        self.flags = {
            "sign": False,
            "overFlow": False,
            "carry": False,
            "auxillaryCarry": False,
            "equal": False,
            "greaterThan": False,
            "parity": False,
            "zero": False
        }

    def run(self):
        pass

    def fetch(self):
        pass

    def decode(self):
        pass

    def execute(self):
        pass
