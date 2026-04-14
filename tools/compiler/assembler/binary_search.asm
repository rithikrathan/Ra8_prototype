; Binary Search Program
; Searches for target in sorted array [1, 3, 5, 7, 9, 11, 13, 15]
; Expected result: target 7 found at index 3

[__data__]
    int8 target = 7
    int8 array0 = 1
    int8 array1 = 3
    int8 array2 = 5
    int8 array3 = 7
    int8 array4 = 9
    int8 array5 = 11
    int8 array6 = 13
    int8 array7 = 15
end

[__inst__]
$START:
    LDI A, 7           ; A = target = 7
    LDI B, 1           ; B = low = 1 (start of array in memory)
    LDI C, 8           ; C = high = 8 (end index + 1)
    LDI D, 0           ; D = result (output)

$LOOP:
    CMP B, C             ; while low < high
    CAN 1               ; If Zero (low == high), exit
    JMP $NOT_FOUND
    
    ADD E, B, C         ; E = low + high
    RS E, E             ; E = (low + high) / 2 (mid)
    
    LD F, E             ; F = array[mid] = memory[mid]
    CMP F, A            ; Compare array[mid] with target
    CAN 1               ; If Zero (found!)
    JMP $FOUND
    
    CMP F, A            ; Compare again for < or >
    CAN 16              ; If Sign (array[mid] < target)
    JMP $RIGHT
    
    SUI C, E, 1        ; high = mid - 1
    JMP $LOOP

$RIGHT:
    ADI B, E, 1         ; low = mid + 1
    JMP $LOOP

$FOUND:
    SUI D, E, 1         ; result = mid - 1 (convert to array index)
    HLT

$NOT_FOUND:
    LDI D, 255          ; result = 255 (not found)
    HLT
end
