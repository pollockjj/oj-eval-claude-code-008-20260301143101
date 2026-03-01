#!/usr/bin/env python3
"""Generate optimized A+B mov program using [imm]<imm syntax."""

lines = []

def emit(line):
    lines.append(line)

def comment(text):
    lines.append(f"# {text}")

comment("=== Problem 2281: A+B ===")

# Identity mapping: mem[x] = x for x in 96..115
comment("Identity mapping for sum computation")
for x in range(96, 116):
    emit(f"[{x}]<{x}")

# Digit result table: mem[224..243] for sum values 96..115
# sum-96 in 0..19: digit = (sum-96) % 10 + 48
comment("Digit result table")
for v in range(20):
    digit = v % 10 + 48
    emit(f"[{224+v}]<{digit}")

# Carry out table: mem[256..275] for sum values 96..115
# carry = 1 if (sum-96) >= 10, else 0
comment("Carry out table")
for v in range(20):
    carry = 1 if v >= 10 else 0
    if carry != 0:  # skip zeros (already 0)
        emit(f"[{256+v}]<{carry}")

# Leading digit lookup: mem[400+0]=0 (already), mem[401]=49 ('1')
comment("Leading digit lookup")
emit("[401]<49")

# Read 21 input chars into mem[0..20]
comment("Read input")
for i in range(21):
    emit(f"[{i}]<I")

# Wait, can I do [i]<I? [imm]<register. I is the input register.
# The parser: src = "I", src[0] = 'I'. In the parser code:
# else if (src[0] >= 'A' && src[0] <= 'Z') { src_mode = 1; src = src[0] - 'A'; }
# So I is treated as register 8 (I='I'-'A'=8).
# But then: if (code[q].src == 8) err("I can't be used here");
# Wait, the check is at line 73: if ((code[q].src == 8 || code[q].src == 14) && code[q].src_mode != 5)
# Wait no, that check is for when src_mode is 2,3,4 (memory indirection).
# For src_mode == 1 (register), src == 8 means I register.
# The check at line 79: if (code[q].src == 14) err("O can't be used as src");
# So I as src register is FINE (it reads input). src == 8 with mode 1 triggers the
# special I handling at runtime (line 141).
# So [0]<I reads one byte from input and stores at mem[0]. YES!

# And dest [imm] is mode 5. So this is valid.

# Actually, let me re-read: for the [imm]<I case:
# dest = [0], dest_mode = 5, src = I, src_mode = 1, src_val = 8
# At runtime: src is read via the I special case (fgetc).
# Then dest is handled: case 5: mem[code[i].dest] = src.
# This works!

# Process digits right to left
comment("Add digits right to left")
emit("C<0")  # carry = 0

for pos in range(10):
    i = 9 - pos
    j = 20 - pos
    k = 40 - pos

    emit(f"A<[{i}]")
    emit(f"B<[{j}]")
    emit("E<[A+B]")       # E = A+B (identity)
    emit("F<[E+C]")       # F = A+B+carry (identity)
    emit(f"[{k}]<[F+128]")  # store digit result directly
    emit("C<[F+160]")      # carry out

# Output result
comment("Output result")
emit("D<[C+400]")  # leading digit (0 or '1')
emit("O<D")

for k in range(31, 41):
    emit(f"O<[{k}]")

emit("Z<1")

with open("/tmp/projdevbench-oj-eval-claude-code-008-20260301143101/code/2281.mv", "w") as f:
    f.write("\n".join(lines) + "\n")

code_lines = [l for l in lines if l and not l.startswith("#")]
print(f"Total lines: {len(lines)}, Code lines: {len(code_lines)}")
