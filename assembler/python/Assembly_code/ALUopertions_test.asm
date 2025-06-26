; hello idiots
; some data to load in the memory
.data ; see you can also have inline comments
	x:1
	x:3
	x:5
	x:7
	x:11
	x:13

ld r1 0 ; r1 = 1
ld r2 1 ; r2 = 3
st 8 r1 ; data[addr = 8] =>  1
st 9 r2 ; data[addr = 9] =>  3
add r1 r1 r2 ; r1 = 4
st 8 r1 ; data[addr = 8] =>  4
