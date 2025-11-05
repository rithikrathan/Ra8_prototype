`timescale 1ns / 1ps
module gprf_tb;
  reg clk = 0;
  reg reset = 0;
  reg en = 0;
  reg [2:0] writeAddr;
  reg [7:0] data;
  reg [2:0] A_addr, B_addr;
  wire [7:0] A, B;

  // DUT
  gprf uut (
      .clk(clk),
      .reset(reset),
      .en(en),
      .writeAddr(writeAddr),
      .data(data),
      .A_addr(A_addr),
      .A(A),
      .B_addr(B_addr),
      .B(B)
  );

  // 10-unit clock
  always #5 clk = ~clk;

  initial begin
    $dumpfile("build/vcd/dump.vcd");
    $dumpvars(0, gprf_tb);

    // reset
    reset = 1;
    en = 0;
    #10 reset = 0;

    // write to registers
    en = 1;
    writeAddr = 3'b000;
    data = 8'hF1;
    #10;
    writeAddr = 3'b001;
    data = 8'hC4;
    #10;
    writeAddr = 3'b010;
    data = 8'h9A;
    #10;
    writeAddr = 3'b011;
    data = 8'h7E;
    #10;
    writeAddr = 3'b100;
    data = 8'h55;
    #10;
    writeAddr = 3'b101;
    data = 8'hAA;
    #10;
    writeAddr = 3'b110;
    data = 8'h3C;
    #10;
    writeAddr = 3'b111;
    data = 8'hE7;
    #10;
    en = 0;

    // read back
    A_addr = 3'b000;
    B_addr = 3'b111;
    #10;
    A_addr = 3'b001;
    B_addr = 3'b100;
    #10;
    A_addr = 3'b010;
    B_addr = 3'b101;
    #10;
    A_addr = 3'b011;
    B_addr = 3'b110;
    #10;
    A_addr = 3'b111;
    B_addr = 3'b111;
    #10;
    #10 reset = 1;
    #10 reset = 0;

    A_addr = 3'b000;
    B_addr = 3'b111;
    #10;
    A_addr = 3'b001;
    B_addr = 3'b100;
    #10;
    A_addr = 3'b010;
    B_addr = 3'b101;
    #10;
    A_addr = 3'b011;
    B_addr = 3'b110;
    #10;
    A_addr = 3'b111;
    B_addr = 3'b111;
    #10;

    #20 $finish;
  end
endmodule

