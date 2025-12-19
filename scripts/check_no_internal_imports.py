import sys
from pathlib import Path

FORBIDDEN = "from orchestrator._internal"


def check_path(root: Path) -> int:
    failures = 0
    for p in root.rglob("*.py"):
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if FORBIDDEN in txt:
            print(f"Forbidden _internal import in: {p}")
            failures += 1
    return failures


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: check_no_internal_imports.py <path> [<path2> ...]")
        return 2
    total = 0
    for arg in sys.argv[1:]:
        root = Path(arg)
        if not root.exists():
            print(f"Path not found: {root}")
            return 2
        total += check_path(root)
    if total > 0:
        print(f"Found {total} files importing orchestrator._internal in public code paths.")
        return 1
    print("No forbidden _internal imports detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
