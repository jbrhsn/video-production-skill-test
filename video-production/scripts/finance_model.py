"""Illustrative fixed-rate amortization and investment series; no market defaults."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def number(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name} must be finite and >= {minimum}")
    return float(value)


def months(years):
    years = number(years, "years")
    count = years * 12
    if count < 1 or count > 1200 or not math.isclose(count, round(count)):
        raise ValueError("years must represent 1–1200 whole months")
    return round(count)


def amortization(principal, annual_rate, years):
    balance = number(principal, "principal")
    rate = number(annual_rate, "annual_rate") / 12
    count = months(years)
    payment = balance / count if rate == 0 else balance * rate / -math.expm1(-count * math.log1p(rate))
    rows = [{"month": 0, "balance": balance, "payment": 0, "principal": 0, "interest": 0}]
    for month in range(1, count + 1):
        interest = balance * rate
        paid_principal = balance if month == count else min(balance, max(0, payment - interest))
        balance = max(0, balance - paid_principal)
        rows.append({"month": month, "balance": balance, "payment": paid_principal + interest,
                     "principal": paid_principal, "interest": interest})
    return {"scheduled_monthly_payment": payment, "rows": rows}


def investment(initial, monthly_contribution, annual_return, years):
    balance = number(initial, "initial")
    contribution = number(monthly_contribution, "monthly_contribution")
    annual_return = number(annual_return, "annual_return", -1)
    if annual_return == -1:
        raise ValueError("annual_return must exceed -1")
    rate = math.expm1(math.log1p(annual_return) / 12)
    contributed = balance
    rows = [{"month": 0, "balance": balance, "contributed": contributed, "growth": 0}]
    for month in range(1, months(years) + 1):
        balance = balance * (1 + rate) + contribution
        contributed += contribution
        rows.append({"month": month, "balance": balance, "contributed": contributed, "growth": balance - contributed})
    return {"rows": rows}


def calculate(data):
    if not isinstance(data, dict) or not any(k in data for k in ("mortgage", "investment")):
        raise ValueError("Input must contain mortgage and/or investment parameters")
    result = {"assumptions": data, "conventions": {
        "mortgage": "Fixed rate; nominal annual interest divided by 12; monthly payments; no fees or taxes.",
        "investment": "Effective annual return; monthly compounding; month-end contributions; no fees or taxes."}}
    if "mortgage" in data:
        result["mortgage"] = amortization(**data["mortgage"])
    if "investment" in data:
        result["investment"] = investment(**data["investment"])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    output = Path(args.out)
    payload = json.dumps(calculate(json.loads(Path(args.input).read_text())), indent=2, allow_nan=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(payload + "\n")


if __name__ == "__main__":
    main()
