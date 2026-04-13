[__data__]
	int8 count = 0
end

[__inst__]
$START:
	LDI A, 0
	LDI B, 10

$LOOP:
	ADI A, A, 1
	CMP A, B
	CON 0
	JMP $LOOP

	HLT
end