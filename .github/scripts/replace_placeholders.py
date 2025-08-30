#!/usr/bin/env python3
import os
import json
import sys

SKIP_DIRS = {'.git', '.next', 'node_modules', 'dist', 'build', '.cache', '.venv', 'venv', '.pnpm-store'}
BIN_EXT = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.pdf', '.zip', '.gz', '.tar', '.rar', '.7z', '.jar', '.wasm',
    '.woff', '.woff2', '.ttf', '.otf', '.mp3', '.mp4', '.mov', '.avi', '.mkv'
}

# Subdirectories inside .github we want to SKIP entirely
GITHUB_SKIP_SUBDIRS = {'workflows', 'scripts'}

def is_bin(p):
    _, e = os.path.splitext(p.lower())
    if e in BIN_EXT:
        return True
    try:
        with open(p, 'rb') as f:
            if b'\x00' in f.read(4096):
                return True
    except Exception:
        # If we can't read it as text, treat as binary and skip
        return True
    return False


def replace_file(p, map_):
    try:
        with open(p, 'r', encoding='utf-8', errors='strict') as f:
            t = f.read()
    except Exception as e:
        print(f"  Error reading {p}: {e}")
        return 0

    replaced = False
    for k, v in map_.items():
        if k in t:
            print(f"  Found placeholder {k} in {p}")
            t = t.replace(k, v)
            replaced = True

    if replaced:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(t)
        print(f"  Updated {p}")
        return 1
    return 0


def walk(map_):
    c = 0
    print(f"Looking for placeholders: {list(map_.keys())}")
    files_with_placeholders = []

    for d, ds, fs in os.walk('.', topdown=True):
        norm_d = os.path.normpath(d)

        # Prune general skip directories wherever they appear
        ds[:] = [x for x in ds if x not in SKIP_DIRS and x != '.git']

        # If we're inside .github, prune only the unwanted subdirectories
        if os.path.basename(norm_d) == '.github':
            ds[:] = [x for x in ds if x not in GITHUB_SKIP_SUBDIRS]
            # This keeps ISSUE_TEMPLATE (and any other allowed dirs/files) intact
            # while skipping .github/workflows and .github/scripts entirely.

        for fn in fs:
            p = os.path.join(d, fn)

            # Skip binary-ish files
            if is_bin(p):
                continue

            print(f"Processing file: {p}")
            result = replace_file(p, map_)
            if result > 0:
                files_with_placeholders.append(p)
            c += result

    if not files_with_placeholders:
        print("No placeholders found in any files")
    else:
        print(f"Files with placeholders: {files_with_placeholders}")

    return c


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 replace_placeholders.py <mapping.json>")
        sys.exit(1)

    mapping_file = sys.argv[1]
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)

        if not mapping:
            print("0")
            sys.exit(0)

        changed_count = walk(mapping)
        print(changed_count)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
