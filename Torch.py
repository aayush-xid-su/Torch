#!/usr/bin/env python3

import itertools
import os
import sys
import time


def parse_user_input(raw: str) -> tuple:
    # Strip everything except digits
    cleaned = ''.join(c for c in raw if c.isdigit())
    
    # If starts with 91 and has more than 2 digits, strip country code
    # But be careful — if someone enters "91" alone, that's no real digits
    if cleaned.startswith('91') and len(cleaned) > 2:
        cleaned = cleaned[2:]
    elif cleaned.startswith('091') and len(cleaned) > 3:
        cleaned = cleaned[3:]
    
    # If starts with 0, strip it
    if cleaned.startswith('0'):
        cleaned = cleaned.lstrip('0')
    
    # If cleaned is now empty or just "91", user gave no real digits
    if not cleaned:
        return "", 0
    
    # If user gave more than 10 digits, truncate to last 10
    if len(cleaned) > 10:
        cleaned = cleaned[-10:]
    
    return cleaned, len(cleaned)


def count_possible_numbers(known_digits: str) -> int:
    """Count how many numbers we need to generate."""
    known = len(known_digits)
    unknown = 10 - known
    
    if unknown <= 0:
        return 1  # Already a complete 10-digit number
    
    # If no known digits, we need to account for first digit being 6/7/8/9
    if known == 0:
        return 4 * (10 ** 9)  # 4,000,000,000 — probably too many!
    
    # If first digit is known, check if it's valid
    first_digit = known_digits[0]
    if first_digit in '6789':
        return 10 ** unknown
    else:
        return 0  # Invalid — Indian mobile must start with 6/7/8/9


def validate_known_digits(known_digits: str) -> str:
    """
    Validate that the known digits can form valid Indian mobile numbers.
    Returns error message or empty string if valid.
    """
    if not known_digits:
        # Empty input — we'll generate ALL, but warn the user
        return ""
    
    first_digit = known_digits[0]
    if first_digit not in '6789':
        return (f"Indian mobile numbers must start with 6, 7, 8, or 9.\n"
                f"    Your input starts with '{first_digit}' which cannot "
                f"be the first digit of an Indian mobile number.")
    
    return ""


def generate_numbers(known_digits: str) -> list:
    """
    Generate all possible 10-digit Indian mobile numbers from known digits.
    
    If known_digits is empty, generate all numbers starting with 6/7/8/9
    (WARNING: this is 4 billion numbers).
    """
    known_len = len(known_digits)
    unknown_count = 10 - known_len
    
    print(f"[*] Known digits: '{known_digits}' ({known_len} digits)")
    print(f"[*] Unknown positions to fill: {unknown_count}")
    print()
    
    numbers = []
    
    if known_len == 0:
        # Generate ALL Indian numbers — first digit must be 6/7/8/9
        print("[!] No known digits — generating ALL Indian mobile numbers!")
        print("    This is 4,000,000,000 (4 billion) combinations.")
        print("    This would take massive storage and time.")
        print()
        
        # For empty input, we actually generate per-first-digit
        for first_digit in ['6', '7', '8', '9']:
            for suffix_tuple in itertools.product('0123456789', repeat=9):
                numbers.append(first_digit + ''.join(suffix_tuple))
        
    elif known_len == 10:
        # Already a complete number
        numbers = [known_digits]
        
    else:
        # Fill remaining positions with all digit combinations
        for suffix_tuple in itertools.product('0123456789', repeat=unknown_count):
            suffix = ''.join(suffix_tuple)
            numbers.append(known_digits + suffix)
    
    return numbers


