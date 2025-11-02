module gprf (
    input wire clk,
    input wire reset,
    input wire en,

    input wire [2:0] writeAddr,  // write address
    input wire [7:0] data,       // write data

    input  wire [2:0] A_addr,  // read address port A
    output wire [7:0] A,       // tri-state read port A

    input  wire [2:0] B_addr,  // read address port B
    output wire [7:0] B        // tri-state read port B
);
  reg [7:0] regs[0:7];

  integer i;
  always @(posedge clk or posedge reset) begin
    if (reset) for (i = 0; i < 8; i = i + 1) regs[i] <= 8'b0;
    else if (en) regs[writeAddr] <= data;
  end
  // tri-state outputs controlled by address validity
  assign A = (A_addr < 8) ? regs[A_addr] : 8'bz;
  assign B = (B_addr < 8) ? regs[B_addr] : 8'bz;

endmodule

