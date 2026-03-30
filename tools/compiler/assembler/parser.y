%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ast.h"
#include "parser.tab.h"

void yyerror(const char *s);
int yylex(void);
extern char *yytext;
astNode *ast_root = NULL;

dataType parse_data_type(const char *s) {
    if (strcmp(s, "int8") == 0) return int8;
    if (strcmp(s, "int16") == 0) return int16;
    if (strcmp(s, "chr") == 0) return chr;
    if (strcmp(s, "str") == 0) return str;
    if (strcmp(s, "bool") == 0) return boolean;
    if (strcmp(s, "char") == 0) return chr;
    return str;
}
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
%type <node> lines line operands operand

%start program

%%

program:
    sections {
        ast_root = createNode(root);
        if ($1 != NULL) {
            addchild(ast_root, $1);
        }
        $$ = ast_root;
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
        $$ = createNode(dataDeclaration, parse_data_type($1), $2, $4);
    }
    | DATA_TYPE IDENTIFIER POINTER_EQUALS data_value {
        $$ = createNode(dataDeclaration, parse_data_type($1), $2, $4);
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
            addchild($1, $2);
            $$ = $1;
        }
    }
    ;

line:
    LABELDEF {
        $$ = createNode(labelDef, $1);
    }
    | INST operands {
        $$ = createNode(instruction, $1);
        if ($2 != NULL) {
            for (size_t i = 0; i < $2->childCount; i++) {
                addchild($$, $2->children[i]);
            }
            free($2->children);
            free($2);
        }
    }
    | INST {
        $$ = createNode(instruction, $1);
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
    REG { $$ = createNode(reg, $1); }
    | LABELREF { $$ = createNode(labelRef, $1); }
    | NUM { $$ = createNode(literal, strdup(yytext), $1); }
    | BIN { $$ = createNode(literal, strdup(yytext), $1); }
    | HEX { $$ = createNode(literal, strdup(yytext), $1); }
    | STRING_LITERAL { $$ = createNode(literal, $1, 0); }
    ;

%%

void yyerror(const char *s) {
    fprintf(stderr, "Parse error: %s\n", s);
}
