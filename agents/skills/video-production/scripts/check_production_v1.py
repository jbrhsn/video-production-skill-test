#!/usr/bin/env python3
"""Check whether the canonical production project may export its reviewed master."""
from __future__ import annotations

import argparse

from production_workflow import check_export


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--project")
    parser.add_argument("--state")
    args = parser.parse_args()
    result = check_export(args.project_dir, args.project, args.state)
    print(f"Master export approval is current: {result['snapshot']}")


if __name__ == "__main__":
    main()
