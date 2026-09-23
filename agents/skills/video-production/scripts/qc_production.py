#!/usr/bin/env python3
"""Aggregate deterministic timeline and instrumented render observations honestly."""
from __future__ import annotations

from qc_timeline import check_timeline


def check(render_timeline, observations=None):
    base = check_timeline(render_timeline); findings = list(base["findings"]); coverage = {name: "passed" for name in base["coverage"]}
    observations = observations or {"schema": "render-observations", "version": 1, "coverage": {}, "findings": []}
    if not isinstance(observations, dict) or observations.get("schema") != "render-observations" or observations.get("version") != 1:
        raise ValueError("observations require render-observations version 1")
    for detector, status in observations.get("coverage", {}).items():
        if status not in {"passed", "unavailable", "error", "partial"}: raise ValueError("observation coverage has invalid state")
        coverage[detector] = status
    for finding in observations.get("findings", []):
        if not isinstance(finding, dict) or finding.get("severity") not in {"warning", "error"} or not isinstance(finding.get("rule"), str): raise ValueError("observation finding is invalid")
        findings.append(finding)
    # Instrumentation failure is never silently treated as a successful check.
    for detector, status in coverage.items():
        if status in {"unavailable", "error", "partial"}:
            findings.append({"rule": f"coverage.{detector}", "severity": "warning", "message": f"{detector} coverage is {status}"})
    status = "fail" if any(item["severity"] == "error" for item in findings) else "pass"
    return {"schema": "qc-report", "version": 2, "status": status, "coverage": coverage, "findings": findings}


def bounded_repair(report, policy):
    if not isinstance(policy, dict) or set(policy) != {"enabledRules", "maxRepairs"} or not isinstance(policy["enabledRules"], list) or type(policy["maxRepairs"]) is not int or policy["maxRepairs"] < 0:
        raise ValueError("repair policy requires enabledRules and nonnegative maxRepairs")
    repaired = []
    for finding in report.get("findings", []):
        if len(repaired) >= policy["maxRepairs"]: break
        if finding.get("severity") == "error" and finding.get("rule") in policy["enabledRules"]:
            repaired.append({"rule": finding["rule"], "action": "requires deterministic source artifact regeneration", "range": finding.get("frames"), "status": "queued"})
    return {"schema": "bounded-repair-record", "version": 1, "repairs": repaired, "unrepairedErrors": [item for item in report.get("findings", []) if item.get("severity") == "error" and item.get("rule") not in policy["enabledRules"]]}
