#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "ast.h"
#include "parser.tab.h"

extern astNode *ast_root;
// no repeated labed definitions
// no use of keywords

const char *kwords[] = {
    "int8", "int16", "chr", "str", "bool", "ldi", "int16", "int16", "int16",
};
