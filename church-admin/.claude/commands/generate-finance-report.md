---
description: "Generate the monthly finance report with offering/expense summary"
---

Execute the monthly-finance-report workflow for the specified month.

## IMPORTANT: Finance Safety

**Autopilot is PERMANENTLY DISABLED for finance operations.**
Every write to `data/finance.yaml` requires explicit human confirmation.
This is triple-enforced: state.yaml config, agent spec, and workflow definition.

## Steps

1. Read `state.yaml` → get `church.workflow_states.finance.current_month` as target month
2. Read `data/finance.yaml` → collect all non-void offerings and expenses for the target month
3. Compute monthly totals:
   - Total income: sum of all `offerings[].total` where `date` is within target month and `void: false`
   - Total expense: sum of all `expenses[].amount` where `date` is within target month and `void: false`
   - Net balance: total income - total expense
4. Verify arithmetic: computed totals must match `monthly_summary` if present
5. Run P1 validation:
   ```bash
   python3 .claude/hooks/scripts/validate_finance.py --data-dir data/
   ```
6. Generate report:
   - `docs/generated/{year}-{month}-finance-report.md` — Full monthly report
   - Includes: income breakdown by category, expense breakdown, budget comparison, year-to-date summary
7. **(human)** Present report for review — ALL financial figures require human verification
8. On approval: update `state.yaml` finance workflow state

Target month: $ARGUMENTS (defaults to previous calendar month if not specified)

## Report Sections

1. **Header** — Church name, report period, generation date
2. **Income Summary** — By offering category (십일조, 주일헌금, 감사헌금, 선교헌금, 건축헌금)
3. **Expense Summary** — By expense category (관리비, 인건비, 사역비, 선교비, 교육비, 기타)
4. **Monthly Balance** — Income - Expense = Net
5. **Budget Comparison** — Actual vs budgeted amounts, execution rate (%)
6. **Year-to-Date** — Cumulative totals for the fiscal year
7. **Pledged Giving** — Individual pledge tracking (anonymized unless authorized)

## Data Integrity Rules

- All amounts in KRW (integer, no decimals)
- Voided records (void: true) excluded from all calculations
- Cross-reference: `member_id` in pledges must exist in `data/members.yaml`
- Only `@finance-recorder` agent may write to `data/finance.yaml`
