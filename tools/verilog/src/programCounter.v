module programCounter (
    input wire clk,
    input wire reset,
    input wire load,
    input wire enable,

    input  wire [15:0] inAddr,
    output wire [15:0] outAddr
);

  reg [15:0] pc;

  always @(posedge clk or posedge reset) begin
    if (reset) pc <= 16'b0;
    else if (load) pc <= inAddr;
    else if (enable) pc <= pc + 1;
  end
  assign outAddr = (enable) ? pc : 16'bz;
endmodule




