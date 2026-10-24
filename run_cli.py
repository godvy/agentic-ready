"""Checkpoint: audit a docs page from the terminal.

Usage:
  python run_cli.py [guide] [mode]       # bad vs good sample guide (default: ducktape execute)
  python run_cli.py <url> <mode> "<task>"
"""
import json
import sys

from engine.pipeline import audit

CATALOG = json.load(open("samples/catalog.json", encoding="utf-8"))


def show(result: dict) -> None:
    print(f"\n=== {result['source']} [{result['mode']}] ===  AIO Score: {result['score']}/100")
    for p in result["profiles"].values():
        if not p["available"]:
            print(f"  {p['label']:<20} {'BURIED' if p.get('buried') else 'n/a'}  ({p['note']})")
            continue
        r = p["report"]
        print(f"  {p['label']:<20} {r['score']:>3}  {r.get('verdict', '')}")
        for f in r["failures"]:
            print(f"      [{f.get('severity')}] {f.get('what_broke')}  ({f.get('root_cause')})")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    if len(sys.argv) >= 4:
        show(audit(sys.argv[1], sys.argv[3], sys.argv[2]))
    else:
        guide = CATALOG[sys.argv[1] if len(sys.argv) > 1 else "ducktape"]
        mode = sys.argv[2] if len(sys.argv) > 2 else "execute"
        for version in ("bad", "good"):
            show(audit(guide[version], guide["tasks"][mode], mode, reference=guide["reference"]))
