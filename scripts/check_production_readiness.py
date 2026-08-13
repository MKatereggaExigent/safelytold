"""Evidence-based production readiness gate for SafelyTold."""
from __future__ import annotations
import argparse
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "production-readiness.yaml"
READY = {"implemented", "verified"}
VALID = READY | {"pending_evidence", "pending_external", "not_started", "waived"}

def assess() -> tuple[list[str], list[str]]:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    errors, blockers, seen = [], [], set()
    for item in data.get("requirements", []):
        identifier, status = item.get("id", "<missing-id>"), item.get("status")
        if identifier in seen: errors.append(f"{identifier}: duplicate requirement id")
        seen.add(identifier)
        if status not in VALID: errors.append(f"{identifier}: invalid status {status!r}")
        evidence = item.get("evidence") or []
        if not evidence: errors.append(f"{identifier}: no evidence paths declared")
        for relative in evidence:
            if not (ROOT / relative).exists(): errors.append(f"{identifier}: missing evidence {relative}")
        if item.get("launch_gate") and status not in READY:
            blockers.append(f"{identifier} [{status}] {item['requirement']}: {item.get('action', 'approval required')}")
    return errors, blockers

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="fail while launch blockers remain")
    args = parser.parse_args()
    errors, blockers = assess()
    for error in errors: print(f"ERROR: {error}")
    for blocker in blockers: print(f"BLOCKER: {blocker}")
    print(f"Readiness manifest: {len(errors)} error(s), {len(blockers)} launch blocker(s)")
    return 1 if errors or (args.strict and blockers) else 0

if __name__ == "__main__": raise SystemExit(main())
