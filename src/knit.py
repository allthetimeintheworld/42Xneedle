#!/usr/bin/env python3
"""Knitting Compiler - parses .knit files and outputs JSON."""

import json
import re
import sys
from typing import Any, Optional

# --- Constants ---
VALID_KEYWORDS = {'pattern', 'cast_on', 'row', 'repeat', 'bind_off'}
VALID_STITCHES = {'k', 'p', 'yo', 'k2tog', 'ssk', 'inc', 'dec'}

# --- Comment removal ---
def remove_comments(line: str) -> str:
    """Remove comments from a line, respecting quotes."""
    in_quote = False
    for i, ch in enumerate(line):
        if ch == '"':
            in_quote = not in_quote
        elif ch == '#' and not in_quote:
            return line[:i]
    return line

# --- Statement parsing ---
def parse_pattern(line: str) -> Optional[str]:
    m = re.match(r'^pattern\s+"([^"]*)"\s*$', line)
    if m:
        return m.group(1)
    return None

def parse_cast_on(line: str) -> Optional[int]:
    m = re.match(r'^cast_on\s+(\d+)\s*$', line)
    if m:
        return int(m.group(1))
    return None

def parse_row(line: str) -> Optional[tuple[int, str]]:
    m = re.match(r'^row\s+(\d+):\s*(.*?)\s*$', line)
    if m:
        rnum = int(m.group(1))
        instr = m.group(2)
        if instr == '':
            return None
        return (rnum, instr)
    return None

def parse_repeat(line: str) -> Optional[tuple[int, int, int]]:
    m = re.match(r'^repeat\s+rows\s+(\d+)\s*-\s*(\d+)\s+x(\d+)\s*$', line)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None

def parse_bind_off(line: str) -> bool:
    return line.strip() == 'bind_off'

# --- Stitch parsing ---
def parse_stitches(instr: str) -> Optional[list[tuple[str, int]]]:
    """Parse instruction into list of (operation, count). Returns None if invalid."""
    parts = [p.strip() for p in instr.split(',')]
    stitches = []
    for part in parts:
        if not part:
            continue
        m = re.match(r'^([a-z]+)(\d*)$', part)
        if not m:
            return None
        op = m.group(1)
        num_str = m.group(2)
        if op not in VALID_STITCHES:
            return None
        count = int(num_str) if num_str else 1
        stitches.append((op, count))
    return stitches

def stitch_delta(stitches: list[tuple[str, int]]) -> int:
    """Compute net stitch change for a list of stitches."""
    delta = 0
    for op, count in stitches:
        if op in ('k', 'p', 'yo', 'inc'):
            delta += count
        elif op in ('k2tog', 'ssk', 'dec'):
            delta -= count
    return delta

