; make sure the assembler adds a jump to the top of the code that jumps to the start label also handle the addressing correctly

; Binary Search for value in A, within array at Index Reg
; Registers: A=Target, B=Low, C=High, H=Mid

[__data__]
	int8 hallo = 23
	int8 hee  = 3
	char helo  = 3
	str ello   = "hahah"
	str ptr   *= 0xffff
	str LDI    = thishouldreturnanerror
end


[__inst__]
$START:
    LDI B, 0         ; Low = 0
    LDI C, 10        ; High = 10 (Array size)

$BSEARCH_LOOP:
    CMP B, C         ; Compare Low and High
    CON 1            ; If Low > High (Greater Than)
    JMP $NOT_FOUND

    ; Calculate Mid: H = (B + C) / 2
    ADD H, B, C
    RS H, H, 1       ; H = H / 2 (shift right by 1 to divide by 2)

    ; Load value at Mid into Register D
    ; (Assuming you'd set Index Reg to H here)
    LD D, H          ; Get array[mid]


    CMP D, A         ; Compare array[mid] with Target
    CON 0            ; If Equal
    JMP $FOUND_IT

    CON 1            ; If array[mid] > Target
    JMP $SEARCH_LEFT

$SEARCH_RIGHT:
    ADI B, H, 1      ; Low = Mid + 1
    CON 0
    JMP $BSEARCH_LOOP

$SEARCH_LEFT:
    SUI C, H, 1      ; High = Mid - 1
    CON 0
    JMP $BSEARCH_LOOP

$FOUND_IT:
    ST 0x50, H       ; Store index where found
    HLT

$NOT_FOUND:
    LDI D, 0xFF
    ST 0x50, D       ; Store -1 (0xFF) for not found
    HLT
end
