# IT Admin Guide — Maintenance & Operations

A technical guide for IT volunteers (박준호 persona: developer/IT background) covering routine maintenance, backup procedures, data migration, monitoring, and system extension.

**Target User**: IT volunteer (CLI proficient, Git familiar)
**Prerequisite**: System installed per [Installation Guide](installation-guide.md)

---

## Routine Maintenance

### Daily Tasks

| Task | Command | Frequency |
|------|---------|-----------|
| Automated backup | `./scripts/daily-backup.sh` (via cron) | Daily 2 AM |
| Check backup log | `tail backups/backup.log` | Daily (visual check) |

### Weekly Tasks

| Task | Command | Frequency |
|------|---------|-----------|
| Validate all data | Run all 4 validation scripts (see below) | Weekly |
| Check inbox/errors/ | `ls inbox/errors/` | Weekly |
| Review disk usage | `du -sh backups/ data/ output/` | Weekly |

### Monthly Tasks

| Task | Command | Frequency |
|------|---------|-----------|
| Maintenance health check | `claude --maintenance` | Monthly |
| Clean old backups | Automatic (30-day retention) | Monthly verify |
| Update Claude Code | `claude update` | As available |

---

## Backup Procedures

### Automated Daily Backup

The backup system runs via cron at 2:00 AM daily:

```bash
# View current cron configuration
crontab -l

# Expected entry:
# 0 2 * * * cd /path/to/church-admin && ./scripts/daily-backup.sh >> backups/backup.log 2>&1
```

**What gets backed up**:
- All `data/*.yaml` files (members, finance, schedule, newcomers, bulletin-data, church-glossary)
- Templates directory
- Configuration files

**Retention**: Backups older than 30 days are automatically removed.

### Manual Backup

Run a backup at any time:

```bash
./scripts/daily-backup.sh
```

### Restore from Backup

```bash
# List available backups
ls backups/

# Extract a specific backup
cd backups/
tar xzf church-admin-backup-20260301_020000.tar.gz

# Copy restored files to data directory
cp -i 20260301_020000/data/*.yaml ../data/

# Validate restored data
python3 .claude/hooks/scripts/validate_members.py --data-dir data/
python3 .claude/hooks/scripts/validate_finance.py --data-dir data/
python3 .claude/hooks/scripts/validate_schedule.py --data-dir data/
python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/
```

**Important**: Always validate data after restoration to ensure consistency.

---

## Data Validation Suite

Run the full P1 validation suite to verify data integrity:

```bash
# Member data (M1-M7: ID format, required fields, phone, status enum, family refs, dates, stats)
python3 .claude/hooks/scripts/validate_members.py --data-dir data/

# Finance data (F1-F5: ID format, KRW integers, category enum, dates, budget refs)
python3 .claude/hooks/scripts/validate_finance.py --data-dir data/

# Schedule data (S1-S5: ID format, time format, recurrence, status enum, facility overlap)
python3 .claude/hooks/scripts/validate_schedule.py --data-dir data/

# Newcomer data (N1-N6: ID format, stage/milestones, contact, shepherd refs, dates, stats)
python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/

# Bulletin data (B1-B3: structure, VR references, generation history)
python3 .claude/hooks/scripts/validate_bulletin.py --data-dir data/
```

All scripts output JSON with `summary: "N/N checks passed"`. Any failures include specific error descriptions.

---

## Data Migration from Existing ChMS

### From Excel/Spreadsheet

1. **Prepare Excel files** with columns matching the system's field structure:
   - Members: id, name, phone, birth_date, role, status, registration_date
   - Finance: offering_id, donor_id, amount, category, date
   - Newcomers: id, name, phone, visit_date, journey_stage

2. **Drop files** into `inbox/documents/`

3. **Process**: Start Claude and run "inbox 처리해줘"

4. **Validate**: Run the validation suite to ensure imported data is correct

### From Another Church Management System

1. **Export data** from existing system as CSV or Excel
2. **Map fields** to match this system's schema (see `planning/data-architecture-spec.md`)
3. **Import** via inbox or manual YAML editing
4. **Validate** all data after import

### Manual Data Entry

For small datasets, edit YAML files directly:

```yaml
# data/members.yaml — add a new member
members:
  - id: "MBR-2026-012"          # Unique ID: MBR-YYYY-NNN
    name: "새교인이름"
    phone: "010-1234-5678"       # Korean mobile: 010-NNNN-NNNN
    birth_date: "1990-01-15"     # YYYY-MM-DD
    role: "member"               # member, deacon, elder, pastor
    status: "active"             # active, inactive, transferred, deceased
    registration_date: "2026-03-01"
```

Always run validation after manual edits.

---

## System Monitoring

### Health Check

```bash
# Infrastructure verification
claude --init

# Periodic health check
claude --maintenance
```

### Common Indicators

