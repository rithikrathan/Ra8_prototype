`timescale 1ns / 1ps

module alu_tb;

  reg        mode;
  reg  [3:0] operation;
  reg  [7:0] Ain;
  reg  [7:0] Bin;

  wire [7:0] result;
  wire [7:0] flags;

  // DUT
  alu dut (
      .mode(mode),
      .operation(operation),
      .Ain(Ain),
      .Bin(Bin),
      .result(result),
      .flags(flags)
  );

  initial begin
    $dumpfile("build/vcd/dump.vcd");
    $dumpvars(0, alu_tb);
  end

  task run;
    input _mode;
    input [3:0] _op;
    input [7:0] _A;
    input [7:0] _B;
    begin
      mode      = _mode;
      operation = _op;
      Ain       = _A;
      Bin       = _B;
      #10;
    end
  endtask

  initial begin
    // -----------------------------------
    // TEST DIFFERENT OPERATIONS
    // -----------------------------------

    // arithmetic mode
    run(1, 4'd1, 8'h05, 8'h03);  // add
    run(1, 4'd2, 8'h07, 8'h01);  // adc
    run(1, 4'd3, 8'h10, 8'h02);  // sub
    run(1, 4'd4, 8'h10, 8'h02);  // sbb
    run(1, 4'd5, 8'h04, 8'h03);  // mul
    run(1, 4'd6, 8'h12, 8'h03);  // div
    run(1, 4'd7, 8'h12, 8'h05);  // mod
    run(1, 4'd8, 8'hF0, 8'h00);  // arith >> 1
    run(1, 4'd9, 8'h0F, 8'h00);  // inc
    run(1, 4'd10, 8'h10, 8'h00);  // dec

    // logical mode
    run(0, 4'd1, 8'h0F, 8'hF0);  // and
    run(0, 4'd2, 8'h0F, 8'hF0);  // or
    run(0, 4'd3, 8'hAA, 8'h00);  // not A
    run(0, 4'd4, 8'h0F, 8'h33);  // xor
    run(0, 4'd5, 8'h55, 8'h00);  // buffer A
    run(0, 4'd6, 8'h00, 8'hAA);  // buffer B
    run(0, 4'd7, 8'h00, 8'h00);  // all ones
    run(0, 4'd8, 8'h81, 8'h00);  // << 1
    run(0, 4'd9, 8'h81, 8'h00);  // >> 1
    run(0, 4'd10, 8'h96, 8'h00);  // rol
    run(0, 4'd11, 8'h96, 8'h00);  // ror
    run(0, 4'd12, 8'h00, 8'h00);  // zero

    #50;
    $finish;
  end

endmodule







