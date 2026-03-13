#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ERROR 0
#define INST 1
#define REG 2
#define BIN 3
#define HEX 4
#define NUM 5
#define LABELDEF 6
#define LABELREF 7
#define END 8
#define EQUALS 9
#define IDENTIFIER 10
#define DATASEGMENTSTART 11
#define INSTSEGMENTSTART 12

// use variables from the lexer
extern FILE *yyin;   // The file Lex reads from
extern int yylex();  // The function that gets the next token
extern char *yytext; // The lexeme string
extern int yyleng; // string length of the yytext excluding the null terminator

int str2int(char *text, int token_type) {
  if (token_type == NUM) {
    return (int)strtol(text, NULL, 10); // Decimal
  }
  if (token_type == HEX) {
    return (int)strtol(text + 2, NULL, 16); // Hex (skip 0x)
  }
  if (token_type == BIN) {
    return (int)strtol(text + 2, NULL, 2); // Binary (skip 0b)
  }
  return 0;
}

char *cleanup(int instruction, char *yt, int len) {
  int newlen;
  char *res;

  switch (instruction) {
  case LABELDEF:
    newlen = len - 2; // to remove the '$' and ':' from the label definition
    if (newlen < 0)
      return NULL;
    res = (char *)malloc(newlen + 1); // newlen for to store the string
                                      // and +1 to store the null terminator
    strncpy(res, yt + 1, newlen);
    res[newlen] = '\0'; // add the terminator
    break;

  case LABELREF:
    newlen = len - 1; // to remove the '$' from the label reference
    if (newlen < 0)
      return NULL;
    res = (char *)malloc(newlen + 1); // newlen for to store the string
                                      // and +1 to store the null terminator
    strncpy(res, yt + 1, newlen);
    res[newlen] = '\0'; // add the terminator
    break;
  }
  return res;
}

int main(int argc, char **argv) {

  // check if the filename is provided
  if (argc < 2) {
    printf("Usage: ./assembler <your_code.asm>\n");
    return 1;
  }

  // Open the assembly file
  FILE *file = fopen(argv[1], "r");
  if (!file) {
    perror("Failed to open file");
    return 1;
  }

  // Tell Lex to read from this file
  yyin = file;

  printf("--- Running lexer ---\n");
  printf("Tokens:\n");
  int token;

  // Loop until yylex() returns 0 (End of File)
  while ((token = yylex()) != 0) {

    // Print out what Lex found based on the token ID
    switch (token) {
    case INST:
      printf("Instruction:  %s\n", yytext);
      break;
    case REG:
      printf("Register:     %s\n", yytext);
      break;
    case NUM:
      printf("Number: %i\n", str2int(yytext, token));
      break;
    case BIN:
      printf("Number: %i\n", str2int(yytext, token));
      break;
    case HEX:
      printf("Number: %i\n", str2int(yytext, token));
      break;
    case LABELDEF:
      printf("LabelDef:    %s\n", cleanup(token, yytext, yyleng));
      break;
    case LABELREF:
      printf("LabelRef:    %s\n", cleanup(token, yytext, yyleng));
      break;
    case DATASEGMENTSTART:
      printf("__dataSegment__\n");
      break;
    case INSTSEGMENTSTART:
      printf("__instructionSegment__\n");
      break;
    case END:
      printf("segment ends\n");
      break;
    case EQUALS:
      printf("Assign\n");
      break;

    case ERROR:
      printf("Error: Owned by skill issue");
      break;

    case IDENTIFIER:
      printf("Identifier:    %s\n", yytext);
      break;
    default:
      printf("Owned by skill issue, Unknown Token ID: %d\n", token);
      break;
    }
  }
  printf("--- Lexing Complete ---\n");

  fclose(file);
  return 0;
}
