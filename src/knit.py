#!/usr/bin/env python3
"""Knitting Compiler - Main entry point."""
import sys
import json

def main():
    if len(sys.argv) < 3 or sys.argv[1] != 'compile':
        print("Usage: python knit.py compile <input_file>", file=sys.stderr)
        sys.exit(1)
    input_file = sys.argv[2]
    try:
        with open(input_file, 'r') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    # Placeholder: parse, validate, simulate, output JSON
    result = {"pattern": "scarf", "rows": []}
    print(json.dumps(result))

if __name__ == '__main__':
    main()
