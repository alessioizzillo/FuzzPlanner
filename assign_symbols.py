#!/usr/bin/env python3

import argparse
import angr
import bisect
import sys
import os
import re
from typing import List, Tuple, Optional

LINE_ADDR_RE = re.compile(r'^\s*(\([^\)]*\))\s*(0x[0-9A-Fa-f]+)\s*$')

def parse_address_hex(addr_str: str) -> Optional[int]:
    try:
        return int(addr_str, 16)
    except ValueError:
        return None

def build_function_ranges(proj: angr.Project) -> List[Tuple[int, int, str]]:
    funcs = []
    for faddr, func in proj.kb.functions.items():
        start = func.addr
        size = func.size if getattr(func, "size", 0) else 1
        end = start + size
        name = func.name if getattr(func, "name", None) else f"func_{start:#x}"
        funcs.append((start, end, name))
    funcs.sort(key=lambda t: t[0])
    return funcs

def find_function_name(func_ranges: List[Tuple[int, int, str]], addr: int) -> Optional[str]:
    if not func_ranges:
        return None
    starts = [s for (s, _, _) in func_ranges]
    idx = bisect.bisect_right(starts, addr) - 1
    if idx >= 0:
        s, e, name = func_ranges[idx]
        if s <= addr < e:
            return name
    return None

def main():
    ap = argparse.ArgumentParser(description="Map addresses in lines like '(S) 0x401ea0' to function symbols using angr.")
    ap.add_argument("--addrs", "-a", required=True, help="Input file with one row per line (e.g. '(S) 0x401ea0').")
    ap.add_argument("--bin", "-b", required=True, help="Target binary to analyze.")
    ap.add_argument("-o", "--out", default=None, help="Output file (default: same dir as input, named <input>_mapped.txt).")
    ap.add_argument("--auto-load-libs", action="store_true", help="Let angr auto-load shared libraries (default: OFF).")
    args = ap.parse_args()

    if args.out is None:
        base, _ = os.path.splitext(args.addrs)
        args.out = base + "_mapped.txt"

    with open(args.addrs, "r", encoding="utf-8", errors="replace") as f:
        lines = [ln.rstrip("\n") for ln in f]

    load_opts = {"auto_load_libs": args.auto_load_libs}
    try:
        proj = angr.Project(args.bin, load_options=load_opts)
    except Exception as e:
        print(f"Failed to load binary '{args.bin}': {e}", file=sys.stderr)
        sys.exit(1)

    try:
        proj.analyses.CFGFast()
    except Exception as e:
        print(f"CFGFast failed or raised: {e}. Continuing with currently-known functions.", file=sys.stderr)

    func_ranges = build_function_ranges(proj)

    output_lines = []
    prev_name = None

    for line in lines:
        m = LINE_ADDR_RE.match(line)
        if not m:
            output_lines.append(line)
            prev_name = None
            continue

        prefix = m.group(1)
        addr_str = m.group(2)

        addr = parse_address_hex(addr_str)
        if addr is None:
            output_lines.append(line)
            prev_name = None
            continue

        name = find_function_name(func_ranges, addr)
        if name is None:
            output_lines.append(line)
            prev_name = None
            continue

        if name == prev_name:
            continue

        output_lines.append(f"{prefix} {addr_str}\t{name}")
        prev_name = name

    with open(args.out, "w") as outf:
        outf.write("\n".join(output_lines))

    print(f"Wrote {len(output_lines)} lines to {args.out}")

if __name__ == "__main__":
    main()
