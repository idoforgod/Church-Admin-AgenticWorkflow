---
description: "Generate the weekly church bulletin for the upcoming Sunday"
---

Execute the weekly-bulletin workflow for the upcoming Sunday.

## Steps

1. Read `state.yaml` → get `church.workflow_states.bulletin.next_due_date` as the target Sunday
2. Read `data/schedule.yaml` → verify Sunday services exist and identify any special events
3. Read `data/bulletin-data.yaml` → verify all required fields are populated:
   - `bulletin.issue_number` (positive integer)
   - `bulletin.date` (valid Sunday date)
   - `bulletin.sermon.title`, `bulletin.sermon.scripture`, `bulletin.sermon.preacher`
   - `bulletin.worship_order` (≥ 3 items)
4. Read `data/members.yaml` → filter birthday/anniversary members for the target week
5. Cross-reference: verify all `member_id` in celebrations.birthday exist in members.yaml
6. Cross-reference: verify all `family_id` in celebrations.wedding_anniversary exist in members.yaml
7. Load `templates/bulletin-template.yaml` → populate all 16 variable regions (VR-BUL-01 through VR-BUL-16)
8. Generate two files:
   - `bulletins/{date}-bulletin.md` — Full bulletin
   - `bulletins/{date}-worship-order.md` — Worship order sheet
9. Run P1 validation:
   ```bash
   python3 .claude/hooks/scripts/validate_bulletin.py --data-dir data/
   ```
10. Present bulletin for review
11. On approval: update `data/bulletin-data.yaml` generation_history and `state.yaml` workflow state

Target date: $ARGUMENTS (defaults to `church.workflow_states.bulletin.next_due_date` if not specified)

## Important Notes

- All 16 VRs must be populated — no placeholder text allowed
- Korean formatting: dates use 년/월/일, issue numbers use 제 N호
- Only `@bulletin-generator` agent may write to `data/bulletin-data.yaml`
- Only Orchestrator may write to `state.yaml`
