; Simple Arithmetic and Branching Demo
; Tests LDI, ADD, CMP, CAN, JMP

[__inst__]
$START:
    LDI A, 10
    LDI B, 5
    ADD C, A, B       ; C = 15
    
    CMP A, B          ; Compare 10 vs 5
    CAN 16            ; If Sign flag set (A < B is false)
    JMP $GREATER
    
    LDI D, 1          ; Not reached
    HLT

$GREATER:
    LDI D, 99         ; Reached because A > B
    HLT
end
