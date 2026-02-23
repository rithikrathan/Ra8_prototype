%{
#include <stdio.h>
#include <string.h>

#define INST 1
#define REG  2

#define BIN  3
#define HEX  4
#define NUM  5

#define LABELDEF 6
#define LABELREF 7

const char* instructions[] = {
    "ADD", "ADI", "ADDC", "SUB", "SUI", "SUBB", "AND",
    "ANI", "OR", "ORI", "NOT", "XOR", "XRI", "XNR", "XNI",
    "IIN", "DIN", "CMP", "RS", "LS", "RR", "LR", "ARS",
    "MV", "LD", "LDI", "ST", "STI", "LIN", "SIN", "RIN",
    "RPC", "RSP", "CON", "COR", "CAN", "JMP", "NOPE",
    "HLT", "SET", NULL
};

int is_instruction(const char* str) {
    for (int i = 0; instructions[i] != NULL; i++) {
        if (strcmp(str, instructions[i]) == 0) {
            return 1; // It's an instruction
        }
    }
    return 0; // Not an instruction
}
%}

%%
	/* patterns */
	/* basic */
[ ,\t\n]+                  { /* Skip whitespace */ }
";".* { /* Skip comments */ }
                                           
	/* defining numeric literals: binary, hexadecimal, and decimal */
"0b"[01]+                 { return BIN; }   /* Matches binary literals */
"0x"[0-9a-fA-F]+          { return HEX; }   /* Matches hexadecimal literals */
[0-9]+                    { return NUM; }   /* Matches decimal literals */
                                           
	/* defining instruction and registers */
	/* "ADD"|"SUB"|"MV"          { return INST; }   Matches instruction names */
	/* [A-H]                     { return REG; }    Matches your A-H registers */

[a-zA-Z_][a-zA-Z0-9_]* { 
    if (is_instruction(yytext)) {
        return INST; // It's an instruction
    } 
    if (strlen(yytext) == 1 && yytext[0] >= 'A' && yytext[0] <= 'H') {
        return REG; // It's a register
    }
    printf("owned by skill issue, not an instruction or a register\n"); // Not an instruction or register
}
                           
	/* so the label must only start with a letter or underscore, and can be followed by letters, digits, or underscores */
	/* [a-zA-Z_][a-zA-Z0-9_]*:   { return LABELDEF; } Matches label definitions */
"$"[a-zA-Z_][a-zA-Z0-9_]*":" { return LABELDEF; } /* Matches label definitions */
"$"[a-zA-Z_][a-zA-Z0-9_]* { return LABELREF; } /* Matches label references */

	/* add macros later */
	/* add variable definitions later */
						   
	/* other stuffs */
.                         { printf("Err\n"); } /* Catch-all for junk */

%%

int yywrap() { return 1; }
