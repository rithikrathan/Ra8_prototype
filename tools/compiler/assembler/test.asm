; normal comment
; another normal comment
[__data__]
    int8 test   = 1 ; an inline commnet
    int8 test1  = 3
    int8 test2  = 5
    int16 hallo = 7
    int8 test4  = 11
    int8 test5  = 13
end

[__inst__]
$START: ; load the values into the registers
    LD A, 0
    LD B, 2
    LD C, 2
    LD D, 3
    LD E, 4
    LD F, 5

    ; move the register contents of A to all other registers B - F
    MV B, A
    MV C, B
    MV D, C
    MV E, D
    MV F, E

    ; store the values of registers to the memory
    ; if it worked properly then you must have the value 1 in addresses given below
    ST 8 , A
    ST 9 , B
    ST 10, C
    ST 11, D
    ST 12, E
    ST 13, F
    HLT

$testLabel2:
    HLT

$testLabel1:
    HLT

$testLabel3:
    HLT

$testLabel4:
    HLT

end
