#!/usr/bin/env python3
import sys
import json
import re

# Stitch operations
STITCHES = {'k', 'p', 'yo', 'k2tog', 'ssk', 'inc', 'dec'}
KEYWORDS = {'pattern', 'cast_on', 'row', 'repeat', 'bind_off'}

def parse_line(line, line_num):
    """Parse a single line after stripping comments and whitespace.
    Returns (stmt_type, data, error) where error is None if valid.
    """
    # Strip comments: find first '#' outside quotes
    in_quote = False
    comment_start = -1
    for i, ch in enumerate(line):
        if ch == '"':
            in_quote = not in_quote
        elif ch == '#' and not in_quote:
            comment_start = i
            break
    if comment_start != -1:
        line = line[:comment_start]
    line = line.strip()
    if not line:
        return ('empty', None, None)
    
    # Check for keyword at start with token boundary
    # Find first word
    match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)', line)
    if not match:
        return ('unknown', None, 'UNKNOWN_STATEMENT')
    keyword = match.group(1)
    rest = line[match.end():]
    
    # Check if keyword is recognized
    if keyword not in KEYWORDS:
        return ('unknown', None, 'UNKNOWN_STATEMENT')
    
    # Check token boundary: keyword must be followed by whitespace or end
    if rest and not rest[0].isspace():
        return ('unknown', None, 'UNKNOWN_STATEMENT')
    
    rest = rest.strip()
    
    if keyword == 'pattern':
        # pattern "name"
        if not rest.startswith('"'):
            return ('malformed', None, 'MALFORMED_PATTERN')
        # Find closing quote
        end_quote = rest.find('"', 1)
        if end_quote == -1:
            return ('malformed', None, 'MALFORMED_PATTERN')
        name = rest[1:end_quote]
        # Check for extra non-whitespace after closing quote
        after = rest[end_quote+1:].strip()
        if after:
            return ('malformed', None, 'MALFORMED_PATTERN')
        return ('pattern', {'name': name}, None)
    
    elif keyword == 'cast_on':
        # cast_on number
        if not rest:
            return ('malformed', None, 'MALFORMED_CAST_ON')
        parts = rest.split()
        if len(parts) != 1:
            return ('malformed', None, 'MALFORMED_CAST_ON')
        try:
            n = int(parts[0])
        except ValueError:
            return ('malformed', None, 'MALFORMED_CAST_ON')
        return ('cast_on', {'count': n}, None)
    
    elif keyword == 'bind_off':
        if rest:
            return ('malformed', None, 'MALFORMED_BIND_OFF')
        return ('bind_off', None, None)
    
    elif keyword == 'row':
        # row number: stitch_list
        # Must have colon
        if ':' not in rest:
            return ('malformed', None, 'MALFORMED_ROW')
        before_colon, after_colon = rest.split(':', 1)
        before_colon = before_colon.strip()
        after_colon = after_colon.strip()
        if not before_colon or not after_colon:
            return ('malformed', None, 'MALFORMED_ROW')
        try:
            row_num = int(before_colon)
        except ValueError:
            return ('malformed', None, 'MALFORMED_ROW')
        # Parse stitch list
        stitches = parse_stitch_list(after_colon)
        if stitches is None:
            return ('malformed', None, 'MALFORMED_ROW')
        # Check for extra non-whitespace after stitch list? Already stripped.
        return ('row', {'row_num': row_num, 'stitches': stitches}, None)
    
    elif keyword == 'repeat':
        # repeat rows start-end x times
        # pattern: repeat rows \d+\-\d+ x\d+
        m = re.match(r'rows\s+(\d+)\s*\-\s*(\d+)\s+x\s*(\d+)$', rest)
        if not m:
            return ('malformed', None, 'MALFORMED_REPEAT')
        start = int(m.group(1))
        end = int(m.group(2))
        times = int(m.group(3))
        return ('repeat', {'start': start, 'end': end, 'times': times}, None)
    
    else:
        return ('unknown', None, 'UNKNOWN_STATEMENT')

def parse_stitch_list(s):
    """Parse stitch list like 'k10, p2, yo, k2tog'.
    Returns list of (op, count) tuples, or None if invalid.
    """
    if not s:
        return None
    parts = [p.strip() for p in s.split(',')]
    stitches = []
    for part in parts:
        if not part:
            return None
        # Match operation optionally followed by number
        m = re.match(r'([a-zA-Z][a-zA-Z0-9]*)(\d*)$', part)
        if not m:
            return None
        op = m.group(1)
        count_str = m.group(2)
        if op not in STITCHES:
            return None
        count = int(count_str) if count_str else 1
        stitches.append((op, count))
    return stitches

