#!/usr/bin/env python3
"""Generate mov language code for A+B problem (2281).

Input: two 10-digit numbers separated by '+' (exactly 21 chars)
Output: their sum (up to 11 digits, no leading zeros)

Strategy:
- Read all 21 chars into memory at positions 0-20
- Positions 0-9: first number digits
- Position 10: '+' (skip)
- Positions 11-20: second number digits
- Use lookup tables for digit addition with carry
- Process from right to left
- Store result, then output

Memory layout:
- mem[0..20]: input characters
- mem[30..40]: result digits (up to 11 digits), stored right-to-left
  mem[40] = units, mem[39] = tens, ..., mem[30] = max position
- Lookup tables:
  - mem[256+s]: result digit (ASCII) for sum s where s = ascii_a + ascii_b + carry
    s ranges from 96 (48+48+0) to 115 (57+57+1)
  - mem[384+s]: new carry for sum s (0 or 1)

Since we can't loop with mov, we unroll the loop for 10 digit positions.
"""

lines = []

def emit(line):
    lines.append(line)

def comment(text):
    lines.append(f"# {text}")

# Phase 1: Read 21 input chars into mem[0..20]
comment("=== Phase 1: Read input into memory ===")
# Use register A as pointer, store at [A], increment A via lookup
# Actually, we can't increment. Let's just unroll.
for i in range(21):
    emit(f"A<I")
    emit(f"[{i}]<A")

# Phase 2: Build lookup tables
comment("=== Phase 2: Build lookup tables ===")
comment("Sum table: mem[256+s] = result digit, mem[384+s] = carry")
comment("s = ascii_a + ascii_b + carry, range 96-115")

for s in range(96, 116):
    val = s - 96  # 0-19
    digit = val % 10
    carry = 1 if val >= 10 else 0
    digit_ascii = 48 + digit
    emit(f"A<{digit_ascii}")
    emit(f"[{256+s}]<A")
    emit(f"A<{carry}")
    emit(f"[{384+s}]<A")

# Phase 3: Add digits from right to left
comment("=== Phase 3: Add digits right to left ===")
comment("Result stored in mem[30..40], 40=rightmost")

# Initialize carry to 0 (already 0 in a fresh register)
emit("C<0")  # C = carry

# For each position from 9 down to 0:
# digit_a = mem[9-pos..0] -> mem[i] where i = 9,8,...,0
# digit_b = mem[20-pos..11] -> mem[j] where j = 20,19,...,11
# result position: mem[40-pos..31] -> mem[k] where k = 40,39,...,31

