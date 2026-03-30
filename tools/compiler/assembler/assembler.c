#include <stdio.h>
#include <stdlib.h>
#include "ast.h"

extern int yyparse();
extern FILE *yyin;
extern astNode *ast_root;

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
    }

    return result;
}
