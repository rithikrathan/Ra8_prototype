%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ast.h"
#include "parser.tab.h"

void yyerror(const char *s);
int yylex(void);
%}

%union {
    int num;
    char *str;
    astNode *node;
}

%token <str> INST REG LABELDEF LABELREF DATA_TYPE STRING_LITERAL IDENTIFIER
%token <num> BIN HEX NUM
%token DATASEGMENTSTART INSTSEGMENTSTART END EQUALS POINTER_EQUALS ','

%type <node> program sections section data_section inst_section
%type <node> data_declarations data_declaration data_value
%type <node> instructions inst_line operand operands

%start program

%%

program:
    sections {
        astNode *rootNode = createNode(root);
        if ($1 != NULL) {
            addchild(rootNode, $1);
        }
        $$ = rootNode;
    }
    ;

sections:
    %empty { $$ = NULL; }
    | sections section {
        if ($1 == NULL) {
            $$ = $2;
        } else {
            addchild($1, $2);
            $$ = $1;
        }
    }
    ;

section:
    data_section { $$ = $1; }
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
            addchild($1, $2);
            $$ = $1;
        }
    }
    ;

data_declaration:
    DATA_TYPE IDENTIFIER EQUALS data_value {
        $$ = createNode(dataDeclaration, str, $2, $4);
        free($2);
    }
    | DATA_TYPE IDENTIFIER POINTER_EQUALS data_value {
        $$ = createNode(dataDeclaration, str, $2, $4);
        free($2);
    }
    ;

data_value:
    NUM { $$ = createNode(literal); }
    | BIN { $$ = createNode(literal); }
    | HEX { $$ = createNode(literal); }
    | STRING_LITERAL { $$ = createNode(literal); }
    | IDENTIFIER { $$ = createNode(literal); free($1); }
    ;

inst_section:
    INSTSEGMENTSTART instructions END {
        $$ = createNode(section, "inst");
        if ($2 != NULL) {
            addchild($$, $2);
        }
    }
    ;

instructions:
    %empty { $$ = NULL; }
    | instructions inst_line {
        if ($1 == NULL) {
            $$ = $2;
        } else {
            addchild($1, $2);
            $$ = $1;
        }
    }
    ;

inst_line:
    LABELDEF INST operands {
        astNode *labelNode = createNode(labelDef, $1);
        astNode *instNode = createNode(instruction, $2);
        if ($3 != NULL) {
            for (size_t i = 0; i < $3->childCount; i++) {
                addchild(instNode, $3->children[i]);
            }
            free($3->children);
            free($3);
        }
        addchild(labelNode, instNode);
        $$ = labelNode;
        free($1);
        free($2);
    }
    | LABELDEF INST {
        astNode *labelNode = createNode(labelDef, $1);
        astNode *instNode = createNode(instruction, $2);
        addchild(labelNode, instNode);
        $$ = labelNode;
        free($1);
        free($2);
    }
    | INST operands {
        astNode *instNode = createNode(instruction, $1);
        if ($2 != NULL) {
            for (size_t i = 0; i < $2->childCount; i++) {
                addchild(instNode, $2->children[i]);
            }
            free($2->children);
            free($2);
        }
        $$ = instNode;
        free($1);
    }
    | INST {
        $$ = createNode(instruction, $1);
        free($1);
    }
    ;

operands:
    operand { $$ = $1; }
    | operands ',' operand {
        addchild($1, $3);
        $$ = $1;
    }
    ;

operand:
    REG { $$ = createNode(reg, $1); free($1); }
    | LABELREF { $$ = createNode(labelRef, $1); free($1); }
    | NUM { $$ = createNode(literal); }
    | BIN { $$ = createNode(literal); }
    | HEX { $$ = createNode(literal); }
    | STRING_LITERAL { $$ = createNode(literal); }
    ;

%%

void yyerror(const char *s) {
    fprintf(stderr, "Parse error: %s\n", s);
}
