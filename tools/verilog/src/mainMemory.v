module mainMemory (
    input wire clk,
    input wire [7:0] data,
    input wire [15:0] addr,
    input wire writeEnable,
    input wire outputEnable,
    output wire [7:0] out
);
  reg [7:0] mem[0:65535];

  always @(posedge clk) begin
    if (writeEnable) mem[addr] = data;  // sync write
  end

  assign out = (outputEnable) ? mem[addr] : 8'bz;
endmodule



