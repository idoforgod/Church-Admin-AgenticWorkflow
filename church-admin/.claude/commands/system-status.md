Check church administration system health and display status summary.

Read the following files and report system status:

1. **`state.yaml`** — Read and display:
   - Church name and denomination
   - Feature flags (which workflows are enabled/disabled)
   - Workflow states (last generated dates, pending actions)
   - Autopilot configuration
   - Last backup date

2. **Data file health** — For each file in `data/`, report:
   - File exists: yes/no
   - Last modified date
   - Record count (number of top-level list entries)

3. **Validation status** — Run:
   ```
   python3 scripts/validate_all.py
   ```
   Report pass/fail summary.

4. **Pending actions** — Check:
   - `data/newcomers.yaml`: Any newcomers past 14-day follow-up mark
   - `data/bulletin-data.yaml`: Is next Sunday's bulletin prepared?
   - `data/finance.yaml`: Is current month's summary computed?

5. **Infrastructure** — Verify:
   - 8 agents present in `.claude/agents/`
   - 5 validators present in `.claude/hooks/scripts/`
   - 6 inbox directories present

Format the output as a Korean-language dashboard (존댓말):
```
=== 교회 행정 시스템 상태 ===
교회: [name]
교단: [denomination]
...
```
