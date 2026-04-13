[__data__]
	int8 val = 5
end

[__inst__]
$START:
	JMP $END

$END:
	JMP $START
	HLT

$END:
	NOPE
end