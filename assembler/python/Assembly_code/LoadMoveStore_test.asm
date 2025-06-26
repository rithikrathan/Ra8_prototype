; hello idiots
; some data to load in the memory
.data ; see you can also have inline comments
	x:1
	x:3
	x:5
	x:7
	x:11
	x:13

; load the values into the registers
ld r1 0
ld r2 1
ld r3 2
ld r4 3
ld r5 4
ld r6 5

; move the register contents of r1 to all other registers r2 - r6 
mv r2 r1
mv r3 r2
mv r4 r3
mv r5 r4
mv r6 r5

; store the values of registers to the memory 
; if it worked properly then you must have the value 1 in addresses given below
st 8 r1
st 9 r2
st 10 r3
st 11 r4
st 12 r5
st 13 r6

