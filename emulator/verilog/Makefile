# ==========================
# Directory setup
# ==========================
SRC_DIR      := src
PROC_DIR     := processor
TEST_DIR     := tests
UNIT_DIR     := $(TEST_DIR)/unit
INT_DIR      := $(TEST_DIR)/integration
BUILD_DIR    := build
VVP_DIR      := $(BUILD_DIR)/vvp
VCD_DIR      := $(BUILD_DIR)/vcd
LOG_DIR      := $(BUILD_DIR)/logs

# Tools
IVERILOG     := iverilog
VVP          := vvp
GTKWAVE      := gtkwave

# Make sure build dirs exist
$(shell mkdir -p $(VVP_DIR) $(VCD_DIR) $(LOG_DIR))

# ==========================
# Handle test name
# ==========================
TEST := $(word 2, $(MAKECMDGOALS))

# Ignore extra args (like the test name)
%:
	@:

# ==========================
# Rules
# ==========================

# ----------- UNIT TESTS -----------
unit:
	@if [ -z "$(TEST)" ]; then \
		echo "Usage: make unit <testname>"; exit 1; \
	fi; \
	echo "▶ Running unit test: $(TEST)"; \
	$(IVERILOG) -o $(VVP_DIR)/$(TEST).vvp $(UNIT_DIR)/$(TEST)_tb.v $(SRC_DIR)/*.v; \
	$(VVP) $(VVP_DIR)/$(TEST).vvp > $(LOG_DIR)/$(TEST).log; \
	echo "✔ $(TEST) done."

# ----------- INTEGRATION TESTS -----------
integrate:
	@if [ -z "$(TEST)" ]; then \
		echo "Usage: make integrate <testname>"; exit 1; \
	fi; \
	echo "▶ Running integration test: $(TEST)"; \
	# $(IVERILOG) -o $(VVP_DIR)/$(TEST).vvp $(INT_DIR)/$(TEST)_tb.v $(SRC_DIR)/*.v $(PROC_DIR)/*.v; \
	$(IVERILOG) -o $(VVP_DIR)/$(TEST).vvp $(INT_DIR)/$(TEST)_tb.v $(SRC_DIR)/*.v; \
	$(VVP) $(VVP_DIR)/$(TEST).vvp > $(LOG_DIR)/$(TEST).log; \
	echo "✔ $(TEST) done."

# ----------- BUILD PROCESSOR -----------
build:
	@echo "🔧 Building processor..."
	$(IVERILOG) -o $(VVP_DIR)/processor.vvp $(PROC_DIR)/*.v $(SRC_DIR)/*.v
	@echo "✅ Processor build complete."

# ----------- RUN / WAVE / CLEAN -----------
run:
	@echo "▶ Running last build..."
	$(VVP) $(VVP_DIR)/processor.vvp

wave:
	@$(GTKWAVE) $(VCD_DIR)/*.vcd &

clean:
	rm -rf $(BUILD_DIR)/*
	@echo "🧹 Clean done."

.PHONY: unit integrate build run wave clean

