# Level03 - XOR Cipher and Random Number Confusion

## The Question: Does Our Password Depend on Time?

**Short Answer: NO!** The password is always **322424827**, regardless of when you run the program.

## Understanding the Confusion

When you look at the code, you see:

```c
srand(time(NULL));  // Seeds random number generator with current time
```

This makes it look like the password might change based on time. But let's trace through the execution to understand why it doesn't matter.

## Complete Program Flow

### Step 1: Main Function Setup

```c
int main(void)
{
    int password;
    
    srand(time(NULL));  // ← Seeds RNG with current timestamp
    
    // Display banner
    puts("***********************************");
    puts("*\t\tlevel03\t\t**");
    puts("***********************************");
    
    printf("Password:");
    scanf("%d", &password);  // ← We enter 322424827
    
    test(password, 0x1337d00d);  // ← Calls test with our input
    
    return 0;
}
```

**Key Point:** `srand()` is called, but `rand()` is **NOT** called in `main()`.

### Step 2: Test Function Logic

```c
int test(int password, int magic)
{
    int diff;
    
    diff = magic - password;  // 0x1337d00d - 322424827 = 18
    
    switch (diff)
    {
        case 1:  decrypt(1);  break;
        case 2:  decrypt(2);  break;
        ...
        case 18: decrypt(18); break;  // ← We hit this case!
        ...
        case 21: decrypt(21); break;
        default: decrypt(rand()); break;  // ← We NEVER reach this!
    }
    
    return 0;
}
```

**Key Point:** When we enter password `322424827`:
- `diff = 0x1337d00d - 322424827 = 18`
- We hit `case 18:` in the switch statement
- We call `decrypt(18)` directly
- We **NEVER** reach the `default:` case that calls `rand()`

### Step 3: Decrypt Function

```c
int decrypt(int xor_key)  // xor_key = 18
{
    char buffer[17];
    char encrypted[] = "Q}|u`sfg~sf{}|a3";
    
    // XOR each byte with key 18
    for (int i = 0; i < 16; i++)
    {
        buffer[i] = encrypted[i] ^ 18;
    }
    buffer[16] = '\0';
    
    // buffer now contains "Congratulations!"
    
    if (strcmp(buffer, "Congratulations!") == 0)
    {
        system("/bin/sh");  // ← Success! Shell spawned
    }
    else
    {
        puts("\nInvalid Password");
    }
}
```

**Key Point:** The XOR key is **18** (hardcoded by our password choice), not random.

## When Does `rand()` Matter?

The `rand()` function is **ONLY** called in the `default:` case of the switch statement:

```c
default: decrypt(rand()); break;
```

This happens when `diff` is **NOT** one of the valid cases (1-9, 16-21).

### Example: Wrong Password

Let's say we enter password `123456`:

```c
diff = 0x1337d00d - 123456 = 322301389
```

This doesn't match any case (1-9, 16-21), so we hit the `default:` case:

```c
default: decrypt(rand()); break;
```

Now `rand()` is called, and it returns a pseudo-random number based on the seed from `srand(time(NULL))`.

**But this doesn't help us!** Because:
1. The random number is unpredictable
2. It's extremely unlikely to be 18 (the correct XOR key)
3. The decryption will fail and print "Invalid Password"

## Why `srand(time(NULL))` is a Red Herring

The developers added `srand(time(NULL))` to make the program **harder to brute force** with wrong passwords:

### Without `srand(time(NULL))`:
```c
srand(0);  // Default seed
```

If you enter a wrong password multiple times, `rand()` would return the **same** sequence of numbers each time. You could potentially:
1. Run the program many times with wrong passwords
2. Eventually, `rand()` might return 18 by chance
3. You'd get lucky and spawn a shell

### With `srand(time(NULL))`:
```c
srand(time(NULL));  // Seed changes every second
```

Each time you run the program, `rand()` returns a **different** sequence. This makes it nearly impossible to get lucky with a wrong password.

## The Correct Solution Path

Our solution **completely bypasses** the random number generator:

```
1. We analyze the encrypted string in the binary
   ↓
2. We perform known-plaintext attack on XOR cipher
   ↓
3. We find XOR key = 18
   ↓
