#!/usr/bin/env python
# Level06 Serial Number Keygen

def calculate_serial(login):
    """Calculate the correct serial number for a given login."""
    
    # Remove newline if present
    login = login.strip()
    
    # Check constraints
    if len(login) <= 5:
        print("Error: Login must be more than 5 characters")
        return None
    
    for c in login:
        if ord(c) <= 31:
            print("Error: All characters must be printable (ASCII > 31)")
            return None
    
    # Calculate serial using the same algorithm as auth()
    v4 = (ord(login[3]) ^ 0x1337) + 6221293
    
    for i in range(len(login)):
        v4 += (v4 ^ ord(login[i])) % 0x539
    
    return v4

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        login = sys.argv[1]
    else:
        login = raw_input("Enter login: ")
    
    serial = calculate_serial(login)
    if serial is not None:
        print("Serial: %d" % serial)

