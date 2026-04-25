#include "ast.h"
#include "uthash.h"
#include <bits/pthreadtypes.h>
#include <stdio.h>
#include <stdlib.h>

extern int yyparse();
extern FILE *yyin;
extern astNode *ast_root;
extern astNode *getNextNode();
astNode *initTraversal(astNode *root);
extern char *yytext;

astNode *traversalCurr;
astNode *traversalNext;
int address = 0;

struct hashMap {
  char *key;
  int value;
  UT_hash_handle hh;
};

struct hashMap *symbolTable = NULL;

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

void get(const char *key_str) {
  struct hashMap *item;

  HASH_FIND_STR(symbolTable, key_str, item);

  if (item != NULL) {
    printf("Found [%s] : %d\n", item->key, item->value);
  } else {
    printf("[%s] not found.\n", key_str);
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

void firstPass() {
  while (1) {
    traversalCurr = getNextNode();
    if (traversalCurr == NULL) {
      break;
    }
    if (traversalCurr->type == labelDef) {
      put(traversalCurr->as.label.name, address);
    }
  }
}

void secondPass() {
  // code generation
}

// main function
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

  if (result == 0) {
    print_ast_json(ast_root, stdout);
    initTraversal(ast_root);
    secondPass();
    firstPass();
    printSymbolTable();
  }
  return result;
}