def expand_stitches(stitches):
    """Expand stitch list into individual operations."""
    expanded = []
    for op, count in stitches:
        for _ in range(count):
            expanded.append(op)
    return expanded

def simulate_row(stitches, current_stitches):
    """Simulate a row and return new stitch count."""
    count = current_stitches
    for op in stitches:
        if op == 'k' or op == 'p':
            # knit or purl: consumes 1, produces 1
            pass
        elif op == 'yo':
            # yarn over: increases by 1
            count += 1
        elif op == 'k2tog' or op == 'ssk':
            # decrease: consumes 2, produces 1
            count -= 1
        elif op == 'inc':
            # increase: consumes 1, produces 2
            count += 1
        elif op == 'dec':
            # decrease: consumes 1, produces 1? Actually dec is a generic decrease, assume consumes 1 produces 1? But spec says dec is valid. Let's treat as decrease by 1 (consumes 2? No, dec is single stitch decrease? Usually dec means k2tog or ssk, but here it's separate. Assume dec consumes 1 and produces 0? That would be a bind off? Not sure. Let's assume dec consumes 1 and produces 0 (decrease by 1). But spec doesn't define. We'll treat as consuming 1 and producing 0 (net -1).
            count -= 1
    return count

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"errors": [{"line": 0, "message": "No input file provided"}]}))
        sys.exit(1)
    
    filename = sys.argv[1]
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(json.dumps({"errors": [{"line": 0, "message": "File not found"}]}))
        sys.exit(1)
    
    # Parse all lines
    statements = []
    errors = []
    for i, raw_line in enumerate(lines):
        line_num = i + 1
        stmt_type, data, error = parse_line(raw_line, line_num)
        if stmt_type == 'empty':
            continue
        if error:
            errors.append({"line": line_num, "message": error})
        else:
            statements.append((line_num, stmt_type, data))
    
    # Validate structure
    pattern_name = None
    cast_on = None
    bind_off_found = False
    rows = []
    repeats = []
    
    # Check for missing pattern
    has_pattern = any(t == 'pattern' for _, t, _ in statements)
    if not has_pattern:
        errors.append({"line": 0, "message": "MISSING_PATTERN"})
    
    # Process statements in order
    for line_num, stmt_type, data in statements:
        if stmt_type == 'pattern':
            if pattern_name is not None:
                errors.append({"line": line_num, "message": "DUPLICATE_PATTERN"})
            pattern_name = data['name']
        elif stmt_type == 'cast_on':
            if cast_on is not None:
                errors.append({"line": line_num, "message": "DUPLICATE_CAST_ON"})
            cast_on = data['count']
        elif stmt_type == 'bind_off':
            bind_off_found = True
        elif stmt_type == 'row':
            rows.append((line_num, data))
        elif stmt_type == 'repeat':
            repeats.append((line_num, data))
    
    # Check for missing cast_on
    if cast_on is None:
        errors.append({"line": 0, "message": "MISSING_CAST_ON"})
    
    # Check for missing bind_off
    if not bind_off_found:
        errors.append({"line": 0, "message": "MISSING_BIND_OFF"})
    
    # Expand repeats
    expanded_rows = []
    row_map = {data['row_num']: (line_num, data) for line_num, data in rows}
    
    # Build ordered list of row numbers from original statements (including repeats)
    # We'll process statements in order, expanding repeats
    expanded_ops = []
    for line_num, stmt_type, data in statements:
        if stmt_type == 'row':
            expanded_ops.append(('row', data))
        elif stmt_type == 'repeat':
            start = data['start']
            end = data['end']
            times = data['times']
            for _ in range(times):
                for r in range(start, end+1):
                    if r in row_map:
                        expanded_ops.append(('row', row_map[r][1]))
                    else:
                        errors.append({"line": line_num, "message": f"INVALID_REPEAT: row {r} not found"})
    
    # Simulate
    valid = len(errors) == 0
    final_stitch_count = cast_on if cast_on is not None else 0
    current_stitches = final_stitch_count
    
    for op_type, data in expanded_ops:
        if op_type == 'row':
            stitches = expand_stitches(data['stitches'])
            current_stitches = simulate_row(stitches, current_stitches)
            expanded_rows.append({
                "row": data['row_num'],
                "stitches": data['stitches'],
                "expanded": stitches,
                "stitch_count": current_stitches
            })
    
    # Build output
    output = {
        "pattern_name": pattern_name if pattern_name else "",
        "cast_on": cast_on if cast_on is not None else 0,
        "bind_off": bind_off_found,
        "valid": valid,
        "errors": errors,
        "expanded_rows": expanded_rows,
        "final_stitch_count": current_stitches
    }
    
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()
