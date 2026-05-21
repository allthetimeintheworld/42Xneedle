#!/usr/bin/env python3
"""Knitting Compiler CLI."""
import sys
import json
from src.parser import parse
from src.validator import validate
from src.simulator import simulate

def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python knit.py compile <input_file>", file=sys.stderr)
        sys.exit(1)
    input_file = sys.argv[2]
    try:
        with open(input_file, 'r') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    try:
        ast = parse(source)
        errors = validate(ast)
        if errors:
            result = {"status": "error", "errors": errors}
        else:
            simulation = simulate(ast)
            result = {"status": "ok", "simulation": simulation}
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
