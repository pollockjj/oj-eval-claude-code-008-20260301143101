#!/usr/bin/env python3
"""Generate compact counting sort for 5 digits - optimized v3."""

lines = []

def emit(line):
    lines.append(line)

def comment(text):
    lines.append(f"# {text}")

comment("=== Problem 2282: Sort 5 digits (compact v3) ===")

# Once-gated initialization for R and S
emit("A<[65]")
emit("[66]<48")
emit("[67]<R")
emit("R<[A+66]")
emit("[68]<5")
emit("[69]<S")
emit("S<[A+68]")
emit("[65]<1")

# Setup tables (idempotent)
comment("Increment table: mem[200+k]=k+1 for k=0..5")
for k in range(6):
    emit(f"[{200+k}]<{k+1}")

comment("Decrement table: mem[210+k]=k-1 for k=1..5")
for k in range(1, 6):
    emit(f"[{210+k}]<{k-1}")

comment("Nonzero flag: mem[220+k]=1 for k=1..5")
for k in range(1, 6):
    emit(f"[{220+k}]<1")

comment("Advance table: mem[300+d]=d+1 for d=48..57")
for d in range(48, 58):
    emit(f"[{300+d}]<{d+1}")

emit("[310]<1")

# Read 5 digits - optimized to 3 lines each
comment("Read 5 digits")
for i in range(5):
    emit("A<I")
    emit("B<[A]")
    emit("[A]<[B+200]")

# Output loop
comment("Output loop")
emit("C<[R]")
emit("F<[C+220]")
emit("[281]<R")
emit("O<[F+280]")
emit("[R]<[C+210]")
emit("E<[R+300]")
emit("[290]<E")
emit("[291]<R")
emit("R<[F+290]")
emit("K<[S+210]")
emit("[292]<S")
emit("[293]<K")
emit("S<[F+292]")
emit("Z<[S+310]")

with open("/tmp/projdevbench-oj-eval-claude-code-008-20260301143101/code/2282.mv", "w") as f:
    f.write("\n".join(lines) + "\n")

code_lines = [l for l in lines if l and not l.startswith("#")]
print(f"Total lines: {len(lines)}, Code lines: {len(code_lines)}")
