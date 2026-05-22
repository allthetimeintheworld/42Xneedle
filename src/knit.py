#!/usr/bin/env python3
import sys
import json
import re

STITCHES = {'k', 'p', 'yo', 'k2tog', 'ssk', 'inc', 'dec'}
KEYWORDS = {'pattern', 'cast_on', 'row', 'repeat', 'bind_off'}

def strip_comments(line):
    in_quote = False
    for i, ch in enumerate(line):
        if ch == '"':
            in_quote = not in_quote
        elif ch == '#' and not in_quote:
            return line[:i]
    return line

def parse_line(line, line_num):
    original = line
    line = strip_comments(line)
    stripped = line.strip()
    if not stripped:
        return ('empty', None, None)
    
    # Check for keyword at start with token boundary
    match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)', stripped)
    if not match:
        return ('unknown', None, 'UNKNOWN_STATEMENT')
    keyword = match.group(1)
    rest = stripped[match.end():]
    
    if keyword not in KEYWORDS:
        return ('unknown', None, 'UNKNOWN_STATEMENT')
    
    if keyword == 'pattern':
        # pattern must be followed by whitespace
        if not rest or rest[0] != ' ':
            return ('unknown', None, 'UNKNOWN_STATEMENT')
        # rest should be a quoted string
        m = re.match(r'^\s*"([^"]*)"\s*$', rest)
        if m:
            return ('pattern', m.group(1), None)
        else:
            # check if there is any quoted string attempt
            if '"' in rest:
                return ('malformed', None, 'MALFORMED_PATTERN')
            else:
                return ('malformed', None, 'MALFORMED_PATTERN')
    
    elif keyword == 'cast_on':
        if not rest or rest[0] != ' ':
            return ('unknown', None, 'UNKNOWN_STATEMENT')
        m = re.match(r'^\s*(\d+)\s*$', rest)
        if m:
            return ('cast_on', int(m.group(1)), None)
        else:
            return ('malformed', None, 'MALFORMED_CAST_ON')
    
    elif keyword == 'row':
        if not rest or rest[0] != ' ':
            return ('unknown', None, 'UNKNOWN_STATEMENT')
        m = re.match(r'^\s*(\d+)\s*:\s*(.*)$', rest)
        if m:
            row_num = int(m.group(1))
            instr_str = m.group(2).strip()
            if not instr_str:
                return ('malformed', None, 'MALFORMED_ROW')
            # parse instructions
            instrs = []
            parts = [p.strip() for p in instr_str.split(',')]
            for part in parts:
                if not part:
                    return ('malformed', None, 'MALFORMED_ROW')
                # match stitch operation
                m2 = re.match(r'^([a-z]+)(\d*)$', part)
                if m2:
                    op = m2.group(1)
                    count_str = m2.group(2)
                    if op not in STITCHES:
                        return ('malformed', None, 'MALFORMED_ROW')
                    count = int(count_str) if count_str else 1
                    instrs.append({'operation': op, 'count': count})
                else:
                    return ('malformed', None, 'MALFORMED_ROW')
            return ('row', {'row_number': row_num, 'instructions': instrs}, None)
        else:
            return ('malformed', None, 'MALFORMED_ROW')
    
    elif keyword == 'repeat':
        if not rest or rest[0] != ' ':
            return ('unknown', None, 'UNKNOWN_STATEMENT')
        m = re.match(r'^\s*rows\s+(\d+)\s*-\s*(\d+)\s*x\s*(\d+)\s*$', rest)
        if m:
            start = int(m.group(1))
            end = int(m.group(2))
            times = int(m.group(3))
            return ('repeat', {'start': start, 'end': end, 'times': times}, None)
        else:
            return ('malformed', None, 'MALFORMED_REPEAT')
    
    elif keyword == 'bind_off':
        if rest and rest.strip():
            return ('malformed', None, 'MALFORMED_BIND_OFF')
        return ('bind_off', None, None)
    
    else:
        return ('unknown', None, 'UNKNOWN_STATEMENT')

def expand_repeats(parsed_lines):
    expanded = []
    i = 0
    while i < len(parsed_lines):
        typ, data, err = parsed_lines[i]
        if typ == 'repeat':
            start = data['start']
            end = data['end']
            times = data['times']
            # collect rows to repeat
            rows_to_repeat = []
            for j in range(i-1, -1, -1):
                if parsed_lines[j][0] == 'row':
                    rn = parsed_lines[j][1]['row_number']
                    if start <= rn <= end:
                        rows_to_repeat.append(parsed_lines[j])
                    elif rn < start:
                        break
            rows_to_repeat.reverse()
            for _ in range(times):
                expanded.extend(rows_to_repeat)
        else:
            expanded.append(parsed_lines[i])
        i += 1
    return expanded

def simulate(expanded_lines, cast_on_count):
    stitch_count = cast_on_count
    rows = []
    for typ, data, err in expanded_lines:
        if typ == 'row':
            row_num = data['row_number']
            instrs = data['instructions']
            for instr in instrs:
                op = instr['operation']
                cnt = instr['count']
                if op == 'k' or op == 'p':
                    # no change
                    pass
                elif op == 'yo':
                    stitch_count += cnt
                elif op == 'k2tog' or op == 'ssk' or op == 'dec':
                    stitch_count -= cnt
                elif op == 'inc':
                    stitch_count += cnt
            rows.append({'row_number': row_num, 'stitch_count': stitch_count})
    return rows

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'errors': [{'line': 0, 'message': 'No input file provided'}]}))
        sys.exit(1)
    filename = sys.argv[1]
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(json.dumps({'errors': [{'line': 0, 'message': 'File not found'}]}))
        sys.exit(1)
    
    parsed_lines = []
    errors = []
    for i, line in enumerate(lines):
        line_num = i + 1
        typ, data, err = parse_line(line, line_num)
        if typ == 'empty':
            continue
        if err:
            errors.append({'line': line_num, 'message': err})
        else:
            parsed_lines.append((typ, data, err))
    
    # Check for missing required statements
    has_pattern = any(t == 'pattern' for t, _, _ in parsed_lines)
    has_cast_on = any(t == 'cast_on' for t, _, _ in parsed_lines)
    has_bind_off = any(t == 'bind_off' for t, _, _ in parsed_lines)
    if not has_pattern:
        errors.append({'line': 0, 'message': 'MISSING_PATTERN'})
    if not has_cast_on:
        errors.append({'line': 0, 'message': 'MISSING_CAST_ON'})
    if not has_bind_off:
        errors.append({'line': 0, 'message': 'MISSING_BIND_OFF'})
    
    # Extract pattern name
    pattern_name = ''
    for typ, data, err in parsed_lines:
        if typ == 'pattern':
            pattern_name = data
            break
    
    # Extract cast_on count
    cast_on_count = 0
    for typ, data, err in parsed_lines:
        if typ == 'cast_on':
            cast_on_count = data
            break
    
    # Expand repeats
    expanded_lines = expand_repeats(parsed_lines)
    
    # Simulate
    rows = simulate(expanded_lines, cast_on_count)
    
    # Determine valid
    valid = len(errors) == 0
    
    # Build output
    output = {
        'pattern_name': pattern_name,
        'cast_on': cast_on_count,
        'bind_off': True if has_bind_off else False,
        'valid': valid,
        'errors': errors,
        'expanded_rows': rows,
        'final_stitch_count': rows[-1]['stitch_count'] if rows else cast_on_count
    }
    
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()
