# Finding exit@GOT Address Using GDB PEDA

This document explains how to determine the **Global Offset Table (GOT)** address for the `exit()` function using GDB with PEDA, specifically in the context of level05's format string exploitation.

## What is the GOT?

The **Global Offset Table (GOT)** is a section in ELF binaries used for dynamic linking. When a program calls a library function (like `exit()`), it doesn't call the function directly. Instead:

1. The program calls a **PLT (Procedure Linkage Table)** stub
2. The PLT stub jumps to an address stored in the **GOT**
3. The GOT contains the actual address of the library function

By overwriting the GOT entry, we can redirect function calls to arbitrary addresses (like our shellcode).

## Method 1: Using `objdump` (Easiest)

The simplest way to find the GOT address is using `objdump`:

```bash
objdump -R level05 | grep exit
```

**Output:**
```
080497e0 R_386_JUMP_SLOT   exit
```

**Result:** `exit@GOT = 0x080497e0`

This shows that the GOT entry for `exit()` is located at address `0x080497e0`.

## Method 2: Using GDB PEDA Commands

### Step 1: Start GDB with the binary

```bash
gdb level05
```

### Step 2: Use PEDA's `got` command

PEDA provides a convenient command to display all GOT entries:

```bash
gdb-peda$ got
```

**Output:**
```
[0x080497e0] exit@GLIBC_2.0  ->  0x8048376
[0x080497e4] fgets@GLIBC_2.0  ->  0x8048386
[0x080497e8] printf@GLIBC_2.0  ->  0x8048396
...
```

The first column shows the GOT address, and the arrow shows where it currently points (the PLT stub before first call).

**Result:** `exit@GOT = 0x080497e0`

### Step 3: Verify with `x/x` (examine memory)

You can verify the GOT entry by examining it:

```bash
gdb-peda$ x/x 0x080497e0
0x80497e0 <exit@got.plt>:	0x08048376
```

This shows the GOT entry contains `0x08048376` (the PLT stub address).

## Method 3: Manual Disassembly Approach

### Step 1: Disassemble the main function

```bash
gdb-peda$ disas main
```

Look for the `call` to `exit`:

```asm
0x08048513 <+127>:   call   0x8048370 <exit@plt>
```

### Step 2: Disassemble the PLT stub

```bash
gdb-peda$ disas 0x8048370
```

**Output:**
```asm
Dump of assembler code for function exit@plt:
   0x08048370 <+0>:     jmp    *0x80497e0
   0x08048376 <+6>:     push   $0x18
   0x0804837b <+11>:    jmp    0x8048340
```

The `jmp *0x80497e0` instruction shows that the PLT jumps to the address stored at `0x80497e0`.

**Result:** `exit@GOT = 0x80497e0`

## Method 4: Using `readelf`

```bash
readelf -r level05 | grep exit
```

**Output:**
```
080497e0  00000407 R_386_JUMP_SLOT   00000000   exit@GLIBC_2.0
```

**Result:** `exit@GOT = 0x080497e0`

## Understanding the GOT Address Structure

For a 32-bit binary:
- **GOT address:** `0x080497e0` (where the pointer to `exit()` is stored)
- **GOT+2 address:** `0x080497e2` (used for writing the high 2 bytes)

When using format string `%hn` (write 2 bytes), we split the write into two parts:
- Write to `0x080497e0` (low 2 bytes)
- Write to `0x080497e2` (high 2 bytes)

## Practical Example: Verifying GOT Overwrite

After crafting your exploit, you can verify if the GOT was successfully overwritten:

```bash
gdb-peda$ break *main+127    # Break before exit() call
gdb-peda$ run < exploit_payload
gdb-peda$ x/x 0x080497e0
```

**Before exploit:**
```
0x80497e0 <exit@got.plt>:	0x08048376
```

**After successful exploit:**
```
0x80497e0 <exit@got.plt>:	0xffffd87c
```

The GOT now points to your shellcode address instead of the PLT stub!

## Summary

| Method | Command | Difficulty |
|--------|---------|------------|
| objdump | `objdump -R level05 \| grep exit` | ⭐ Easiest |
| PEDA got | `gdb-peda$ got` | ⭐ Easy |
| readelf | `readelf -r level05 \| grep exit` | ⭐ Easy |
| Disassembly | `disas main` → `disas <plt_addr>` | ⭐⭐ Medium |

**Recommended:** Use `objdump -R` or PEDA's `got` command for quick results.

