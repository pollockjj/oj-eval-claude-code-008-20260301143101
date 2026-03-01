#!/usr/bin/env python3
"""Generate compact counting sort for 5 digits - optimized v3.

Key optimizations vs v2 (64 lines -> 43 lines):
1. No once-gate for R: R starts at 0 (default register value).
   Advance table has mem[300]=48 so R goes 0->48 on first iteration.
   This saves 5 lines (the entire once-gate init).

2. No separate decrement table: Reuse increment table at offset 198.
   mem[198]=0 (default), mem[199]=0 (default), mem[200]=1, mem[201]=2, ...
   So [C+198] gives C-1 for C=1..5 (using mem[199..203] = 0,1,2,3,4).
   Wait: mem[199]=0(default), mem[200]=1, mem[201]=2, mem[202]=3, mem[203]=4.
   For C=1: mem[199]=0. For C=2: mem[200]=1. Correct! Saves 5 lines.

3. Inverted flag: Instead of nonzero table (5 lines: mem[221..225]=1),
   use is-zero table (1 line: mem[230]=1).
   F=1 when count=0 (advance), F=0 when count>0 (output).
   Saves 4 lines.

4. No S register tracking: Halt when R advances past 57 (digit '9'),
   detected by mem[458]=1 check. Saves 7 lines (S init + S update in loop).

5. Increment table only needs 5 entries (0->1 through 4->5) since max
   count is 5. Saves 1 line vs original 6 entries.

Total: 43 code lines.
"""

import os

lines = []

def emit(line):
    lines.append(line)

def comment(text):
    lines.append(f"# {text}")

comment("=== Problem 2282: Sort 5 digits (optimized v3) ===")
comment("Counting sort: count digits, then sweep 0-9 outputting each count times")
comment("")

comment("Increment table: mem[200+k]=k+1 for k=0..4")
for k in range(5):
    emit(f"[{200+k}]<{k+1}")

comment("Is-zero table: mem[230]=1 (F=1 when count=0, F=0 when count>0)")
emit("[230]<1")

comment("Advance table: mem[300+R]=R+1 for digits, plus init shortcut")
emit("[300]<48")  # R=0 -> 48 (first iteration init shortcut)
for d in range(48, 58):
    emit(f"[{300+d}]<{d+1}")

comment("Halt flag: mem[458]=1 (triggers Z=1 when R=58, past digit '9')")
emit("[458]<1")

comment("Read 5 digits into count array at mem[48..57]")
for i in range(5):
    emit("A<I")
    emit("B<[A]")
    emit("[A]<[B+200]")

comment("Output loop: sweep digits, output each count[R] times")
comment("F=0 means count>0 (output R, stay). F=1 means count=0 (suppress, advance).")
emit("C<[R]")           # C = count at current digit R
emit("F<[C+230]")       # F = is-zero flag (1 if C=0, 0 if C>0)
emit("[280]<R")          # store R for conditional output
emit("O<[F+280]")       # F=0: output mem[280]=R. F=1: output mem[281]=0 (suppressed)
emit("[R]<[C+198]")      # count[R]-- (uses increment table: mem[199..203] = 0,1,2,3,4)
emit("E<[R+300]")        # E = next digit (R+1 via advance table)
emit("[290]<R")           # store R (for F=0: stay at R)
emit("[291]<E")           # store E (for F=1: advance to E)
emit("R<[F+290]")        # F=0: R=mem[290]=R (stay). F=1: R=mem[291]=E (advance)
emit("Z<[R+400]")        # Z = mem[R+400]. R=58: mem[458]=1 -> halt. Else: 0.

# Write output
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "code", "2282.mv")
with open(output_path, "w") as f:
    f.write("\n".join(lines) + "\n")

code_lines = [l for l in lines if l and not l.startswith("#")]
print(f"Total lines (with comments): {len(lines)}, Code lines: {len(code_lines)}")
print(f"Written to: {output_path}")
