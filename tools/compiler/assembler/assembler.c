#include "ast.h"
#include "uthash.h"
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern int yyparse();
extern FILE *yyin;
extern astNode *ast_root;
extern char *yytext;
extern int inDataSection;

astNode *curr;
int address = 0;
int hasStartLabel = 0;

int inInstSection = 0;

struct hashMap {
    char *key;
    int value;
    UT_hash_handle hh;
};

struct hashMap *symbolTable = NULL;

typedef struct {
    char *opcode;
    int machineCode;
    int size;
} InstructionInfo;

InstructionInfo *instructionTable = NULL;
int instructionCount = 0;

unsigned char *instOutput = NULL;
size_t instOutputSize = 0;
size_t instOutputCapacity = 0;

unsigned char *dataOutput = NULL;
size_t dataOutputSize = 0;
size_t dataOutputCapacity = 0;

void put(const char *key_str, int val) {
    struct hashMap *item;
    HASH_FIND_STR(symbolTable, key_str, item);
    if (item == NULL) {
        item = malloc(sizeof(struct hashMap));
        item->key = strdup(key_str);
        item->value = val;
        HASH_ADD_KEYPTR(hh, symbolTable, item->key, strlen(item->key), item);
    } else {
        item->value = val;
    }
}

int get(const char *key_str) {
    struct hashMap *item;
    HASH_FIND_STR(symbolTable, key_str, item);
    if (item != NULL) {
        return item->value;
    }
    return -1;
}

void printSymbolTable() {
    struct hashMap *current, *temp;
    unsigned int symbolCount = HASH_COUNT(symbolTable);
    printf("\n---[SYMBOL TABLE]---\n");
    if (symbolCount == 0) {
        printf("symbolTable is empty\n");
    }
    HASH_ITER(hh, symbolTable, current, temp) {
        printf("Label: %s \t Addr: %d\n", current->key, current->value);
    }
    printf("--------------------\n");
}

void free_table() {
    struct hashMap *current, *tmp;
    HASH_ITER(hh, symbolTable, current, tmp) {
        HASH_DEL(symbolTable, current);
        free(current->key);
        free(current);
    }
}

int encodeRegister(const char *regName) {
    static const char *registers[] = {
        "A", "B", "C", "D", "E", "F", "G", "H",
        "SI", "DI", "RNG", "TEMPH", "TEMPL", NULL
    };
    for (int i = 0; registers[i] != NULL; i++) {
        if (strcasecmp(regName, registers[i]) == 0) {
            return i;
        }
    }
    return -1;
}

int loadInstructionSet(const char *path) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        perror("Failed to open instruction set file");
        return -1;
    }

    char line[256];
    instructionCount = 0;

    while (fgets(line, sizeof(line), fp)) {
        if (line[0] == '\n' || line[0] == '#' || strncmp(line, "opcode", 6) == 0) {
            continue;
        }

        char opcode[32];
        int size, machineCode;

        int fields = sscanf(line, " %31[^,],%d,%d", opcode, &size, &machineCode);
        if (fields == 3) {
            char *end = opcode + strlen(opcode) - 1;
            while (end > opcode && isspace((unsigned char)*end)) end--;
            *(end + 1) = '\0';

            instructionTable = realloc(instructionTable, (instructionCount + 1) * sizeof(InstructionInfo));
            instructionTable[instructionCount].opcode = strdup(opcode);
            instructionTable[instructionCount].size = size;
            instructionTable[instructionCount].machineCode = machineCode;
            instructionCount++;
        }
    }

    fclose(fp);
    return 0;
}

InstructionInfo *lookupInstruction(const char *opcode) {
    for (int i = 0; i < instructionCount; i++) {
        if (strcasecmp(opcode, instructionTable[i].opcode) == 0) {
            return &instructionTable[i];
        }
    }
    return NULL;
}

void emitInstByte(unsigned char byte) {
    if (instOutputSize >= instOutputCapacity) {
        instOutputCapacity = instOutputCapacity == 0 ? 256 : instOutputCapacity * 2;
        instOutput = realloc(instOutput, instOutputCapacity);
    }
    instOutput[instOutputSize++] = byte;
}

void emitDataByte(unsigned char byte) {
    if (dataOutputSize >= dataOutputCapacity) {
        dataOutputCapacity = dataOutputCapacity == 0 ? 256 : dataOutputCapacity * 2;
        dataOutput = realloc(dataOutput, dataOutputCapacity);
    }
    dataOutput[dataOutputSize++] = byte;
}

int getDataSize(dataType type) {
    switch (type) {
        case int8:
        case chr:
            return 1;
        case int16:
            return 2;
        case str:
        case boolean:
        default:
            return 1;
    }
}

