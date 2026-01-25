module returnRegister (
    input wire clk,
    input wire reset,
    input wire en,
    input wire load,
    input wire [15:0] inAddr,
    output reg [15:0] index
);
  always @(posedge clk or posedge reset) begin
    if (reset) index <= 16'h0000;
    else if (en && load) index <= inAddr;
  end
endmodule

