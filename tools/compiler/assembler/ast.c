#include "ast.h"
#include <stdarg.h>
#include <stdlib.h>
// #include <string.h>

astNode *createNode(nodeType type, ...) {
  // Allocate memory and check for allocation errors
  astNode *node = (astNode *)malloc(sizeof(astNode));
  if (node == NULL) {
    return NULL;
  }

  node->type = type;

  // Initialize the dynamic array properties for children
  node->children = NULL;
  node->childCount = 0;
  node->childCapacity = 0;

  va_list args;
  va_start(args, type);

  switch (type) {
  case instruction:
    node->as.instruction.opcode = va_arg(args, char *);
    node->as.instruction.operands = NULL;
    node->as.instruction.operandCount = 0;
    break;

  case labelDef:
  case labelRef:
    node->as.label.name = va_arg(args, char *);
    break;

  case reg:
    node->as.reg.name = va_arg(args, char *);
    break;

  case dataDeclaration:
    // Enums promote to int in va_arg, and valueNode is an astNode*
    node->as.dataDeclaration.type = (dataType)va_arg(args, int);
    node->as.dataDeclaration.identifier = va_arg(args, char *);
    node->as.dataDeclaration.valueNode = va_arg(args, astNode *);
    break;

  case section:
    node->as.section.name = va_arg(args, char *);
    break;

  default:
    break;
  }

  // CRITICAL: Prevent memory leaks from the variadic list meh man fuxkt htis
  va_end(args);

  return node;
}

void addchild(astNode *parentNode, astNode *childNode) {
  if (parentNode == NULL || childNode == NULL)
    return;

  if (parentNode->childCount >= parentNode->childCapacity) {
    size_t newCapacity =
        (parentNode->childCapacity == 0) ? 4 : parentNode->childCapacity * 2;
    astNode **newChildren =
        realloc(parentNode->children, newCapacity * sizeof(astNode *));

    if (newChildren == NULL) {
      return;
    }

    parentNode->children = newChildren;
    parentNode->childCapacity = newCapacity;
  }

  // Assign the child and increment the counter
  parentNode->children[parentNode->childCount] = childNode;
  parentNode->childCount++;
}

void freeNode(astNode *node) {} // not defined so yea free everything only when
                                // the program exits, cus frick you