# --- Main compilation ---
def compile_pattern(lines: list[str]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    pattern_name: Optional[str] = None
    cast_on: Optional[int] = None
    has_bind_off = False
    rows: dict[int, str] = {}
    repeats: list[tuple[int, int, int]] = []
    seen_pattern = False
    seen_cast_on = False
    seen_bind_off = False
    
    for line_number, raw_line in enumerate(lines, start=1):
        # Remove comments
        stripped = remove_comments(raw_line.rstrip('\n'))
        trimmed = stripped.strip()
        if not trimmed:
            continue
        
        # Check for keyword boundary: first word must be a keyword
        first_word = trimmed.split()[0] if trimmed.split() else ''
        if first_word not in VALID_KEYWORDS:
            errors.append({
                "type": "error",
                "code": "UNKNOWN_STATEMENT",
                "line": line_number,
                "message": f"Unknown statement: {trimmed}"
            })
            continue
        
        # Pattern
        if first_word == 'pattern':
            if seen_pattern:
                errors.append({
                    "type": "error",
                    "code": "MALFORMED_PATTERN",
                    "line": line_number,
                    "message": "Duplicate pattern statement"
                })
                continue
            seen_pattern = True
            name = parse_pattern(trimmed)
            if name is not None:
                pattern_name = name
            else:
                errors.append({
                    "type": "error",
                    "code": "MALFORMED_PATTERN",
                    "line": line_number,
                    "message": "Malformed pattern statement"
                })
            continue
        
        # Cast on
        if first_word == 'cast_on':
            if seen_cast_on:
                errors.append({
                    "type": "error",
                    "code": "MALFORMED_CAST_ON",
                    "line": line_number,
                    "message": "Duplicate cast_on statement"
                })
                continue
            seen_cast_on = True
            val = parse_cast_on(trimmed)
            if val is not None:
                cast_on = val
            else:
                errors.append({
                    "type": "error",
                    "code": "MALFORMED_CAST_ON",
                    "line": line_number,
                    "message": "Malformed cast_on statement"
                })
            continue
        
        # Row
        if first_word == 'row':
            parsed = parse_row(trimmed)
            if parsed is not None:
                rnum, instr = parsed
                if rnum in rows:
                    errors.append({
                        "type": "error",
                        "code": "MALFORMED_ROW",
                        "line": line_number,
                        "message": f"Duplicate row {rnum}"
                    })
                    continue
                # Validate stitches
                st = parse_stitches(instr)
                if st is None:
                    errors.append({
                        "type": "error",
                        "code": "MALFORMED_ROW",
                        "line": line_number,
                        "message": f"Invalid stitches in row {rnum}: {instr}"
                    })
                    continue
                rows[rnum] = instr
            else:
                errors.append({
                    "type": "error",
                    "code": "MALFORMED_ROW",
                    "line": line_number,
                    "message": "Malformed row statement"
                })
            continue
        
        # Repeat
        if first_word == 'repeat':
            parsed = parse_repeat(trimmed)
            if parsed is not None:
                repeats.append(parsed)
            else:
                errors.append({
                    "type": "error",
                    "code": "MALFORMED_REPEAT",
                    "line": line_number,
                    "message": "Malformed repeat statement"
                })
            continue
        
        # Bind off
        if first_word == 'bind_off':
            if seen_bind_off:
                errors.append({
                    "type": "error",
                    "code": "MALFORMED_BIND_OFF",
                    "line": line_number,
                    "message": "Duplicate bind_off statement"
                })
                continue
            seen_bind_off = True
            if parse_bind_off(trimmed):
                has_bind_off = True
            else:
                errors.append({
                    "type": "error",
                    "code": "MALFORMED_BIND_OFF",
                    "line": line_number,
                    "message": "Malformed bind_off statement"
                })
            continue
        
        # Should not reach here
        errors.append({
            "type": "error",
            "code": "UNKNOWN_STATEMENT",
            "line": line_number,
            "message": f"Unknown statement: {trimmed}"
        })
    
    # Check for missing required statements
    if not seen_pattern:
        errors.append({
            "type": "error",
            "code": "MISSING_PATTERN",
            "line": 0,
            "message": "Missing pattern statement"
        })
    if not seen_cast_on:
        errors.append({
            "type": "error",
            "code": "MISSING_CAST_ON",
            "line": 0,
            "message": "Missing cast_on statement"
        })
    if not seen_bind_off:
        errors.append({
            "type": "error",
            "code": "MISSING_BIND_OFF",
            "line": 0,
            "message": "Missing bind_off statement"
        })
    
    # Expand rows with repeats
    expanded_rows: list[dict[str, Any]] = []
    row_order: list[int] = []
    # Collect all row numbers from explicit rows and repeats
    all_row_nums = set(rows.keys())
    for start, end, times in repeats:
        for r in range(start, end+1):
            all_row_nums.add(r)
    # Build ordered list of row numbers (sorted)
    sorted_rows = sorted(all_row_nums)
    # Process in order, inserting repeats
    i = 0
    while i < len(sorted_rows):
        rnum = sorted_rows[i]
        # Check if this row starts a repeat
        matched_repeat = None
        for start, end, times in repeats:
            if rnum == start:
                matched_repeat = (start, end, times)
                break
        if matched_repeat:
            start, end, times = matched_repeat
            # Add rows from start to end, repeated times
            for _ in range(times):
                for r in range(start, end+1):
                    if r in rows:
                        row_order.append(r)
                    else:
                        # Row not defined, error? Spec says simulation should handle missing rows? We'll add error.
                        errors.append({
                            "type": "error",
                            "code": "MISSING_ROW",
                            "line": 0,
                            "message": f"Row {r} referenced in repeat but not defined"
                        })
            # Skip rows that are part of this repeat
            while i < len(sorted_rows) and sorted_rows[i] <= end:
                i += 1
        else:
            if rnum in rows:
                row_order.append(rnum)
            else:
                errors.append({
                    "type": "error",
                    "code": "MISSING_ROW",
                    "line": 0,
                    "message": f"Row {rnum} not defined"
                })
            i += 1
    
    # Build expanded_rows list
    for rnum in row_order:
        instr = rows.get(rnum, "")
        st = parse_stitches(instr)
        if st is None:
            st = []
        expanded_rows.append({
            "row_number": rnum,
            "instruction": instr,
            "stitches": [{"operation": op, "count": cnt} for op, cnt in st]
        })
    
    # Simulation
    simulation: list[dict[str, Any]] = []
    current_stitches = cast_on if cast_on is not None else 0
    for row_data in expanded_rows:
        st = parse_stitches(row_data["instruction"])
        if st is None:
            st = []
        delta = stitch_delta(st)
        current_stitches += delta
        simulation.append({
            "row_number": row_data["row_number"],
            "stitch_count": current_stitches
        })
    
    # Build output
    output = {
        "pattern_name": pattern_name if pattern_name else "",
        "cast_on": cast_on if cast_on is not None else 0,
        "bind_off": has_bind_off,
        "valid": len(errors) == 0,
        "errors": errors,
        "expanded_rows": expanded_rows,
        "simulation": simulation,
        "final_stitch_count": current_stitches if not has_bind_off else 0
    }
    return output

# --- Main ---
def main():
    if len(sys.argv) != 2:
        print("Usage: knit.py <file.knit>", file=sys.stderr)
        sys.exit(1)
    
    filepath = sys.argv[1]
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(json.dumps({
            "pattern_name": "",
            "cast_on": 0,
            "bind_off": False,
            "valid": False,
            "errors": [{"type": "error", "code": "FILE_NOT_FOUND", "line": 0, "message": f"File not found: {filepath}"}],
            "expanded_rows": [],
            "simulation": [],
            "final_stitch_count": 0
        }, indent=2))
        sys.exit(1)
    
    result = compile_pattern(lines)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
