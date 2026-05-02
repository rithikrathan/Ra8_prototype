CC = gcc
FLEX = flex
BISON = bison

PARSER_OUT = parser.tab.c
PARSER_HDR = parser.tab.h
LEX_OUT = lex.yy.c
OUTPUT = assembler

all: $(OUTPUT)

$(PARSER_OUT) $(PARSER_HDR): parser.y
	$(BISON) -d parser.y

$(LEX_OUT): lexer.l
	$(FLEX) lexer.l

$(OUTPUT): assembler.c $(LEX_OUT) $(PARSER_OUT) ast.c cJSON.c
	$(CC) assembler.c $(LEX_OUT) $(PARSER_OUT) ast.c cJSON.c -o $(OUTPUT)

run: $(OUTPUT)
	./$(OUTPUT) test.asm

test: $(OUTPUT)
	mkdir -p out
	python3 tests/test_basic.py && python3 tests/test_extended.py && python3 tests/test_block.py

clean:
	rm -f $(LEX_OUT) $(PARSER_OUT) $(PARSER_HDR) $(OUTPUT)
	rm -rf out/

.PHONY: all run test clean
