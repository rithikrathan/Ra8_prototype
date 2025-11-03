`timescale 1ns / 1ps
module stackPointer_tb;
  reg clk = 0;
  reg reset = 0;
  reg load = 0;
  reg enable = 0;
  reg pop = 0;
  reg [15:0] inAddr;
  wire [15:0] sp;

  stackPointer uut (
      .clk(clk),
      .reset(reset),
      .load(load),
      .enable(enable),
      .pop(pop),
      .inAddr(inAddr),
      .sp(sp)
  );

  always #5 clk = ~clk;

  initial begin
    $dumpfile("dump.vcd");
    $dumpvars(0, stackPointer_tb);

    // normal operation
    reset  = 0;
    enable = 1;
    load   = 1;
    inAddr = 16'h00F0;
    #10;
    load = 0;

    // push operations (decrement)
    pop  = 0;
    #50;

    // pop operations (increment)
    pop = 1;
    #50;

    // hold
    enable = 0;
    #20;

    // reset and repeat same sequence
    reset = 1;
    #10;
    reset  = 0;
    enable = 1;

    load   = 1;
    inAddr = 16'h0100;
    #10;
    load = 0;
    pop  = 0;
    #50;
    pop = 1;
    #50;

    // disable and show no activity
    enable = 0;
    pop = 0;
    load = 1;
    inAddr = 16'hAAAA;
    #10;
    load = 0;
    #50;

    $finish;
  end
endmodule

