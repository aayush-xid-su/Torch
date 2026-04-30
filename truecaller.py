#!/usr/bin/env python3
"""
Script 3: Truecaller Name Lookup
=================================
Reads valid numbers from validnumber.txt and looks up the owner name
and other details using the Truecaller API (truecallerpy).

Requirements:
    pip install truecallerpy

Getting your Truecaller Installation ID:
    1. pip install truecallerpy
    2. truecallerpy login          # Enter +91XXXXXXXXXX when prompted
    3. Enter the OTP you receive
    4. truecallerpy -i -r          # Prints your Installation ID

Usage:
    python3 truecaller_lookup.py YOUR_INSTALLATION_ID
    python3 truecaller_lookup.py a1k07--Vgdfyvv_... --concurrency 10
    python3 truecaller_lookup.py a1k07--Vgdfyvv_... --limit 500
"""

import argparse
import asyncio
import csv
import json
import os
import sys
import time
from datetime import datetime

try:
    from truecallerpy import search_phonenumber
except ImportError:
    print("[!] Required: pip install truecallerpy")
    sys.exit(1)


def read_valid_numbers(filepath: str, limit: int = None) -> list:
    """Read numbers from validnumber.txt."""
    numbers = []
    with open(filepath, 'r') as f:
        for i, line in enumerate(f):
            if i == 0 and line.startswith('#'):
                continue  # Skip header
            parts = line.strip().split(',')
            if parts and parts[0].isdigit() and len(parts[0]) == 10:
                numbers.append(parts[0])
            if limit and len(numbers) >= limit:
                break
    return numbers


async def lookup_tc_name(full_10: str, install_id: str, 
                          timeout: int = 15) -> dict:
    """
    Search Truecaller for a phone number.
    Returns dict with all available info.
    """
    result = {
        "number": full_10,
        "international": f"+91 {full_10[:5]} {full_10[5:]}",
        "name": None,
        "alternate_name": None,
        "carrier": None,
        "city": None,
        "spam_score": None,
        "found": False,
        "error": None
    }
    
    try:
        response = await asyncio.wait_for(
            search_phonenumber(f"+91{full_10}", "IN", install_id),
            timeout=timeout
        )
        
        if response and isinstance(response, dict):
            data = response.get("data", [])
            if data and isinstance(data, list) and len(data) > 0:
                entry = data[0]
                name = entry.get("name")
                if name:
                    result["name"] = name
                    result["found"] = True
                
                result["carrier"] = entry.get("carrier")
                result["spam_score"] = entry.get("spamScore")
                result["alternate_name"] = entry.get("alternateName")
                result["phone_type"] = entry.get("phoneType")
                
                email = entry.get("emailId")
                if email:
                    result["email"] = email
                
                city = entry.get("city")
                if city:
                    result["city"] = city
                    
                addresses = entry.get("addresses")
                if addresses:
                    result["addresses"] = addresses
    
    except asyncio.TimeoutError:
        result["error"] = "timeout"
    except Exception as e:
        result["error"] = str(e)
    
    return result


async def process_all(numbers: list, install_id: str,
                      concurrency: int = 5, quiet: bool = False) -> list:
    """Process all numbers through Truecaller with concurrency control."""
    semaphore = asyncio.Semaphore(concurrency)
    results = []
    total = len(numbers)
    start_time = time.time()
    
    async def lookup_one(num):
        async with semaphore:
            return await lookup_tc_name(num, install_id)
    
    batch_size = concurrency * 5
    
    for i in range(0, total, batch_size):
        batch = numbers[i:i + batch_size]
        tasks = [lookup_one(num) for num in batch]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
        
        if not quiet:
            pct = min(100, (i + len(batch)) / total * 100)
            elapsed = time.time() - start_time
            rate = (i + len(batch)) / max(elapsed, 0.01)
            found = sum(1 for r in results if r.get("found"))
            print(f"    [{int(pct)}%] {i+len(batch)}/{total} "
                  f"| {rate:.1f}/s | names found: {found}", end='\r')
        
        if i + batch_size < total:
            await asyncio.sleep(0.3)
    
    return results