for pos in range(10):
    i = 9 - pos   # first number digit index (rightmost first)
    j = 20 - pos  # second number digit index
    k = 40 - pos  # result position

    comment(f"Position {pos}: mem[{i}] + mem[{j}] + carry -> mem[{k}]")

    # Load digit_a into A
    emit(f"A<[{i}]")
    # Load digit_b into B
    emit(f"B<[{j}]")

    # Now we need mem[A+B+C] where C is carry (0 or 1)
    # But [R+R] only adds two registers. So we need a two-step approach.
    # Step 1: D = mem[256 + A + B] - but we can't do 256+A+B in one step
    # Instead: use the fact that A+B ranges 96-114, and carry is 0 or 1
    # So total = A+B+carry ranges 96-115

    # We need to compute A+B first. Use [A+B] to read mem[A+B].
    # But we need mem[256+A+B].
    # Trick: add 128 to both A and B? No, that would make A+B = original + 256.
    # Actually! If we set A = digit_a + 128, then [A+B] accesses mem[digit_a+128+digit_b]
    # = mem[digit_a+digit_b+128]. For digit_a+digit_b in 96-114, this is 224-242.
    # We'd put our lookup at 224-243. That works!

    # Better yet: just store tables at addresses that match raw A+B values.
    # A+B ranges 96-114, +carry 0/1 → 96-115.
    # We stored at mem[256+s]. But 256+96=352, 256+115=371.
    # We can't reach 352 with [R+R] since max is 510. OK that works.
    # But we need [R+R] where one R = A+B result and other = 256 base. No, [R+R] reads mem[R1+R2].
    # We need mem[256 + A + B + carry]. That's 3 additions...

    # Alternative: store lookup at raw address. mem[96..115] for digit result.
    # But that overlaps with our input storage at mem[0..20]!
    # The input uses 0-20, and 96-115 doesn't overlap. Good!

    # So: put lookup at mem[96..115] for digit, mem[116..135] for carry?
    # Wait, but we also need to add carry.
    # Approach:
    # 1. Use [A+B] to get preliminary result from table at mem[96..114]
    # 2. Add carry separately using another lookup

    # Actually the simplest approach:
    # Round 1: compute partial = A+B. Use mem[partial] for temp result.
    # Round 2: add carry to partial. But we can't add!

    # Let me use a different approach.
    # Store the "digit with no carry" table at offsets 96-114 (mem[96+0] to mem[96+18])
    # Store the "carry out with no carry in" table similarly
    # Then handle carry-in by having a second set of tables.
    #
    # Actually, simplest: two separate lookup tables.
    # Table A (no carry in): mem[96..114] = result digits, mem[224..242] = carry out
    # Table B (carry in=1): mem[97..115] shifted by 1 = same as table A shifted
    #
    # Wait, if carry_in=1, the sum is A+B+1. So we could add carry to one of the
    # registers before lookup. How to add 1? Use a lookup table!
    # mem[300+x] = x+1 for x in 0..255 (with wrapping)
    # Then: if carry==1, A = mem[300+A] (A += 1)
    # Then: result_digit = mem[A+B] using table at 96-115
    # carry_out = mem[128+A+B] using table at 128+96=224 to 128+115=243
    #
    # But we need conditional execution (only add 1 if carry==1).
    # With only mov, no conditionals!

    # KEY INSIGHT: Use carry as index to select between two code paths.
    # Not possible with linear execution...

    # BETTER IDEA:
    # We have two cases: carry=0 and carry=1.
    # For carry=0: index = A + B (96-114)
    # For carry=1: index = A + B + 1 (97-115)
    # We can compute both and select based on carry.

    # Store: mem[200 + s] = result digit for sum s (s=96..115)
    #        mem[320 + s] = carry out for sum s
    # For carry=0: use [A+B] → s=A+B, then access mem[200+s] somehow
    # For carry=1: use [(A+1)+B] or [A+(B+1)]

    # Actually, let me try a completely different approach.
    # Use mem as workspace.
    # Observation: if carry=0, we want to add 0 to A; if carry=1, add 1 to A.
    # Trick: add carry to A using [R+R]. Put value at mem[A+C] where table maps it.
    # mem[x] = x for x in 0..255 (identity table). Then A = mem[A+C] won't help...
    #
    # Wait: mem[x] = x+1 at some offset, then selective add?
    #
    # SIMPLEST APPROACH: Just make two separate table lookups.
    # Step 1: E = mem[A+B] where mem[96..114] has sum_no_carry result
    # Step 2: F = mem[A+B+128] where mem[224..242] has carry_out_no_carry
    # Step 3: Use carry C to adjust:
    #   If C=0, final_digit = E, final_carry = F
    #   If C=1, we need to "increment" E and possibly update carry
    #
    # For incrementing E: mem[400+E] = E+1 (with wrapping for '9'→'0')
    # When E goes from '9' to '0', extra carry is generated.
    #
    # So: if C=1, new_E = mem[400+E], new_carry_extra = mem[430+E]
    # final_carry = F OR carry_extra (but OR isn't available)
    # final_carry = F + carry_extra (works since at most one can be 1... no, both could be 1)
    # Actually if E='9' (from no-carry sum) and C=1, then:
    #   Original sum = A+B = 114 (both '9'), E = '8' (digit 8), F = 1 (carry)
    #   Wait let me recalculate. If A+B=114 (both 9+9=18), digit='8', carry=1
    #   Then +carry_in: should be 19, digit='9', carry=1
    #   So E='8', incrementing gives '9', no extra carry. F was already 1. Good.
    #
    #   What if A+B=105 (sum=9)? E='9', F=0.
    #   +carry_in=1: should be 10, digit='0', carry=1.
    #   E='9' incremented = '0', extra_carry=1. F=0. final_carry = 0+1 = 1. Correct!
    #
    #   What if A+B=114 and carry=1? Sum=19. digit='9', carry=1.
    #   E='8', F=1. Increment E: '9', extra_carry=0. final_carry=1+0=1. Digit='9'. Correct!
    #
    # So the approach works if we can handle: final_carry = F + extra_carry.
    # Both are 0 or 1, and F+extra_carry can be 0,1,2. But carry should be 0 or 1.
    # Can F=1 and extra_carry=1 happen? F=1 means A+B>=106 (sum>=10). extra_carry=1 means E='9'.
    # E is the digit from A+B, which is (A+B-96)%10 + 48. E='9' means (A+B-96)%10=9,
    # so A+B-96=9 or 19. A+B=105 or 115(impossible, max is 114). So A+B=105, F=0. Contradiction!
    # So F=1 and extra_carry=1 cannot both happen. Great, final_carry = F + extra_carry works,
    # and the result is always 0 or 1.
    #
    # But how to add F + extra_carry? Use [R+R] with a lookup!
    # mem[500+0]=0, mem[500+1]=1, mem[500+2]=... but we proved max is 1, so just:
    # We need [F+extra_carry+500] but that's 3 terms again...
    #
    # Simpler: since they can't both be 1, use [R+R] where R1=F, R2=extra_carry → mem[F+extra_carry]
    # and at mem[0]=0, mem[1]=1. These are in our input buffer though...
    #
    # OK this is getting complicated. Let me just use the approach where I have TWO complete
    # lookup tables (one for carry_in=0, one for carry_in=1), and use carry as an offset selector.

    # FINAL APPROACH:
    # Table at mem[96..114]: result digit when carry_in = 0
    # Table at mem[160..178]: carry_out when carry_in = 0 (offset by 64 from digit table)
    # Table at mem[224..242]: result digit when carry_in = 1 (offset by 128 from no-carry)
    # Table at mem[288..306]: carry_out when carry_in = 1 (offset by 64 from digit table)
    #
    # For carry_in = 0: digit = mem[A+B], carry_out = mem[A+B+some_register_holding_64]
    # For carry_in = 1: digit = mem[A+B+some_register_holding_128], carry_out = same+64
    #
    # To select: set an offset register based on carry.
    # If carry=0, offset=0. If carry=1, offset=128.
    # Use lookup: mem[carry_select_table + C] where C is carry.
    # mem[450+0] = 0, mem[450+1] = 128.
    # Then D = mem[450+C] → nope, need [R+I] and C is a register. [C+450] works!
    # D = [C+450] → D = 0 or 128.
    #
    # Then: digit = mem[A+B+D]. But that's 3 registers!
    # We can do: first compute E = A+B using... wait, we can't add two registers and get the result.
    # [A+B] reads from memory. We need the ADDRESS A+B as a value.
    # If mem[x] = x for all x (identity mapping), then [A+B] = A+B. Then we can use that value!
    #
    # YES! Create identity table: mem[96..115] isn't useful for identity, but:
    # If I make mem[x] = x for x in range 96-242 or whatever range I need, then:
    # Step 1: E = [A+B] → E = A + B (since mem[A+B] = A+B due to identity)
    # Step 2: Then I need mem[E + D] for the actual digit. Using [E+D]!
    #
    # This works! But I need identity mapping at mem[96..114]. These addresses might
    # not conflict since input is at 0-20.

    # Hmm wait, identity mapping means mem[96]=96, mem[97]=97, etc.
    # But values are uint8, so all fits in 0-255. Addresses 96-114 are fine.

    pass  # placeholder, will implement below

