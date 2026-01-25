module alu (
    input wire mode,
    input wire en,
    input wire imm,
    input wire [3:0] operation,

    input wire [7:0] Ain,
    input wire [7:0] Iin,
    input wire [7:0] Bin,

    output wire [7:0] result,
    output wire [7:0] flags
);

  // mux Bin/Iin when immediate is used
  wire [7:0] B = imm ? Iin : Bin;

  reg  [7:0] flagsRegister;
  reg  [7:0] resultRegister;
  reg  [8:0] tempRegister;

  assign flags  = flagsRegister;
  assign result = en ? resultRegister : {8{1'bz}};

  function [7:0] handleFlags;
    input [7:0] Ain;
    input [7:0] Bin;
    input [7:0] result;
    reg [7:0] temp;
    begin
      // [S|-|OV|C|AC|EQ|P|Z]
      // [7  6   5 4  3  2  1 0]

      temp[0] = result == 0 ? 1 : 0;  // zero
      temp[1] = ~^result;  // parity
      temp[2] = 0;  // reserved

      // the commented part is for using add instruction to do the subtraction
      // like a + ~b + 1 so handle all the carry and auxillary carry flags
      // externally.
      // temp[3] = ((Ain ^ Bin ^ Result) & 8'h10) >> 4;  // auxillary carry
      // temp[4] = result > 255 ? 1 : 0;  // carry
      //
      temp[3] = 0;  // handle externally
      temp[4] = 0;  // handle externally
      temp[5] = ((Ain[7] ^ result[7]) & ~(Ain[7] ^ Bin[7]));  // overflow
      temp[6] = 0;  // reserved
      temp[7] = result[7];  // sign

      handleFlags = temp;
    end
  endfunction

  initial begin
    flagsRegister  = 0;
    resultRegister = 0;
    tempRegister   = 0;
  end

  always @(*) begin
    if (mode) begin  // Arithmetic operations modeBit: 1
      case (operation)

        4'd1: begin  // addition opcode: 1
          resultRegister = Ain + B;
          tempRegister = {1'b0, Ain} + {1'b0, B};
          flagsRegister = handleFlags(Ain, B, resultRegister);
          flagsRegister[3] = ((Ain[3:0] + B[3:0]) > 4'hF);  // auxillary carry
          flagsRegister[4] = tempRegister[8];  // carry
        end

        4'd2: begin  // addition with carry opcode: 2
          resultRegister = Ain + B + flagsRegister[4];
          tempRegister = {1'b0, Ain} + {1'b0, B} + flagsRegister[4];
          flagsRegister = handleFlags(Ain, B, resultRegister);
          flagsRegister[3] = ((Ain[3:0] + B[3:0] + flagsRegister[4]) > 4'hF);  // auxillary carry
          flagsRegister[4] = tempRegister[8];  // carry
        end

        4'd3: begin  // subtraction opcode: 3
          resultRegister = Ain - B;
          tempRegister = {1'b0, Ain} - {1'b0, B};
          flagsRegister = handleFlags(Ain, B, resultRegister);
          flagsRegister[3] = (Ain[3:0] < B[3:0]);  // auxillary borrow
          flagsRegister[4] = tempRegister[8];  // borrow
        end

        4'd4: begin  // subtraction with borrow opcode: 4
          resultRegister = Ain - B - flagsRegister[4];
          tempRegister = {1'b0, Ain} - {1'b0, B} - flagsRegister[4];
          flagsRegister = handleFlags(Ain, B, resultRegister);
          flagsRegister[3] = (Ain[3:0] < (B[3:0] + flagsRegister[4]));  // auxillary borrow
          flagsRegister[4] = tempRegister[8];  // borrow 
        end

        4'd5: begin  // multiplication low_byte: 5
          logic [15:0] prod = Ain * B;
          resultRegister = prod[7:0];
          flagsRegister  = handleFlags(Ain, B, prod);
        end

        4'd11: begin  // multiplication high_byte: 11
          logic [15:0] prod = Ain * B;
          resultRegister = prod[15:8];
          flagsRegister  = handleFlags(Ain, B, prod);
        end

        4'd6: begin  // division: 6
          resultRegister = Ain / B;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd7: begin  // modulus: 7
          resultRegister = Ain % B;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd8: begin  // Arithmetic right shift: 8
          resultRegister = $signed(Ain) >>> 1;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd9: begin  // increment: 9
          resultRegister = Ain + 8'd1;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd10: begin  // decrement: 10
          resultRegister = Ain - 8'd1;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        default: begin
        end
      endcase

    end else begin  // Logical operations
      case (operation)
        4'd1: begin  // and: 1
          resultRegister = Ain & B;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd2: begin  // or: 2
          resultRegister = Ain | B;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd3: begin  // negation: 3
          resultRegister = ~Ain;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd4: begin  // xor: 4
          resultRegister = Ain ^ B;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd5: begin  // buffer A: 5
          resultRegister = Ain;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd6: begin  // buffer B: 6
          resultRegister = B;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd7: begin  // all ones: 7
          resultRegister = 8'b11111111;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd8: begin  // logic left shift: 8
          resultRegister = Ain << 1;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd9: begin  // logic right shift: 9
          resultRegister = Ain >> 1;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd10: begin  // rotate left: 10
          resultRegister = {Ain[6:0], Ain[7]};
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd11: begin  // rotate right: 11
          resultRegister = {Ain[0], Ain[7:1]};
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        4'd12: begin  // all zeros: 12
          resultRegister = 8'b00000000;
          flagsRegister  = handleFlags(Ain, B, resultRegister);
        end

        default: begin
        end
      endcase
    end
  end

endmodule







