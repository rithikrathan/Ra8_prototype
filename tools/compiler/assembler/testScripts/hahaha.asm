[__inst__]
$START:

	LDI A, 5
	LDI B, 3
	ADD C, A, B
	LDI A, 5
	LDI B, 3
	AND C, A, B
	LDI A, 10
	SUI D, A, 4
	ADI E, D, 2
	HLT
end
