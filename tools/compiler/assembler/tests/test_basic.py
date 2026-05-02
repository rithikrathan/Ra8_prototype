#!/usr/bin/env python3
"""Ra8 assembly examples."""
import subprocess, sys, os

ASMDIR = "/home/rathan/Desktop/projects/Ra8_prototype/tools/compiler/assembler"
EMU = "/home/rathan/Desktop/projects/Ra8_prototype/tools/emulator/main"

def run_test(name, src, exp_mem):
    with open("/tmp/t.asm","w") as f: f.write(src)
    r = subprocess.run(["./assembler","/tmp/t.asm"], capture_output=True, text=True, cwd=ASMDIR)
    if r.returncode!=0 or "ERROR" in r.stderr:
        print(f"  FAIL {name}: assemble: {r.stderr[:200]}"); return False
    with open(f"{ASMDIR}/out/dataSegment.txt") as f:
        data=[int(l.strip(),16) for l in f if l.strip()]
    with open(f"{ASMDIR}/out/data.bin","wb") as f: f.write(bytes(data))
    r=subprocess.run([EMU,"--dump-mem","--data","out/data.bin","out/program.bin","--max-steps","5000"],
                    capture_output=True,text=True,cwd=ASMDIR)
    mem={}
    for line in r.stdout.splitlines():
        if ":" in line and not line.startswith("[") and line.strip():
            p=line.split(":",1)
            try:
                a=int(p[0].strip(),16); vs=p[1].strip().split()
                for i,v in enumerate(vs): mem[a+i]=int(v,16)
            except: pass
    ok=True
    for o,e in exp_mem:
        a=mem.get(o)
        if a!=e: print(f"  FAIL {name}: mem[{o}]=0x{a:02x} exp 0x{e:02x}"); ok=False
    if ok: print(f"  PASS {name}"); return True
    return False

passed=failed=0
def test(n,s,e):
    global passed,failed
    if run_test(n,s,e): passed+=1
    else: failed+=1

# CMP X,Y => Y-X.  COR 128=>jump if S(Y<X).  CAN 1=>jump if Z(Y==X).
# RIN G,E,SI => SI = E|(G<<8).

print("=== 1. Add 5+3=8 ===")
test("add","""
[__data__] int8 r=0 end
[__inst__] LDI A,5 LDI B,3 ADD C,A,B ST 0,C HLT end
""",[(0,8)])

print("=== 2. Fib(7)=13 ===")
test("fib","""
[__data__] int8 r=0 end
[__inst__]
LDI A,0 LDI B,1 LDI D,7 LDI C,0
$L: CMP C,D CAN 1 JMP $D
ADD E,A,B LDI G,0 ADD G,B,G LDI H,0 ADD H,E,H
LDI A,0 ADD A,G,A LDI B,0 ADD B,H,B
LDI G,1 SUB D,D,G JMP $L
$D: ST 0,A HLT end
""",[(0,13)])

print("=== 3. Sum [3,5,7,9,11]=35 ===")
test("sum","""
[__data__] int8 s=0 int8 a0=3 int8 a1=5 int8 a2=7 int8 a3=9 int8 a4=11 end
[__inst__]
LDI A,0 LD B,1 ADD A,A,B LD B,2 ADD A,A,B LD B,3 ADD A,A,B
LD B,4 ADD A,A,B LD B,5 ADD A,A,B ST 0,A HLT end
""",[(0,35)])

print("=== 4. strlen('hi')=2 ===")
# RIN G,E,SI => SI=E|(G<<8). Need SI=1+A for s0,s1,s2 at offsets 1,2,3
test("str","""
[__data__] int8 l=0 int8 s0=104 int8 s1=105 int8 s2=0 end
[__inst__]
LDI A,0 LDI B,0 LDI H,0
$L: LDI E,1 ADD E,E,A LDI G,0 RIN G,E,SI LSX D
CMP H,D CAN 1 JMP $D
LDI G,1 ADD A,A,G ADD B,B,G JMP $L
$D: ST 0,B HLT end
""",[(0,2)])

print("=== 5. GCD(48,18)=6 (compare before subtract) ===")
# SUB wraps: 12-18=250. Must check A>=B before subtracting.
test("gcd","""
[__data__] int8 a=48 int8 b=18 int8 r=0 end
[__inst__]
LDI A,48 LDI B,18
$O: CMP A,B CAN 1 JMP $D
    CMP B,A COR 128 JMP $S
    SUB A,A,B JMP $O
$S: LDI C,0 ADD C,A,C LDI A,0 ADD A,B,A LDI B,0 ADD B,C,B JMP $O
$D: ST 2,A HLT end
""",[(2,6)])

print("=== 6. Max [4,8,2,9,3]=9 (loop, no immediates in LD) ===")
test("max","""
[__data__] int8 m=0 int8 a0=4 int8 a1=8 int8 a2=2 int8 a3=9 int8 a4=3 int8 n=5 end
[__inst__]
LDI A,0 LDI B,0 LDI C,5 LDI D,0
$L: CMP B,C CAN 1 JMP $D
    LDI E,1 ADD E,E,B LDI G,0 RIN G,E,SI LSX F
    CMP D,F COR 128 JMP $N
    LDI G,0 ADD G,F,G LDI D,0 ADD D,G,D
$N: LDI G,1 ADD B,B,G JMP $L
$D: ST 0,D HLT end
""",[(0,9)])

