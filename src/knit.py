#!/usr/bin/env python3
import sys
import json
from parser import parse
from validator import validate
from simulator import simulate

def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python knit.py compile <input_file>", file=sys.stderr)
        sys.exit(1)
    input_file = sys.argv[2]
    try:
        with open(input_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: file '{input_file}' not found", file=sys.stderr)
        sys.exit(1)
    try:
        pattern = parse(content)
        errors = validate(pattern)
        if errors:
            result = {"status": "error", "errors": errors}
        else:
            simulation = simulate(pattern)
            result = {"status": "ok", "pattern": pattern, "simulation": simulation}
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
