# Ra8 Build & Run Makefile
# Usage:
#   make                  - assemble and run test.asm
#   make run SRC=test.asm - assemble and run a specific file
#   make trace            - run with per-step trace output
#   make data             - show data memory dump only
#   make clean            - clean build outputs

SRC_DIR  := ../compiler/assembler
PYTHON   := python3

SRC      ?= test.asm
ABS_SRC  := $(SRC_DIR)/$(SRC)
PROG_BIN := $(SRC_DIR)/out/program.bin
DATA_BIN := $(SRC_DIR)/out/data.bin

assemble:
	@if [ ! -f "$(ABS_SRC)" ]; then echo "Error: $(ABS_SRC) not found"; exit 1; fi
	@echo "[+] Assembling $(SRC)..."
	@cd $(SRC_DIR) && ./assembler $(SRC) 1>/dev/null
	@if [ ! -f "$(PROG_BIN)" ]; then echo "Error: assembly failed"; exit 1; fi
	@echo "[+] $(PROG_BIN) ($(shell wc -c < $(PROG_BIN)) bytes)"

run: assemble
	@echo ""
	@if [ -f "$(DATA_BIN)" ]; then \
		$(PYTHON) dump.py $(PROG_BIN) --data $(DATA_BIN); \
	else \
		$(PYTHON) dump.py $(PROG_BIN); \
	fi

trace: assemble
	@echo ""
	@if [ -f "$(DATA_BIN)" ]; then \
		$(PYTHON) dump.py $(PROG_BIN) --data $(DATA_BIN) --trace; \
	else \
		$(PYTHON) dump.py $(PROG_BIN) --trace; \
	fi

data: assemble
	@echo ""
	@if [ -f "$(DATA_BIN)" ]; then \
		$(PYTHON) dump.py $(PROG_BIN) --data $(DATA_BIN) --data-only; \
	else \
		$(PYTHON) dump.py $(PROG_BIN) --data-only; \
	fi

.PHONY: assemble run trace data clean
