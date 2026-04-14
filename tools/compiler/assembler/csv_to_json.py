import csv
import json
import sys
from pathlib import Path


def csv_to_json(csv_path: str, json_path: str) -> None:
    instructions = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        for row in reader:
            instruction = {
                "opcode": row["opcode"].strip(),
                "size": int(row["size"].strip()),
                "machineCode": int(row["machineCode"].strip()),
                "comment": row["comment"].strip(),
                "operandCount": int(row["operandCount"].strip()) if row["operandCount"].strip() else 0,
            }
            instructions.append(instruction)
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(instructions, f, indent=2)


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/instructionSet.csv"
    json_path = sys.argv[2] if len(sys.argv) > 2 else "data/instructionSet.json"
    csv_to_json(csv_path, json_path)
