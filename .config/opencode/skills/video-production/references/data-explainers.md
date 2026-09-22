# Data and finance explainers

Keep facts, illustrative assumptions, calculations, and conclusions distinct. The agent can research and verify claims; obtain current primary sources when accuracy or changing figures require it. The user approves the intended scenario and consequential assumptions. Do not treat a reference video's figures as verified input.

Keep `assumptions.json` or CSV data with units, jurisdiction/date where relevant, source or `illustrative` status, and the convention used. Render numbers, charts, and narration claims from the same computed dataset. Record rounding rules; calculate at full precision and round for display.

## Included calculation helper

`scripts/finance_model.py` is a deliberately limited illustrative fixed-rate loan and investment calculator. It has no live market assumptions and makes no rent-versus-buy recommendation. Run through the pipeline's uv environment:

```bash
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/finance_model.py --input PROJECT/assumptions.json --out PROJECT/public/data/model.json
```

Example input:

```json
{
  "status": "illustrative",
  "currency": "USD",
  "mortgage": {"principal": 300000, "annual_rate": 0.06, "years": 30},
  "investment": {"initial": 60000, "monthly_contribution": 500, "annual_return": 0.05, "years": 20}
}
```

Rates are decimals, not percentages. Mortgage interest is nominal annual rate / 12; investment return is an effective annual return converted to its monthly equivalent. Contributions occur at month-end. Output includes full monthly loan balance/interest/principal and investment balance/contributions/growth series with assumptions retained. Zero interest/return and negative investment returns greater than -100% are supported. Borrowing rates must be nonnegative. This model excludes taxes, inflation, investment fees, mortgage insurance, refinancing, and transaction/ownership costs.

For an actual rent-versus-buy comparison, extend the project model explicitly to include down payment, purchase/sale costs, mortgage balance, maintenance, property taxes/insurance, rent escalation, appreciation, investment returns, and a declared common cash-flow budget. Define what happens when the cost difference reverses. Distinguish home equity from net sale proceeds and investment balances from after-tax proceeds. Present sensitivity scenarios rather than implying one assumed return is a forecast. Add tests for the extended calculation before animating its results.

## Chart implementation

The whiteboard `LineChart` uses explicit fixed domains so axes do not silently rescale during a reveal. It is also usable in other styles by copying the helper. Add axis labels, units, time horizon, series legend, and an illustrative/source note. Use distinct strokes or labels as well as colors. Define whether amounts are nominal or inflation-adjusted and whether a comparison shows wealth, costs, or cash flows. Use equally spaced time values or plot actual x coordinates; do not make a large amount appear small by changing scales between shots.

Test accounting identities and known cases (zero-rate loan payoff, interest plus principal equals payment, investment zero-return balance equals contributions). Check narration numbers against generated data. Review dense and final chart frames for label overlap, meaningful domains, source-note readability, and consistency with the spoken qualifications.
