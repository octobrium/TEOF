from importlib import import_module
import sys

# Delegate to the existing ensemble CLI in your repo
_TARGET = "extensions.validator.scorers.ensemble_cli"

def main():
    try:
        mod = import_module(_TARGET)
    except ModuleNotFoundError as e:
        print(f"Error: could not import {_TARGET}. Is the repo installed in the same env?", file=sys.stderr)
        sys.exit(1)
    if hasattr(mod, "main") and callable(mod.main):
        mod.main()
    else:
        print(f"Error: {_TARGET} has no callable main()", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
