; Simple Branching Demo
; Demonstrates basic conditional jumps

[__inst__]
$START:
    LDI A, 5
    LDI B, 5
    CMP A, B          ; Compare A and B (should be equal)
    CAN 1             ; If Zero flag set (A == B)
    JMP $EQUAL
    
    LDI C, 0         ; Not reached (A == B)
    HLT

$EQUAL:
    LDI C, 99         ; Reached because A == B
    HLT
end
