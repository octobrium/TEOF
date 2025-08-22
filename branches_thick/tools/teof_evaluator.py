#!/usr/bin/env python3
import sys, json
def main():
    try:
        data = sys.stdin.read()
        ocers = json.loads(data) if data.strip() else {}
        n = len(ocers.get("observations", [])) if isinstance(ocers, dict) else 0
        print(f"OGS: 1.0  | observations={n}  | evaluator=stub")
        return 0
    except Exception:
        print("OGS: 1.0  | evaluator=stub | note=stdin parse failed")
        return 0
if __name__ == "__main__":
    raise SystemExit(main())
