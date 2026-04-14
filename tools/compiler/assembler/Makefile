CC = gcc
CFLAGS = -Wall -Wextra -g
LEX = flex
YACC = bison

SRC = assembler.c ast.c parser.tab.c lex.yy.c
HDR = ast.h parser.tab.h uthash.h
OUT = assembler
DATA_DIR = data
DATA = $(DATA_DIR)/instructionSet.csv

.PHONY: all clean rebuild

all: $(OUT)

$(OUT): $(SRC) $(HDR) $(DATA)
	$(CC) $(CFLAGS) $(SRC) -o $(OUT) -lfl

lex.yy.c: lexer.l parser.tab.h
	$(LEX) -o lex.yy.c lexer.l

parser.tab.c parser.tab.h: parser.y
	$(YACC) -d -o parser.tab.c parser.y

clean:
	rm -f $(OUT) lex.yy.c parser.tab.c parser.tab.h

rebuild: clean all
