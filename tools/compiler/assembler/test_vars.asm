[__data__]
    int8 count = 10
    int8 result = 0
    int8 message = 2
    int8 message3 = 2
    int8 message4 = 2
    int8 message1 = 2
    int8 message5 = 2
end

[__inst__]
$LOOP:
    LD A, count
    LD B, result
    LD B, message
    LD B,message3
    LD B,message4
    LD B,message1
    LD B,message5
        ADD C,A,B
    ST 16, A
    JMP $END
    JMP $END2
    JMP $END3
    JMP $END5
    HLT
$END2:
        HLT
$END3:
        HLT
$END5:
        HLT
$END:
        HLT
end
