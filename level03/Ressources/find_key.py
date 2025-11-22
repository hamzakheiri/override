#!/usr/bin/env python3
import struct

# Encrypted string from the binary (little-endian)
encrypted = [
    0x757c7d51,
    0x67667360,
    0x7b66737e,
    0x33617c7d
]

# Convert to bytes (little-endian)
encrypted_bytes = b''
for val in encrypted:
    encrypted_bytes += struct.pack('<I', val)

print(f"Encrypted bytes: {encrypted_bytes.hex()}")
print(f"Encrypted string: {encrypted_bytes}")

# Target string
target = b"Congratulations!"

print(f"\nTarget: {target}")
print(f"Target length: {len(target)}")
print(f"Encrypted length: {len(encrypted_bytes)}")

# Try to find the XOR key
# The key should be a single byte that when XORed with encrypted gives target
for key in range(256):
    decrypted = bytes([b ^ key for b in encrypted_bytes])
    if decrypted == target:
        print(f"\n✅ Found XOR key: {key}")
        print(f"Decrypted: {decrypted}")
        
        # Now calculate the password
        # main() calls test(password, 0x1337d00d)
        # test() calculates: diff = 0x1337d00d - password
        # We need: diff = key (18)
        # So: 0x1337d00d - password = 18
        # Therefore: password = 0x1337d00d - 18
        password = 0x1337d00d - key
        print(f"\n🔑 Password: {password}")
        print(f"   Hex: 0x{password:x}")
        break
else:
    print("\n❌ No key found! Trying partial matches...")
    for key in range(256):
        decrypted = bytes([b ^ key for b in encrypted_bytes])
        if decrypted.startswith(b"Congratulations"):
            print(f"\nPartial match with key {key}: {decrypted}")

