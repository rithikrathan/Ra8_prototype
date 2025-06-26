import csv
import glob
import os


def loadCSV(csvFile):
    instructionID = {}
    CuSelect = {}
    with open(csvFile, mode='r') as file:
        reader = csv.DictReader(file)
        for instr in reader:
            if instr['INSTRUCTION'] and instr['instrID']:
                instruction = instr['INSTRUCTION']
                instructionID[instruction] = instr['instrID']
            if instr['INSTRUCTION'] and instr['Cuselect']:
                instruction = instr['INSTRUCTION']
                CuSelect[instruction] = instr['Cuselect']
    return instructionID, CuSelect


def getfile(directory='./Assembly_code'):
    asmFiles = glob.glob(directory+'/*.asm')

    if not asmFiles:
        print('no .asm files found')
        return

    print('---------------------------------------------')
    print('Choose a program to generate control signals:')
    print('---------------------------------------------')
    for i, file in enumerate(asmFiles):
        print(f'{i} => {os.path.basename(file)}')
    print('---------------------------------------------')

    while True:
        try:
            choice = int(input('Enter the index of your choice:'))
            print('---------------------------------------------')
            if 0 <= choice < len(asmFiles):
                path = asmFiles[choice]
                name = os.path.basename(path)
                print(f'Control signals for the program {
                      name} will be generated')
                print('---------------------------------------------')
                return path, name
            else:
                print('Invalid index value')
                print('---------------------------------------------')
        except:
            print('index must be a number!')
            print('---------------------------------------------')


def getOpcodes(lines):
    opcodes = set()
    is_dataLine = False
    for line in lines:
        line = line.strip()

        # handle comments
        commentPos = line.find(';')
        if commentPos != -1:
            line = line[:commentPos].strip()

        # handle empty lines
        if not line:
            continue

        # handle data stuffs
        if line == '.data':
            is_dataLine = True
            continue
        if is_dataLine and ':' not in line:
            is_dataLine = False
        if not is_dataLine:
            splits = line.split()
            opcode = splits[0]
            opcodes.add(opcode)

    return opcodes


def generateControlSignals(opcodes, id, filename, sel):
    controlROM = [0x00] * 64
    selectROM = [0x00] * 64
    controlSignals = ['ALUmode', 'Cin', 'dload', 'dstore']
    name = filename.removesuffix('.asm')
    for opcode in opcodes:
        addr = int(id[opcode])
        controlSignal = 0
        print(f"For {opcode}: ")
        print("------------------------------------------")
        Sel = int(sel[opcode])
        for j, i in enumerate(controlSignals):
            val = int(input(f"Enter value for {i} (0/1): "))
            if val:
                controlSignal |= val << j
        print("------------------------------------------")
        print(bin(controlSignal))
        controlROM[addr] = controlSignal
        selectROM[addr] = Sel
        print("------------------------------------------")
    os.makedirs(f'./Control_signals/{name}', exist_ok=True)
    with open(f'./Control_signals/{name}/{name}_CS1.bin', 'wb') as file:
        for val in controlROM:
            file.write(val.to_bytes(2, byteorder="big"))
    with open(f'./Control_signals/{name}/{name}_CS2.bin', 'wb') as file:
        for val in selectROM:
            file.write(val.to_bytes(2, byteorder="big"))

    print(f"Generated control signals at ./Control_signals/{name}/")
    print("------------------------------------------")


def main():
    instrID, sel = loadCSV('../../someotherstuffs/instruction set.csv')
    filePath, name = getfile()
    inputFile = open(filePath).read()
    lines = inputFile.splitlines()
    opcodes = getOpcodes(lines)
    try:
        generateControlSignals(opcodes, instrID, name, sel)
    except KeyboardInterrupt:
        print('\nended')


if __name__ == '__main__':
    main()