4. We calculate: password = 0x1337d00d - 18 = 322424827
   ↓
5. We enter 322424827
   ↓
6. diff = 18 → hits case 18 → calls decrypt(18)
   ↓
7. decrypt(18) XORs encrypted string with 18
   ↓
8. Result = "Congratulations!" → spawns shell
```

**At no point do we use `rand()`!**

## Visual Diagram

```
                    ┌─────────────────────────────────────┐
                    │  main()                             │
                    │  srand(time(NULL))  ← Seeds RNG     │
                    │  scanf("%d", &password)             │
                    └──────────────┬──────────────────────┘
                                   │
                                   │ password = 322424827
                                   ↓
                    ┌─────────────────────────────────────┐
                    │  test(322424827, 0x1337d00d)        │
                    │  diff = 0x1337d00d - 322424827      │
                    │  diff = 18                          │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────┴──────────────────────┐
                    │  switch (diff)                      │
                    │    case 1:  decrypt(1)              │
                    │    case 2:  decrypt(2)              │
                    │    ...                              │
                    │    case 18: decrypt(18)  ← WE HIT THIS!
                    │    ...                              │
                    │    default: decrypt(rand()) ← NEVER REACHED
                    └──────────────┬──────────────────────┘
                                   │
                                   │ xor_key = 18
                                   ↓
                    ┌─────────────────────────────────────┐
                    │  decrypt(18)                        │
                    │  "Q}|u`sfg~sf{}|a3" ^ 18            │
                    │  = "Congratulations!"               │
                    │  → system("/bin/sh")                │
                    └─────────────────────────────────────┘
```

## Summary

| Question | Answer |
|----------|--------|
| Does the password depend on time? | **NO** |
| Is `srand(time(NULL))` used in our solution? | **NO** |
| When is `rand()` called? | Only when entering **wrong** passwords |
| Why is `srand()` there? | To make brute-forcing with wrong passwords harder |
| What is the password? | **322424827** (always the same) |
| Why does it work? | Because `diff = 18` hits `case 18:` which calls `decrypt(18)` |

## Key Takeaway

The `srand(time(NULL))` is a **defensive mechanism** against brute force attacks with wrong passwords. But our solution uses **cryptanalysis** (breaking the XOR cipher) to find the correct password directly, completely bypassing the need for random numbers.

This is a great example of how understanding the **logic** of a program is more powerful than trying to brute force it!

## Bonus: Understanding XOR Cipher

### What is XOR?

XOR (exclusive OR) is a bitwise operation:

```
0 ^ 0 = 0
0 ^ 1 = 1
1 ^ 0 = 1
1 ^ 1 = 0
```

**Key property:** `A ^ B ^ B = A` (XORing twice with the same value returns the original)

### How XOR Encryption Works

```
Plaintext:  "C"           = 0x43 = 01000011
XOR Key:    18            = 0x12 = 00010010
            ─────────────────────────────────
Ciphertext: "Q"           = 0x51 = 01010001
```

### How XOR Decryption Works (Same Operation!)

```
Ciphertext: "Q"           = 0x51 = 01010001
XOR Key:    18            = 0x12 = 00010010
            ─────────────────────────────────
Plaintext:  "C"           = 0x43 = 01000011
```

### Known Plaintext Attack

If we know both plaintext and ciphertext, we can find the key:

```
Ciphertext: "Q"           = 0x51 = 01010001
Plaintext:  "C"           = 0x43 = 01000011
            ─────────────────────────────────
Key:        18            = 0x12 = 00010010
```

This is exactly what we did in level03!

### Why Single-Byte XOR is Weak

1. **Only 256 possible keys** (0-255) - trivial to brute force
2. **Known plaintext attack** - if you know any plaintext/ciphertext pair, you can find the key
3. **Frequency analysis** - letter frequencies are preserved (just shifted)
4. **No diffusion** - each byte is encrypted independently

### Proper Encryption

Modern encryption uses:
- **AES**: 128/192/256-bit keys, complex substitution-permutation network
- **ChaCha20**: Stream cipher with 256-bit key
- **Proper key derivation**: PBKDF2, Argon2, etc.
- **Authentication**: HMAC, GCM mode, etc.

Never use single-byte XOR for real encryption!

