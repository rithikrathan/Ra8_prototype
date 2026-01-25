module pipeline (
    input wire [7:0] instruction,
    input wire clk,
    input wire reset,
    output wire mutexStatus,
    output wire [15:0] controlBus,
    output wire enAlu,
    output wire enGPRF
);
  // Registers for each stage
  reg [7:0] fetchRegister;
  reg [7:0] decodeRegiste;  // Name preserved
  // reg [15:0] executionRegister;

  // Internal signal used by decode unit
  reg ready;

  // Registers to store immediate bytes
  reg [7:0] pipelineReg1;
  reg [7:0] pipelineReg2;
  reg [7:0] pipelineReg3;

  // Internal logic signals to drive the Mutex wires
  reg internal_req_lock;
  reg internal_req_release;

  // Counters for loading immediate bytes
  reg [1:0] bytes_needed;
  reg [1:0] load_counter;

  reg mutex;
  wire mutex_aquireLock;
  wire mutex_releaseLock;

  assign mutexStatus = mutex;

  assign mutex_aquireLock = internal_req_lock;
  assign mutex_releaseLock = internal_req_release;

  always @(posedge clk or negedge reset) begin
    if (reset) begin
      mutex <= 0;
    end else begin
      if (mutex_aquireLock) begin
        mutex <= 1;
      end else if (mutex_releaseLock) begin
        mutex <= 0;
      end
    end
  end

  always @(posedge clk or negedge reset) begin
    if (reset) begin
      fetchRegister <= 0;
      decodeRegiste <= 0;
      executionRegister <= 0;
      pipelineReg1 <= 0;
      pipelineReg2 <= 0;
      pipelineReg3 <= 0;

      ready <= 0;  // Reset ready signal

      internal_req_lock <= 0;
      internal_req_release <= 0;
      bytes_needed <= 0;
      load_counter <= 0;
    end else begin
      // --- FETCH STAGE ---
      fetchRegister <= instruction;

      // Clear pulse signals
      internal_req_lock <= 0;
      internal_req_release <= 0;

      if (!mutex) begin
        // === STATE: NEW INSTRUCTION LOADING ===

        // 1. Move Fetch -> Decode
        decodeRegiste <= fetchRegister;

        // 2. RESET READY SIGNAL 
        // (Must be 0 when new instruction loads)
        ready <= 0;

        // 3. Pipeline Register Padding
        pipelineReg1 <= 0;
        pipelineReg2 <= 0;
        pipelineReg3 <= 0;

        // 4. Check Immediate Bytes (Top 3 bits)
        if (fetchRegister[7:5] > 3) bytes_needed <= 3;
        else bytes_needed <= fetchRegister[7:5][1:0];

        // 5. Decision Logic
        if (fetchRegister[7:5] > 0) begin
          // Needs extra data -> Request Lock
          internal_req_lock <= 1;
          load_counter <= 0;
          // ready stays 0
        end else begin
          // No extra data needed -> Ready immediately
          ready <= 1;
        end
      end else begin
        // === STATE: LOADING IMMEDIATE DATA (LOCKED) ===

        // Load data into correct register
        case (load_counter)
          2'd0: pipelineReg1 <= fetchRegister;
          2'd1: pipelineReg2 <= fetchRegister;
          2'd2: pipelineReg3 <= fetchRegister;
        endcase

        load_counter <= load_counter + 1;

        // Check if done
        if (load_counter == (bytes_needed - 1)) begin
          internal_req_release <= 1;  // Release Mutex
          ready                <= 1;  // Data gathered -> Set Ready
        end
      end
    end
  end

  // ============================================================
  // 4. DECODE UNIT (Executes only when Ready)
  // ============================================================
  always @(posedge clk) begin
    if (ready) begin

    end
  end

  // Dummy outputs
  assign controlBus = 16'b0;
  assign enAlu = 0;
  assign enGPRF = 0;

endmodule
