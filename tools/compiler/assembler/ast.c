#include "ast.h"
#include <stdarg.h>
#include <stdlib.h>
#include <stdio.h>

astNode *createNode(nodeType type, ...) {
  astNode *node = (astNode *)malloc(sizeof(astNode));
  if (node == NULL) {
    return NULL;
  }

  node->type = type;
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

  case literal:
    node->as.literal.value = va_arg(args, char *);
    node->as.literal.intValue = va_arg(args, int);
    break;

  case dataDeclaration:
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
        case root: return "root";
        case section: return "section";
        case instruction: return "instruction";
        case labelDef: return "labelDef";
        case labelRef: return "labelRef";
        case reg: return "reg";
        case literal: return "literal";
        case dataDeclaration: return "dataDeclaration";
        default: return "unknown";
    }
}

void print_node_json(astNode *node, FILE *out, int *node_id) {
    if (node == NULL) return;
    
    int this_id = (*node_id)++;
    
    fprintf(out, "  %d [label=\"%s", this_id, node_type_str(node->type));
    
    switch (node->type) {
        case instruction:
            if (node->as.instruction.opcode) {
                fprintf(out, "\\n%s", node->as.instruction.opcode);
            }
            break;
        case labelDef:
        case labelRef:
            if (node->as.label.name) {
                fprintf(out, "\\n%s", node->as.label.name);
            }
            break;
        case reg:
            if (node->as.reg.name) {
                fprintf(out, "\\n%s", node->as.reg.name);
            }
            break;
        case section:
            if (node->as.section.name) {
                fprintf(out, "\\n%s", node->as.section.name);
            }
            break;
        case dataDeclaration:
            if (node->as.dataDeclaration.identifier) {
                fprintf(out, "\\n%s", node->as.dataDeclaration.identifier);
            }
            break;
        case literal:
            if (node->as.literal.value) {
                fprintf(out, "\\n%s", node->as.literal.value);
            }
            break;
        default:
            break;
    }
    fprintf(out, "\" shape=box];\n");
    
    for (size_t i = 0; i < node->childCount; i++) {
        int child_id = *node_id;
        print_node_json(node->children[i], out, node_id);
        fprintf(out, "  %d -> %d;\n", this_id, child_id);
    }
}

void print_ast_json(astNode *node, FILE *out) {
    if (node == NULL) {
        fprintf(out, "{\n  \"nodes\": [],\n  \"edges\": []\n}\n");
        return;
    }
    
    fprintf(out, "{\n");
    fprintf(out, "  \"nodes\": [\n");
    
    int node_id = 0;
    print_node_json(node, out, &node_id);
    
    fprintf(out, "  ],\n");
    fprintf(out, "  \"edges\": []\n");
    fprintf(out, "}\n");
}
