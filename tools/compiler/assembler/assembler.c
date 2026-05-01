#include "ast.h"
#include "cJSON.h"
#include "uthash.h"
#include <bits/pthreadtypes.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_ERRORS 100

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

void get(const char *key_str) {
  struct hashMap *item;
  HASH_FIND_STR(symbolTable, key_str, item);
  if (item != NULL) {
    printf("Found [%s] : %d\n", item->key, item->value);
  } else {
    printf("[%s] not found.\n", key_str);
  }
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

void free_table() {
  struct hashMap *current, *tmp;
  HASH_ITER(hh, symbolTable, current, tmp) {
    HASH_DEL(symbolTable, current);
    free(current->key); // Don't forget to free the strdup'd key!
    free(current);      // Free the struct
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

void printInstructionTable() {
  struct hashMap *current, *temp;
  unsigned int count = HASH_COUNT(instructionTable);
  printf("\n---[INSTRUCTION TABLE]---\n");
  if (count == 0) {
    printf("instructionTable is empty\n");
    return;
  }
  HASH_ITER(hh, instructionTable, current, temp) {
    printf("Opcode: %s \t Code: %d\n", current->key, current->value);
  }
  printf("-------------------------\n");
}

// =-=-=-=-=-=[my stuffs]=-=-=-=-=-=

void collectLabels(astNode *node) {
  if (!node) return;
  if (node->type == labelDef) {
    struct hashMap *existing;
    HASH_FIND_STR(symbolTable, node->as.label.name, existing);
    if (existing != NULL) {
      addError(0, "Duplicate label '%s'", node->as.label.name);
    }
    put(node->as.label.name, symbolAddress);
  }
  for (size_t i = 0; i < node->childCount; i++) {
    collectLabels(node->children[i]);
  }
}

void resolvePass(astNode *node, astNode *parent) {
  if (!node) return;

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

typedef struct {
  char *opcode;
  int operands[4];
  int operandCount;
} inRep;

void dump_dot(const char *path) {
  FILE *f = fopen(path, "w");
  if (!f) {
    perror("Failed to open DOT output file");
    return;
  }
  print_ast_json(ast_root, f);
  fclose(f);
}

void emitCode(astNode *node, FILE *instFile) {
  if (!node) return;

  switch (node->type) {
  case dataDeclaration:
  case labelDef:
    return;
  case instruction: {
    inRep inst;
    inst.opcode = node->as.instruction.opcode;
    inst.operandCount = 0;

    for (size_t i = 0; i < node->childCount; i++) {
      astNode *child = node->children[i];
      if (child->type == literal) {
        // TODO: encode literal operand
        // child->as.literal.intValue contains the resolved address/value
        // add encoding logic here, write to instFile
      } else if (child->type == reg) {
        // TODO: encode register operand
        // child->as.reg.name contains the register name (e.g. "A", "B")
        // map to numeric encoding and write to instFile
      }
    }

    // TODO: write fully encoded instruction bytes to instFile
    // currently only the opcode byte is written, operands are skipped
    int machineCode = getMachineCode(inst.opcode);
    if (machineCode != -1) {
      write_value(instFile, machineCode);
    } else {
      addError(0, "Unknown opcode '%s'", inst.opcode);
    }
    instAddress++;

    return;
  }
  case literal:
    // orphan literal — skip (not an instruction child)
    return;
  default:
    break;
  }

  for (size_t i = 0; i < node->childCount; i++) {
    emitCode(node->children[i], instFile);
  }
}

void secondPass() {
  FILE *dataFile = fopen("out/dataSegment.txt", "w");
  FILE *instFile = fopen("out/instSegment.txt", "w");

  if (dataFile == NULL || instFile == NULL) {
    perror("fopen");
    return;
  }

  for (int i = 0; i < dataValuesCount; i++) {
    write_value(dataFile, dataValues[i]);
  }

  // == do code generation here ==
  emitCode(ast_root, instFile);
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
