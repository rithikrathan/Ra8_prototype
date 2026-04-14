%{
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include "ast.h"
#include "parser.tab.h"

int inDataSection = 0;

const char* instructions[] = {
    "NOPE", "HLT", "ADD", "ADI", "ADDC", "SUB", "SUI", "SUBB", "AND", "ANI",
    "OR", "ORI", "NOT", "XOR", "XRI", "XNR", "XNI", "IIN", "DIN", "CMP", "RS",
    "LS", "RR", "LR", "ARS", "MV", "LD", "LDI", "ST", "STI", "LIN", "SIN", "RIN",
    "RPC", "RSP", "CON", "COR", "CAN", "JMP", "SET", NULL
};

const char *dataTypes[] = {
    "INT8", "INT16", "STR", "BOOL", "CHAR", NULL
};

int is_instruction(const char *str) {
    for (int i = 0; instructions[i] != NULL; i++) {
        if (strcasecmp(str, instructions[i]) == 0) {
            return 1;
        }
    }
    return 0;
}

int is_dataType(const char *str) {
    for (int i = 0; dataTypes[i] != NULL; i++) {
        if (strcasecmp(str, dataTypes[i]) == 0) {
            return 1;
        }
    }
    return 0;
}

int is_register(const char *str) {
    static const char *registers[] = {
        "A", "B", "C", "D", "E", "F", "G", "H",
        "SI", "DI", "RNG", "TEMPH", "TEMPL", NULL
    };
    for (int i = 0; registers[i] != NULL; i++) {
        if (strcasecmp(str, registers[i]) == 0) {
            return 1;
        }
    }
    return 0;
}

char *strdup_custom(const char *s) {
    size_t len = strlen(s) + 1;
    char *copy = malloc(len);
    if (copy) {
        memcpy(copy, s, len);
    }
    return copy;
}
%}

%option noyywrap
%option yylineno

%%

"," { return ','; }
[ \t\n]+ { }
";".* { }

"0b"[01]+ {
    yylval.num = strtol(yytext + 2, NULL, 2);
    yylval.str = strdup_custom(yytext);
    return BIN;
}

"0x"[0-9a-fA-F]+ {
    yylval.num = strtol(yytext + 2, NULL, 16);
    yylval.str = strdup_custom(yytext);
    return HEX;
}

[0-9]+ {
    yylval.num = atoi(yytext);
    yylval.str = strdup_custom(yytext);
    return NUM;
}

\"[^\"]*\" {
    yylval.str = strdup_custom(yytext);
    return STRING_LITERAL;
}

"[__data__]" {
    inDataSection = 1;
    return DATASEGMENTSTART;
}

"[__inst__]" {
    inDataSection = 0;
    return INSTSEGMENTSTART;
}

"=" { return EQUALS; }

"*=" { return POINTER_EQUALS; }

"end" {
    inDataSection = 0;
    return END;
}

"$"[a-zA-Z_][a-zA-Z0-9_]*":" {
    yylval.str = strdup_custom(yytext);
    return LABELDEF;
}

"$"[a-zA-Z_][a-zA-Z0-9_]* {
    yylval.str = strdup_custom(yytext);
    return LABELREF;
}

[a-zA-Z_][a-zA-Z0-9_]* {
    if (is_instruction(yytext)) {
        if (inDataSection) {
            yylval.str = strdup_custom(yytext);
            return IDENTIFIER;
        }
        yylval.str = strdup_custom(yytext);
        return INST;
    }
    if (is_dataType(yytext)) {
        yylval.str = strdup_custom(yytext);
        return DATA_TYPE;
    }
    if (is_register(yytext)) {
        yylval.str = strdup_custom(yytext);
        return REG;
    }
    yylval.str = strdup_custom(yytext);
    return IDENTIFIER;
}

. { }
