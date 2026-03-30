CC = gcc
FLEX = flex
BISON = bison
LEXER = lexer.l
PARSER = parser.y
PARSER_OUT = parser.tab.c
PARSER_HDR = parser.tab.h
LEX_OUT = lex.yy.c
OUTPUT = assembler

all: $(OUTPUT)

$(PARSER_OUT) $(PARSER_HDR): $(PARSER)
	$(BISON) -d $(PARSER)

$(LEX_OUT): $(LEXER)
	$(FLEX) $(LEXER)

$(OUTPUT): assembler.c $(LEX_OUT) $(PARSER_OUT) ast.c
	$(CC) assembler.c $(LEX_OUT) $(PARSER_OUT) ast.c -o $(OUTPUT)

run: $(OUTPUT)
	./$(OUTPUT) test.asm

visualize: $(OUTPUT)
	python3 visualize_ast.py test.asm --text

visualize-dot: $(OUTPUT)
	python3 visualize_ast.py test.asm -f dot

clean:
	rm -f $(LEX_OUT) $(PARSER_OUT) $(PARSER_HDR) $(OUTPUT) *.dot *.png *.svg *.pdf

.PHONY: all compile run clean visualize visualize-dot