# Let me restart with a cleaner generation approach

lines.clear()

comment("=== Problem 2281: A+B ===")
comment("Read two 10-digit numbers separated by '+', output their sum")
comment("")

# Memory layout:
# mem[0..9]: first number digits (ASCII)
# mem[10]: '+' character
# mem[11..20]: second number digits (ASCII)
# mem[30..41]: result (up to 12 chars, right-aligned at 41)
#
# Lookup tables:
# mem[96..115]: identity mapping (mem[x] = x) for computing A+B as value
# After computing sum_index = A+B (96-114):
# Need to add carry offset.
# Two lookup tables at different base addresses:
# Digit result: base 128 for carry=0, base 256 for carry=1
# mem[128+s] = digit for sum s with carry_in=0 (s in 96..114)
# mem[256+s] = digit for sum s with carry_in=1 (s in 96..115... wait s=96+carry would start at 97)
# Actually carry_in=1 means effective sum = s+1, so we look up s+1 in the table.
# Just offset by 1: mem[256+s] = digit for sum s when carry_in=1 = digit for (s-96+1)
#
# Simpler: just have two separate tables
# No-carry table (carry_in=0): for sum s=A+B (96..114)
#   mem[128+s] = result digit, mem[192+s] = carry out  (wait, 128+114=242, 192+96=288)
#   Hmm, let me use completely separate ranges to avoid overlap.

