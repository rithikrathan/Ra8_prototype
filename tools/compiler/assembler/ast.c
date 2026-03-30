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

void freeNode(astNode *node) {
  if (node == NULL)
    return;

  // 1. Post-order traversal: Free the lowest leaves of the tree first
  for (size_t i = 0; i < node->childCount; i++) {
    freeNode(node->children[i]);
  }

  // 2. Free the array holding the child pointers
  if (node->children != NULL) {
    free(node->children);
  }

  // 3. Free specific union payloads
  if (node->type == instruction && node->as.instruction.operands != NULL) {
    // Free the operands array.
    // Note: The actual operand nodes should ideally be freed in step 1 if they
    // are children.
    free(node->as.instruction.operands);
  }

  /* * NOTE ON STRINGS:
   * Because createNode just points to the strings passed in (e.g., va_arg(args,
   * char*)) rather than duplicating them with strdup(), we assume those strings
   * are either string literals or are being freed elsewhere by your lexer. If
   * you ever change createNode to use strdup(), you must add free() calls for
   * those strings right here before freeing the node.
   */

  // 4. Finally, free the node itself
  free(node);
}
