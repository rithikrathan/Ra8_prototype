CC = gcc
FLEX = flex
LEXER = lexer.l
LEX_OUT = lex.yy.c
OUTPUT = assembler

$(LEX_OUT): $(LEXER)
	$(FLEX) $(LEXER)

$(OUTPUT): assembler.c $(LEX_OUT)
	$(CC) assembler.c $(LEX_OUT) -o $(OUTPUT)

compile: $(OUTPUT)

run: $(OUTPUT)
	./$(OUTPUT) test.asm

clean:
	rm -f $(LEX_OUT) $(OUTPUT)

.PHONY: compile run clean
