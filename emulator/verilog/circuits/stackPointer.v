module stackPointer (
    input wire clk,
    input wire reset,
    input wire load,
    input wire enable,
    input wire pop,
    input wire [15:0] inAddr,
    output reg [15:0] sp
);
  always @(posedge clk or posedge reset) begin
    if (reset) sp <= 16'hFFFF;
    else if (load && enable) sp <= inAddr;
    else if (enable && ~pop) sp <= sp - 1;
    else if (enable && pop) sp <= sp + 1;
  end
endmodule

