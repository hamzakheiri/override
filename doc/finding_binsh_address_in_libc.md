# Finding /bin/sh Address in libc Using GDB PEDA

This document explains the correct methods to find the address of the `/bin/sh` string in libc for ret2libc exploits.

## The Problem with `find system,+9999999,"/bin/sh"`

The command `find system,+9999999,"/bin/sh"` has issues:

1. **`system` is a symbol, not an address** - You need to use the actual address
2. **The search range might not include the string** - `/bin/sh` might be in a different part of libc
3. **Syntax might be incorrect** - Depending on GDB version

## Method 1: Using PEDA's `find` Command (Correct Syntax)

### Step 1: Find the libc base address

```bash
gdb-peda$ break main
gdb-peda$ run
gdb-peda$ vmmap
```

**Output:**
```
Start      End        Perm	Name
0x08048000 0x08049000 r-xp	/home/users/level07/level07
0xf7e2b000 0xf7fcc000 r-xp	/lib32/libc-2.15.so
0xf7fcc000 0xf7fcd000 r--p	/lib32/libc-2.15.so
0xf7fcd000 0xf7fcf000 rw-p	/lib32/libc-2.15.so
```

**libc base address: `0xf7e2b000`**
**libc end address: `0xf7fcc000`**

### Step 2: Search for "/bin/sh" in libc

```bash
gdb-peda$ find "/bin/sh"
```

**Output:**
```
Searching for '/bin/sh' in: None ranges
Found 1 results, display max 1 items:
libc : 0xf7f897ec --> 0x6e69622f ('/bin')
```

**Result: `/bin/sh` is at `0xf7f897ec`**

### Alternative: Specify the search range explicitly

```bash
gdb-peda$ find 0xf7e2b000, 0xf7fcc000, "/bin/sh"
```

**Output:**
```
Searching for '/bin/sh' in range: 0xf7e2b000 - 0xf7fcc000
Found 1 results, display max 1 items:
0xf7f897ec --> 0x6e69622f ('/bin')
```

## Method 2: Using Standard GDB `find` Command

```bash
gdb-peda$ break main
gdb-peda$ run

# Find libc range first
gdb-peda$ info proc mappings
# Or use: shell cat /proc/$(pidof level07)/maps

# Search in libc memory range
gdb-peda$ find 0xf7e2b000, 0xf7fcc000, "/bin/sh"
```

## Method 3: Using `searchmem` (PEDA Command)

```bash
gdb-peda$ searchmem "/bin/sh"
```

**Output:**
```
Searching for '/bin/sh' in: None ranges
Found 1 results, display max 1 items:
libc : 0xf7f897ec --> 0x6e69622f ('/bin')
```

## Method 4: Using `strings` and `grep` (Outside GDB)

### Step 1: Find which libc is being used

```bash
ldd level07
```

**Output:**
```
linux-gate.so.1 =>  (0xf7fde000)
libc.so.6 => /lib32/libc.so.6 (0xf7e2b000)
/lib/ld-linux.so.2 (0xf7fdf000)
```

### Step 2: Find the offset of "/bin/sh" in libc

```bash
strings -a -t x /lib32/libc.so.6 | grep "/bin/sh"
```

**Output:**
```
 15e7ec /bin/sh
```

**Offset: `0x15e7ec`**

### Step 3: Calculate the actual address

```
libc_base + offset = actual_address
0xf7e2b000 + 0x15e7ec = 0xf7f897ec
```

**Result: `/bin/sh` is at `0xf7f897ec`**

## Method 5: Using `info proc mappings` and Manual Search

```bash
gdb-peda$ break main
gdb-peda$ run
gdb-peda$ info proc mappings
```

Find the libc mapping, then:

```bash
gdb-peda$ x/s 0xf7f897ec
0xf7f897ec:	"/bin/sh"
```

If you don't know the address yet, you can search:

```bash
# Search starting from libc base
gdb-peda$ find 0xf7e2b000, +0x1a1000, "/bin/sh"
```

## Method 6: Using PEDA's `libc` Command

Some PEDA versions have a `libc` command:

```bash
gdb-peda$ libc
```

This might show useful libc information and common gadget addresses.

## Why Your Command Doesn't Work

```bash
find system,+9999999,"/bin/sh"
```

**Problems:**

1. **`system` is a symbol, not an address**
   - GDB might interpret this as the function symbol
   - You need: `find &system, +9999999, "/bin/sh"`
   - Or better: use the actual address

2. **`/bin/sh` might not be near `system()`**
   - `system()` is in the `.text` section (code)
   - `/bin/sh` is usually in the `.rodata` section (read-only data)
   - They might be far apart in memory

3. **The range might be wrong**
   - `+9999999` is about 9.5 MB
   - libc is typically 1-2 MB
   - The string might be outside this range

## Correct Command Using system Address

If you really want to search from `system`:

```bash
# First, get system address
gdb-peda$ p system
$1 = {<text variable, no debug info>} 0xf7e6aed0 <system>

# Then search (but this is not recommended)
gdb-peda$ find 0xf7e6aed0, 0xf7fcc000, "/bin/sh"
```

**Better approach:** Just search the entire libc range or use `find "/bin/sh"` without range.

## Verification

After finding the address, verify it:

```bash
gdb-peda$ x/s 0xf7f897ec
0xf7f897ec:	"/bin/sh"
```

✅ **Confirmed!**

## Complete Example for Level07

```bash
gdb level07
gdb-peda$ break main
gdb-peda$ run

# Find system address
gdb-peda$ p system
$1 = {<text variable, no debug info>} 0xf7e6aed0 <system>

# Find /bin/sh address
gdb-peda$ find "/bin/sh"
Searching for '/bin/sh' in: None ranges
Found 1 results, display max 1 items:
libc : 0xf7f897ec --> 0x6e69622f ('/bin')

# Verify
gdb-peda$ x/s 0xf7f897ec
0xf7f897ec:	"/bin/sh"

# Convert to decimal for the exploit
gdb-peda$ p/d 0xf7e6aed0
$2 = 4159090384  # system address

gdb-peda$ p/d 0xf7f897ec
$3 = 4160264172  # /bin/sh address
```

## Summary: Recommended Methods

| Method | Command | Difficulty | Reliability |
|--------|---------|------------|-------------|
| PEDA find | `find "/bin/sh"` | ⭐ Easiest | ⭐⭐⭐ Best |
| PEDA searchmem | `searchmem "/bin/sh"` | ⭐ Easy | ⭐⭐⭐ Best |
| strings + offset | `strings -t x /lib32/libc.so.6 \| grep "/bin/sh"` | ⭐⭐ Medium | ⭐⭐⭐ Best |
| Manual range search | `find 0xf7e2b000, 0xf7fcc000, "/bin/sh"` | ⭐⭐ Medium | ⭐⭐⭐ Good |

**Recommended:** Use `find "/bin/sh"` or `searchmem "/bin/sh"` in PEDA - it's the simplest and most reliable!

## Common Mistakes to Avoid

❌ `find system,+9999999,"/bin/sh"` - Wrong syntax, wrong range
❌ `find "/bin/bash"` - Wrong string (it's `/bin/sh`, not `/bin/bash`)
❌ Searching without running the program first - libc not loaded yet
✅ `find "/bin/sh"` - Correct and simple!

