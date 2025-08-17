import argparse, json, pathlib, sys
from .wrapper import validate_text

def main():
    p = argparse.ArgumentParser(prog="ocers-validate", description="Validate text/files with the OCERS rubric.")
    p.add_argument("input", help="Path to file or '-' for stdin")
    p.add_argument("--out", default="ocers_out", help="Output directory for report.json (default: ocers_out)")
    args = p.parse_args()

    if args.input == "-":
        text = sys.stdin.read()
    else:
        text = pathlib.Path(args.input).read_text(encoding="utf-8")

    report = validate_text(text)

    outdir = pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / "report.json"
    outfile.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps({"status": "ok", "out": str(outfile)}))

if __name__ == "__main__":
    main()
