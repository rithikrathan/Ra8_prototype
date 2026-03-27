#ifndef AST_H
#define AST_H

#include <stddef.h>

// typedef enum {} nodeType;
typedef enum {
  rort,
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

    // dataDeclaration struct
    struct {
      dataType type;
      char *identifier;
      struct astNode *valueNode;
    } dataDeclaration;

    // section struct
    struct {
      char *name;
      struct astNode **valueNode;
      size_t statement_count;
    } section;
  } as;
} astNode;

void addChild(astNode *parent, astNode *child);

astNode *createLabelNode();
astNode *createInstructionNode();
astNode *createRegisterNode();
astNode *createDataDeclarationNode();
astNode *createSectionNode();

#endif // !AST_H