void firstPass() {
    address = 0;
    hasStartLabel = 0;

    if (ast_root == NULL) return;

    for (size_t s = 0; s < ast_root->childCount; s++) {
        astNode *sec = ast_root->children[s];
        if (sec->type != section) continue;

        astNode *node = sec->childCount > 0 ? sec->children[0] : NULL;
        while (node != NULL) {
            if (node->type == labelDef) {
                put(node->as.label.name, address);
                if (strcasecmp(node->as.label.name, "START") == 0) {
                    hasStartLabel = 1;
                }
            } else if (node->type == instruction) {
                InstructionInfo *info = lookupInstruction(node->as.instruction.opcode);
                if (info) {
                    address += info->size;
                }
            } else if (node->type == dataDeclaration) {
                dataType dt = node->as.dataDeclaration.type;
                address += getDataSize(dt);
            }
            node = node->nextSibling;
        }
    }
}

void secondPass() {
    if (ast_root == NULL) return;

    for (size_t s = 0; s < ast_root->childCount; s++) {
        astNode *sec = ast_root->children[s];
        if (sec->type != section) continue;

        int isDataSection = (sec->as.section.name && strcasecmp(sec->as.section.name, "data") == 0);

        astNode *node = sec->childCount > 0 ? sec->children[0] : NULL;
        while (node != NULL) {
            if (node->type == instruction) {
                InstructionInfo *info = lookupInstruction(node->as.instruction.opcode);

                if (info == NULL) {
                    continue;
                }

                // Encode size in top 2 bits: (size-1) << 6 | opcode
                int sizeBits = info->size - 1; // 0=1byte, 1=2bytes, 2=3bytes, 3=4bytes
                unsigned char instructionByte = (unsigned char)((sizeBits << 6) | info->machineCode);
                emitInstByte(instructionByte);

                size_t operandCount = node->childCount;

                if (strcasecmp(node->as.instruction.opcode, "lin") == 0 ||
                    strcasecmp(node->as.instruction.opcode, "sin") == 0) {
                    printf("Warning: %s is a future addition, not implemented\n", node->as.instruction.opcode);
                    continue;
                }

                if (info->size == 1) {
                    // no operand
                } else if (info->size == 2) {
                    if (operandCount == 1 && node->children[0]->type == reg) {
                        int regIdx = encodeRegister(node->children[0]->as.reg.name);
                        emitInstByte((unsigned char)regIdx);
                    } else if (operandCount == 2 && node->children[0]->type == reg && node->children[1]->type == reg) {
                        int regDest = encodeRegister(node->children[0]->as.reg.name); // first operand = destination
                        int regSrc = encodeRegister(node->children[1]->as.reg.name); // second operand = source
                        unsigned char byte = (unsigned char)((regDest << 4) | regSrc);
                        emitInstByte(byte);
                    } else if (operandCount == 1 && node->children[0]->type == literal) {
                        emitInstByte((unsigned char)node->children[0]->as.literal.intValue);
                    }
                } else if (info->size == 3) {
                    if (operandCount == 3 && node->children[0]->type == reg && 
                        node->children[1]->type == reg && node->children[2]->type == reg) {
                        // For 3-register: ADD C, A, B means C = A + B
                        // Emit: (srcB << 4) | srcA, then dest
                        int regA = encodeRegister(node->children[1]->as.reg.name); // first source (A)
                        int regB = encodeRegister(node->children[2]->as.reg.name); // second source (B)
                        int regC = encodeRegister(node->children[0]->as.reg.name); // destination (C)
                        emitInstByte((unsigned char)((regB << 4) | regA));
                        emitInstByte((unsigned char)regC);
                    } else if (operandCount == 3 && node->children[0]->type == reg && 
                               node->children[1]->type == reg && node->children[2]->type == literal) {
                        // For 2-reg + immediate: ADI D, A, 4 means D = A + 4
                        // Emit: (dest << 4) | src, then immediate
                        int regA = encodeRegister(node->children[1]->as.reg.name); // source
                        int regDest = encodeRegister(node->children[0]->as.reg.name); // destination
                        int imm = node->children[2]->as.literal.intValue;
                        emitInstByte((unsigned char)((regDest << 4) | regA));
                        emitInstByte((unsigned char)imm);
                    } else if (operandCount == 1 && node->children[0]->type == labelRef) {
                        int addr = get(node->children[0]->as.label.name);
                        if (addr >= 0) {
                            emitInstByte((unsigned char)(addr & 0xFF));
                            emitInstByte((unsigned char)((addr >> 8) & 0xFF));
                        }
                    } else {
                        if (operandCount >= 1 && node->children[0]->type == reg) {
                            int regIdx = encodeRegister(node->children[0]->as.reg.name);
                            emitInstByte((unsigned char)regIdx);
                        }
                        if (operandCount >= 2) {
                            if (node->children[1]->type == literal) {
                                emitInstByte((unsigned char)node->children[1]->as.literal.intValue);
                            } else if (node->children[1]->type == reg) {
                                int regIdx = encodeRegister(node->children[1]->as.reg.name);
                                emitInstByte((unsigned char)regIdx);
                            }
                        }
                    }
                } else if (info->size == 4) {
                    if (strcasecmp(node->as.instruction.opcode, "st") == 0) {
                        if (operandCount >= 2 && node->children[1]->type == reg) {
                            int regIdx = encodeRegister(node->children[1]->as.reg.name);
                            emitInstByte((unsigned char)regIdx);
                        }
                        if (operandCount >= 1 && node->children[0]->type == literal) {
                            int addr = node->children[0]->as.literal.intValue;
                            emitInstByte((unsigned char)(addr & 0xFF));
                            emitInstByte((unsigned char)((addr >> 8) & 0xFF));
                        }
                    } else if (strcasecmp(node->as.instruction.opcode, "ld") == 0) {
                        if (operandCount >= 1 && node->children[0]->type == reg) {
                            int regIdx = encodeRegister(node->children[0]->as.reg.name);
                            emitInstByte((unsigned char)regIdx);
                        }
                        if (operandCount >= 2 && node->children[1]->type == literal) {
                            int addr = node->children[1]->as.literal.intValue;
                            emitInstByte((unsigned char)(addr & 0xFF));
                            emitInstByte((unsigned char)((addr >> 8) & 0xFF));
                        }
                    } else if (strcasecmp(node->as.instruction.opcode, "sti") == 0) {
                        if (operandCount >= 1 && node->children[0]->type == literal) {
                            int addr = node->children[0]->as.literal.intValue;
                            emitInstByte((unsigned char)(addr & 0xFF));
                            emitInstByte((unsigned char)((addr >> 8) & 0xFF));
                        }
                        if (operandCount >= 2 && node->children[1]->type == literal) {
                            emitInstByte((unsigned char)node->children[1]->as.literal.intValue);
                        } else {
                            emitInstByte(0);
                        }
                    }
                }
            } else if (node->type == dataDeclaration) {
                if (isDataSection) {
                    dataType dt = node->as.dataDeclaration.type;
                    if (node->childCount >= 2 && node->children[1]->type == literal) {
                        int val = node->children[1]->as.literal.intValue;
                        int size = getDataSize(dt);
                        if (size == 1) {
                            emitDataByte((unsigned char)(val & 0xFF));
                        } else if (size == 2) {
                            emitDataByte((unsigned char)(val & 0xFF));
                            emitDataByte((unsigned char)((val >> 8) & 0xFF));
                        }
                    }
                }
            }
            node = node->nextSibling;
        }
    }
}

