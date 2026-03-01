# Installation Guide — Church Administration System

A step-by-step guide for IT volunteers (박준호 persona: developer/IT background, CLI proficient) to install and configure the Church Administration AI Agentic Workflow Automation System.

---

## Prerequisites Checklist

Before starting, verify the following are available:

| Requirement | Version | Check Command | Notes |
|-------------|---------|---------------|-------|
| Python | 3.10+ | `python3 --version` | macOS: pre-installed or `brew install python3` |
| PyYAML | latest | `pip3 install pyyaml` | Core data format library |
| openpyxl | latest | `pip3 install openpyxl` | Excel file parsing for inbox/ tier 1 |
| pandas | latest | `pip3 install pandas` | Data manipulation for reports |
| python-docx | latest | `pip3 install python-docx` | Document generation (certificates, official letters) |
| Git | 2.0+ | `git --version` | Repository management |
| Claude Code | latest | `claude --version` | AI agent runtime — requires Anthropic subscription |

### Claude Code Subscription

The system requires an active [Claude Code](https://claude.com/claude-code) subscription. This provides:
- Claude AI model access (Opus/Sonnet) for agent execution
- Hook infrastructure for validation and safety
- Sub-agent and team coordination capabilities

---

## Step 1: Clone the Repository

```bash
# Navigate to your preferred installation directory
cd ~/Documents

# Clone the repository
git clone <repository-url> church-admin-system
cd church-admin-system
```

---

## Step 2: Install Python Dependencies

```bash
# Install all required packages
pip3 install pyyaml openpyxl pandas python-docx

# Verify installations
python3 -c "import yaml; import openpyxl; import pandas; import docx; print('All dependencies OK')"
```

Expected output: `All dependencies OK`

---

## Step 3: Navigate to Church Admin Directory

```bash
cd church-admin
```

This is the primary working directory for all church administration operations.

---

## Step 4: Run Initial Setup Verification

```bash
claude --init
```

This triggers the `setup_init.py` hook which verifies:

1. **Python version** — 3.10+ confirmed
2. **Script syntax** — All 19+ hook scripts parse without errors
3. **Directory structure** — Required directories exist or are created:
   - `verification-logs/`
   - `pacs-logs/`
   - `review-logs/`
   - `autopilot-logs/`
   - `translations/`
   - `diagnosis-logs/`
4. **PyYAML availability** — Required for all data operations
5. **SOT integrity** — `state.yaml` structure validated (if present)

### Expected Output

```
Setup Init — Infrastructure Health Check
✓ Python 3.12.x
✓ 19/19 scripts OK
✓ Runtime directories OK
✓ PyYAML available
✓ SOT schema valid
```

If any check fails, the output will indicate the specific issue. See the [Troubleshooting Guide](troubleshooting.md) for resolution steps.

---

## Step 5: Verify Data Files

Confirm all seed data files exist and are valid:

```bash
# Check data file existence
ls -la data/

# Expected files:
# members.yaml       (sample member records)
# finance.yaml        (sample financial data)
# schedule.yaml       (sample worship schedule)
# newcomers.yaml      (sample newcomer records)
# bulletin-data.yaml  (bulletin configuration)
# church-glossary.yaml (church terminology reference)
```

Run P1 validation across all data files:

```bash
# Validate member data (M1-M7)
python3 .claude/hooks/scripts/validate_members.py --data-dir data/

# Validate finance data (F1-F7)
python3 .claude/hooks/scripts/validate_finance.py --data-dir data/

# Validate schedule data (S1-S6)
python3 .claude/hooks/scripts/validate_schedule.py --data-dir data/

# Validate newcomer data (N1-N6)
python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/
```

All scripts should report `X/X checks passed` with zero errors.

---

## Step 6: Verify Agent Configuration

```bash
# List all agents
ls .claude/agents/

# Expected agents:
# bulletin-generator.md
# data-ingestor.md
# document-generator.md
# finance-recorder.md
# member-manager.md
# newcomer-tracker.md
# schedule-manager.md
# template-scanner.md
```

---

## Step 7: Verify Inbox Infrastructure

```bash
# Check inbox directories
ls inbox/

# Expected subdirectories:
# documents/   — Word/PDF files for parsing
# errors/      — Invalid files quarantined here
# images/      — Namecard/document images
# processed/   — Successfully processed files
# staging/     — Files awaiting processing
# templates/   — Template images for scan-and-replicate
```

---

## Step 8: First-Run Test

Start Claude Code and verify the system responds:

```bash
claude
```

Once Claude Code starts, try a simple command:

```
주보 미리보기
```

If the NL interface is working, Claude should read `data/bulletin-data.yaml` and display the current bulletin data summary.

---

## Post-Installation Checklist

- [ ] Python 3.10+ installed and verified
- [ ] All 5 Python packages installed (pyyaml, openpyxl, pandas, python-docx)
- [ ] Repository cloned and `church-admin/` directory accessible
- [ ] `claude --init` passes all checks
- [ ] 6 data files exist in `data/`
- [ ] All P1 validation scripts pass (29/29 rules)
- [ ] 8 agent files exist in `.claude/agents/`
- [ ] 6 inbox directories exist
- [ ] Claude Code starts and responds to Korean commands

---

## Sensitive Data Warning

The following files contain personally identifiable information (PII) and are excluded from git:

- `data/members.yaml` — Member names, phone numbers, addresses
- `data/finance.yaml` — Donation records with donor names
- `data/newcomers.yaml` — Newcomer personal information

These files are listed in `.gitignore` and should NEVER be committed to a public repository. Always use the backup system (`scripts/daily-backup.sh`) to protect this data.

---

## Next Steps

- [Quick Start Guide](quick-start.md) — Generate your first bulletin in 30 minutes
- [User Guide](user-guide.md) — Daily operations for 행정 간사
- [IT Admin Guide](it-admin-guide.md) — Ongoing maintenance tasks
