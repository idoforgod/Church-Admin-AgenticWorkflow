# Troubleshooting Guide — Top 10 Common Issues

Solutions for the most common issues encountered when using the Church Administration system. Each issue includes symptoms, cause, and step-by-step resolution.

**Target Users**: 행정 간사 (first-line troubleshooting) and IT volunteers (technical resolution)

---

## Issue 1: YAML Syntax Error

### Symptoms
- Error message: "YAML parse error" or "invalid syntax"
- Data file won't load
- Validation fails with cryptic error

### Cause
YAML files are sensitive to formatting. Common mistakes:
- Using tabs instead of spaces (YAML requires spaces only)
- Missing colon after field names
- Incorrect indentation level

### Resolution (행정 간사)

1. Open the file that caused the error
2. Look for the line number mentioned in the error
3. Check for these common issues:

```yaml
# WRONG — tab character (invisible but breaks YAML)
	name: "김철수"

# CORRECT — 2 spaces
  name: "김철수"
```

```yaml
# WRONG — missing colon
  name "김철수"

# CORRECT
  name: "김철수"
```

```yaml
# WRONG — misaligned indentation
members:
  - id: "MBR-2026-001"
  name: "김철수"

# CORRECT — name indented under list item
members:
  - id: "MBR-2026-001"
    name: "김철수"
```

### Resolution (IT Volunteer)

```bash
python3 -c "import yaml; yaml.safe_load(open('data/members.yaml'))"
```

---

## Issue 2: Excel File Parse Failure

### Symptoms
- Excel file stays in `inbox/documents/` without processing
- File moved to `inbox/errors/`
- Error: "unsupported format" or "parse error"

### Cause
- File uses `.xls` (old format) instead of `.xlsx`
- Merged cells or complex formatting
- Password-protected file

### Resolution

1. **Check file format**: Save as `.xlsx` (Excel Workbook)
   - Open in Excel → Save As → Select "Excel Workbook (.xlsx)"

2. **Simplify formatting**: Remove merged cells
   - Select all → Format → Cells → Remove merge

3. **Remove protection**: File must not be password-protected

4. **Check encoding**: Korean characters should be UTF-8
   - Save As → Tools → Web Options → Encoding → UTF-8

---

## Issue 3: Validation Fails After Data Edit

### Symptoms
- After manually editing a YAML file, validation reports errors
- Error messages like "M1 FAIL" or "F3 FAIL"

### Cause
Manual edits introduced data that violates validation rules:

| Rule | What It Checks | Common Mistake |
|------|---------------|----------------|
| M1 | Member ID uniqueness + format | Duplicate or malformed ID |
| M3 | Phone format (010-NNNN-NNNN) | Missing dashes or wrong prefix |
| M4 | Status enum | Using invalid status value |
| F2 | Amounts are KRW integers | Decimals or commas in amounts |
| S4 | Event status enum | Using "scheduled" instead of "planned" |
| N2 | Stage/milestone consistency | Stage doesn't match milestones |

### Resolution

1. Read the error message — it specifies which rule and field failed
2. Fix the value to match the expected format
3. Re-run validation:

```bash
python3 .claude/hooks/scripts/validate_members.py --data-dir data/
```

Or ask the AI: "데이터 검증 오류 도와줘"

---

## Issue 4: Permission Denied Error

### Symptoms
- "Permission denied" when Claude tries to write
- Agent can't create output files
- Backup script won't run

### Resolution (IT Volunteer)

```bash
# Fix file permissions
chmod 644 data/*.yaml

# Fix directory permissions
chmod 755 data/ inbox/ output/ bulletins/

# Fix backup script
chmod +x scripts/daily-backup.sh
```

---

## Issue 5: Korean Characters Display Incorrectly

### Symptoms
- Korean text shows as `????` or garbled characters
- Names display wrong in generated documents

### Cause
File not saved as UTF-8, or terminal doesn't support Korean.

### Resolution

```bash
# Check encoding (IT volunteer)
file -I data/members.yaml
# Expected: text/plain; charset=utf-8
```

- **Terminal**: Set to UTF-8 (Terminal → Preferences → Profiles → Advanced → UTF-8)
- **Files**: Open in UTF-8 editor (VS Code), save

---

## Issue 6: Bulletin Generation Fails

### Symptoms
- "이번 주 주보 만들어줘" produces an error
- Missing sections in generated bulletin

### Resolution

1. Validate bulletin data:
```bash
python3 .claude/hooks/scripts/validate_bulletin.py --data-dir data/
```

2. Check required files exist:
```bash
ls data/members.yaml data/schedule.yaml data/bulletin-data.yaml templates/bulletin-template.yaml
```

3. Fix any missing or corrupted files from backup

---

## Issue 7: Newcomer Pipeline Not Advancing

### Symptoms
- Newcomer stuck at current stage
- "Stage transition denied" message

### Cause
Prerequisite milestones not completed, or human approval not given.

### Resolution

1. Check newcomer status: "새신자 현황: [이름]"
2. The AI shows which milestones are needed
3. Complete missing milestones first
4. Stage changes require explicit human approval

The 6 stages are: `first_visit → attending → small_group → baptism_class → baptized → settled`

---

## Issue 8: Backup Failure

### Symptoms
- `daily-backup.sh` reports errors
- Backup directory empty

### Resolution (IT Volunteer)

```bash
# Check disk space
df -h

# Run manual backup
chmod +x scripts/daily-backup.sh
./scripts/daily-backup.sh

# Create backup directory if needed
mkdir -p backups/

# Set up cron (daily 2 AM)
crontab -e
# Add: 0 2 * * * cd /path/to/church-admin && ./scripts/daily-backup.sh >> backups/backup.log 2>&1
```

---

## Issue 9: Finance Report Double-Review Not Working

### Symptoms
- Finance report auto-approves (this should NEVER happen)

### Resolution

This is a safety-critical issue. The finance workflow has Autopilot permanently disabled.

1. Check `workflows/monthly-finance-report.md` line 10: must say `Autopilot: disabled`
2. Both 재정 담당 집사 AND 담임 목사 must review
3. If single approval is possible, stop and contact IT volunteer immediately

---

## Issue 10: Claude Code Won't Start

### Symptoms
- `claude` command not found
- Claude starts but immediately exits

### Resolution (IT Volunteer)

```bash
# Check installation
which claude
claude --version

# Check network (Claude requires internet)
ping api.anthropic.com

# Verify subscription at claude.com
```

---

## General Troubleshooting Steps

When encountering any issue:

1. **Read the error message** — it usually tells you what went wrong
2. **Run validation** — use the appropriate validation script
3. **Ask the AI** — type "도와줘" and describe the problem
4. **Contact IT volunteer** — for issues you can't resolve

### When to Contact IT Volunteer

- System won't start at all
- Permission errors that won't resolve
- Backup/restore operations
- Network or API issues
- Recurring errors after following these steps

---

## See Also

- [Installation Guide](installation-guide.md) — System setup
- [User Guide](user-guide.md) — Daily operations
- [IT Admin Guide](it-admin-guide.md) — Advanced maintenance
