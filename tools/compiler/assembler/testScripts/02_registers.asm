[__data__]
	int8 val1 = 5
	int8 val2 = 3
end

[__inst__]
$START:
	LDI A, 10
	LDI B, 20
	MV C, A
	MV D, B
	HLT
end