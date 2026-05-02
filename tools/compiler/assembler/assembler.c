#include "ast.h"
#include "cJSON.h"
#include "uthash.h"
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_ERRORS 100

#define A 0
#define B 1
#define C 2
#define D 3
#define E 4
#define F 5
#define G 6
#define H 7
#define SI 8
#define DI 9
#define RNG 10
#define SP 11
#define PC 12
#define templ 13
#define temph 14

#define HIGH_BYTE(x) (((x) >> 8) & 0xFF)
#define LOW_BYTE(x) ((x) & 0xFF)
#define PACK_REGS(a, b) (((b) << 4) | ((a) & 0xF))

int getLiteralValue(astNode *node) {
  if (!node || node->type != literal) return 0;
  if (node->as.literal.value) {
    char c = node->as.literal.value[0];
    if (c >= '0' && c <= '9')
      return atoi(node->as.literal.value);
    if (c == '-' && node->as.literal.value[1] >= '0' && node->as.literal.value[1] <= '9')
      return atoi(node->as.literal.value);
  }
  return node->as.literal.intValue;
}

int getInstSize(int machineCode) {
  switch (machineCode) {
  case 0: return 1;  // nope
  case 1: return 1;  // hlt
  case 12: return 2; // not
  case 17: return 2; // iin
  case 18: return 2; // din
  case 19: return 2; // cmp
  case 25: return 2; // mv
  case 29: return 2; // sti
  case 30: return 2; // lin
  case 31: return 2; // sin
  case 32: return 2; // rin
  case 33: return 2; // rpc
  case 34: return 2; // rsp
  case 35: return 2; // con
  case 36: return 2; // cor
  case 37: return 2; // can
  case 38: return 3; // jmp
  case 39: return 2; // set
  default: return 3; // most 3-operand instructions (add, adi, etc)
  }
}

int regToNum(const char *name) {
  if (!name)
    return -1;
  if (strcmp(name, "A") == 0 || strcmp(name, "a") == 0)
    return A;
  if (strcmp(name, "B") == 0 || strcmp(name, "b") == 0)
    return B;
  if (strcmp(name, "C") == 0 || strcmp(name, "c") == 0)
    return C;
  if (strcmp(name, "D") == 0 || strcmp(name, "d") == 0)
    return D;
  if (strcmp(name, "E") == 0 || strcmp(name, "e") == 0)
    return E;
  if (strcmp(name, "F") == 0 || strcmp(name, "f") == 0)
    return F;
  if (strcmp(name, "G") == 0 || strcmp(name, "g") == 0)
    return G;
  if (strcmp(name, "H") == 0 || strcmp(name, "h") == 0)
    return H;
  if (strcmp(name, "SI") == 0 || strcmp(name, "si") == 0)
    return SI;
  if (strcmp(name, "DI") == 0 || strcmp(name, "di") == 0)
    return DI;
  if (strcmp(name, "RNG") == 0 || strcmp(name, "rng") == 0)
    return RNG;
  if (strcmp(name, "SP") == 0 || strcmp(name, "sp") == 0)
    return SP;
  if (strcmp(name, "PC") == 0 || strcmp(name, "pc") == 0)
    return PC;
  if (strcmp(name, "templ") == 0)
    return templ;
  if (strcmp(name, "temph") == 0)
    return temph;
  return -1;
}

typedef struct {
  int line;
  char message[256];
} Error;

Error errors[MAX_ERRORS];
int errorCount = 0;

void addError(int line, const char *fmt, ...) {
  if (errorCount < MAX_ERRORS) {
    va_list args;
    va_start(args, fmt);
    errors[errorCount].line = line;
    vsnprintf(errors[errorCount].message, 255, fmt, args);
    errors[errorCount].message[255] = '\0';
    va_end(args);
    errorCount++;
  }
}

void printErrors() {
  if (errorCount == 0)
    return;
  fprintf(stderr, "\n=== ASSEMBLY ERRORS ===\n");
  for (int i = 0; i < errorCount; i++) {
    fprintf(stderr, "line %d: %s\n", errors[i].line, errors[i].message);
  }
  fprintf(stderr, "=======================\n");
}

int hasErrors() { return errorCount > 0; }

extern int yyparse();
extern FILE *yyin;
extern astNode *ast_root;
extern char *yytext;
extern const char *node_type_str(nodeType type);
extern const char *data_type_str(dataType type);

int symbolAddress = 0;
int dataAddress = 0;
int instAddress = 0;

struct hashMap {
  char *key;
  int value;
  UT_hash_handle hh;
};

struct hashMap *symbolTable = NULL;
struct hashMap *dataTable = NULL;

struct hashMap *instructionTable = NULL;