# Let me use a Python-driven approach. Generate all the code explicitly.
# Since there are only 10 digit positions and the code runs in one pass (first time through),
# I'll unroll everything.

# But the program LOOPS. So all the table-building code will re-execute.
# That's OK - it just overwrites the same values. The read and process code
# will re-execute too, but by that point Z<1 should have fired.

# Actually, there's a problem: the program loops from instruction 0. If I read input
# in the first section, on the second loop it will read more (or get 0s).
# Solution: Build tables first, then read input, then process, then halt.
# Since halt happens before the loop, we won't re-execute.

# Let me restructure:
# 1. Build all lookup tables (these are harmless to repeat)
# 2. Read input
# 3. Process and output
# 4. Halt

lines.clear()

comment("=== Problem 2281: A+B ===")

# Build identity mapping for address computation
comment("Identity mapping: mem[x] = x for x in 96..115")
for x in range(96, 116):
    emit(f"A<{x}")
    emit(f"[{x}]<A")

# Build addition tables
# For sum value v (range 0..19, corresponding to A+B sum 96..115 minus 96):
# digit = v % 10 + 48
# carry = 1 if v >= 10 else 0

# Table for carry_in=0: digit at mem[128+96..128+114]=mem[224..242], carry at mem[160+96..160+114]=mem[256..274]
# Table for carry_in=1: digit at mem[128+97..128+115]=mem[225..243], carry at mem[160+97..160+115]=mem[257..275]
# Wait, I need to be more careful. For carry_in=1, the effective sum is A+B+1.
# sum_index from identity = A+B. With carry_in=1, I want the result for (A+B-96+1).
# So I could use mem[128 + sum_index + 1] for carry_in=1...
# That means I need digit table at mem[128+96..128+115] = mem[224..243]
# For carry_in=0: access mem[128 + sum_index]
# For carry_in=1: access mem[128 + sum_index + 1] = mem[129 + sum_index]
# So if I adjust the base by 1 when carry=1!
# carry_offset: 0 for carry=0, 1 for carry=1. That IS the carry value!
# So: E = [A+B] (identity, = A+B), then digit = mem[128 + E + C] where C is carry.
# But 128 + E + C = 128 + sum_index + carry. That's again 3 terms.
#
# Alternative: adjust E. E' = E + C using [E+C] where mem has identity.
# But identity only at 96-115. E+C ranges 96-115. [E+C] = mem[E+C].
# If identity covers 96-115, then [E+C] = E+C. So E' = [E+C]. But wait,
# E+C ranges 96+0=96 to 114+1=115, which IS in range.
# Then digit = mem[128 + E']. Using [E'+128] as [R+I] mode.

