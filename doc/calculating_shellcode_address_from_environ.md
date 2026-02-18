# Calculating Shellcode Address from Environment Variables

This document explains how to determine the exact address of your shellcode in memory when it's stored in an environment variable, specifically how to get from the `environ` output to the actual shellcode address like `0xffffd87c`.

## The Problem

When you store shellcode in an environment variable:

```bash
export SHELLCODE=`python -c 'print "\x90"*100 + "<actual_shellcode>"'`
```

You need to find the **exact memory address** where the shellcode (specifically the NOP sled) starts, so you can redirect execution to it.

## Example Output from GDB

When you examine environment variables in GDB:

```bash
gdb-peda$ x/200s environ
```

You might see:

```
0xffffd820: "SHELLCODE=\220\220\220\220\220\220...\061\300\061\333..."
```

**Question:** How do we get from `0xffffd820` to `0xffffd87c`?

## Understanding the Structure

The environment variable string has this structure:

```
[Address]     [Content]
0xffffd820 -> "SHELLCODE="     (10 bytes: S H E L L C O D E = \0)
0xffffd82a -> "\x90\x90..."    (NOP sled starts here)
```

## Step-by-Step Calculation

### Step 1: Identify the Base Address

From the GDB output:
```
0xffffd820: "SHELLCODE=..."
```

**Base address = `0xffffd820`**

This is where the string `"SHELLCODE="` starts.

### Step 2: Calculate the Offset

The environment variable format is: `VARIABLE_NAME=VALUE`

For `SHELLCODE=`, we need to skip:
- `S` `H` `E` `L` `L` `C` `O` `D` `E` `=` = **10 bytes**

So the NOP sled starts at:
```
0xffffd820 + 10 (0xa) = 0xffffd82a
```

### Step 3: Why Not 0xffffd82a?

You might wonder: if the NOP sled starts at `0xffffd82a`, why do we use `0xffffd87c`?

**Answer:** We jump into the **middle of the NOP sled** for safety!

```
0xffffd82a ─┐
            │ NOP sled (100 bytes of \x90)
            │ \x90 \x90 \x90 \x90 ...
0xffffd87c ─┤ ← We jump here (middle of NOPs)
            │ \x90 \x90 \x90 ...
0xffffd88e ─┘
0xffffd88e    Actual shellcode starts
```

**Calculation:**
```
NOP sled start:  0xffffd82a
Jump target:     0xffffd87c
Offset:          0xffffd87c - 0xffffd82a = 0x52 (82 bytes into NOP sled)
```

## Method 1: Manual Calculation in GDB

### Step 1: Find the environment variable

```bash
gdb-peda$ break main
gdb-peda$ run
gdb-peda$ x/200s environ
```

Look for your `SHELLCODE=` string and note the address (e.g., `0xffffd820`).

### Step 2: Calculate the NOP sled start

```bash
gdb-peda$ p/x 0xffffd820 + 10
$1 = 0xffffd82a
```

### Step 3: Examine the memory to verify

```bash
gdb-peda$ x/40xb 0xffffd820
```

**Output:**
```
0xffffd820:  0x53  0x48  0x45  0x4c  0x4c  0x43  0x4f  0x44  # "SHELLCOD"
0xffffd828:  0x45  0x3d  0x90  0x90  0x90  0x90  0x90  0x90  # "E=" then NOPs
0xffffd830:  0x90  0x90  0x90  0x90  0x90  0x90  0x90  0x90  # More NOPs
```

You can see:
- `0xffffd820-0xffffd829`: `"SHELLCODE="`
- `0xffffd82a`: First `\x90` (NOP)

### Step 4: Choose a safe address in the NOP sled

Pick an address in the middle of the NOP sled:

```bash
gdb-peda$ p/x 0xffffd82a + 82
$2 = 0xffffd87c
```

### Step 5: Verify it's still in the NOP sled

```bash
gdb-peda$ x/20xb 0xffffd87c
```