#define MAX_DATA_ENTRIES 256
int dataValues[MAX_DATA_ENTRIES];
int dataValuesCount = 0;

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

void printSymbolTable() {
  struct hashMap *current, *temp;
  unsigned int symbolCount = HASH_COUNT(symbolTable);
  printf("\n---[SYMBOL TABLE]---\n");
  if (symbolCount == 0) {
    printf("symbolTable is empty\n");
    return;
  }
  HASH_ITER(hh, symbolTable, current, temp) {
    printf("Label: %s \t Addr: %d\n", current->key, current->value);
  }
  printf("--------------------\n");
}

void printDataTable() {
  struct hashMap *current, *temp;
  unsigned int dataCount = HASH_COUNT(dataTable);
  printf("\n---[DATA TABLE]---\n");
  if (dataCount == 0) {
    printf("dataTable is empty\n");
    return;
  }
  HASH_ITER(hh, dataTable, current, temp) {
    printf("Data: %s \t Addr: %d\n", current->key, current->value);
  }
  printf("------------------\n");
}

void putData(const char *key_str, int val) {
  struct hashMap *item;
  HASH_FIND_STR(dataTable, key_str, item);
  if (item == NULL) {
    item = malloc(sizeof(struct hashMap));
    item->key = strdup(key_str);
    item->value = val;
    HASH_ADD_KEYPTR(hh, dataTable, item->key, strlen(item->key), item);
  } else {
    item->value = val;
  }
}

int write_value(FILE *fp, int val) {
  if (fp == NULL)
    return -1;
  if (fprintf(fp, "%X\n", val) < 0)
    return -1;
  return 0;
}

int getMachineCode(const char *opcode) {
  char key[32];
  int len = strlen(opcode);
  if (len >= 32)
    len = 31;
  for (int i = 0; i < len; i++) {
    key[i] = opcode[i] >= 'A' && opcode[i] <= 'Z' ? opcode[i] + 32 : opcode[i];
  }
  key[len] = '\0';
  struct hashMap *item;
  HASH_FIND_STR(instructionTable, key, item);
  if (item != NULL)
    return item->value;
  return -1;
}

void loadInstructionTable() {
  FILE *fp = fopen("data/instructionSet.json", "r");
  if (!fp) {
    perror("Failed to open instructionSet.json");
    return;
  }

  fseek(fp, 0, SEEK_END);
  long len = ftell(fp);
  fseek(fp, 0, SEEK_SET);

  char *jsonStr = malloc(len + 1);
  fread(jsonStr, 1, len, fp);
  jsonStr[len] = '\0';
  fclose(fp);

  cJSON *json = cJSON_Parse(jsonStr);
  free(jsonStr);
  if (!json) {
    fprintf(stderr, "Failed to parse instructionSet.json: %s\n",
            cJSON_GetErrorPtr());
    return;
  }

  int count = cJSON_GetArraySize(json);
  for (int i = 0; i < count; i++) {
    cJSON *entry = cJSON_GetArrayItem(json, i);
    cJSON *opcode = cJSON_GetObjectItem(entry, "opcode");
    cJSON *machineCode = cJSON_GetObjectItem(entry, "machineCode");

    if (opcode && machineCode) {
      struct hashMap *item = malloc(sizeof(struct hashMap));
      item->key = strdup(opcode->valuestring);
      item->value = atoi(machineCode->valuestring);
      HASH_ADD_KEYPTR(hh, instructionTable, item->key, strlen(item->key), item);
    }
  }

  cJSON_Delete(json);
}

// =-=-=-=-=-=[my stuffs]=-=-=-=-=-=

void collectLabels(astNode *node) {
  if (!node)
    return;
  if (node->type == labelDef) {
    struct hashMap *existing;
    HASH_FIND_STR(symbolTable, node->as.label.name, existing);
    if (existing != NULL) {
      addError(0, "Duplicate label '%s'", node->as.label.name);
    }
    put(node->as.label.name, symbolAddress);
    for (size_t i = 0; i < node->childCount; i++) {
      collectLabels(node->children[i]);
    }
    return;
  }
  if (node->type == instruction) {
    char *op = node->as.instruction.opcode;
    int mc = getMachineCode(op);
    if (mc >= 0) {
      symbolAddress += getInstSize(mc);
    }
    return;
  }
  for (size_t i = 0; i < node->childCount; i++) {
    collectLabels(node->children[i]);
  }
}

