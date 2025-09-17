#!/usr/bin/env python3
# 遍历 out_proc_probe 下的文件，找到包含小写 "flag" 的文件并把内容全部输出与保存
# Usage: python3 dump_flags.py [--dir out_proc_probe] [--save-text found_flags.txt]
# 默认把二进制原始文件也复制到 found_flags_raw/<filename>.bin

import os
import sys
import argparse
import shutil

DEFAULT_DIR = "out_proc_probe"
OUT_RAW_DIR = "found_flags_raw"
OUT_TEXT_FILE = "found_flags.txt"
PAT = b"flag"  # 只匹配完全小写 flag

def is_binary(data: bytes) -> bool:
    # heuristic: if many nulls or non-printable, treat as binary
    text_chars = bytearray(range(32,127)) + b'\n\r\t\b'
    if not data:
        return False
    nontext = sum(1 for b in data[:4096] if b not in text_chars)
    return (nontext / min(len(data), 4096)) > 0.30

def main():
    parser = argparse.ArgumentParser(description="Dump files that contain lowercase 'flag' from a probe output directory.")
    parser.add_argument('--dir', '-d', default=DEFAULT_DIR, help='directory with probe outputs (default: out_proc_probe)')
    parser.add_argument('--save-text', '-o', default=OUT_TEXT_FILE, help='save combined text output to this file (default: found_flags.txt)')
    args = parser.parse_args()

    d = args.dir
    if not os.path.isdir(d):
        print(f"Directory not found: {d}", file=sys.stderr)
        sys.exit(2)

    os.makedirs(OUT_RAW_DIR, exist_ok=True)
    matched = []
    for root, _, files in os.walk(d):
        for fn in files:
            path = os.path.join(root, fn)
            try:
                data = open(path, 'rb').read()
            except Exception as e:
                print(f"[ERR] cannot read {path}: {e}", file=sys.stderr)
                continue
            if PAT in data:
                matched.append((path, data))

    if not matched:
        print("No files containing lowercase 'flag' found in", d)
        return

    # open combined text output
    with open(args.save_text, 'w', encoding='utf-8', errors='replace') as outf:
        for path, data in matched:
            rel = os.path.relpath(path, d)
            size = len(data)
            header = f"\n=== FILE: {rel}  (size={size} bytes) ===\n"
            print(header, end='')
            outf.write(header)
            # save raw binary copy
            raw_dest = os.path.join(OUT_RAW_DIR, rel.replace(os.sep, '_'))
            try:
                with open(raw_dest, 'wb') as f:
                    f.write(data)
            except Exception as e:
                print(f"[WARN] failed saving raw {raw_dest}: {e}", file=sys.stderr)

            # try to decode as utf-8, fallback to latin-1
            try:
                text = data.decode('utf-8')
            except Exception:
                text = data.decode('latin-1', errors='replace')

            # Print to stdout and write to combined file
            # For very large files, still print fully as user requested but show size first
            print(text)
            outf.write(text)
            outf.write("\n" + ("-"*80) + "\n")
    print(f"\nDone. Matched {len(matched)} files. Raw copies saved to {OUT_RAW_DIR}, combined text saved to {args.save_text}")

if __name__ == "__main__":
    main()