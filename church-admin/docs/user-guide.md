# User Guide — Daily Operations for 행정 간사

A comprehensive guide for church administrative staff to manage daily, weekly, and monthly tasks using the Church Administration AI system. Written for non-technical users with zero CLI experience. [trace:step-1:personas]

**Target User**: 행정 간사 (김미영 persona: 한글/엑셀 능숙, CLI 경험 없음)
**IT Support**: Your church's IT volunteer handles installation and maintenance

---

## How the System Works

The Church Administration system uses AI agents to automate repetitive tasks. You interact by:

1. **Dropping files** into the `inbox/` folder (Excel, Word, images)
2. **Typing commands** in Korean (natural language)
3. **Reviewing and approving** AI-generated outputs

The AI does the heavy lifting. You make the decisions.

---

## Starting the System

Your IT volunteer will show you how to open Terminal and start the system:

```bash
cd ~/Documents/church-admin-system/church-admin
claude
```

Once started, you can type commands in Korean.

---

## Weekly Tasks

### Task 1: Generate Weekly Bulletin (주보 제작)

**When**: Every Thursday or Friday
**Time**: 10-15 minutes

#### Step 1: Update Bulletin Data

Open `data/bulletin-data.yaml` and update:
- Sermon title and scripture
- Announcements (add new, remove old)
- Hymn numbers
- Special prayer requests

#### Step 2: Generate

```
이번 주 주보 만들어줘
```

#### Step 3: Review

The AI will present the bulletin. Check each section:
- Sermon information
- Worship order
- Announcements
- Birthdays and anniversaries (automatically pulled from member records)
- This week's schedule

#### Step 4: Approve or Edit

- If correct: "주보 승인"
- If changes needed: Tell the AI what to change (e.g., "공지사항 두번째 항목 삭제해줘")

---

### Task 2: Newcomer Check (새신자 관리)

**When**: Every Monday
**Time**: 5-10 minutes

#### Check Newcomer Status

```
새신자 현황 보여줘
```

The AI will show:
- This week's new visitors
- Newcomers needing follow-up (2-week check)
- Newcomers ready for stage advancement

#### Register a New Visitor

If someone visited on Sunday:

```
새신자 등록
```

The AI will ask for:
- Name (이름)
- Phone number (전화번호)
- How they found the church (방문 경로)
- Which service they attended (참석 예배)

#### Follow Up on Overdue Contacts

```
재방문 확인 필요한 새가족 보여줘
```

---

### Task 3: Schedule Updates (일정 관리)

**When**: As needed
**Time**: 2-5 minutes per change

#### View This Week's Schedule

```
이번 주 일정 보여줘
```

#### Add a Special Event

```
특별 행사 등록: 부활절 찬양 예배, 4월 20일 오전 10시, 본당
```

The AI will check for facility conflicts and register the event.

---

## Monthly Tasks

### Task 1: Monthly Finance Report (월간 재정 보고서)

**When**: First week of each month
**Time**: 30-45 minutes (includes review time)

**Important**: Financial reports require **double review** — both the 재정 담당 집사 and 담임 목사 must approve. The AI will NOT auto-approve financial outputs.

#### Generate the Report

```
이번 달 재정 보고서 만들어줘
```

The AI will:
1. Summarize all offerings by category (십일조, 감사헌금, 특별헌금, 기타)
2. List all expenses by category (관리비, 인건비, 사역비, 선교비, 기타)
3. Compare budget vs. actual spending
4. Generate individual donation receipts (기부금영수증)

#### Review Process

1. **Your review** (행정 간사): Check amounts against church records
2. **Treasurer review** (재정 담당 집사): Verify financial accuracy
3. **Pastor approval** (담임 목사): Final sign-off

---

### Task 2: Newcomer Stage Reviews (새신자 단계 검토)

**When**: Monthly
**Time**: 15-20 minutes

Review all newcomers and advance those who meet milestones:

```
새신자 단계 현황 보여줘
```

For each newcomer ready to advance:

```
새신자 단계 변경: [이름] → [다음 단계]
```

Example: "새신자 단계 변경: 박지민 → 소그룹 연결"

---

### Task 3: Member Updates (교인 정보 갱신)

**When**: As needed
**Time**: 2-5 minutes per update

#### Search for a Member

```
교인 검색 김철수
```

#### Update Contact Information

```
교인 정보 수정: 김철수 전화번호 010-1234-5678
```

#### Process a Transfer

```
이명 처리: 김철수 전출 (사유: 이사)
```

---

## Using the Inbox Folder

The `inbox/` folder is the easiest way to get data into the system. Just drop files into the appropriate subfolder:

### Folder Structure

```
inbox/
├── documents/    ← Drop Excel/Word files here
├── images/       ← Drop namecard photos, document scans
├── templates/    ← Drop template images for scan-and-replicate
├── staging/      ← Files being processed (don't touch)
├── processed/    ← Successfully processed files
└── errors/       ← Files that couldn't be processed
```

