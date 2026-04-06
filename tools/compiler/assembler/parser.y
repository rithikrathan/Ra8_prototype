%{
    // inlcudes
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ast.h"
#include "parser.tab.h"

    // boiler plate things
void yyerror(const char *s);
int yylex(void);
extern char *yytext;

// external variables for symbolTable
extern struct hashMap *symbolTable;
// idk if i should add this
extern void put(const char *key_str, int val);
extern void get(const char *key_str);
extern void freeTable();

astNode *ast_root = NULL;
int address = 0; // still needs to handle address calculation
                 // take care of it when implementing the code generation part

dataType parse_data_type(const char *s) {
    if (strcmp(s, "int8") == 0) return int8;
    if (strcmp(s, "int16") == 0) return int16;
    if (strcmp(s, "chr") == 0) return chr;
    if (strcmp(s, "str") == 0) return str;
    if (strcmp(s, "bool") == 0) return boolean;
    if (strcmp(s, "char") == 0) return chr;
    return str;
}

char *cleanup(int instruction, char *yt, int len) {
  int newlen;
  char *res;

  switch (instruction) {
  case 0: // label definition
    newlen = len - 2; // to remove the '$' and ':' from the label definition
    if (newlen < 0)
      return NULL;
    res = (char *)malloc(newlen + 1); // newlen for to store the string
                                      // and +1 to store the null terminator
    strncpy(res, yt + 1, newlen);
    res[newlen] = '\0'; // add the terminator
    break;

  case 1: // lable refernece
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

%}


// union to differentiate operands
%union {
    int num;
    char *str;
    astNode *node;
}

// define tokens and types of tokens
%token <str> INST REG LABELDEF LABELREF DATA_TYPE STRING_LITERAL IDENTIFIER
%token <num> BIN HEX NUM
%token DATASEGMENTSTART INSTSEGMENTSTART END EQUALS POINTER_EQUALS ','

%type <node> root section data_section inst_section
%type <node> data_declarations data_declaration data_value
%type <node> lines line operands operand
%type <node> sections

%start root

%%

root:
    sections {
        ast_root = createNode(root);
        astNode *current = $1;
        while (current != NULL) {
            addchild(ast_root, current);
            current = current->nextSibling;
        }
        $$ = ast_root;
    }
    ;

sections:
    section {
        $$ = $1;
        if ($$ != NULL) $$->nextSibling = NULL;
    }
    | sections section {
        $$ = $1;
        if ($2 != NULL) {
            astNode *last = $$;
            while (last->nextSibling != NULL) {
                last = last->nextSibling;
            }
            last->nextSibling = $2;
        }
    }
    ;

section: data_section { $$ = $1;}
    | inst_section { $$ = $1; }
    ;


data_section:
    DATASEGMENTSTART data_declarations END {
        $$ = createNode(section, "data");
        if ($2 != NULL) {
            addchild($$, $2);
        }
    }
    ;

data_declarations:
    %empty { $$ = NULL; }
    | data_declarations data_declaration {
        if ($1 == NULL) {
            $$ = $2;
        } else {
            astNode *last = $1;
            while (last->nextSibling != NULL) {
                last = last->nextSibling;
            }
            last->nextSibling = $2;
            $$ = $1;
        }
    }
    ;

data_declaration:
    DATA_TYPE IDENTIFIER EQUALS data_value {
        $$ = createNode(dataDeclaration, parse_data_type($1));
        astNode *idNode = createNode(identifier, $2);
        addchild($$, idNode);
        addchild($$, $4);
    }
    | DATA_TYPE IDENTIFIER POINTER_EQUALS data_value {
        $$ = createNode(dataDeclaration, parse_data_type($1));
        astNode *idNode = createNode(identifier, $2);
        addchild($$, idNode);
        addchild($$, $4);
    }
    ;

data_value:
    NUM { $$ = createNode(literal, strdup(yytext), $1); }
    | BIN { $$ = createNode(literal, strdup(yytext), $1); }
    | HEX { $$ = createNode(literal, strdup(yytext), $1); }
    | STRING_LITERAL { $$ = createNode(literal, $1, 0); }
    | IDENTIFIER { $$ = createNode(literal, $1, 0); }
    ;

inst_section:
    INSTSEGMENTSTART lines END {
        $$ = createNode(section, "inst");
        if ($2 != NULL) {
            addchild($$, $2);
        }
    }
    ;

lines:
    %empty { $$ = NULL; }
    | lines line {
        if ($1 == NULL) {
            $$ = $2;
        } else {
            astNode *last = $1;
            while (last->nextSibling != NULL) {
                last = last->nextSibling;
            }
            last->nextSibling = $2;
            $$ = $1;
        }
    }
    ;

line:
    LABELDEF {
        char *cleanName = cleanup(0, $1, strlen($1));
        put(cleanName, address);

        $$ = createNode(labelDef, cleanName);
    }
    | INST operands {
        $$ = createNode(instruction, $1);
        astNode *op = $2;
        while (op != NULL) {
            addchild($$, op);
            astNode *next = op->nextSibling;
            op->nextSibling = NULL;
            op = next;
        }
    }
    | INST {
        $$ = createNode(instruction, $1);
    }
    ;

operands:
    operand { $$ = $1; }
    | operands ',' operand {
        astNode *last = $1;
        while (last->nextSibling != NULL) {
            last = last->nextSibling;
        }
        last->nextSibling = $3;
        $$ = $1;
    }
    ;

operand:
    REG { $$ = createNode(reg, $1); }
    | LABELREF {
        $$ = createNode(labelRef, cleanup(1, $1, strlen($1)));
     }
    | NUM { $$ = createNode(literal, strdup(yytext), $1); }
    | BIN { $$ = createNode(literal, strdup(yytext), $1); }
    | HEX { $$ = createNode(literal, strdup(yytext), $1); }
    | STRING_LITERAL { $$ = createNode(literal, $1, 0); }
    ;

%%

void yyerror(const char *s) {
    fprintf(stderr, "Parse error: %s\n", s);
}
