#include "ast.h"
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

astNode *createNode(nodeType type, ...) {
  astNode *node = (astNode *)malloc(sizeof(astNode));
  if (node == NULL) {
    return NULL;
  }

  node->type = type;
  node->children = NULL;
  node->childCount = 0;
  node->childCapacity = 0;
  node->nextSibling = NULL;

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

  case literal:
    node->as.literal.value = va_arg(args, char *);
    node->as.literal.intValue = va_arg(args, int);
    break;

  case identifier:
    node->as.identifier.name = va_arg(args, char *);
    break;

  case dataDeclaration:
    node->as.dataDeclaration.type = (dataType)va_arg(args, int);
    break;

  case section:
    node->as.section.name = va_arg(args, char *);
    break;

  default:
    break;
  }

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

  parentNode->children[parentNode->childCount] = childNode;
  parentNode->childCount++;
}

void freeNode(astNode *node) {}

const char *node_type_str(nodeType type) {
  switch (type) {
  case root:
    return "root";
  case section:
    return "section";
  case instruction:
    return "instruction";
  case labelDef:
    return "labelDef";
  case labelRef:
    return "labelRef";
  case reg:
    return "reg";
  case literal:
    return "literal";
  case identifier:
    return "identifier";
  case dataDeclaration:
    return "dataDeclaration";
  default:
    return "unknown";
  }
}

const char *data_type_str(dataType type) {
  switch (type) {
  case int8:
    return "int8";
  case int16:
    return "int16";
  case chr:
    return "char";
  case str:
    return "str";
  case boolean:
    return "boolean";
  default:
    return "unknown";
  }
}

void print_node_json(astNode *node, FILE *out, int *node_id, int parent_id) {
  if (node == NULL)
    return;

  int this_id = (*node_id)++;

  fprintf(out, "  %d [label=\"type: %s", this_id, node_type_str(node->type));

  switch (node->type) {
  case root:
    break;
  case section:
    fprintf(out, "\\nname: %s",
            node->as.section.name ? node->as.section.name : "(nil)");
    break;
  case instruction:
    fprintf(out, "\\nname: %s",
            node->as.instruction.opcode ? node->as.instruction.opcode
                                        : "(nil)");
    break;
  case labelDef:
    fprintf(out, "\\nname: %s",
            node->as.label.name ? node->as.label.name : "(nil)");
    break;
  case labelRef:
    fprintf(out, "\\nname: %s",
            node->as.label.name ? node->as.label.name : "(nil)");
    break;
  case reg:
    fprintf(out, "\\nname: %s",
            node->as.reg.name ? node->as.reg.name : "(nil)");
    break;
  case literal:
    fprintf(out, "\\nvalue: %s",
            node->as.literal.value ? node->as.literal.value : "(nil)");
    break;
  case identifier:
    fprintf(out, "\\nname: %s",
            node->as.identifier.name ? node->as.identifier.name : "(nil)");
    break;
  case dataDeclaration:
    fprintf(out, "\\ndatatype: %s",
            data_type_str(node->as.dataDeclaration.type));
    break;
  default:
    break;
  }

  fprintf(out, "\" shape=box];\n");

  if (parent_id >= 0) {
    fprintf(out, "  %d -> %d;\n", parent_id, this_id);
  }

  for (size_t i = 0; i < node->childCount; i++) {
    print_node_json(node->children[i], out, node_id, this_id);
  }

  if (node->type != root && node->type != section &&
      node->nextSibling != NULL) {
    print_node_json(node->nextSibling, out, node_id, parent_id);
  }
}

void print_ast_json(astNode *node, FILE *out) {
  printf("helo\n");
  if (node == NULL) {
    fprintf(out, "{\n  \"nodes\": [],\n  \"edges\": []\n}\n");
    return;
  }

  fprintf(out, "{\n");
  fprintf(out, "  \"nodes\": [\n");

  int node_id = 0;
  print_node_json(node, out, &node_id, -1);

  fprintf(out, "  ],\n");
  fprintf(out, "  \"edges\": []\n");
  fprintf(out, "}\n");
}

void semanticAnalysis() {}
