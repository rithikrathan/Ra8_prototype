CC = gcc
FLEX = flex
BISON = bison

PARSER_OUT = parser.tab.c
PARSER_HDR = parser.tab.h
LEX_OUT = lex.yy.c
OUTPUT = assembler

PYTHON = python3
PYASM_DIR = python
PYASM = assembler.py

all: $(OUTPUT)

$(PARSER_OUT) $(PARSER_HDR): parser.y
	$(BISON) -d parser.y

$(LEX_OUT): lexer.l
	$(FLEX) lexer.l

$(OUTPUT): assembler.c $(LEX_OUT) $(PARSER_OUT) ast.c cJSON.c
	$(CC) assembler.c $(LEX_OUT) $(PARSER_OUT) ast.c cJSON.c -o $(OUTPUT)

run: $(OUTPUT)
	./$(OUTPUT) test.asm

tree: $(OUTPUT)
	$(PYTHON) visualize_ast.py test.asm --text

python:
	(cd $(PYASM_DIR) && echo "1" | $(PYTHON) $(PYASM))

assemble: run python

clean:
	rm -f $(LEX_OUT) $(PARSER_OUT) $(PARSER_HDR) $(OUTPUT)

.PHONY: all run tree python cheeky clean
