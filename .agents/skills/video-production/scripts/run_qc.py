#!/usr/bin/env python3
"""Run the currently available machine checks for a compiled render timeline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from qc_timeline import check_timeline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    timeline = json.loads(Path(args.timeline).read_text(encoding="utf-8"))
    report = check_timeline(timeline)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"QC {report['status']}: {len(report['findings'])} findings -> {output}")
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
