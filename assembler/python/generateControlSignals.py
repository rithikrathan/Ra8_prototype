import csv
import glob
import os


def loadCSV(csvFile):
    instructionID = {}
    with open(csvFile, mode='r') as file:
        reader = csv.DictReader(file)
        for instr in reader:
            if instr['INSTRUCTION'] and instr['instrID']:
                instruction = instr['INSTRUCTION']
                instructionID[instruction] = instr['instrID']
    return instructionID


def getfile(directory='./Assembly_code'):
    asmFiles = glob.glob(directory+'/*.asm')

    if not asmFiles:
        print('no .asm files found')
        return

    print('---------------------------------------------')
    print('Choose a program to assemble:')
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
                print(f'{name} will be assembled into Machine_code directory')
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
        commentPos = line.find('#')
        if commentPos != -1:
            line = line[:commentPos].stip()

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


def generateControlSignals(opcodes, id):
    controlROM = [0x00] * 64
    controlSignals = ['ALUmode', 'Cin', 'enALU', 'dload', 'dstore']
    for opcode in opcodes:
        addr = id[opcode]


def main():
    instrID = loadCSV('../../someotherstuffs/instruction set.csv')
    for i, j in instrID.items():
        print(f'{i} => {j}')
    filePath, name = getfile()
    inputFile = open(filePath).read()
    lines = inputFile.splitlines()
    opcodes = getOpcodes(lines)
    generateControlSignals(opcodes, instrID)


if __name__ == '__main__':
    main()