### What Happens When You Drop Files

| File Type | Where to Drop | What Happens |
|-----------|--------------|--------------|
| Excel (.xlsx, .xls) | documents/ | Tier 1 parser extracts data → validates → imports |
| Word (.docx) | documents/ | Tier 1 parser extracts text → categorizes |
| CSV (.csv) | documents/ | Tier 1 parser reads data → validates → imports |
| Images (.jpg, .png) | images/ | Tier 2 parser recognizes text → creates records |
| PDF (.pdf) | documents/ | Tier 1 parser extracts content → categorizes |
| Template images | templates/ | Scan-and-replicate creates template.yaml |
| Unknown formats | → errors/ | Moved to errors/ with explanation |

### After Dropping Files

Start Claude and tell it to process:

```
inbox 처리해줘
```

The AI will:
1. Scan all inbox folders
2. Parse each file with the appropriate tier parser
3. Validate extracted data
4. Import into the correct data file
5. Move processed files to `inbox/processed/`
6. Move failed files to `inbox/errors/` with error description

---

## Generating Documents

### Official Letters (공문)

```
공문 작성: [수신처], [제목]
```

Example: "공문 작성: 서울노회, 2026년 통계 보고서 제출"

### Baptism Certificates (세례증서)

```
세례증서 발급: [이름], [세례 날짜]
```

### Transfer Certificates (이명증서)

```
이명증서 발급: [이름], [전출 교회]
```

### Session Resolutions (당회 결의문)

```
당회 결의문 작성: [안건]
```

### Worship Orders (예배 순서지)

```
예배 순서지 만들어줘
```

---

## Understanding AI Outputs

### Approval Levels

The system uses different approval levels based on risk:

| Task | Approval | Why |
|------|----------|-----|
| Bulletin generation | Single review (you) | Low risk — formatting only |
| Newcomer registration | Auto + your review | Medium risk — new data entry |
| Stage transitions | Your explicit approval | Medium risk — care decisions |
| Finance reports | Double review (you + treasurer + pastor) | High risk — financial data |
| Official documents | Single review (you) | Medium risk — church representation |

### What "PASS" and "FAIL" Mean

When the AI shows validation results:
- **PASS**: Data is correct and consistent
- **FAIL**: Something needs attention — the AI will explain what

If validation fails, fix the issue before proceeding. The AI will guide you.

---

## Quick Command Reference

### Bulletin (주보)

| Command | Action |
|---------|--------|
| 이번 주 주보 만들어줘 | Generate weekly bulletin |
| 주보 미리보기 | Preview current data |
| 설교 제목 변경 | Change sermon title |
| 공지사항 추가 | Add announcement |
| 주보 승인 | Approve and save bulletin |

### Newcomers (새신자/새가족)

| Command | Action |
|---------|--------|
| 새신자 등록 | Register new visitor |
| 새신자 현황 | View newcomer dashboard |
| 새신자 단계 변경 | Advance journey stage |
| 환영 메시지 작성 | Generate welcome message |
| 재방문 확인 | Check overdue follow-ups |

### Members (교인)

| Command | Action |
|---------|--------|
| 교인 검색 [이름] | Search by name |
| 교인 등록 | Register new member |
| 교인 정보 수정 | Update member info |
| 이명 처리 | Process transfer |
| 이번 주 생일 | Birthday members |
| 교인 통계 | Member statistics |

### Finance (재정)

| Command | Action |
|---------|--------|
| 재정 보고서 | Generate monthly report |
| 헌금 내역 | View offering records |
| 지출 내역 | View expense records |
| 기부금영수증 | Generate donation receipts |
| 예산 현황 | Budget vs. actual |

### Schedule (일정)

| Command | Action |
|---------|--------|
| 이번 주 일정 | View weekly schedule |
| 특별 행사 등록 | Register special event |
| 시설 예약 | Book facility |
| 예배 일정 | View worship times |

### Documents (문서)

| Command | Action |
|---------|--------|
| 공문 작성 | Write official letter |
| 세례증서 발급 | Issue baptism certificate |
| 이명증서 발급 | Issue transfer certificate |
| 당회 결의문 | Session resolution |
| 예배 순서지 | Worship order sheet |

---

## Tips for Effective Use

1. **Be specific**: "이번 주 주보 만들어줘" is better than "주보"
2. **Include details**: "공지사항 추가: 성가대 연습 시간이 토요일 오후 3시로 변경됩니다" works better than "공지 추가"
3. **Check before approving**: Always review AI outputs before approving, especially for finance
4. **Ask for help**: If unsure, type "도와줘" — the AI will explain available options
5. **Report issues**: If something looks wrong, contact your IT volunteer

---

## Need Help?

- [Quick Start Guide](quick-start.md) — First bulletin walkthrough
- [Troubleshooting Guide](troubleshooting.md) — Common issues and solutions
- Contact your IT volunteer for technical support
