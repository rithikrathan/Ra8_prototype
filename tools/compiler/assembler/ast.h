#ifndef AST_H
#define AST_H

#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>

typedef enum {
  root,
  section,
  instruction,
  labelDef,
  labelRef,
  reg,
  literal,
  dataDeclaration
} nodeType;

typedef enum {
  int8,
  int16,
  chr,
  str,
  boolean,
} dataType;

typedef struct astNode {
  nodeType type;

  struct astNode **children; // Pointer to the actual array of child nodes
  size_t childCount;         // How many children are currently attached
  size_t childCapacity;      // How much memory is currently allocated

  union {
    // instruction struct
    struct {
      char *opcode;
      struct astNode **operands;
      size_t operandCount;
    } instruction;

    // label struct
    struct {
      char *name;
    } label;

    // register struct
    struct {
      char *name;
    } reg;

    // literal struct
    struct {
      char *value;
      int intValue;
    } literal;

    // dataDeclaration struct
    struct {
      dataType type;
      char *identifier;
      struct astNode *valueNode;
    } dataDeclaration;

    // section struct
    struct {
      char *name;
    } section;

  } as;
} astNode;

void addchild(astNode *parent, astNode *child);
astNode *createNode(nodeType type, ...);
void freeNode(astNode *node);
void print_ast_json(astNode *node, FILE *out);

#endif // !AST_H