| Indicator | Healthy | Action if Unhealthy |
|-----------|---------|---------------------|
| Validation scripts: N/N pass | All pass | Fix data per error message |
| inbox/errors/ empty | No files | Check and reprocess files |
| Backup log shows success | Recent timestamp | Check cron, disk space |
| Data files > 0 bytes | All exist | Restore from backup |

---

## Security Considerations

### Sensitive Data

These files contain PII and are excluded from git:

| File | Contains | Protection |
|------|----------|------------|
| data/members.yaml | Names, phones, addresses | .gitignore |
| data/finance.yaml | Donation records, amounts | .gitignore |
| data/newcomers.yaml | Visitor personal info | .gitignore |

### Access Control

- **Agent write permissions**: Each agent can only write to its designated data file
  - `member-manager` → `data/members.yaml`
  - `finance-recorder` → `data/finance.yaml`, `output/finance-reports/`, `certificates/receipts/`
  - `schedule-manager` → `data/schedule.yaml`
  - `newcomer-tracker` → `data/newcomers.yaml`
  - `bulletin-generator` → `data/bulletin-data.yaml`

- **SOT write restriction**: Only the orchestrator can modify `state.yaml`

- **Finance safety**: Autopilot is permanently disabled for finance workflows. Double human review required.

### Backup Security

- Backups are stored locally in `backups/`
- Consider encrypting backups if stored off-site:

```bash
# Encrypt a backup
gpg -c backups/church-admin-backup-20260301.tar.gz

# Decrypt when needed
gpg -d backups/church-admin-backup-20260301.tar.gz.gpg > restored-backup.tar.gz
```

---

## Adding New Features

### Using Workflow Generator

The system can be extended with new workflows using the `workflow-generator` skill:

```bash
claude
```

Then:
```
새 워크플로우 만들어줘: [feature description]
```

The workflow generator will:
1. Analyze requirements
2. Design the workflow structure (Research → Planning → Implementation)
3. Generate workflow.md with inherited DNA from the parent system
4. Create necessary agent definitions
5. Set up validation rules

### Adding New Data Fields

1. **Update schema**: Modify the relevant `.yaml` data file
2. **Update validation**: Add new rules to the appropriate validation script
3. **Update agents**: Modify agent definitions to handle new fields
4. **Test**: Run validation to ensure consistency

### Adding New Templates

1. **Scan existing template**: Drop a template image into `inbox/templates/`
2. **Or create manually**: Add a new `.yaml` file in `templates/`
3. **Register in workflow**: Update the document-generator workflow if needed
4. **Validate**: Ensure template fields match data schema

---

## Troubleshooting for IT Volunteers

### Debug Commands

```bash
# Check Python environment
python3 --version
pip3 list | grep -E "pyyaml|openpyxl|pandas|docx"

# Validate all data
for script in validate_members validate_finance validate_schedule validate_newcomers; do
    echo "=== $script ==="
    python3 .claude/hooks/scripts/${script}.py --data-dir data/
done

# Check file permissions
ls -la data/ inbox/ scripts/

# Check disk usage
du -sh backups/ data/ output/ bulletins/

# View recent backup log
tail -20 backups/backup.log
```

### Common IT Issues

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| Script import error | `python3 -c "import yaml"` | `pip3 install pyyaml` |
| Permission denied | `ls -la data/` | `chmod 644 data/*.yaml` |
| Cron not running | `crontab -l` | Add cron entry |
| Disk full | `df -h` | Clean old backups, output files |
| Git merge conflicts | `git status` | Resolve conflicts in non-PII files only |

---

## Architecture Reference

For detailed system architecture, see:
- `planning/system-architecture.md` (project root) — Full system design
- `planning/data-architecture-spec.md` (project root) — Data schema specifications
- `workflows/` — All workflow definitions

### Directory Structure

```
church-admin/
├── data/                    ← YAML data files (PII — gitignored)
├── inbox/                   ← File drop zone (6 subdirectories)
├── scripts/                 ← Parsers and backup script
├── templates/               ← Document templates (4 YAML files)
├── workflows/               ← Workflow definitions (5 + translations)
├── output/                  ← Generated outputs
│   ├── documents/           ← Official letters, certificates
│   └── finance-reports/     ← Monthly reports, receipts
├── bulletins/               ← Generated bulletins
├── backups/                 ← Timestamped backup archives
├── docs/                    ← This documentation
└── .claude/
    ├── agents/              ← 8 AI agent definitions
    ├── hooks/scripts/       ← Validation and safety scripts
    └── skills/              ← NL interface skill
```

---

## See Also

- [Installation Guide](installation-guide.md) — Initial setup
- [Quick Start Guide](quick-start.md) — First bulletin
- [User Guide](user-guide.md) — Daily operations for 행정 간사
- [Troubleshooting Guide](troubleshooting.md) — Common issues
