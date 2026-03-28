%{
#include <stdio.h>
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

// some variables
bool inDataBlock = false;
bool expectingValue = false;
bool inInstBlock = false;
bool inLinkBlock = false;

const char *instructions[] = {
    "ADD", "ADI",  "ADDC", "SUB", "SUI", "SUBB", "AND", "ANI", "OR",
    "ORI", "NOT",  "XOR",  "XRI", "XNR", "XNI",  "IIN", "DIN", "CMP",
    "RS",  "LS",   "RR",   "LR",  "ARS", "MV",   "LD",  "LDI", "ST",
    "STI", "LIN",  "SIN",  "RIN", "RPC", "RSP",  "CON", "COR", "CAN",
    "JMP", "NOPE", "HLT",  "SET", NULL
};

const char *dataTypes[] = {
    "int8", "int16", "str", "bool", "char", NULL
};

int is_instruction(const char *str) {
    for (int i = 0; instructions[i] != NULL; i++) {
        if (strcmp(str, instructions[i]) == 0) {
            return 1; // It's an instruction
        }
    }
    return 0; // Not an instruction
}

int is_dataType(const char *str) {
    for (int i = 0; dataTypes[i] != NULL; i++) {
        if (strcmp(str, dataTypes[i]) == 0) {
            return 1; // It's an dataType
        }
    }
    return 0; // Not an dataType
}

// i believe i can do this a lot better but for now this is like this
void endSegment(){
	if(inInstBlock){
		inInstBlock = false;
	}
	else if(inDataBlock){
		inDataBlock = false;
	}
    else if(inLinkBlock){
		inLinkBlock = false;
	}
	else{
		printf("Owned by skill issue, 'end' does not match any segments\n");
	}
}


%}

%%
    /* patterns */
    /* basic */
[,\t\n ]+ { /* Skip whitespace */ }

";".* { /* Skip comments */ }

    /* defining numeric literals: binary, hexadecimal, and decimal */
"0b"[01]+ { expectingValue = false; return BIN; }              /* Matches binary literals */
"0x"[0-9a-fA-F]+ { expectingValue = false; return HEX; }       /* Matches hexadecimal literals */
[0-9]+ { expectingValue = false; return NUM; }                 /* Matches decimal literals */

\"[^\"]*\" { expectingValue = false; return STRING_LITERAL; }  /* Matches quoted string literals */

    /* defining the segments */
"[__data__]" { inDataBlock = true; return DATASEGMENTSTART; }
"[__inst__]" { inInstBlock = true; return INSTSEGMENTSTART; }
"=" { expectingValue = true; return EQUALS; } /* delimeter for the key value pairs */
"*=" { expectingValue = true; return POINTER_EQUALS; } /* delimeter for the pointer key and value pairs */
"end" { expectingValue = false; endSegment(); return END; } /* terminator */

    /* Matches label definitions */
"$"[a-zA-Z_][a-zA-Z0-9_]*":" { return LABELDEF; }

    /* Matches label references */
"$"[a-zA-Z_][a-zA-Z0-9_]* { return LABELREF;}

[a-zA-Z_][a-zA-Z0-9_]* {
    if (inDataBlock) {
        if (expectingValue) {
            expectingValue = false;
            return STRING_LITERAL;
        }
        if (is_instruction(yytext)) {
            return ERROR; // instructions cannot be used in data block
        }
        else if (is_dataType(yytext)) {
            return DATA_TYPE;
        } else {
            return IDENTIFIER;
        }
    }

	else if (inInstBlock){
		if (is_instruction(yytext)) {
			return INST; // It's an instruction
		}

		if (strlen(yytext) == 1 && yytext[0] >= 'A' && yytext[0] <= 'H') {
			return REG; // It's a register
		}
	}

    printf("owned by skill issue, not an instruction or a register\n");
}

    /* add macros later */
    /* other stuffs */
. { printf("Err\n");} /* Catch-all for junk */
%%


int yywrap() {
    return 1;
}

