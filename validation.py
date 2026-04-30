#!/usr/bin/env python3

import os
import sys
import time

try:
    import phonenumbers
except ImportError:
    print("[!] Required: pip install phonenumbers")
    sys.exit(1)


def is_valid_mobile(full_10_digit: str) -> tuple:
    """
    Check if +91{number} is a valid mobile number.
    Returns (is_valid: bool, carrier: str|None, location: str|None)
    """
    try:
        parsed = phonenumbers.parse(f"+91{full_10_digit}")
        valid = phonenumbers.is_valid_number(parsed)
        
        if valid:
            # Get carrier info
            from phonenumbers import carrier, geocoder
            carrier_name = carrier.name_for_number(parsed, "en")
            location = geocoder.description_for_number(parsed, "en")
            return True, carrier_name, location
        return False, None, None
    except Exception:
        return False, None, None


def main():
    input_file = "numbergen.txt"
    output_file = "validnumber.txt"
    
    print("=" * 60)
    print("  PHONE NUMBER VALIDATION")
    print("=" * 60)
    print()
    
    # Check input file exists
    if not os.path.exists(input_file):
        print(f"[!] Input file '{input_file}' not found!")
        print(f"    Run number_generator.py first to create it.")
        sys.exit(1)
    
    # Count lines in file
    with open(input_file, 'r') as f:
        total_lines = sum(1 for _ in f)
    
    print(f"[*] Input file: {input_file} ({total_lines:,} numbers)")
    print(f"[*] Validating each number against Indian mobile patterns...")
    print()
    
    start_time = time.time()
    valid_count = 0
    invalid_count = 0
    
    with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
        # Write header
        fout.write("# Number,Carrier,Location\n")
        
        for i, line in enumerate(fin, 1):
            number = line.strip()
            if not number:
                continue
            
            is_valid, carrier_name, location = is_valid_mobile(number)
            
            if is_valid:
                valid_count += 1
                carrier_str = carrier_name if carrier_name else "Unknown"
                location_str = location if location else "India"
                fout.write(f"{number},{carrier_str},{location_str}\n")
            else:
                invalid_count += 1
            
            # Progress every 10,000
            if i % 10000 == 0:
                elapsed = time.time() - start_time
                rate = i / max(elapsed, 0.01)
                print(f"    {i:,}/{total_lines:,} checked ... "
                      f"valid: {valid_count:,} | invalid: {invalid_count:,} "
                      f"| {rate:.0f}/s", end='\r')
        
        print(f"    {total_lines:,}/{total_lines:,} checked ... "
              f"valid: {valid_count:,} | invalid: {invalid_count:,}      ")
    
    elapsed = time.time() - start_time
    print()
    print(f"[+] Validation complete!")
    print(f"    Time: {elapsed:.2f}s")
    print(f"    Total checked: {total_lines:,}")
    print(f"    Valid numbers: {valid_count:,}")
    print(f"    Invalid numbers: {invalid_count:,}")
    print(f"    Valid rate: {valid_count/max(total_lines,1)*100:.1f}%")
    print()
    print(f"[+] Valid numbers saved to: {output_file}")
    print(f"    Format: 10-digit,Carrier,Location")
    print(f"    File size: {os.path.getsize(output_file):,} bytes")
    print()
    print(f"    Next step for owner names:")
    print(f"    - python3 truecaller_lookup.py")
    print(f"    - python3 abstractapi_lookup.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)