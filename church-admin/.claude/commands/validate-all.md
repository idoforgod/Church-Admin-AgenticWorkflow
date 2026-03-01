Run all P1 validation scripts and report aggregated results.

Execute the following command:
```
python3 scripts/validate_all.py
```

After execution, report:
1. Total checks passed vs total checks
2. Any FAILED checks with their rule IDs and error messages
3. If all pass, confirm "29/29 checks passed — all data files are valid"
4. If any fail, list the specific remediation steps for each failure

This runs 5 validators:
- `validate_members.py` (M1-M7): Member data integrity
- `validate_finance.py` (F1-F7): Financial data integrity
- `validate_schedule.py` (S1-S6): Schedule data integrity
- `validate_newcomers.py` (N1-N6): Newcomer data integrity
- `validate_bulletin.py` (B1-B3): Bulletin data integrity
