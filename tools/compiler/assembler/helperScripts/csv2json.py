#!/usr/bin/env python3
import csv
import json
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

def csv_to_json(csv_file, json_file=None, headers=None):
    rows = []

    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f) if headers is None else csv.DictReader(f, fieldnames=headers)
        for row in reader:
            rows.append({k.strip(): v.strip() if isinstance(v, str) else v for k, v in row.items()})

    output = json.dumps(rows, indent=2)

    if json_file:
        with open(json_file, 'w', encoding='utf-8') as f:
            f.write(output)
    else:
        print(output)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python csv2json.py <csv_file> [json_file] [headers...]")
        sys.exit(1)

    csv_file = sys.argv[1]
    if not os.path.isabs(csv_file):
        csv_file = os.path.join(DATA_DIR, csv_file)

    json_file = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('-') else None
    if json_file and not os.path.isabs(json_file):
        json_file = os.path.join(DATA_DIR, json_file)

    headers = sys.argv[3:] if len(sys.argv) > 3 else None

    csv_to_json(csv_file, json_file, headers)
