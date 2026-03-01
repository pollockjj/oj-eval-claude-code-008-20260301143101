#!/usr/bin/env python3
"""Generate mov language code for sort problem (2282).

Read 5 ASCII digits '0'-'9', output sorted ascending.

Strategy: Counting sort using lookup tables.
- Read 5 digits
- For each digit, increment count at mem[digit_value]
  (using digit ASCII as address: mem[48]..mem[57] for '0'..'9')
- Use increment lookup table: mem[256+x] = x+1 for x=0..5
- Then output: for each digit '0' to '9', output it count times

Memory layout:
- mem[48..57]: counts for digits '0'..'9' (initially 0)
- mem[256..261]: increment table (mem[256+x] = x+1 for x=0..5)
- Decrement table: mem[384+x] = x-1 for x=1..5, mem[384+0] = 0

For outputting: need to loop over digits 0-9, and for each, output the digit
count times. With only mov and no branching, we have to unroll.

Since there are 5 digits and 10 possible values, max count for any digit is 5.
We need to output each digit up to 5 times.

For each digit d ('0'..'9'):
  For each potential output slot (5 times max):
    If count[d] > 0: output d, decrement count
    Else: output 0 (suppressed)

To check "if count > 0": use lookup mem[320+count] where:
  mem[320+0] = 0 (suppress)
  mem[320+1] = mem[320+2] = ... = mem[320+5] = d (the digit to output)
But d changes for each digit... so we need per-digit tables. Too much.

Alternative approach: use the count itself to conditionally output.
If count > 0, output the digit. If count = 0, output 0 (suppressed).

Trick: mem[300+0] = 0, mem[300+1] = 1, mem[300+2] = 1, ..., mem[300+5] = 1
(nonzero check table)
Then: check = mem[300 + count]. If check=0, suppress. If check=1, output digit.
But how to select between digit and 0?
Use: output_value = mem[400 + check] where mem[400+0]=0, mem[400+1]=digit.
Again, digit varies...

SIMPLER APPROACH:
For each digit d (48-57), repeat 5 times:
  R = [d] (count)
  Use lookup: mem[300+R] where mem[300+0]=0, mem[300+k]=d for k=1..5
  Output mem[300+R]
  If R > 0, decrement: [d] = mem[256+R-1] ... tricky

Let me try yet another approach. Since we only have 5 digits, there are limited orderings.

EVEN SIMPLER: Bubble sort using conditional swap via lookup tables.

Actually, the cleanest approach for mov language:
1. Read 5 digits into registers/memory
2. Use comparison-based swap operations using lookup tables
3. Output sorted result

For comparing two values a and b and potentially swapping:
- mem[a*256+b] could store min(a,b) and max(a,b), but that's too much memory.

Let me go with counting sort but handle the output carefully.

For counting sort output, for each digit '0'-'9', I need to output it count times.
Max count is 5. I'll unroll: check if count >= 1, >= 2, >= 3, >= 4, >= 5.

For "count >= k": if count >= k, output the digit, else output 0 (suppress).
This is: output = mem[table + count] where table has 0 for count < k, digit for count >= k.

For each digit and each threshold, I need different table entries. But digits vary.

ALTERNATIVE: Don't output the ASCII character directly. Instead, set up the count,
then have a master output loop.

OK let me just do this: for each digit d in '0'..'9':
  Repeat 5 times:
    C = [d]  (count of digit d, address is ASCII value of d, 48-57)
    R = [C+300] where mem[300+0]=0, mem[300+k]=ASCII of d for k>=1
    O<R  (output or suppress)
    # Decrement count if > 0
    [d] = [C+350] where mem[350+0]=0, mem[350+k]=k-1 for k>=1

But the problem is mem[300+k] needs to be the digit d, and d changes!
We'd need to rebuild the lookup for each digit.

OR: Use a different table per digit. 10 digits * 1 table = 10 tables. Each table is 6 entries.
That's 60 entries total. Manageable!

For digit d (ASCII a):
  mem[d*6 + 300 + 0] = 0
  mem[d*6 + 300 + k] = a for k=1..5

Wait, d*6 isn't computable with mov. Let me just pre-assign fixed table offsets.

Actually, let me use a different approach entirely. I'll have:
- Table at 300: mem[300+0]=0, mem[301]=1, ..., mem[305]=1 (nonzero flag)
- For each digit d, for each slot, check if count > 0, if yes output d

For each digit d:
  Set S = d (the digit ASCII)
  For 5 iterations:
    Load count R = [d_addr]  (where d_addr is 48+digit)
    F = [R+300]  # flag: 0 if count=0, 1 if count>0
    # Now output: if F=1, output S; if F=0, output 0
    # Use: mem[400+0]=0, mem[400+1]=S (but S varies!)
    # Set mem[401] = S before each digit block
    V = [F+400]  # 0 or S
    O<V
    # Decrement count: new_count = mem[350+R] where mem[350+0]=0, mem[350+k]=k-1
    N = [R+350]
    [d_addr] = N (but d_addr is an immediate... we can use [immediate])
"""

lines = []

def emit(line):
    lines.append(line)

def comment(text):
    lines.append(f"# {text}")

comment("=== Problem 2282: Sort 5 digits ===")
comment("")

# Phase 1: Build tables
comment("Nonzero flag: mem[300+k] = 0 for k=0, 1 for k=1..5")
emit("A<1")
for k in range(1, 6):
    emit(f"[{300+k}]<A")

comment("Decrement: mem[350+k] = k-1 for k=1..5, mem[350+0] = 0 (already 0)")
for k in range(1, 6):
    emit(f"A<{k-1}")
    emit(f"[{350+k}]<A")

comment("")
comment("=== Read 5 digits ===")
# Read into mem[48..57] as counts: for each digit read, increment count at its address
# mem[digit_ascii] += 1
# Increment: load current, lookup increment table, store back
comment("Increment table: mem[256+k] = k+1 for k=0..5")
for k in range(6):
    emit(f"A<{k+1}")
    emit(f"[{256+k}]<A")

comment("")
for i in range(5):
    comment(f"Read digit {i+1}")
    emit("A<I")        # A = digit ASCII
    emit("B<[A]")      # B = current count at mem[A]
    emit("C<[B+256]")  # C = B + 1 (increment)
    emit("[A]<C")       # store back

comment("")
comment("=== Output sorted ===")
# For each digit '0'(48) to '9'(57), output it count times

for d in range(48, 58):  # digits '0' to '9'
    comment(f"Digit '{chr(d)}' (ASCII {d})")
    # Set mem[401] = d (the output character for this digit)
    emit(f"A<{d}")
    emit(f"[401]<A")
    # Repeat 5 times
    for rep in range(5):
        emit(f"R<[{d}]")       # R = count
        emit("S<[R+300]")      # S = nonzero flag (0 or 1)
        emit("V<[S+400]")      # V = 0 (suppress) or d (output)
        emit("O<V")            # output
        emit("N<[R+350]")      # N = max(0, R-1)
        emit(f"[{d}]<N")       # decrement count
    # Note: we use registers R, S, V, N which are valid (not I, O, Z)
    # R=17, S=18, V=21, N=13 - all valid general-purpose registers

comment("")
emit("Z<1")

# Write file
with open("/tmp/projdevbench-oj-eval-claude-code-008-20260301143101/code/2282.mv", "w") as f:
    f.write("\n".join(lines) + "\n")

code_lines = [l for l in lines if l and not l.startswith("#")]
print(f"Total lines: {len(lines)}, Code lines: {len(code_lines)}")
