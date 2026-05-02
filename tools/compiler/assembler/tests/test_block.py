#!/usr/bin/env python3
"""Block operation tests."""
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

# Available regs: A B C D E F G H SI DI RNG SP PC
# Data layout: mem[0..n-1] for first n variables

print("=== 31. memcpy: copy [10,20,30,40,50] to zeros ===")
# src at mem[0..4], dest at mem[10..14], count=5 at mem[15]
test("memcpy","""
[__data__]
    int8 s0=10 int8 s1=20 int8 s2=30 int8 s3=40 int8 s4=50
    int8 p1=0 int8 p2=0 int8 p3=0 int8 p4=0 int8 p5=0
    int8 cnt=5
end
[__inst__]
LDI A,0 LDI B,5 LDI H,0
$LOOP:
    CMP A,B CAN 1 JMP $D
    RIN H,A,SI LSX C
    LDI E,5 ADD E,E,A RIN H,E,SI SSX C
    LDI E,1 ADD A,A,E JMP $LOOP
$D: HLT end
""",[(5,10),(6,20),(7,30),(8,40),(9,50)])

print("=== 32. memset: fill 8 bytes with 0xAA ===")
test("memset","""
[__data__]
    int8 b0=0 int8 b1=0 int8 b2=0 int8 b3=0 int8 b4=0 int8 b5=0 int8 b6=0 int8 b7=0
    int8 cnt=8
end
[__inst__]
LDI A,0 LDI B,8 LDI C,170 LDI H,0
$LOOP:
    CMP A,B CAN 1 JMP $D
    RIN H,A,SI SSX C
    LDI E,1 ADD A,A,E JMP $LOOP
$D: HLT end
""",[(0,170),(1,170),(2,170),(3,170),(4,170),(5,170),(6,170),(7,170)])

print("=== 33. memcmp: compare [1,2,3,4,5] vs [1,2,3,4,5] => equal (result=0) ===")
test("cmpeq","""
[__data__]
    int8 a0=1 int8 a1=2 int8 a2=3 int8 a3=4 int8 a4=5
    int8 b0=1 int8 b1=2 int8 b2=3 int8 b3=4 int8 b4=5
    int8 r=0
    int8 cnt=5
end
[__inst__]
LDI A,0 LDI B,5 LDI H,0 LDI F,0
$LOOP:
    CMP A,B CAN 1 JMP $D
    RIN H,A,SI LSX C
    LDI E,5 ADD E,E,A RIN H,E,SI LSX D
    CMP C,D CAN 1 JMP $SAME
    LDI G,1
    ST 10,G
    JMP $D
$SAME:
    LDI G,1 ADD A,A,G JMP $LOOP
$D: HLT end
""",[(10,0)])

print("=== 34. memcmp: compare [1,2,9,4,5] vs [1,2,3,4,5] => not equal (result=1) ===")
test("cmpne","""
[__data__]
    int8 a0=1 int8 a1=2 int8 a2=9 int8 a3=4 int8 a4=5
    int8 b0=1 int8 b1=2 int8 b2=3 int8 b3=4 int8 b4=5
    int8 r=0
    int8 cnt=5
end
[__inst__]
LDI A,0 LDI B,5 LDI H,0 LDI F,0
$LOOP:
    CMP A,B CAN 1 JMP $D
    RIN H,A,SI LSX C
    LDI E,5 ADD E,E,A RIN H,E,SI LSX D
    CMP C,D CAN 1 JMP $SAME
    LDI G,1 ST 10,G JMP $D
$SAME:
    LDI G,1 ADD A,A,G JMP $LOOP
$D: HLT end
""",[(10,1)])

print("=== 35. memswap: swap [1,2,3] and [4,5,6] ===")
test("memswap","""
[__data__]
    int8 a0=1 int8 a1=2 int8 a2=3 int8 a3=4 int8 a4=5 int8 a5=6
    int8 cnt=3
end
[__inst__]
LDI A,0 LDI B,3 LDI H,0
$LOOP:
    CMP A,B CAN 1 JMP $D
    RIN H,A,SI LSX C
    LDI E,3 ADD E,E,A RIN H,E,SI LSX D
    RIN H,A,SI SSX D
    RIN H,E,SI SSX C
    LDI G,1 ADD A,A,G JMP $LOOP
$D: HLT end
""",[(0,4),(1,5),(2,6),(3,1),(4,2),(5,3)])

print("=== 36. memcpy backwards: copy with decrementing SI ===")
# Use DIN to decrement SI after each load
test("memcpyb","""
[__data__]
    int8 s0=99 int8 s1=88 int8 s2=77 int8 s3=66 int8 s4=55
    int8 d0=0 int8 d1=0 int8 d2=0 int8 d3=0 int8 d4=0
    int8 cnt=5
end
[__inst__]
LDI A,0 LDI B,5 LDI H,0 LDI F,4
$LOOP:
    CMP A,B CAN 1 JMP $D
    RIN H,F,SI LSX C
    LDI E,5 ADD E,E,F RIN H,E,SI SSX C
    LDI G,1 SUB F,F,G ADD A,A,G JMP $LOOP
$D: HLT end
""",[(5,99),(6,88),(7,77),(8,66),(9,55)])

print("=== 37. block zero: clear 10 bytes to 0 ===")
test("clear","""
[__data__]
    int8 b0=255 int8 b1=255 int8 b2=255 int8 b3=255 int8 b4=255
    int8 b5=255 int8 b6=255 int8 b7=255 int8 b8=255 int8 b9=255
    int8 cnt=10
end
[__inst__]
LDI A,0 LDI B,10 LDI C,0 LDI H,0
$LOOP:
    CMP A,B CAN 1 JMP $D
    RIN H,A,SI SSX C
    LDI G,1 ADD A,A,G JMP $LOOP
$D: HLT end
""",[(0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0),(8,0),(9,0)])

print("=== 38. memcpy overlapping forward: copy [1..8] to offset+3 ===")
# src=[1,2,3,4,5,6,7,8], copy 5 bytes from offset 0 to offset 3
# Overlapping forward: reads [1,2,3,mem[3]was1,mem[4]was2] → [1,2,3,1,2,3,1,2]
test("memcpovf","""
[__data__]
    int8 b0=1 int8 b1=2 int8 b2=3 int8 b3=4 int8 b4=5 int8 b5=6 int8 b6=7 int8 b7=8
    int8 cnt=5
end
[__inst__]
LDI A,0 LDI B,5 LDI H,0
$LOOP:
    CMP A,B CAN 1 JMP $D
    RIN H,A,SI LSX C
    LDI E,3 ADD E,E,A RIN H,E,SI SSX C
    LDI G,1 ADD A,A,G JMP $LOOP
$D: HLT end
""",[(3,1),(4,2),(5,3),(6,1),(7,2)])

print(f"\n=== {passed} passed, {failed} failed ===")
if failed: sys.exit(1)
