#!/usr/bin/env python3
"""Generate optimized printf (2280) mov program with addresses 0-511."""

lines = []

def emit(line):
    lines.append(line)

def comment(text):
    lines.append(f"# {text}")

comment("Problem 2280: printf - output decimal ASCII code of input char")
comment("Tables at offsets 128 (hundreds), 256 (tens), 384 (units)")
comment("")

# Build tables for values 0-127
# Only emit non-zero entries since memory starts as 0

# Hundreds digit (mem[128+v]): '1' for v=100-127, 0 otherwise
comment("Hundreds digit table at mem[128+v]")
emit("A<49")  # '1'
for v in range(100, 128):
    emit(f"[{128+v}]<A")

comment("")

# Tens digit (mem[256+v]):
# v=0-9: 0 (suppress)
# v=10-19: '1', v=20-29: '2', ..., v=90-99: '9'
# v=100-109: '0', v=110-119: '1', v=120-127: '2'
comment("Tens digit table at mem[256+v]")
for decade_start in range(10, 100, 10):
    tens_digit = decade_start // 10
    tens_ascii = 48 + tens_digit
    emit(f"A<{tens_ascii}")
    for v in range(decade_start, decade_start + 10):
        emit(f"[{256+v}]<A")

emit("A<48")  # '0' for v=100-109
for v in range(100, 110):
    emit(f"[{256+v}]<A")

emit("A<49")  # '1' for v=110-119
for v in range(110, 120):
    emit(f"[{256+v}]<A")

emit("A<50")  # '2' for v=120-127
for v in range(120, 128):
    emit(f"[{256+v}]<A")

comment("")

# Units digit (mem[384+v]): '0'+v%10 for all v
comment("Units digit table at mem[384+v]")
# Group by unit digit for efficiency
for digit in range(10):
    digit_ascii = 48 + digit
    emit(f"A<{digit_ascii}")
    for v in range(digit, 128, 10):
        emit(f"[{384+v}]<A")

comment("")
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

# Verify max address
max_addr = 0
for l in lines:
    if l.startswith('#'):
        continue
    import re
    m = re.search(r'\[(\d+)\]', l)
    if m:
        addr = int(m.group(1))
        if addr > max_addr:
            max_addr = addr
print(f"Max memory address: {max_addr}")
