module pipeline (
    input wire [7:0] instruction,
    input wire clk,
    input wire reset,
    output wire mutexStatus,
    // output wire [15:0] controlBus,

    output wire enAlu,
    output wire enGPRF,
    output wire dload,
    output wire dstore,
    output wire regA,
    output wire regB,
    output wire regRes,
    output wire operation,
    output wire addr
);


// registers for each stage
reg [7:0] fetchRegister;
reg [7:0] decodeRegiste;
reg [15:0] executionRegister;

// registers to store immediate and other bytes of the instruction
reg [7:0] pipelineReg1;
reg [7:0] pipelineReg2;
reg [7:0] pipelineReg3;

// mutex lock for stalling pipeline 
// units can request lock and stall the pipeline
reg mutex;
wire mutex_aquireLock;
wire mutex_releaseLock;

assign mutexStatus = mutex;

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
;
end

endmodule