def save_results(results: list, output_base: str, only_named: bool):
    """Save results to JSON and CSV files."""
    # Filter if only named
    if only_named:
        results = [r for r in results if r.get("found")]
    
    # JSON output
    json_file = f"{output_base}.json"
    output_data = {
        "metadata": {
            "total_processed": len(results),
            "names_found": sum(1 for r in results if r.get("found")),
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source": "Truecaller API (truecallerpy)"
        },
        "results": results
    }
    with open(json_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str, ensure_ascii=False)
    
    # CSV output
    csv_file = f"{output_base}.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Number", "International", "Name", "Alternate Name",
                         "Carrier", "City", "Spam Score", "Found", "Error"])
        for r in results:
            writer.writerow([
                r["number"],
                r["international"],
                r.get("name", ""),
                r.get("alternate_name", ""),
                r.get("carrier", ""),
                r.get("city", ""),
                r.get("spam_score", ""),
                r["found"],
                r.get("error", "")
            ])
    
    return json_file, csv_file


async def main_async(args):
    """Async main."""
    # Read valid numbers
    if not os.path.exists(args.input):
        print(f"[!] Input file '{args.input}' not found!")
        print(f"    Run validation.py first.")
        sys.exit(1)
    
    numbers = read_valid_numbers(args.input, args.limit)
    if not numbers:
        print(f"[!] No valid numbers found in '{args.input}'")
        sys.exit(1)
    
    print("=" * 60)
    print("  TRUECALLER OWNER NAME LOOKUP")
    print("=" * 60)
    print()
    print(f"[*] Input file: {args.input}")
    print(f"[*] Numbers to lookup: {len(numbers):,}")
    print(f"[*] Concurrency: {args.concurrency}")
    print(f"[*] Installation ID: {args.installation_id[:15]}...")
    print()
    
    # Process
    all_results = await process_all(numbers, args.installation_id,
                                     args.concurrency, args.quiet)
    
    named = [r for r in all_results if r.get("found")]
    elapsed = time.time() - args._start_time
    
    print()
    print(f"[+] Lookup complete!")
    print(f"    Time: {elapsed:.2f}s")
    print(f"    Processed: {len(all_results):,}")
    print(f"    Names found: {len(named):,}")
    if all_results:
        print(f"    Hit rate: {len(named)/len(all_results)*100:.1f}%")
    print()
    
    # Save
    output_base = args.output
    json_file, csv_file = save_results(all_results, output_base, args.only_named)
    
    print(f"[+] Results saved:")
    print(f"    JSON: {json_file}")
    print(f"    CSV:  {csv_file}")
    print()
    
    # Show sample
    if named:
        print(f"    Sample results:")
        for r in named[:5]:
            name = r.get("name", "?")
            carrier = r.get("carrier") or "?"
            print(f"      {r['international']} -> {name} [{carrier}]")
        if len(named) > 5:
            print(f"      ... and {len(named)-5} more")


def main():
    parser = argparse.ArgumentParser(
        description="Look up Indian phone numbers using Truecaller API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 truecaller_lookup.py a1k07--Vgdfyvv_...
  python3 truecaller_lookup.py a1k07--Vgdfyvv_... --concurrency 10
  python3 truecaller_lookup.py a1k07--Vgdfyvv_... --limit 500 --only-named
  python3 truecaller_lookup.py a1k07--Vgdfyvv_... -o results/tc_output

Getting your Installation ID:
  1. pip install truecallerpy
  2. truecallerpy login
  3. Enter +91XXXXXXXXXX
  4. Enter OTP
  5. truecallerpy -i -r
        """
    )
    parser.add_argument("installation_id", help="Truecaller Installation ID")
    parser.add_argument("-i", "--input", default="validnumber.txt",
                        help="Input file (default: validnumber.txt)")
    parser.add_argument("-o", "--output", default="truecaller_results",
                        help="Output base name (default: truecaller_results)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit how many numbers to process")
    parser.add_argument("--only-named", action="store_true",
                        help="Only save results where name was found")
    parser.add_argument("--concurrency", type=int, default=5,
                        help="Concurrent requests (default: 5)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress progress output")
    
    args = parser.parse_args()
    args._start_time = time.time()
    
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()