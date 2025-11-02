module programCounter (
    input wire clk,
    input wire reset,
    input wire load,
    input wire enable,
    input wire [15:0] inAddr,
    output reg [15:0] pc
);
  always @(posedge clk or posedge reset) begin
    if (reset) pc <= 16'b0;
    else if (load) pc <= inAddr;
    else if (enable) pc <= pc + 1;
  end
endmodule




