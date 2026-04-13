[__data__]
	int8 result = 0
end

[__inst__]
$START:
	LDI A, 0xFF
	LDI B, 0x0F
	AND C, A, B
	OR D, A, B
	XOR E, A, B
	NOT A
	HLT
end