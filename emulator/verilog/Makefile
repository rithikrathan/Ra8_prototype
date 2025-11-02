# === Directories ===
COMP_DIR = components
CIRC_DIR = circuits

# === Tools ===
IVERILOG = iverilog
VVP = vvp
GTKWAVE = gtkwave

# === Files ===
COMP_SRCS = $(wildcard $(COMP_DIR)/*.v)

# === Default target ===
all:
	@echo "Usage:"
	@echo "  make comp        → compile all component files"
	@echo "  make <name>      → build & run circuits/<name>.v + <name>_tb.v"
	@echo "Example: make alu"

# === Compile only components ===
comp:
	@echo "Compiling all components..."
	@$(IVERILOG) -o build_components $(COMP_SRCS)
	@echo "Done."

# === Pattern rule for circuit test ===
%:
	@echo "Building and simulating $@..."
	@$(IVERILOG) -o build_$@ $(COMP_SRCS) $(CIRC_DIR)/$@.v $(CIRC_DIR)/$@_tb.v
	@$(VVP) build_$@
	@$(GTKWAVE) dump.vcd &

# === Clean ===
clean:
	rm -f build_* dump.vcd

