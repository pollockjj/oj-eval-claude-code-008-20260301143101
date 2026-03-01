#!/usr/bin/env python3
"""Generate stack-based recursive Hanoi solver - v2 fixed.

Memory Layout (verified non-overlapping):
  5:       halt check (mem[5]=1, mem[6..26] must stay 0)
  36-56:   Q sub-1 table (offset 35, Q=1..21)
  57:      init flag (was at 60, moved to avoid output gating conflict)
  60:      output gating suppress (must stay 0)
  61:      output gating variable slot
  70-71:   '-' gating (70=0, 71=45)
  80-81:   '>' gating (80=0, 81=62)
  90-91:   '\n' gating (90=0, 91=10)
  100-191: stack (max 21 frames x 4 bytes)
  200:     case table type=0 (print, case=1)
  249-258: case table type=49-58 (expand, case=2)
  260-262: flag_print (offset 260, case 0/1/2)
  265-267: flag_expand (offset 265, case 0/1/2)
  270-273: P/Q selection cells
  329-338: decrement table (offset 280, n=49-58)
  340-421: P tables (add-8 at even, sub-4 at odd offsets from 340)
  423-443: Q add-2 table (offset 422, Q=1..21)
"""

lines = []

def emit(line):
    lines.append(line)

def comment(text):
    lines.append(f"# {text}")

P_MAX = 80  # max P value (for n=10, depth=21, P_max=20*4=80)

comment("=== Problem 2283: Hanoi (stack-based v2) ===")

# ONCE-GATED INIT (using mem[57] as init flag instead of mem[60])
comment("Once-gated init")
emit("A<[57]")        # A = 0 (first) or 1 (subsequent)
emit("[57]<1")

# P restoration/init
emit("[58]<0")        # initial P=0
emit("[59]<P")        # saved P (using 59 instead of 64)
emit("P<[A+58]")     # restore P

# Q restoration/init
emit("[62]<1")        # initial Q=1
emit("[63]<Q")        # saved Q
emit("Q<[A+62]")     # restore Q

# Read input
emit("N<I")

# Push initial frame at mem[100..103]
# When A=0: W=100 (real). When A=1: W=92 (dummy, writing to 92-95 which is safe)
emit("[64]<100")      # real write addr (A=0)
emit("[65]<92")       # dummy addr (A=1)
emit("W<[A+64]")
emit("[W]<N")
emit("[W+1]<65")      # 'A'
emit("[W+2]<67")      # 'C'
emit("[W+3]<66")      # 'B'

# TABLES
comment("Case table: mem[200+type]")
emit("[200]<1")       # type 0 = print (case=1)
for k in range(49, 59):
    emit(f"[{200+k}]<2")   # type 49-58 = expand (case=2)

comment("Flag tables")
emit("[261]<1")       # flag_print[case=1]
emit("[267]<1")       # flag_expand[case=2]

comment("Decrement n: mem[280+n]=n-1 for n=49..58")
for n in range(49, 59):
    emit(f"[{280+n}]<{n-1}")

comment("P add-8 and sub-4: mem[340+P]=P+8, mem[341+P]=P-4")
emit(f"[341]<252")   # P=0 sub-4: wrap to 252 (will never be used for P=0 + expand since P=0 means 1 frame)
for p in range(0, P_MAX+4, 4):
    emit(f"[{340+p}]<{p+8}")
    if p >= 4:
        emit(f"[{341+p}]<{p-4}")

comment("Q add-2: mem[422+Q]=Q+2")
for q in range(1, 22):
    emit(f"[{422+q}]<{q+2}")

comment("Q sub-1: mem[35+Q]=Q-1")
for q in range(1, 22):
    emit(f"[{35+q}]<{q-1}")

comment("Halt: mem[5]=1")
emit("[5]<1")

comment("Output gating")
# mem[60] must stay 0 (suppress). mem[61] holds the variable value.
# mem[70]=0, [71]=45('-'). mem[80]=0, [81]=62('>'). mem[90]=0, [91]=10('\n').
emit("[71]<45")       # '-'
emit("[81]<62")       # '>'
emit("[91]<10")       # '\n'

# MAIN LOOP
comment("")
comment("=== Main loop ===")
emit("T<[P+100]")
emit("U<[P+101]")
emit("V<[P+102]")
emit("W<[P+103]")
emit("C<[T+200]")
emit("F<[C+260]")
emit("G<[C+265]")

comment("Print (gated by F)")
# When F=0: O<mem[60]=0 (suppressed), O<mem[70]=0, O<mem[80]=0, O<mem[90]=0
# When F=1: O<mem[61]=U, O<mem[71]='-', O<mem[81]='>', O<mem[91]='\n'
emit("[61]<U")
emit("O<[F+60]")
emit("O<[F+70]")
emit("O<[F+80]")
emit("[61]<V")
emit("O<[F+60]")
emit("O<[F+90]")

comment("Expand")
emit("D<[T+280]")
emit("[P+100]<D")
emit("[P+101]<W")
emit("[P+102]<V")
emit("[P+103]<U")
emit("[P+104]<0")
emit("[P+105]<U")
emit("[P+106]<V")
emit("[P+107]<0")
emit("[P+108]<D")
emit("[P+109]<U")
emit("[P+110]<W")
emit("[P+111]<V")

comment("P update")
emit("A<[P+340]")     # A = P+8
emit("B<[P+341]")     # B = P-4
emit("[270]<B")
emit("[271]<A")
emit("P<[G+270]")

comment("Q update")
emit("A<[Q+422]")     # A = Q+2
emit("B<[Q+35]")      # B = Q-1
emit("[272]<B")
emit("[273]<A")
emit("Q<[G+272]")

emit("[59]<P")         # save P
emit("[63]<Q")         # save Q
emit("Z<[Q+5]")       # halt when Q=0

with open("/tmp/projdevbench-oj-eval-claude-code-008-20260301143101/code/2283.mv", "w") as f:
    f.write("\n".join(lines) + "\n")

code_lines = [l for l in lines if l and not l.startswith("#")]
print(f"Total lines: {len(lines)}, Code lines: {len(code_lines)}")

import re
max_imm = 0
for l in lines:
    for m in re.finditer(r'\[(\d+)\]', l):
        addr = int(m.group(1))
        max_imm = max(max_imm, addr)
        if addr > 511:
            print(f"ERROR: Address {addr} > 511 in: {l}")
print(f"Max immediate address: {max_imm}")

max_ri = 0
for l in lines:
    for m in re.finditer(r'\[(\w)\+(\d+)\]', l):
        reg = m.group(1)
        imm = int(m.group(2))
        reg_max = {'P': P_MAX, 'Q': 21, 'T': 58, 'C': 2, 'F': 1, 'G': 1, 'W': 103, 'A': 1}.get(reg, 255)
        max_addr = reg_max + imm
        max_ri = max(max_ri, max_addr)
        if max_addr > 511:
            print(f"WARNING: [{reg}+{imm}] max addr={max_addr}")
print(f"Max [R+I] address estimate: {max_ri}")

# Verify mem[60], mem[70], mem[80], mem[90] are never written to with non-zero values
print("\nChecking output suppress addresses (must be 0):")
for addr in [60, 70, 80, 90]:
    written = False
    for l in lines:
        if l.startswith('#') or not l:
            continue
        m = re.match(r'\[(\d+)\]<(\d+)', l)
        if m and int(m.group(1)) == addr and int(m.group(2)) != 0:
            print(f"  WARNING: mem[{addr}] written non-zero by: {l}")
            written = True
    if not written:
        print(f"  mem[{addr}]: OK (stays 0)")
