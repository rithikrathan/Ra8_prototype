"""
RIGHT NOW THIS PROGRAM ASSUMES THE ASSEMBLY CODE IS WRITTEN IN CORRECT SYNTAX
"""
import csv
import glob
import os

print("salutations my fellow humanoids\n")


# load the csv file and return dictionaries for instruction {instruction: opcode}  {instruction: select} {instruction: type}
def loadCSV(csv_file):
    instructionAddr = {}
    sel = {}
    types = {}
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for instr in reader:
            if instr['INSTRUCTION'] and instr['SIZE'] and instr['instrID']:
                instruction = instr['INSTRUCTION']
                opcode = (int(instr['SIZE']) - 1) << 6 | int(instr['instrID'])
                instructionAddr[instruction] = opcode
                if instr['select']:
                    sel[instruction] = int(instr['select'])
                if instr['TYPE']:
                    types[instruction] = instr['TYPE']

    return instructionAddr, sel, types


# get input from the user and return the selected assembly program file
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
        except:  # ignore this this is some of my stupid code idek why i did it this way
            print('index must be a number!')
            print('---------------------------------------------')


def parser(lines):  # lines => list of every line in the assembly program
    tokens = []
    vars = []
    is_dataLine = False
    for line in lines:  # iterate through each line in the assembly program
        line = line.strip()  # ignore whitespaces
        token = {}
        """
        token = {
                'opcode': opcode of the instruction
                'arg1': argument1
                'arg2': argument2
                'arg3': argument3
                }
        """
        data = {}
        """
        NOTE:
        data = {
                'identifier': variableName
                'value': -
                'type': -
                'address': -
                }


        above is the intended use of this, in the future when i add vairables to the assembly program
        right now im just using the value to load data into the data memory

        example usage in assembly code:
            .data
                myVal: byte 69 
                myStr: string 'hello idiots' 
                myArr: array  1 2 3 4 5 6 76   
        """

        # handle comments
        # if there is ';' in the line remove everything that follows it including the symbol itself
        commentPos = line.find(';')
        if commentPos != -1:
            token['comment'] = line[commentPos + 1:].strip()
            line = line[:commentPos].strip()  # remove whitespaces

        # handle empty lines
        if not line:
            continue

        # handle data stuffs
        if line == '.data':
            is_dataLine = True
            continue
        if is_dataLine and ':' not in line:
            is_dataLine = False
        if is_dataLine:
            poss = line.find(':')
            data['identifier'] = line[:poss].strip()
            data['value'] = int(line[poss+1:].strip())
            # add thes data dict to the list of all variable dictionaries
            vars.append(data)
            continue

        # handle instructions
        splits = line.split()
        opcode, arg1, arg2, arg3 = (splits + [None] * 4)[:4]
        token['opcode'] = opcode
        token['arg1'] = arg1
        token['arg2'] = arg2
        token['arg3'] = arg3
        # throws error when there is no arg3 if there is an addr tried solving it by initially assigning it to None
        tokens.append(token)  # add this token dict to the list of all tokens
    return tokens, vars


def lookup(tokens, opcodes, select, types):
    bytes = []
    for token in tokens:
        instruction = token['opcode']
        bytes.append(opcodes[instruction])
        if types[instruction] == "Arithmetic C-type" or types[instruction] == "Logical C-type":
            bytes.append(int(token['arg3'][1:]) << 4 | int(token['arg2'][1:]))
            bytes.append(int(select[instruction]) <<
                         4 | int(token['arg1'][1:]))
        elif types[instruction] == "Load":
            bytes.append(int(token['arg2']) & 0xff)
            bytes.append(int(token['arg2']) >> 8 & 0xff)
            bytes.append(int(token['arg1'][1:]))
        elif types[instruction] == "Store":
            bytes.append(int(token['arg1']) & 0xff)
            bytes.append(int(token['arg1']) >> 8 & 0xff)
            bytes.append(int(token['arg2'][1:]))
        elif types[instruction] == "Move":
            bytes.append(int(token['arg1'][1:]) << 4 | int(token['arg2'][1:]))
    return bytes


def generateBinary(bytes, file, vars):
    instrMemory = [0x00] * 0xffff
    dataMemory = [0x00] * 0xffff
    filename = file.removesuffix(".asm")

    for addr, byte in enumerate(bytes):
        instrMemory[addr] = byte
    for addr, var in enumerate(vars):
        dataMemory[addr] = var['value']

    os.makedirs(f'Machine_code/{filename}', exist_ok=True)
    with open(f"Machine_code/{filename}/{filename}.bin", "wb") as file:
        file.write(bytearray(instrMemory))
    with open(f"Machine_code/{filename}/{filename}_data.bin", "wb") as file:
        file.write(bytearray(dataMemory))


def main():
    csvFile = "../../someotherstuffs/instruction set.csv"
    opcodes, select, types = loadCSV(csvFile)
    filePath, filename = getFile()
    inputFile = open(filePath).read()
    lines = inputFile.splitlines()
    # in the future make it so that the identifier part is used too to address the variables
    tokens, vars = parser(lines)
    bytes = lookup(tokens, opcodes, select, types)
    generateBinary(bytes, filename, vars)


if __name__ == "__main__":
    main()
