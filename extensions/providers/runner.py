from __future__ import annotations
import argparse, sys
from .registry import get

def main(argv=None):
    ap = argparse.ArgumentParser(description="TEOF provider runner")
    ap.add_argument("--provider", default="mock")
    ap.add_argument("--model", default=None)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("prompt", nargs="*", help="prompt text (or stdin)")
    args = ap.parse_args(argv)
    prompt = " ".join(args.prompt).strip() or sys.stdin.read()
    prov = get(args.provider)
    gen = prov.generate(prompt, temperature=args.temperature, max_tokens=args.max_tokens, model=args.model)
    print(gen.text)
    return 0