print("=== 7. NOT ~0=255 ===")
test("not","""
[__data__] int8 r=0 end
[__inst__] LDI A,0 NOT A ST 0,A HLT end
""",[(0,255)])

print("=== 8. LS 3<<2=12 ===")
test("ls","""
[__data__] int8 r=0 end
[__inst__] LDI A,3 LDI B,2 LS D,A,B ST 0,D HLT end
""",[(0,12)])

print("=== 9. RS 32>>3=4 ===")
test("rs","""
[__data__] int8 r=0 end
[__inst__] LDI A,32 LDI B,3 RS D,A,B ST 0,D HLT end
""",[(0,4)])

print("=== 10. Countdown 5 ===")
test("cd","""
[__data__] int8 c=5 int8 i=0 end
[__inst__]
LDI A,5 LDI B,0 LDI C,0
$L: CMP C,A CAN 1 JMP $D LDI D,1 SUB A,A,D ADD B,B,D JMP $L
$D: ST 1,B HLT end
""",[(1,5)])

print("=== 11. 2^5=32 ===")
test("pow","""
[__data__] int8 r=0 end
[__inst__]
LDI A,1 LDI B,5 LDI C,1 LDI D,0
$L: CMP D,B CAN 1 JMP $D LS A,A,C LDI E,1 SUB B,B,E JMP $L
$D: ST 0,A HLT end
""",[(0,32)])

print("=== 12. abs(-5)=5 ===")
test("abs","""
[__data__] int8 v=251 int8 r=0 end
[__inst__]
LDI A,251 LDI B,0 CMP B,A COR 128 JMP $N JMP $D
$N: NOT A LDI C,1 ADD A,A,C $D: ST 1,A HLT end
""",[(1,5)])

print("=== 13. 7*8=56 ===")
test("mul","""
[__data__] int8 r=0 end
[__inst__]
LDI A,0 LDI B,7 LDI C,8 LDI D,0
$L: CMP D,C CAN 1 JMP $D ADD A,A,B LDI E,1 SUB C,C,E JMP $L
$D: ST 0,A HLT end
""",[(0,56)])

print("=== 14. Find zero [3,0,5]=>1 ===")
# RIN G,E,SI => SI=E|(G<<8). arr0 at offset 1.
test("fz","""
[__data__] int8 i=0 int8 a0=3 int8 a1=0 int8 a2=5 int8 n=3 int8 r=255 end
[__inst__]
LDI A,0 LDI B,0 LDI C,3 LDI H,0 LDI D,1
$L: CMP D,C CAN 1 JMP $NF
    LDI E,1 ADD E,E,B LDI G,0 RIN G,E,SI LSX F
    CMP H,F CAN 1 JMP $FO ADD B,B,D ADD A,A,D JMP $L
$FO: ST 7,A HLT $NF: LDI G,255 ST 7,G HLT end
""",[(7,1)])

print("=== 15. Double [1,2,3]->[2,4,6] (count in register, not data) ===")
test("dbl","""
[__data__] int8 a0=1 int8 a1=2 int8 a2=3 end
[__inst__]
LDI A,0 LDI B,3
$L: CMP A,B CAN 1 JMP $D
    LDI E,0 ADD E,E,A LDI G,0 RIN G,E,SI LSX C ADD C,C,C SSX C
    LDI G,1 ADD A,A,G JMP $L
$D: HLT end
""",[(0,2),(1,4),(2,6)])

print("=== 16. AND 240&15=0 ===")
test("and","""
[__data__] int8 r=0 end
[__inst__] LDI A,240 LDI B,15 AND C,A,B ST 0,C HLT end
""",[(0,0)])

print("=== 17. OR 240|15=255 ===")
test("or","""
[__data__] int8 r=0 end
[__inst__] LDI A,240 LDI B,15 OR C,A,B ST 0,C HLT end
""",[(0,255)])

print("=== 18. Clamp 200->100 ===")
test("ch","""
[__data__] int8 v=200 int8 r=0 end
[__inst__]
LDI A,200 LDI B,100 LDI C,10
CMP A,B COR 128 JMP $H CMP A,C COR 128 JMP $L JMP $S
$H: LDI A,0 ADD A,B,A JMP $S $L: LDI A,0 ADD A,C,A
$S: ST 1,A HLT end
""",[(1,100)])

print("=== 19. Clamp 5->10 ===")
test("cl","""
[__data__] int8 v=5 int8 r=0 end
[__inst__]
LDI A,5 LDI B,100 LDI C,10
CMP A,B COR 128 JMP $H CMP C,A COR 128 JMP $L JMP $S
$H: LDI A,0 ADD A,B,A JMP $S $L: LDI A,0 ADD A,C,A
$S: ST 1,A HLT end
""",[(1,10)])

print("=== 20. Clamp 50->50 ===")
test("cm","""
[__data__] int8 v=50 int8 r=0 end
[__inst__]
LDI A,50 LDI B,100 LDI C,10
CMP A,B COR 128 JMP $H CMP C,A COR 128 JMP $L JMP $S
$H: LDI A,0 ADD A,B,A JMP $S $L: LDI A,0 ADD A,C,A
$S: ST 1,A HLT end
""",[(1,50)])

print(f"\n=== {passed} passed, {failed} failed ===")
if failed: sys.exit(1)
