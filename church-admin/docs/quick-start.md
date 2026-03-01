# Quick Start Guide — First Bulletin in 30 Minutes

This guide walks you through generating your first weekly bulletin using the Church Administration system. Target: complete the entire process within 30 minutes, from data entry to final bulletin output. [trace:step-1:personas]

**Target User**: 행정 간사 (with IT volunteer assistance for first run)
**Prerequisite**: Installation complete (see [Installation Guide](installation-guide.md))

---

## Overview

```
Prepare Data (10 min) → Start Claude (2 min) → Generate Bulletin (5 min) → Review & Approve (10 min) → Done!
```

---

## Phase 1: Prepare This Week's Data (10 minutes)

### 1.1 Update Sermon Information

Open `data/bulletin-data.yaml` in any text editor and update the sermon section:

```yaml
sermon:
  title: "은혜의 능력"           # This week's sermon title
  scripture: "에베소서 2:8-10"    # Bible passage
  pastor: "이성훈"               # Preaching pastor
```

### 1.2 Update Announcements

In the same file, update the announcements section:

```yaml
announcements:
  - title: "수요예배 안내"
    content: "이번 주 수요예배는 오후 7시 30분에 진행됩니다."
  - title: "교회 소풍"
    content: "5월 첫째 주 토요일 교회 소풍이 있습니다. 참가 신청서를 제출해주세요."
```

### 1.3 Update Hymn Numbers

```yaml
hymns:
  opening: 21         # Opening hymn number
  offertory: 94       # Offertory hymn number
  closing: 370        # Closing hymn number
```

### 1.4 Save the File

Save `data/bulletin-data.yaml`. The system will automatically:
- Pull birthday/anniversary members from `data/members.yaml`
- Include this week's schedule from `data/schedule.yaml`
- Generate newcomer summary from `data/newcomers.yaml`

---

## Phase 2: Start Claude Code (2 minutes)

### 2.1 Open Terminal

Open the Terminal application (IT volunteer should have set this up).

### 2.2 Navigate to Project

```bash
cd ~/Documents/church-admin-system/church-admin
```

### 2.3 Start Claude Code

```bash
claude
```

Wait for Claude to initialize. You should see a prompt indicating the system is ready.

---

## Phase 3: Generate the Bulletin (5 minutes)

### 3.1 Issue the Command

Type in Korean:

```
이번 주 주보 만들어줘
```

Claude will:
1. Read `data/bulletin-data.yaml` for sermon info, announcements, hymns
2. Read `data/members.yaml` for this week's birthdays and anniversaries
3. Read `data/schedule.yaml` for worship times and special events
4. Read `data/newcomers.yaml` for newcomer count
5. Assemble all 16 variable regions (VR-BUL-01 through VR-BUL-16)
6. Apply the bulletin template (`templates/bulletin-template.yaml`)
7. Generate the bulletin Markdown file

### 3.2 Wait for Generation

The process takes 1-3 minutes. Claude will show progress as it assembles each section.

---

## Phase 4: Review and Approve (10 minutes)

### 4.1 Review the Output

Claude will present the generated bulletin for your review. Check:

- [ ] Sermon title and scripture are correct
- [ ] Pastor name is correct
- [ ] Hymn numbers match your selection
- [ ] Announcements are accurate and complete
- [ ] Birthday/anniversary members are correct (check against your records)
- [ ] Worship times are correct
- [ ] Special events are listed
- [ ] Newcomer welcome section is appropriate

### 4.2 Request Changes (if needed)

If something needs correction, tell Claude in Korean:

```
설교 제목을 "새 생명의 약속"으로 변경해줘
```

or

```
공지사항에 "성가대 연습 시간 변경: 토요일 오후 3시" 추가해줘
```

### 4.3 Approve the Bulletin

When everything looks good:

```
주보 승인
```

The bulletin will be saved to the `bulletins/` directory with a timestamp.

---

## Phase 5: Output (3 minutes)

### 5.1 Find Your Bulletin

The generated bulletin is saved as a Markdown file:

```bash
ls bulletins/
# bulletin-2026-03-01.md (example)
```

### 5.2 Convert for Printing (Optional)

If you need to convert to PDF or Word:
- Open the `.md` file in any Markdown editor
- Export to PDF for printing
- Or copy-paste into your church's existing word processor template

---

## Congratulations!

You have generated your first bulletin. The entire process should have taken approximately 20-30 minutes.

### What Happens Next Week?

The process gets faster each time:

| Week | Estimated Time | Why |
|------|---------------|-----|
| 1st bulletin | 30 minutes | Learning the system |
| 2nd bulletin | 15 minutes | Familiar with data entry |
| 3rd+ bulletin | 10 minutes | Only updating changed fields |

### Regular Weekly Workflow

Every week, you only need to:
1. Update sermon info and announcements in `data/bulletin-data.yaml` (5 min)
2. Run `이번 주 주보 만들어줘` (2 min)
3. Review and approve (3 min)

The system handles everything else automatically — birthdays, schedules, newcomer counts, and formatting.

---

## Quick Reference: Common Commands

| What You Want | What to Say |
|--------------|-------------|
| Generate bulletin | "이번 주 주보 만들어줘" |
| Preview current data | "주보 미리보기" |
| Change sermon title | "설교 제목 변경" |
| Add announcement | "공지사항 추가" |
| View past bulletins | "지난 주보 보여줘" |
| Check member birthdays | "이번 주 생일 대상" |

---

## Need Help?

- [User Guide](user-guide.md) — Complete daily operations reference
- [Troubleshooting Guide](troubleshooting.md) — Common issues and solutions
- Ask your IT volunteer (박준호) for technical assistance
