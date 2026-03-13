run:
	./testassembler test.asm

compile:
	flex lexer.l
	gcc assembler.c lex.yy.c -o testassembler

test:
	flex lexer.l
	gcc assembler.c lex.yy.c -o testassembler
	./testassembler test.asm