void resolvePass(astNode *node, astNode *parent) {
  if (!node)
    return;

  switch (node->type) {
  case dataDeclaration:
    if (node->as.dataDeclaration.type != str) {
      char *name = node->children[0]->as.identifier.name;
      char *valStr = node->children[1]->as.literal.value;
      int value = atoi(valStr);
      putData(name, dataAddress);
      dataValues[dataValuesCount++] = value;
      dataAddress++;
    }
    for (size_t i = 0; i < node->childCount; i++) {
      resolvePass(node->children[i], node);
    }
    return;
  case instruction:
    for (size_t i = 0; i < node->childCount; i++) {
      resolvePass(node->children[i], node);
    }
    return;
  case identifier:
    if (parent && parent->type == instruction) {
      struct hashMap *item;
      HASH_FIND_STR(dataTable, node->as.identifier.name, item);
      if (item != NULL) {
        node->as.literal.intValue = item->value;
        node->type = literal;
      } else {
        addError(0, "Undefined variable '%s'", node->as.identifier.name);
      }
    }
    return;
  case labelRef:
    if (parent && parent->type == instruction) {
      struct hashMap *item;
      HASH_FIND_STR(symbolTable, node->as.label.name, item);
      if (item != NULL) {
        node->as.literal.intValue = item->value;
        node->type = literal;
      } else {
        addError(0, "Undefined label reference '%s'", node->as.label.name);
      }
    }
    return;
  default:
    break;
  }

  for (size_t i = 0; i < node->childCount; i++) {
    resolvePass(node->children[i], node);
  }
}

void firstPass() {
  dataValuesCount = 0;
  collectLabels(ast_root);
  resolvePass(ast_root, NULL);
}

void dump_dot(const char *path) {
  FILE *f = fopen(path, "w");
  if (!f) {
    perror("Failed to open DOT output file");
    return;
  }
  print_ast_json(ast_root, f);
  fclose(f);
}

void emitCode(astNode *node, FILE *instFile, FILE *binFile) {
  if (!node)
    return;

  switch (node->type) {
  case dataDeclaration:
  case labelDef:
    return;

  case instruction: {
    char *op = node->as.instruction.opcode;
    int machineCode = getMachineCode(op);
    if (machineCode == -1) {
      addError(0, "Unknown opcode '%s'", op);
      return;
    }

    astNode *op1 = node->childCount > 0 ? node->children[0] : NULL;
    astNode *op2 = node->childCount > 1 ? node->children[1] : NULL;
    astNode *op3 = node->childCount > 2 ? node->children[2] : NULL;

    int r1 = (op1 && op1->type == reg) ? regToNum(op1->as.reg.name) : 0;
    int r2 = (op2 && op2->type == reg) ? regToNum(op2->as.reg.name) : 0;
    int i1 = (op1 && op1->type == literal) ? getLiteralValue(op1) : 0;
    int i2 = (op2 && op2->type == literal) ? getLiteralValue(op2) : 0;
    int i3 = (op3 && op3->type == literal) ? getLiteralValue(op3) : 0;

    unsigned char bytes[64];
    int byteCount = 0;
    bytes[byteCount++] = (unsigned char)machineCode;

    switch (machineCode) {
    case 0: // nope
    case 1: // hlt
      break;

    case 2: // add regRes, regA, regB
    case 4: // addc regRes, regA, regB
    case 5: // sub regRes, regA, regB
    case 7: // subb regRes, regA, regB
    case 8: // and regRes, regA, regB
    case 10: // or regRes, regA, regB
    case 13: // xor regRes, regA, regB
    case 15: // xnr regRes, regA, regB
    case 20: // rs regRes, regA, regB
    case 21: // ls regRes, regA, regB
    case 22: // rr regRes, regA, regB
    case 23: // lr regRes, regA, regB
    case 24: // ars regRes, regA, regB
      bytes[byteCount++] = (unsigned char)PACK_REGS(r1, r2);
      break;

    case 3: // adi regRes, regA, imm
    case 6: // sui regRes, regA, imm
    case 9: // ani regRes, regA, imm
    case 11: // ori regRes, regA, imm
    case 14: // xri regRes, regA, imm
    case 16: // xni regRes, regA, imm
      bytes[byteCount++] = (unsigned char)PACK_REGS(r1, r2);
      bytes[byteCount++] = (unsigned char)(i3 & 0xFF);
      break;

    case 12: // not regRes, regA
      bytes[byteCount++] = (unsigned char)PACK_REGS(r1, r2);
      break;

    case 17: // iin si/di
    case 18: // din si/di
      bytes[byteCount++] = (unsigned char)(r1 & 0xF);
      break;

    case 19: // cmp regA, regB
      bytes[byteCount++] = (unsigned char)PACK_REGS(r1, r2);
      break;

    case 25: // mv regA, regB
    case 32: // rin regA, regB
    case 33: // rpc regA, regB
    case 34: // rsp regA, regB
      bytes[byteCount++] = (unsigned char)PACK_REGS(r1, r2);
      break;

    case 26: // ld regA, addr
      bytes[byteCount++] = (unsigned char)(r1 & 0xF);
      bytes[byteCount++] = (unsigned char)HIGH_BYTE(i2);
      bytes[byteCount++] = (unsigned char)LOW_BYTE(i2);
      break;

    case 27: // ldi regA, imm
      bytes[byteCount++] = (unsigned char)(i2 & 0xFF);
      bytes[byteCount++] = (unsigned char)HIGH_BYTE(i3);
      bytes[byteCount++] = (unsigned char)LOW_BYTE(i3);
      break;

    case 28: // st addr, reg
      bytes[byteCount++] = (unsigned char)(r2 & 0xF);
      bytes[byteCount++] = (unsigned char)HIGH_BYTE(i1);
      bytes[byteCount++] = (unsigned char)LOW_BYTE(i1);
      break;

    case 29: // sti addr, imm
      bytes[byteCount++] = (unsigned char)(i2 & 0xFF);
      bytes[byteCount++] = (unsigned char)HIGH_BYTE(i1);
      bytes[byteCount++] = (unsigned char)LOW_BYTE(i1);
      break;

    case 30: // lin regsi/di, imm16
      bytes[byteCount++] = (unsigned char)(r1 & 0xF);
      bytes[byteCount++] = (unsigned char)HIGH_BYTE(i2);
      bytes[byteCount++] = (unsigned char)LOW_BYTE(i2);
      break;

    case 31: // sin
      bytes[byteCount++] = (unsigned char)(r1 & 0xF);
      bytes[byteCount++] = (unsigned char)HIGH_BYTE(i2);
      bytes[byteCount++] = (unsigned char)LOW_BYTE(i2);
      break;

    case 35: // con <flag bit number>
      bytes[byteCount++] = (unsigned char)(i1 & 0xFF);
      break;

    case 36: // cor <8 bit mask>
      bytes[byteCount++] = (unsigned char)(i1 & 0xFF);
      break;

    case 37: // can <8 bit mask>
      bytes[byteCount++] = (unsigned char)(i1 & 0xFF);
      break;

    case 38: // jmp addr
      bytes[byteCount++] = (unsigned char)HIGH_BYTE(i1);
      bytes[byteCount++] = (unsigned char)LOW_BYTE(i1);
      break;

    case 39: // set <8 bit mask>
      bytes[byteCount++] = (unsigned char)(i1 & 0xFF);
      break;

    default:
      break;
    }

    for (int i = 0; i < byteCount; i++) {
      write_value(instFile, bytes[i]);
      if (binFile) {
        fputc(bytes[i], binFile);
      }
    }

    instAddress += getInstSize(machineCode);
    return;
  }
  case literal:
    return;

  default:
    break;
  }

  for (size_t i = 0; i < node->childCount; i++) {
    emitCode(node->children[i], instFile, binFile);
  }
}

