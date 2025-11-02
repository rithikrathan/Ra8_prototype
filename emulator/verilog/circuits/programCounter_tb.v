`timescale 1ns / 1ps
module programCounter_tb;
  reg clk = 0;
  reg reset = 0;
  reg load = 0;
  reg enable = 0;
  reg [15:0] inAddr;
  wire [15:0] pc;

  programCounter uut (
      .clk(clk),
      .reset(reset),
      .load(load),
      .enable(enable),
      .inAddr(inAddr),
      .pc(pc)
  );

  always #5 clk = ~clk;

  initial begin
    $dumpfile("dump.vcd");
    $dumpvars(0, programCounter_tb);

    reset  = 0;
    enable = 1;
    #50;

    load   = 1;
    inAddr = 16'h00F0;
    #10;
    load = 0;
    #50;

    reset = 1;
    #10;
    reset = 0;
    #50;

    enable = 0;
    #50;

    load   = 1;
    inAddr = 16'h0100;
    #10;
    load = 0;
    #50;

    reset = 1;
    #10;
    reset = 0;
    #50;

    $finish;
  end
endmodule