**Output:**
```
0xffffd87c:  0x90  0x90  0x90  0x90  0x90  0x90  0x90  0x90
0xffffd884:  0x90  0x90  0x90  0x90  0x31  0xc0  0x31  0xdb
```

✅ Still in NOPs, good! The actual shellcode (`\x31\xc0...`) starts a bit later.

## Method 2: Using GDB's `find` Command

### Step 1: Search for the environment variable

```bash
gdb-peda$ break main
gdb-peda$ run
gdb-peda$ find &environ, +99999, "SHELLCODE"
```

**Output:**
```
0xffffd820
1 pattern found.
```

### Step 2: Calculate NOP sled address

```bash
gdb-peda$ p/x 0xffffd820 + 10
$1 = 0xffffd82a
```

### Step 3: Add offset into NOP sled

```bash
gdb-peda$ p/x 0xffffd82a + 82
$2 = 0xffffd87c
```

## Method 3: Using `getenv` in GDB

### Step 1: Get the environment variable address directly

```bash
gdb-peda$ break main
gdb-peda$ run
gdb-peda$ call (char*)getenv("SHELLCODE")
```

**Output:**
```
$1 = 0xffffd82a "SHELLCODE=\220\220\220..."
```

**Wait!** This gives you the address of the **value** (after the `=`), not the variable name!

Actually, `getenv()` returns the address **after** `SHELLCODE=`, so:

```bash
gdb-peda$ call (char*)getenv("SHELLCODE")
$1 = 0xffffd82a
```

This is already pointing to the start of the NOP sled! Now just add your offset:

```bash
gdb-peda$ p/x 0xffffd82a + 82
$2 = 0xffffd87c
```

## Why Jump into the Middle of the NOP Sled?

The NOP sled is 100 bytes of `\x90` (NOP instruction). Jumping anywhere in this sled will "slide" down to the actual shellcode.

**Benefits:**
1. **Tolerance for address variations** - The address might be slightly different outside GDB
2. **ASLR mitigation** - Even with slight randomization, you'll likely hit the sled
3. **Safety margin** - Ensures you don't accidentally jump before or after the sled

## Address Differences: GDB vs Real Execution

⚠️ **Important:** The address in GDB might differ from real execution!

**Reasons:**
- GDB adds its own environment variables
- Different stack alignment
- Different program name length

**Typical difference:** ±20 to ±100 bytes

**Solution:** Use a large NOP sled (100+ bytes) and jump to the middle.

## Practical Example: Complete Calculation

Given GDB output:
```
0xffffd820: "SHELLCODE=\220\220\220..."
```

**Step-by-step:**

1. Base address: `0xffffd820`
2. Skip "SHELLCODE=": `0xffffd820 + 10 = 0xffffd82a`
3. Jump to middle of 100-byte NOP sled: `0xffffd82a + 82 = 0xffffd87c`

**Verification in GDB:**

```bash
gdb-peda$ x/s 0xffffd820
0xffffd820: "SHELLCODE=..."

gdb-peda$ x/20xb 0xffffd87c
0xffffd87c:  0x90  0x90  0x90  0x90  0x90  0x90  0x90  0x90
```

✅ **Result:** Use `0xffffd87c` as your shellcode address in the exploit!

## Quick Reference

| Step | Command | Result |
|------|---------|--------|
| Find SHELLCODE in environ | `x/200s environ` | `0xffffd820: "SHELLCODE=..."` |
| Calculate NOP start | `p/x 0xffffd820 + 10` | `0xffffd82a` |
| Calculate jump target | `p/x 0xffffd82a + 82` | `0xffffd87c` |
| Verify NOPs | `x/20xb 0xffffd87c` | Should show `0x90` bytes |

## Summary

**Formula:**
```
shellcode_address = environ_base + strlen("SHELLCODE=") + offset_into_nop_sled
                  = 0xffffd820  + 10                   + 82
                  = 0xffffd87c
```

The offset into the NOP sled (82 bytes in this example) is chosen to be roughly in the middle of the 100-byte NOP sled for maximum reliability.

