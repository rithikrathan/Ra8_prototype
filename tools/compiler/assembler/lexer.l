%{
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

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

const char *instructions[] = {
    "ADD", "ADI",  "ADDC", "SUB", "SUI", "SUBB", "AND", "ANI", "OR",
    "ORI", "NOT",  "XOR",  "XRI", "XNR", "XNI",  "IIN", "DIN", "CMP",
    "RS",  "LS",   "RR",   "LR",  "ARS", "MV",   "LD",  "LDI", "ST",
    "STI", "LIN",  "SIN",  "RIN", "RPC", "RSP",  "CON", "COR", "CAN",
    "JMP", "NOPE", "HLT",  "SET", NULL
};

int is_instruction(const char *str) {
    for (int i = 0; instructions[i] != NULL; i++) {
        if (strcmp(str, instructions[i]) == 0) {
            return 1; // It's an instruction
        }
    }
    return 0; // Not an instruction
}

bool inDataBlock = false;
bool inInstBlock = false;
%}

%%
    /* patterns */
    /* basic */
[,\t\n ]+ { /* Skip whitespace */ }

";".* { /* Skip comments */ }

    /* defining numeric literals: binary, hexadecimal, and decimal */
"0b"[01]+ { return BIN; }              /* Matches binary literals */
"0x"[0-9a-fA-F]+ { return HEX; }       /* Matches hexadecimal literals */
[0-9]+ { return NUM; }                 /* Matches decimal literals */

    /* defining the segments */
"[__data__]" { inDataBlock = true; return DATASEGMENTSTART; }
"[__inst__]" { inInstBlock = true; return INSTSEGMENTSTART; }
"=" { return EQUALS; } /* delimeter for the key value pairs */
"end" { endSegment(); return END; } /* terminator */

    /* Matches label definitions */
"$"[a-zA-Z_][a-zA-Z0-9_]*":" { return LABELDEF; }

    /* Matches label references */
"$"[a-zA-Z_][a-zA-Z0-9_]* { return LABELREF;} 

    /* defining instruction and registers */
    /* "ADD"|"SUB"|"MV"          { return INST; }   Matches instruction names */
    /* [A-H]                     { return REG; }    Matches your A-H registers */

[a-zA-Z_][a-zA-Z0-9_]* {
    if (inDataBlock) {
		printf("%i", is_instruction(yytext));
        if (is_instruction(yytext)) {
			// NOTE:this is still being ignored and returning as an instruction so fix it later
            return ERROR; // instructions cannot be used in data block
        } else {
            return IDENTIFIER;
        }
    } // handle data block
	else if (inInstBlock){
		if (is_instruction(yytext)) {
			return INST; // It's an instruction
		}

		if (strlen(yytext) == 1 && yytext[0] >= 'A' && yytext[0] <= 'H') {
			return REG; // It's a register
		}
	} // handle instruction block

    printf("owned by skill issue, not an instruction or a register\n");
}

    /* add macros later */
    /* add variable definitions later */
    /* other stuffs */
. { printf("Err\n");} /* Catch-all for junk */
%%

// i believe i can do this a lot better but for now this is like this
void endSegment(){
	if(inInstBlock){
		inInstBlock = false;
	}
	if(inDataBlock){
		inDataBlock = false;
	}
	else{
		println("Owned by skill issue, 'end' does not match any segments")
	}
}

int yywrap() {
    return 1;
}




