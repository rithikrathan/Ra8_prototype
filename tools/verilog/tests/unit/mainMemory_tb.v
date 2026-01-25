module tb;
  reg [ 7:0] data;
  reg [15:0] addr;
  reg writeEnable, outputEnable;
  wire [7:0] out;

  mainMemory mem_inst (
      .data(data),
      .addr(addr),
      .writeEnable(writeEnable),
      .outputEnable(outputEnable),
      .out(out)
  );

  initial begin
    $dumpfile("build/vcd/dump.vcd");  // waveform file
    $dumpvars(0, tb);
    $readmemb("index_value.mem", mem_inst.mem);
    outputEnable = 1;
    addr = 16'h0000;
    #1 $display("mem[0000] = %h", out);
    addr = 16'h0001;
    #1 $display("mem[0001] = %h", out);
    addr = 16'h00FF;
    #1 $display("mem[00FF] = %h", out);

    $finish;
  end
endmodule