# This works! Let me lay it out:
# Step 1: E = [A+B] (using identity table, E = A+B)
# Step 2: E = [E+C] (using identity table, E = A+B+carry, range 96-115)
# Wait, E is currently A+B (96-114). C is carry (0-1). [E+C] reads mem[E+C].
# E+C = 96-115. Identity maps this correctly. So E becomes A+B+carry.
# But step 2 overwrites E with mem[E+C] = E+C. Let me use a different register.
# F = [E+C] → F = E + C = A+B+carry_in

# Step 3: digit = [F+128] → mem[F+128] where F ranges 96-115.
# Address: 96+128=224 to 115+128=243.
# So digit table at mem[224..243].

# Step 4: carry_out = [F+160] → mem[F+160] where F ranges 96-115.
# Address: 96+160=256 to 115+160=275.
# So carry table at mem[256..275].

# This is clean! Let me build these tables.

comment("")
comment("Digit result table: mem[224+v] for v=0..19 (accessed as mem[F+128] where F=96+v)")
for v in range(20):
    digit = v % 10 + 48
    addr = 224 + v
    emit(f"A<{digit}")
    emit(f"[{addr}]<A")

comment("")
comment("Carry out table: mem[256+v] for v=0..19 (accessed as mem[F+160] where F=96+v)")
for v in range(20):
    carry = 1 if v >= 10 else 0
    addr = 256 + v
    emit(f"A<{carry}")
    emit(f"[{addr}]<A")

# Build table for carry offset selection and output suppression
# For the result output: result may be 10 or 11 digits
# If final carry=1, output 11 digits (starting with '1')
# If final carry=0, output 10 digits

# mem[30..40] will hold result: mem[40] = rightmost digit, mem[31] = leftmost of 10 digits
# mem[30] = possible extra '1' if carry

# For output: we need to know if there's a leading digit
# If final carry = 1: output mem[30] ('1') then mem[31..40]
# If final carry = 0: output mem[31..40]

# We can put '0' at mem[30] and if carry=1, change it to '1'.
# Then use O<0 suppression: but '0' is ASCII 48, not 0.
# We need: mem[30] = 0 if no carry (suppress), '1' if carry.
# Use lookup: mem[400+0] = 0, mem[400+1] = 49
# After all additions, C holds final carry.
# Leading digit = mem[400+C]. If 0, suppressed. If 49 ('1'), output.

comment("")
comment("Leading digit lookup: mem[400+carry]")
emit("A<0")
emit("[400]<A")
emit("A<49")
emit("[401]<A")

comment("")
comment("=== Read input ===")
for i in range(21):
    emit(f"A<I")
    emit(f"[{i}]<A")

comment("")
comment("=== Process: add digits right to left ===")
emit("C<0")  # carry = 0

for pos in range(10):
    i = 9 - pos   # first number digit
    j = 20 - pos  # second number digit
    k = 40 - pos  # result position

    comment(f"Pos {pos}: mem[{i}] + mem[{j}] + carry -> mem[{k}]")
    emit(f"A<[{i}]")
    emit(f"B<[{j}]")
    # E = A+B (via identity)
    emit(f"E<[A+B]")
    # F = E+C (via identity, adds carry)
    emit(f"F<[E+C]")
    # digit = mem[F+128]
    emit(f"D<[F+128]")
    emit(f"[{k}]<D")
    # carry_out = mem[F+160]
    emit(f"C<[F+160]")

comment("")
comment("=== Output result ===")
# Leading digit
emit("D<[C+400]")
emit("O<D")

# Output digits 31..40
for k in range(31, 41):
    emit(f"O<[{k}]")

comment("")
emit("Z<1")

# Write to file
with open("/tmp/projdevbench-oj-eval-claude-code-008-20260301143101/code/2281.mv", "w") as f:
    f.write("\n".join(lines) + "\n")

# Count non-comment, non-blank lines
code_lines = [l for l in lines if l and not l.startswith("#")]
print(f"Total lines: {len(lines)}, Code lines: {len(code_lines)}")
