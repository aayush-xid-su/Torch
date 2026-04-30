#!/usr/bin/env python3

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime

import requests


def read_valid_numbers(filepath: str, limit: int = None) -> list:
    """Read numbers from validnumber.txt."""
    numbers = []
    with open(filepath, 'r') as f:
        for i, line in enumerate(f):
            if i == 0 and line.startswith('#'):
                continue
            parts = line.strip().split(',')
            if parts and parts[0].isdigit() and len(parts[0]) == 10:
                numbers.append(parts[0])
            if limit and len(numbers) >= limit:
                break
    return numbers


def lookup_abstractapi(full_10: str, api_key: str) -> dict:
    """
    Look up a phone number via AbstractAPI Phone Validation API.
    
    API Endpoint: https://phonevalidation.abstractapi.com/v1/
    Response includes: valid, carrier, line_type, location, etc.
    """
    result = {
        "number": full_10,
        "international": f"+91 {full_10[:5]} {full_10[5:]}",
        "valid": None,
        "carrier_name": None,
        "line_type": None,
        "country_name": None,
        "country_code": None,
        "region": None,
        "city": None,
        "timezone": None,
        "line_status": None,
        "is_voip": None,
        "local_format": None,
        "error": None
    }
    
    url = "https://phonevalidation.abstractapi.com/v1/"
    params = {
        "api_key": api_key,
        "phone": f"+91{full_10}",
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            result["valid"] = data.get("valid", False)
            
            # Phone format info
            phone_format = data.get("phone_format", {})
            if phone_format:
                result["local_format"] = phone_format.get("local")
                result["international"] = phone_format.get("international", 
                                                          result["international"])
            
            # Carrier info
            carrier = data.get("phone_carrier", {})
            if carrier:
                result["carrier_name"] = carrier.get("name")
                result["line_type"] = carrier.get("line_type")
            
            # Location info
            location = data.get("phone_location", {})
            if location:
                result["country_name"] = location.get("country_name")
                result["country_code"] = location.get("country_code")
                result["region"] = location.get("region")
                result["city"] = location.get("city")
                result["timezone"] = location.get("timezone")
            
            # Validation info
            validation = data.get("phone_validation", {})
            if validation:
                result["line_status"] = validation.get("line_status")
                result["is_voip"] = validation.get("is_voip")
        
        elif response.status_code == 401:
            result["error"] = "Invalid API key"
        elif response.status_code == 429:
            result["error"] = "Rate limited (check your plan)"
        else:
            result["error"] = f"HTTP {response.status_code}: {response.text[:100]}"
    
    except requests.exceptions.Timeout:
        result["error"] = "timeout"
    except requests.exceptions.ConnectionError:
        result["error"] = "connection_error"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Look up Indian phone numbers using AbstractAPI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 abstractapi_lookup.py YOUR_API_KEY
  python3 abstractapi_lookup.py YOUR_API_KEY --limit 50
  python3 abstractapi_lookup.py YOUR_API_KEY --only-valid -o results/abstract
  python3 abstractapi_lookup.py YOUR_API_KEY --concurrent 3

Get your free API key:
  https://www.abstractapi.com/api/phone-validation-api
  (Free tier: 100 requests/month, no credit card needed)
        """
    )
    parser.add_argument("api_key", help="AbstractAPI Phone Validation API key")
    parser.add_argument("-i", "--input", default="validnumber.txt",
                        help="Input file (default: validnumber.txt)")
    parser.add_argument("-o", "--output", default="abstractapi_results",
                        help="Output base name (default: abstractapi_results)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit how many numbers to process")
    parser.add_argument("--only-valid", action="store_true",
                        help="Only save results where number is valid")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Delay between requests in seconds (default: 0.5)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress progress output")
    
    args = parser.parse_args()
    
    # Read valid numbers
    if not os.path.exists(args.input):
        print(f"[!] Input file '{args.input}' not found!")
        print(f"    Run validation.py first.")
        sys.exit(1)
    
    numbers = read_valid_numbers(args.input, args.limit)
    if not numbers:
        print(f"[!] No numbers found in '{args.input}'")
        sys.exit(1)
    
    print("=" * 60)
    print("  ABSTRACTAPI PHONE LOOKUP")
    print("=" * 60)
    print()
    print(f"[*] Input file: {args.input}")
    print(f"[*] Numbers to process: {len(numbers):,}")
    print(f"[*] API Key: {args.api_key[:5]}...{args.api_key[-4:]}")
    print(f"[*] Delay between requests: {args.delay}s")
    print(f"[*] Only valid output: {args.only_valid}")
    print()
    print(f"[!] Note: Free tier = 100 requests/month.")
    print(f"    Process all {len(numbers):,} numbers? An API plan upgrade may be needed.")
    print()
    
    if not args.quiet:
        confirm = input("Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("[!] Aborted.")
            sys.exit(0)
        print()
    
    # Process
    start_time = time.time()
    results = []
    total = len(numbers)
    
    print(f"[*] Processing {total:,} numbers...")
    print()
    
    for i, number in enumerate(numbers, 1):
        result = lookup_abstractapi(number, args.api_key)
        results.append(result)
        
        if not args.quiet:
            status = "✓" if result.get("valid") else "✗"
            carrier = result.get("carrier_name") or "?"
            location = result.get("city") or result.get("region") or "?"
            elapsed = time.time() - start_time
            rate = i / max(elapsed, 0.01)
            valid_count = sum(1 for r in results if r.get("valid"))
            print(f"    [{i}/{total}] +91 {number[:5]} {number[5:]} "
                  f"| {status} | {carrier} | {location} "
                  f"| {valid_count} valid | {rate:.0f}/s", end='\r')
        
        # Rate limiting delay
        if i < total:
            time.sleep(args.delay)
    
    elapsed = time.time() - start_time
    valid_results = [r for r in results if r.get("valid")]
    invalid_results = [r for r in results if r.get("valid") is False]
    
    print()
    print()
    print(f"[+] Lookup complete!")
    print(f"    Time: {elapsed:.2f}s")
    print(f"    Total processed: {len(results):,}")
    print(f"    Valid: {len(valid_results):,}")
    print(f"    Invalid: {len(invalid_results):,}")
    if results:
        print(f"    Error: {sum(1 for r in results if r.get('error'))}")
    print()
    
    # Filter if only valid
    output_results = valid_results if args.only_valid else results
    output_base = args.output
    
    # Save JSON
    json_file = f"{output_base}.json"
    output_data = {
        "metadata": {
            "total_processed": len(results),
            "valid_count": len(valid_results),
            "invalid_count": len(invalid_results),
            "time_seconds": round(elapsed, 2),
            "rate_per_second": round(len(results) / max(elapsed, 0.01), 2),
            "only_valid": args.only_valid,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source": "AbstractAPI Phone Validation API"
        },
        "results": output_results
    }
    with open(json_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str, ensure_ascii=False)
    
    # Save CSV
    csv_file = f"{output_base}.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Number", "International", "Valid", "Carrier", "Line Type",
            "Country", "Region", "City", "Timezone", "Line Status", "Is VoIP"
        ])
        for r in output_results:
            writer.writerow([
                r["number"],
                r["international"],
                r.get("valid", ""),
                r.get("carrier_name", ""),
                r.get("line_type", ""),
                r.get("country_name", ""),
                r.get("region", ""),
                r.get("city", ""),
                r.get("timezone", ""),
                r.get("line_status", ""),
                r.get("is_voip", "")
            ])
    
    print(f"[+] Results saved:")
    print(f"    JSON: {json_file}")
    print(f"    CSV:  {csv_file}")
    
    if valid_results:
        print()
        print(f"    Sample results:")
        for r in valid_results[:5]:
            carrier = r.get("carrier_name") or "?"
            city = r.get("city") or r.get("region") or "?"
            print(f"      {r['international']} -> {carrier} ({city})")
        if len(valid_results) > 5:
            print(f"      ... and {len(valid_results)-5} more")
        print()
        print(f"    All {len(valid_results):,} valid numbers with details saved.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)