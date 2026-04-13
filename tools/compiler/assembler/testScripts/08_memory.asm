[__data__]
	int8 memLocation = 0x50
	int8 value = 42
end

[__inst__]
$START:
	LDI A, 100
	ST 0x50, A
	LD B, 0x50
	LDI C, 255
	STI 0x60
	HLT
end