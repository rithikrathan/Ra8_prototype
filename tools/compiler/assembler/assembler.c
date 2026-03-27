#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

// token definitions
#define ERROR -1
#define INST 1
#define REG 2
#define BIN 3
#define HEX 4
#define NUM 5
#define DATA_TYPE 6
#define LABELDEF 7
#define LABELREF 8
#define END 9
#define EQUALS 11
#define POINTER_EQUALS 12
#define IDENTIFIER 13
#define DATASEGMENTSTART 14
#define INSTSEGMENTSTART 15
#define LINKSEGMENTSTART 16
#define STRING_LITERAL 17

// use variables from the lexer
extern FILE *yyin;
extern int yylex();
extern char *yytext;
extern int yyleng;

// helper functions
int str2int(char *text, int token_type) {
  if (token_type == NUM) {
    return (int)strtol(text, NULL, 10);
  }
  if (token_type == HEX) {
    return (int)strtol(text + 2, NULL, 16);
  }
  if (token_type == BIN) {
    return (int)strtol(text + 2, NULL, 2);
  }
  return 0;
}

char *cleanup(int instruction, char *yt, int len) {
  int newlen;
  char *res;

  switch (instruction) {
  case LABELDEF:
    newlen = len - 2;
    if (newlen < 0)
      return NULL;
    res = (char *)malloc(newlen + 1);
    strncpy(res, yt + 1, newlen);
    res[newlen] = '\0';
    break;

  case LABELREF:
    newlen = len - 1;
    if (newlen < 0)
      return NULL;
    res = (char *)malloc(newlen + 1);
    strncpy(res, yt + 1, newlen);
    res[newlen] = '\0';
    break;
  }
  return res;
}

// data segment structures
typedef struct {
    char name[64];
    char type[16];
    int intValue;
    char strValue[256];
    bool isPointer;
    bool hasValue;
} DataVariable;

DataVariable dataVars[100];
int dataVarCount = 0;

// parsing state
typedef enum {
    STATE_NONE,
    STATE_IN_DATA,
    EXPECTING_TYPE,
    EXPECTING_NAME,
    EXPECTING_ASSIGN,
    EXPECTING_VALUE,
    STATE_IN_INST
} ParseState;

ParseState currentState = STATE_NONE;
DataVariable currentVar;

// reset current variable
void resetCurrentVar() {
    memset(currentVar.name, 0, sizeof(currentVar.name));
    memset(currentVar.type, 0, sizeof(currentVar.type));
    memset(currentVar.strValue, 0, sizeof(currentVar.strValue));
    currentVar.intValue = 0;
    currentVar.isPointer = false;
    currentVar.hasValue = false;
}

// add completed variable to list
void addDataVar() {
    if (currentVar.hasValue) {
        dataVars[dataVarCount++] = currentVar;
    }
    resetCurrentVar();
}

// remove surrounding quotes from string
void stripQuotes(char *dest, const char *src, int len) {
    strncpy(dest, src + 1, len - 2);
    dest[len - 2] = '\0';
}

void runLexer() {
  printf("--- Running assembler ---\n");
  int token;
  resetCurrentVar();

  while ((token = yylex()) != 0) {
    switch (token) {
    case DATASEGMENTSTART:
      printf("Parsing data segment...\n");
      currentState = STATE_IN_DATA;
      resetCurrentVar();
      break;

    case INSTSEGMENTSTART:
      printf("Parsing instruction segment...\n");
      currentState = STATE_IN_INST;
      break;

    case END:
      if (currentState == STATE_IN_DATA) {
        addDataVar();
        printf("Data segment complete.\n");
      }
      currentState = STATE_NONE;
      break;

    case DATA_TYPE:
      if (currentState == STATE_IN_DATA || currentState == EXPECTING_TYPE) {
        addDataVar();
        strncpy(currentVar.type, yytext, yyleng);
        currentVar.type[yyleng] = '\0';
        currentState = EXPECTING_NAME;
      }
      break;

    case IDENTIFIER:
      if (currentState == EXPECTING_NAME) {
        strncpy(currentVar.name, yytext, yyleng);
        currentVar.name[yyleng] = '\0';
        currentState = EXPECTING_ASSIGN;
      }
      break;

    case EQUALS:
      if (currentState == EXPECTING_ASSIGN) {
        currentVar.isPointer = false;
        currentState = EXPECTING_VALUE;
      }
      break;

    case POINTER_EQUALS:
      if (currentState == EXPECTING_ASSIGN) {
        currentVar.isPointer = true;
        currentState = EXPECTING_VALUE;
      }
      break;

    case NUM:
    case BIN:
    case HEX:
      if (currentState == EXPECTING_VALUE) {
        currentVar.intValue = str2int(yytext, token);
        currentVar.hasValue = true;
        addDataVar();
        currentState = STATE_IN_DATA;
      }
      break;

    case STRING_LITERAL:
      if (currentState == EXPECTING_VALUE) {
        stripQuotes(currentVar.strValue, yytext, yyleng);
        currentVar.hasValue = true;
        addDataVar();
        currentState = STATE_IN_DATA;
      }
      break;

    case INST:
      printf("Instruction: %s\n", yytext);
      break;

    case REG:
      printf("Register: %s\n", yytext);
      break;

    case LABELDEF:
      printf("LabelDef: %s\n", cleanup(token, yytext, yyleng));
      break;

    case LABELREF:
      printf("LabelRef: %s\n", cleanup(token, yytext, yyleng));
      break;

    case ERROR:
      printf("Error: '%s' is a reserved instruction in data segment\n", yytext);
      break;

    default:
      printf("Token ID: %d, Text: %s\n", token, yytext);
      break;
    }
  }

  // print collected data variables
  printf("\n--- Collected Data Variables ---\n");
  for (int i = 0; i < dataVarCount; i++) {
    printf("Name: %s, Type: %s", dataVars[i].name, dataVars[i].type);
    if (dataVars[i].isPointer) {
      printf(", Pointer: true");
    }
    if (strlen(dataVars[i].strValue) > 0) {
      printf(", Value: \"%s\"", dataVars[i].strValue);
    } else {
      printf(", Value: %d", dataVars[i].intValue);
    }
    printf("\n");
  }
  printf("Total: %d variables\n", dataVarCount);
  printf("--- Assembly Complete ---\n");
}

int main(int argc, char **argv) {
  if (argc < 2) {
    printf("Usage: ./assembler <your_code.asm>\n");
    return 1;
  }

  FILE *file = fopen(argv[1], "r");
  if (!file) {
    perror("Failed to open file");
    return 1;
  }

  yyin = file;

  runLexer();

  fclose(file);
  return 0;
}
