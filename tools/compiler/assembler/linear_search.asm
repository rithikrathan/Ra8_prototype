; Simple Linear Search
; Searches for 7 in [3, 5, 7, 9, 11]
; Expected result: index = 2

[__data__]
    int8 target = 7
    int8 array0 = 3
    int8 array1 = 5
    int8 array2 = 7
    int8 array3 = 9
    int8 array4 = 11
end

[__inst__]
$START:
    LDI A, 7           ; A = target = 7
    LDI B, 1          ; B = index into data (memory[1] = array[0])
    LDI C, 3          ; C = found index (output)

$LOOP:
    LD D, B            ; D = memory[B]
    CMP D, A           ; Compare with target
    CAN 1             ; If Zero (found)
    JMP $FOUND
    
    ADI B, B, 1        ; B = B + 1
    CMP B, C           ; Compare B with 6 (end)
    CAN 1             ; If Zero (at end, not found)
    JMP $NOT_FOUND
    
    JMP $LOOP

$FOUND:
    SUI C, B, 1        ; C = B - 1 (convert memory index to array index)
    HLT

$NOT_FOUND:
    LDI C, 255         ; C = 255 (not found)
    HLT
end
