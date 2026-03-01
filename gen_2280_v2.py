#!/usr/bin/env python3
"""Generate optimized printf (2280) - minimal lines using [imm]<imm."""

lines = []

def emit(line):
    lines.append(line)

def comment(text):
    lines.append(f"# {text}")

# Tables at offsets 128 (hundreds), 256 (tens), 384 (units)
# Using [imm]<imm for all entries

comment("Hundreds digit: mem[128+v]='1' for v=100..127")
for v in range(100, 128):
    emit(f"[{128+v}]<49")

comment("Tens digit: mem[256+v]=tens_char for v=10..127")
for v in range(10, 128):
    tens = (v // 10) % 10
    digit_char = 48 + tens
    emit(f"[{256+v}]<{digit_char}")

comment("Units digit: mem[384+v]=units_char for v=0..127")
for v in range(0, 128):
    units = v % 10
    digit_char = 48 + units
    emit(f"[{384+v}]<{digit_char}")

comment("Main logic")
emit("A<I")
emit("O<[A+128]")
emit("O<[A+256]")
emit("O<[A+384]")
emit("Z<1")

with open("/tmp/projdevbench-oj-eval-claude-code-008-20260301143101/code/2280.mv", "w") as f:
    f.write("\n".join(lines) + "\n")

code_lines = [l for l in lines if l and not l.startswith("#")]
print(f"Total lines: {len(lines)}, Code lines: {len(code_lines)}")
