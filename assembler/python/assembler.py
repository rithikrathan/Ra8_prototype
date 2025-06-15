import csv
import glob
import os

print("salutations my fellow humanoids\n")


def loadCSV(csv_file):
    instructionAddr = {}
    sel = {}
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for instr in reader:
            if instr['INSTRUCTION'] and instr['SIZE'] and instr['instrID']:
                instruction = instr['INSTRUCTION']
                opcode = (int(instr['SIZE']) - 1) << 6 | int(instr['instrID'])
                instructionAddr[instruction] = opcode
                if instr['select']:
                    sel[instruction] = int(instr['select'])
    return instructionAddr, sel


def getFile(directory='Assembly_code'):
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
            if 0 <= choice < len(asmFiles):
                path = asmFiles[choice]
                name = os.path.basename(path)
                print(f'{name} will be assembled into Machine_code directory')
                return path, name
            else:
                print('Invalid index value')
        except TypeError:
            print('index must be a number!')


def tokenize(lines):
    tokens = []
    for line in lines:
        line = line.strip()
        token = {}

        # handle empty lines
        if not line:
            continue

        # handle comments
        commentPos = line.find('#')
        if commentPos != -1:
            token['comment'] = line[commentPos + 1:].strip()
            line = line[:commentPos].stip()

        opcode, regR, regA, regB = line.split()
        token['opcode'] = opcode
        token['regR'] = regR
        token['regA'] = regA
        token['regB'] = regB
        tokens.append(token)
    return tokens


def lookup(token, opcodes, select):
    instruction = token['opcode']
    bytes = []
    bytes.append(opcodes[instruction])
    bytes.append(int(token['regR'][1:]) << 4 | int(select[instruction]))
    bytes.append(int(token['regB'][1:]) << 4 | int(token['regA'][1:]))
    # print(token)
    # print(bin(byte1), bin(byte2), bin(byte3))
    # print(byte1, byte2, byte3)
    return bytes


def generateBinary(bytes, filename):

    rom = [0x00] * 0xffff

    with open(f"{filename}.bin", "wb") as file:
        file.write(bytearray(rom))


def main():
    csvFile = "../../someotherstuffs/instruction set.csv"
    opcodes, select = loadCSV(csvFile)
    filePath, filename = getFile()
    inputFile = open(filePath).read()
    lines = inputFile.splitlines()
    tokens = tokenize(lines)
    for token in tokens:
        lookup(token, opcodes, select)


if __name__ == "__main__":
    main()