void exportTxt(const char *baseName) {
    char instFileName[256];
    char dataFileName[256];

    snprintf(instFileName, sizeof(instFileName), "%s_inst.txt", baseName);
    snprintf(dataFileName, sizeof(dataFileName), "%s_data.txt", baseName);

    FILE *instFile = fopen(instFileName, "w");
    if (!instFile) {
        perror("Failed to open inst output file");
        return;
    }
    for (size_t i = 0; i < instOutputSize; i++) {
        fprintf(instFile, "0x%02X\n", instOutput[i]);
    }
    fclose(instFile);

    FILE *dataFile = fopen(dataFileName, "w");
    if (!dataFile) {
        perror("Failed to open data output file");
        return;
    }
    for (size_t i = 0; i < dataOutputSize; i++) {
        fprintf(dataFile, "0x%02X\n", dataOutput[i]);
    }
    fclose(dataFile);

    printf("Output written to %s and %s\n", instFileName, dataFileName);
}

void exportBin(const char *baseName) {
    char instFileName[256];
    char dataFileName[256];

    snprintf(instFileName, sizeof(instFileName), "%s_inst.bin", baseName);
    snprintf(dataFileName, sizeof(dataFileName), "%s_data.bin", baseName);

    FILE *instFile = fopen(instFileName, "wb");
    if (instFile && instOutputSize > 0) {
        fwrite(instOutput, 1, instOutputSize, instFile);
        fclose(instFile);
    }

    FILE *dataFile = fopen(dataFileName, "wb");
    if (dataFile && dataOutputSize > 0) {
        fwrite(dataOutput, 1, dataOutputSize, dataFile);
        fclose(dataFile);
    }
}

char *getBaseName(const char *path) {
    char *base = strdup(path);
    char *dot = strrchr(base, '.');
    if (dot) {
        *dot = '\0';
    }
    return base;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Usage: %s <input.asm>\n", argv[0]);
        return 1;
    }

    if (loadInstructionSet("data/instructionSet.csv") < 0) {
        printf("Failed to load instruction set\n");
        return 1;
    }

    yyin = fopen(argv[1], "r");
    if (!yyin) {
        perror("Failed to open file");
        return 1;
    }

    int result = yyparse();
    fclose(yyin);

    if (result == 0) {
        firstPass();
        printSymbolTable();

        if (!hasStartLabel) {
            printf("Warning: No $START label defined\n");
        }

        secondPass();

        char *baseName = getBaseName(argv[1]);
        exportTxt(baseName);

        free(baseName);
    }

    free_table();

    if (instructionTable) {
        for (int i = 0; i < instructionCount; i++) {
            free(instructionTable[i].opcode);
        }
        free(instructionTable);
    }

    if (instOutput) free(instOutput);
    if (dataOutput) free(dataOutput);

    return result;
}
