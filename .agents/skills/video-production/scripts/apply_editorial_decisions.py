#!/usr/bin/env python3
"""Validate review decisions; this command never mutates an editorial timeline."""
from __future__ import annotations

import argparse, json
from pathlib import Path

def validate(data):
    if not isinstance(data, dict) or data.get("schema") != "editorial-decisions" or data.get("version") != 1 or set(data) != {"schema", "version", "analysisDigest", "decisions"}: raise ValueError("decisions require editorial-decisions version 1")
    for row in data["decisions"]:
        if not isinstance(row, dict) or set(row) != {"candidateId", "decision", "reason", "reviewer"} or row["decision"] not in {"accepted", "rejected", "deferred"}: raise ValueError("decision row is invalid")
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--decisions", required=True); args = parser.parse_args(); print(json.dumps(validate(json.loads(Path(args.decisions).read_text())), indent=2))
if __name__ == "__main__": main()