def generate_numbers_batched(known_digits: str) -> int:
    """
    Generate numbers and write to file in batches to avoid RAM explosion.
    Returns total count of numbers generated.
    """
    output_file = "numbergen.txt"
    known_len = len(known_digits)
    unknown_count = 10 - known_len
    total = count_possible_numbers(known_digits)
    
    if total == 0:
        print("[!] No valid numbers can be generated from this input.")
        print("    Indian mobile numbers must start with 6, 7, 8, or 9.")
        return 0
    
    print(f"[*] Total possible numbers: {total:,}")
    
    # Warn about huge generations
    if total > 1_000_000:
        est_size_gb = (total * 11) / (1024 ** 3)  # 11 bytes per line (10 digits + newline)
        print(f"[!] WARNING: This will generate {total:,} numbers.")
        print(f"    Estimated file size: {est_size_gb:.2f} GB")
        print(f"    This may take significant time and disk space.")
        print()
        
        confirm = input("    Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("[!] Aborted by user.")
            return 0
        print()
    
    print(f"[*] Generating numbers (in batches to save memory)...")
    print()
    
    start_time = time.time()
    count = 0
    
    with open(output_file, 'w') as f:
        if known_len == 0:
            # No known digits — generate per first digit
            for first_digit in ['6', '7', '8', '9']:
                batch = []
                for suffix_tuple in itertools.product('0123456789', repeat=9):
                    number = first_digit + ''.join(suffix_tuple)
                    batch.append(number)
                    count += 1
                    
                    if len(batch) >= 100000:
                        f.write('\n'.join(batch) + '\n')
                        batch = []
                        
                        elapsed = time.time() - start_time
                        rate = count / max(elapsed, 0.01)
                        pct = (count / total) * 100
                        print(f"    Generated {count:,}/{total:,} "
                              f"({pct:.2f}%) | {rate:,.0f}/s", end='\r')
                
                # Write remaining in this first-digit batch
                if batch:
                    f.write('\n'.join(batch) + '\n')
                    
        else:
            # We have some known digits
            batch = []
            for suffix_tuple in itertools.product('0123456789', repeat=unknown_count):
                number = known_digits + ''.join(suffix_tuple)
                batch.append(number)
                count += 1
                
                if len(batch) >= 100000:
                    f.write('\n'.join(batch) + '\n')
                    batch = []
                    
                    elapsed = time.time() - start_time
                    rate = count / max(elapsed, 0.01)
                    pct = (count / total) * 100
                    print(f"    Generated {count:,}/{total:,} "
                          f"({pct:.2f}%) | {rate:,.0f}/s", end='\r')
            
            # Write remaining
            if batch:
                f.write('\n'.join(batch) + '\n')
    
    elapsed = time.time() - start_time
    print(f"\n    Generated {count:,}/{count:,} (100.00%) | Done!")
    print()
    
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    
    print(f"[+] Generation complete!")
    print(f"    Time: {elapsed:.2f}s")
    print(f"    Rate: {count / max(elapsed, 0.01):,.0f} numbers/second")
    print(f"    Total: {count:,} numbers")
    print(f"    File: {output_file}")
    print(f"    Size: {file_size_mb:.2f} MB")
    
    return count


def main():

    
    while True:
        raw = input("Enter incomplete Indian phone number: ").strip()
        
        known_digits, digit_count = parse_user_input(raw)
        error = validate_known_digits(known_digits)
        
        if error:
            print(f"  [!] {error}")
            print()
            continue
        
        total = count_possible_numbers(known_digits)
        
        if total == 0:
            print(f"  [!] No valid Indian mobile numbers possible from this input.")
            print(f"      The first digit must be 6, 7, 8, or 9.")
            print()
            continue
        
        if total > 100_000_000 and digit_count <= 1:
            print()
            print(f"  [!] This will generate {total:,} numbers "
                  f"({total / 1e9:.1f} billion).")
            print(f"  [!] Estimated file size: "
                  f"{total * 11 / (1024**3):.1f} GB")
            print(f"  [!] This is impractical. Please provide more digits.")
            print()
            print(f"  Tip: A 2-digit prefix (like '98') generates "
                  f"10 million numbers (~110 MB)")
            print(f"       A 5-digit prefix generates 100,000 numbers (~1.1 MB)")
            print()
            continue
        
        break
    
    print()
    print(f"[*] Parsed input: {repr(raw)} → known digits: '{known_digits}'")
    print(f"[*] Generating all: {known_digits}[0-9]{{{10 - digit_count}}} "
          f"({total:,} numbers)")
    print()
    
    # Generate!
    generate_numbers_batched(known_digits)
    
    print()
    print(f"    Next step: python3 validation.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)