`timescale 1ns / 1ps
module pc2mem_tb;
  // Clock and control signals
  reg clk;
  reg reset;
  reg loadPC;
  reg enablePC;
  reg writeEnable;
  reg outputEnable;
  reg [15:0] inAddr;
  reg [7:0] dataIn;

  // Wires for buses
  wire [15:0] addressBus;
  wire [7:0] dataOut;

  // Instantiate Program Counter
  programCounter PC (
      .clk(clk),
      .reset(reset),
      .load(loadPC),
      .enable(enablePC),
      .inAddr(inAddr),
      .pc(addressBus)
  );

  // Instantiate Main Memory
  mainMemory MEM (
      .data(dataIn),
      .addr(addressBus),
      .writeEnable(writeEnable),
      .outputEnable(outputEnable),
      .out(dataOut)
  );

  // Clock generation
  initial begin
    clk = 0;
    forever #5 clk = ~clk;  // 10ns period
  end

  // Test sequence
  initial begin
    $display("Testing PC to Memory addressing");
    $dumpfile("build/vcd/dump.vcd");
    $dumpvars(0, pc2mem_tb);

    // ----------------------
    // Initialize
    // ----------------------
    reset = 1;
    loadPC = 0;
    enablePC = 0;
    writeEnable = 0;
    outputEnable = 0;
    inAddr = 16'h0000;
    dataIn = 8'h00;
    #10 reset = 0;

    // ----------------------
    // Load PC
    // ----------------------
    loadPC = 1;
    inAddr = 16'h0010;
    #10;
    loadPC = 0;

    // ----------------------
    // Write memory
    // ----------------------
    enablePC = 1;
    writeEnable = 1;
    repeat (5) begin
      dataIn = dataIn + 8'h11;
      #10;
    end
    writeEnable  = 0;

    // ----------------------
    // Read memory
    // ----------------------
    outputEnable = 1;
    repeat (5) #10;
    outputEnable = 0;

    // ----------------------
    // Test PC reset and reload
    // ----------------------
    reset = 1;
    #10 reset = 0;
    loadPC = 1;
    inAddr = 16'h00A0;
    #10 loadPC = 0;
    enablePC = 1;
    repeat (4) #10;

    // ----------------------
    // Write and read again
    // ----------------------
    writeEnable  = 1;
    outputEnable = 0;
    repeat (4) begin
      dataIn = dataIn + 8'h22;
      #10;
    end
    writeEnable  = 0;

    outputEnable = 1;
    repeat (4) #10;

    $finish;
  end
endmodule



