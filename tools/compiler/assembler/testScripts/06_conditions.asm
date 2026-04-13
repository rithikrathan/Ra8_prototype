[__data__]
	int8 result = 0
end

[__inst__]
$START:
	LDI A, 5
	LDI B, 5
	CMP A, B
	CON 0
	JMP $EQUAL

	LDI A, 1
	JMP $DONE

$EQUAL:
	LDI A, 100

$DONE:
	HLT
end