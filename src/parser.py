#!/usr/bin/env python3
"""Parser for knitting pattern DSL."""
import re

def parse(source):
    """Parse knitting source into an AST."""
    lines = source.strip().split('\n')
    ast = {'type': 'pattern', 'rows': []}
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # Parse row: e.g., "Row 1: k10, p5"
        match = re.match(r'Row\s+(\d+):\s*(.*)', line, re.IGNORECASE)
        if match:
            row_num = int(match.group(1))
            instructions_str = match.group(2)
            instructions = parse_instructions(instructions_str)
            ast['rows'].append({'type': 'row', 'number': row_num, 'instructions': instructions})
        else:
            # Could be a repeat block or other construct; for now, treat as error
            raise SyntaxError(f"Invalid line: {line}")
    return ast

def parse_instructions(instructions_str):
    """Parse instruction string into list of instruction dicts."""
    instructions = []
    parts = instructions_str.split(',')
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Match stitch count and type: e.g., "k10", "p5"
        match = re.match(r'([kKpP])(\d+)', part)
        if match:
            stitch_type = match.group(1).lower()
            count = int(match.group(2))
            instructions.append({'type': 'stitch', 'stitch_type': stitch_type, 'count': count})
        else:
            # Could be repeat: e.g., "[k2, p2] * 3"
            repeat_match = re.match(r'\[(.*)\]\s*\*\s*(\d+)', part)
            if repeat_match:
                inner = repeat_match.group(1)
                times = int(repeat_match.group(2))
                inner_instructions = parse_instructions(inner)
                instructions.append({'type': 'repeat', 'instructions': inner_instructions, 'times': times})
            else:
                raise SyntaxError(f"Invalid instruction: {part}")
    return instructions
