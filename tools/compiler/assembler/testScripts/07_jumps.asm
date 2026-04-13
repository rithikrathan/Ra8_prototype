[__data__]
	int8 value = 0
end

[__inst__]
$START:
	LDI A, 1
	JMP $SKIP
	LDI A, 99

$SKIP:
	HLT
end