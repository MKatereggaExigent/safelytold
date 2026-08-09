#!/usr/bin/env python3
from __future__ import annotations
import argparse
from safelytold_common.hashing import merkle_root


def main() -> None:
    parser = argparse.ArgumentParser(description='Compute the Merkle root for lowercase SHA-256 leaves.')
    parser.add_argument('leaves', nargs='+')
    args = parser.parse_args()
    if any(len(x) != 64 for x in args.leaves):
        raise SystemExit('Every leaf must be a 64-character SHA-256 hex value')
    print(merkle_root(args.leaves))


if __name__ == '__main__':
    main()