void secondPass() {
  FILE *dataFile = fopen("out/dataSegment.txt", "w");
  FILE *instFile = fopen("out/instSegment.txt", "w");
  FILE *binFile = fopen("out/program.bin", "wb");

  if (dataFile == NULL || instFile == NULL) {
    perror("fopen");
    return;
  }

  for (int i = 0; i < dataValuesCount; i++) {
    write_value(dataFile, dataValues[i]);
  }

  // == do code generation here ==
  emitCode(ast_root, instFile, binFile);
  // == end generation here ==

  if (fclose(dataFile) != 0) {
    perror("fclose");
    exit(EXIT_FAILURE);
  }
  printf("File '%s' dataFile written successfully.\n", "dataSegment.txt");

  if (fclose(instFile) != 0) {
    perror("fclose");
    exit(EXIT_FAILURE);
  }
  printf("File '%s' instructionFile written successfully.\n",
         "instSegment.txt");

  if (binFile) {
    if (fclose(binFile) != 0) {
      perror("fclose");
      exit(EXIT_FAILURE);
    }
    printf("File 'program.bin' written successfully.\n");
  }
}

int main(int argc, char **argv) {
  if (argc < 2) {
    printf("Usage: %s <input.asm>\n", argv[0]);
    return 1;
  }

  yyin = fopen(argv[1], "r");
  if (!yyin) {
    perror("Failed to open file");
    return 1;
  }
  int result = yyparse();
  fclose(yyin);

  if (result != 0) {
    printErrors();
    return result;
  }

  loadInstructionTable();

  dump_dot("out/ast_pre.dot");

  firstPass();

  dump_dot("out/ast_post.dot");
  printErrors();

  if (hasErrors()) {
    return 1;
  }

  print_ast_json(ast_root, stdout);
  secondPass();
  printSymbolTable();
  printDataTable();
  return 0;
}

// =-=-=-=-=-=[end my stuffs]=-=-=-=-=-=
