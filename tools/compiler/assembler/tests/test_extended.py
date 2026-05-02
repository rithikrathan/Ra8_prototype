#!/usr/bin/env python3
"""Extended Ra8 assembly tests."""
import subprocess, sys, os

ASMDIR = "/home/rathan/Desktop/projects/Ra8_prototype/tools/compiler/assembler"
EMU = "/home/rathan/Desktop/projects/Ra8_prototype/tools/emulator/main"

def run_test(name, src, exp_mem):
    with open("/tmp/t.asm","w") as f: f.write(src)
    r = subprocess.run(["./assembler","/tmp/t.asm"], capture_output=True, text=True, cwd=ASMDIR)
    if r.returncode!=0 or "ERROR" in r.stderr:
        print(f"  FAIL {name}: {r.stderr[:200]}"); return False
    with open(f"{ASMDIR}/out/dataSegment.txt") as f:
        data=[int(l.strip(),16) for l in f if l.strip()]
    with open(f"{ASMDIR}/out/data.bin","wb") as f: f.write(bytes(data))
    r=subprocess.run([EMU,"--dump-mem","--data","out/data.bin","out/program.bin","--max-steps","10000"],
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

print("=== 21. Left rotate: 0x81 rotl 1 = 0x03 = 3 ===")
test("rol","""
[__data__] int8 r=0 end
[__inst__]
LDI A,129 LDI B,1 LR C,A,B ST 0,C HLT end
""",[(0,3)])

print("=== 22. Arithmetic right shift: -16 >> 2 = -4 = 252 ===")
test("ars","""
[__data__] int8 r=0 end
[__inst__]
LDI A,240 LDI B,2 ARS C,A,B ST 0,C HLT end
""",[(0,252)])

print("=== 23. Bubble sort [5,3,1,4,2] -> [1,2,3,4,5] ===")
# H=0 for RIN high byte, G=4 for pass limit, B=pass counter, F=inner index
test("bsort","""
[__data__] int8 a0=5 int8 a1=3 int8 a2=1 int8 a3=4 int8 a4=2 int8 n=5 end
[__inst__]
LDI H,0 LDI G,4 LDI B,0
$OUTER:
    LDI F,0
$INNER:
    CMP F,G CAN 1 JMP $PASS
    RIN H,F,SI LSX D
    LDI E,1 ADD E,E,F RIN H,E,SI LSX C
    CMP C,D COR 128 JMP $NOSWAP
    RIN H,F,SI SSX C
    RIN H,E,SI SSX D
$NOSWAP:
    LDI E,1 ADD F,F,E JMP $INNER
$PASS:
    LDI E,1 ADD B,B,E CMP B,G CAN 1 JMP $DONE
    JMP $OUTER
$DONE: HLT end
""",[(0,1),(1,2),(2,3),(3,4),(4,5)])

print("=== 24. Popcount of 181 (0b10110101) = 5 ===")
test("pop","""
[__data__] int8 v=181 int8 c=0 end
[__inst__]
LDI A,181 LDI B,0 LDI C,8 LDI H,0 LDI G,1
$L: CMP H,C CAN 1 JMP $D
    LDI D,1 AND D,A,D CMP H,D COR 1 JMP $N
    ADD B,B,G
$N: RS A,A,G SUB C,C,G JMP $L
$D: ST 1,B HLT end
""",[(1,5)])

print("=== 25. Reverse [1,2,3,4,5] -> [5,4,3,2,1] ===")
test("rev","""
[__data__] int8 a0=1 int8 a1=2 int8 a2=3 int8 a3=4 int8 a4=5 int8 n=5 end
[__inst__]
LDI A,0 LDI B,4 LDI H,0
$L: CMP A,B COR 128 JMP $D
    RIN H,A,SI LSX C
    RIN H,B,SI LSX D
    RIN H,A,SI SSX D
    RIN H,B,SI SSX C
    LDI G,1 ADD A,A,G LDI G,1 SUB B,B,G JMP $L
$D: HLT end
""",[(0,5),(1,4),(2,3),(3,2),(4,1)])

print("=== 26. XOR: 5^3=6 ===")
test("xor","""
[__data__] int8 r=0 end
[__inst__]
LDI A,5 LDI B,3 XOR C,A,B ST 0,C HLT end
""",[(0,6)])

print("=== 27. Count occurrences of 3 in [3,1,3,2,3] = 3 ===")
test("count","""
[__data__] int8 a0=3 int8 a1=1 int8 a2=3 int8 a3=2 int8 a4=3 int8 n=5 end
[__inst__]
LDI A,0 LDI B,0 LDI C,5 LDI D,3 LDI G,1 LDI H,0
$L: CMP A,C CAN 1 JMP $D
    RIN H,A,SI LSX F
    CMP F,D CAN 1 JMP $MATCH JMP $N
$MATCH: ADD B,B,G
$N: ADD A,A,G JMP $L
$D: ST 6,B HLT end
""",[(6,3)])

print("=== 28. Two's complement negate: -7 = 249 ===")
test("neg","""
[__data__] int8 r=0 end
[__inst__]
LDI A,7 NOT A,A LDI B,1 ADD A,A,B ST 0,A HLT end
""",[(0,249)])

print("=== 29. Min of [7,3,9,1,5] = 1 ===")
test("min","""
[__data__] int8 a0=7 int8 a1=3 int8 a2=9 int8 a3=1 int8 a4=5 int8 n=5 end
[__inst__]
LDI A,0 LDI B,0 LDI C,5 LDI H,0 RIN H,A,SI LSX D
$LOOP:
    CMP B,C CAN 1 JMP $D
    RIN H,B,SI LSX F
    CMP F,D COR 128 JMP $N
    LDI G,0 ADD D,F,G
$N: LDI G,1 ADD B,B,G JMP $LOOP
$D: ST 0,D HLT end
""",[(0,1)])

print("=== 30. strlen of 'hello' = 5 ===")
test("strlen2","""
[__data__]
    int8 s0=104 int8 s1=101 int8 s2=108 int8 s3=108 int8 s4=111 int8 s5=0
    int8 len=0
end
[__inst__]
LDI A,0 LDI B,0 LDI H,0 LDI G,1
$L: RIN H,A,SI LSX D
    CMP H,D CAN 1 JMP $D
    ADD A,A,G ADD B,B,G JMP $L
$D: ST 6,B HLT end
""",[(6,5)])

print(f"\n=== {passed} passed, {failed} failed ===")
if failed: sys.exit(1)
