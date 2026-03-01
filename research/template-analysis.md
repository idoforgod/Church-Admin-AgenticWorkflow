# Church Document Template Analysis
## Scan-and-Replicate System — Comprehensive Template Reference

**Generated**: 2026-02-28
**Purpose**: Step 2 analysis of all 7 church document templates for the scan-and-replicate pipeline
**Sources**: PRD.md §5.1 F-06, domain-analysis.md, Korean church document conventions
**Audience**: template-scanner agent, pipeline-design agent (Step 5)

---

## 1. Executive Summary

This document provides a comprehensive analysis of the 7 document types targeted by the scan-and-replicate system (PRD §5.1 F-06). For each document type, we identify fixed regions (church identity anchors that do not change between generations), variable regions (data-driven slots populated from YAML sources), a complete YAML template schema, and a precise data source mapping from every variable slot to its originating field.

### 1.1 Document Type Overview

| # | Document Type | Korean Name | Frequency | Priority Tier | Primary Data Sources |
|---|---------------|-------------|-----------|---------------|----------------------|
| 1 | Bulletin | 주보 | Weekly | **Tier A** | bulletin-data.yaml, schedule.yaml, members.yaml |
| 2 | Receipt | 헌금 영수증 | Annual bulk | **Tier A** | finance.yaml, members.yaml |
| 3 | Worship Order | 예배 순서지 | Weekly | **Tier A** | schedule.yaml, bulletin-data.yaml |
| 4 | Official Letter | 공문 | 2–5×/month | **Tier B** | members.yaml, schedule.yaml, church-state.yaml |
| 5 | Meeting Minutes | 당회/제직회 회의록 | 1–4×/month | **Tier B** | members.yaml, church-state.yaml |
| 6 | Certificate | 세례증서/이명증서 | 2–4×/year | **Tier B** | members.yaml |
| 7 | Invitation | 초청장 | Ad-hoc | **Tier C** | schedule.yaml, members.yaml |

### 1.2 Scan-and-Replicate Pipeline Summary

The scan-and-replicate system (F-06) operates in four stages for all document types:

```
Stage 1 — Image/PDF Upload
  inbox/templates/{category}-sample.{jpg|pdf}

Stage 2 — Claude Multimodal Analysis
  Fixed region detection (anchors: church name, logo, seal, denomination header)
  Variable region detection (data slots: date, content, recipient, amounts)
  Layout extraction (grid, columns, font zones)

Stage 3 — Template Generation
  {category}-template.yaml  (machine-processable structure)
  {category}-output.md      (human-readable output format)

Stage 4 — Human Confirmation + Iterative Generation
  First-run: human verifies structure and variable slots
  Subsequent: fully automatic with data injection from YAML sources
```

### 1.3 Key Design Decisions

1. **Fixed vs Variable Classification**: Fixed regions are detected by consistency across multiple sample scans. If the same text/image appears in the same position across 3+ samples, it is classified as fixed.
2. **Slot Typing**: Every variable slot is typed (string, date, currency, integer, list, boolean) to enable P1 validation at generation time.
3. **Data Source Traceability**: Every variable slot specifies the exact YAML file + field path, enabling automated population and validation.
4. **Denomination Variants**: Templates include denomination-specific branches for the 3 major Korean Protestant denominations: 예장통합 (Presbyterian Church of Korea), 예장합동 (Presbyterian Church in Korea), 기감 (Korean Methodist Church).

---

## 2. Document Type Analysis

---

### 2.1 Bulletin (주보 — Weekly Church Bulletin)

#### Overview

The 주보 (bulletin) is the most frequently produced document in Korean churches — generated every Sunday without exception. It serves as the week's information hub: sermon details, worship order, announcements, prayer topics, and member celebrations. A typical bulletin is A4 (sometimes B5 folded to create a 4-page booklet) and printed in quantities equal to congregation size plus 20% buffer.

The bulletin has the highest scan-and-replicate ROI: it is produced 52 times per year, its structure is highly consistent week-to-week, and the only meaningful changes are in the variable data slots. Once a template is extracted from a sample scan, subsequent generations require zero manual layout work.

#### Fixed Regions

Fixed regions are areas that appear identically in every bulletin of a given church, regardless of date or content.

| Region ID | Region Name | Korean Name | Position (typical) | Content Description |
|-----------|-------------|-------------|-------------------|---------------------|
| FR-BUL-01 | Church Name Banner | 교회명 배너 | Top center, full width | Full official church name in large font (바탕체 or 굴림체, 24–36pt) |
| FR-BUL-02 | Church Logo / Cross Symbol | 교회 로고/십자가 | Top left or top center-left | Church logo image or stylized cross. Position varies by church but is consistent within a church |
| FR-BUL-03 | Denomination Header | 교단 명칭 | Below church name or top-right corner | Denomination affiliation text (e.g., "대한예수교장로회 [노회명]" or "기독교대한감리회") |
| FR-BUL-04 | Bulletin Title Label | 주보 제목 라벨 | Below church name | The word "주 보" (spaced for formality) or "주간안내" in fixed typography |
| FR-BUL-05 | Church Address Block | 교회 주소 블록 | Footer area | Church street address, phone number, website, email. Printed in small font (8–10pt) |
| FR-BUL-06 | Decorative Border / Frame | 장식 테두리 | Outer margin | Thin single or double line frame around the entire page. Common in traditional churches |
| FR-BUL-07 | Section Header Labels | 섹션 제목 | Left margin or inline | Fixed section titles: "말씀" (The Word), "공지사항" (Announcements), "기도제목" (Prayer Requests), "이번주 행사" (This Week's Events) |

#### Variable Regions

Variable regions change with each bulletin generation and are populated from YAML data sources.

| Region ID | Region Name | Korean Name | Slot Type | Position | Notes |
|-----------|-------------|-------------|-----------|----------|-------|
| VR-BUL-01 | Issue Number | 발행 번호 | integer | Near bulletin title | Format: "제 NNN호" (Issue No. NNN) |
| VR-BUL-02 | Date | 날짜 | date | Below issue number | Format: "2026년 3월 1일 주일" — includes day-of-week "주일" |
| VR-BUL-03 | Sermon Title | 설교 제목 | string | Prominent, center or upper body | Often in large font, sometimes boxed |
| VR-BUL-04 | Scripture Reference | 성경 본문 | string | Adjacent to sermon title | Format: "요한복음 3:16" or "요 3:16" |
| VR-BUL-05 | Preacher Name | 설교자 | string | Below scripture | Format: "담임목사 [이름]" or just "[이름] 목사" |
| VR-BUL-06 | Sermon Series | 설교 시리즈 | string (nullable) | Above sermon title | Format: "시리즈 N부: [시리즈명]" |
| VR-BUL-07 | Worship Order Items | 예배 순서 | list[object] | Left column or center | Numbered list: 순서번호, 항목명, 담당자/찬송가번호 |
| VR-BUL-08 | Hymn Numbers | 찬송가 번호 | list[integer] | Within worship order | References to 찬송가 (Korean hymnal) by number |
| VR-BUL-09 | Announcements | 공지사항 | list[object] | Body section | Each: title + brief content. Variable count (0–10 items) |
| VR-BUL-10 | Prayer Requests | 기도 제목 | list[object] | Body section | Each: category + content. Standard categories: 교회, 국가, 선교, 교인 |
| VR-BUL-11 | Birthday Members | 생일자 | list[string] | Small box or sidebar | Format: "○○○ 성도 (N월 N일)" — partial name privacy masking common |
| VR-BUL-12 | Wedding Anniversaries | 결혼기념일 | list[string] | Same box as birthdays | Format: "○○○, ○○○ 집사 부부 (N월 N일)" |
| VR-BUL-13 | This Week Events | 이번 주 행사 | list[object] | Sidebar or footer section | Date + event name + time + location |
| VR-BUL-14 | Next Week Preview | 다음 주 예고 | string (nullable) | Footer area | Brief preview of next Sunday sermon or event |
| VR-BUL-15 | Offering Team | 헌금 봉사자 | list[string] | Small sidebar | Names of the week's offering deacons/volunteers |
| VR-BUL-16 | Attendance Statistics | 출석 통계 | object (nullable) | Small table or footer | Prior week's attendance by service and total |

#### YAML Template Schema

```yaml
# bulletin-template.yaml
# Generated by template-scanner agent from inbox/templates/bulletin-sample.jpg
# Human-confirmed: [YYYY-MM-DD]

template_id: "bulletin-v1"
document_type: "bulletin"
version: "1.0"
church_name: "{{ church_state.church.name }}"
denomination: "{{ church_state.church.denomination }}"
scan_source: "inbox/templates/bulletin-sample.jpg"
confirmed_by: null  # set after human confirmation
confirmed_date: null

paper:
  size: "A4"              # A4 (210×297mm) most common; B5 for folded booklets
  orientation: "portrait"
  pages: 2                # 1 sheet front+back = 2 logical pages; 1 for single-sided
  folds: 0                # 0=flat, 1=half-fold (creates 4 logical pages from 2)

layout:
  margins:
    top_mm: 15
    bottom_mm: 15
    left_mm: 15
    right_mm: 15
  columns: 2              # most bulletins use 2-column layout
  column_gap_mm: 8

fixed_regions:
  - id: "FR-BUL-01"
    name: "church_name_banner"
    position: { top_mm: 5, left_mm: 0, width_pct: 100, height_mm: 20 }
    content: "{{ church_state.church.name }}"
    font: { family: "바탕체", size_pt: 28, weight: "bold", align: "center" }

  - id: "FR-BUL-02"
    name: "church_logo"
    position: { top_mm: 3, left_mm: 5, width_mm: 25, height_mm: 25 }
    content_type: "image"
    image_path: "assets/church-logo.png"

  - id: "FR-BUL-03"
    name: "denomination_header"
    position: { top_mm: 2, left_mm: 0, width_pct: 100, height_mm: 6 }
    content: "{{ church_state.church.denomination_full_name }}"
    font: { family: "굴림체", size_pt: 9, weight: "normal", align: "center" }

  - id: "FR-BUL-04"
    name: "bulletin_title_label"
    position: { top_mm: 26, left_mm: 0, width_pct: 100, height_mm: 10 }
    content: "주  보"
    font: { family: "바탕체", size_pt: 18, weight: "bold", align: "center" }

  - id: "FR-BUL-05"
    name: "church_address_block"
    position: { top_mm: 280, left_mm: 0, width_pct: 100, height_mm: 12 }
    content: "{{ church_state.church.address }} | TEL: {{ church_state.church.phone }}"
    font: { family: "굴림체", size_pt: 8, weight: "normal", align: "center" }

  - id: "FR-BUL-06"
    name: "decorative_border"
    type: "border"
    style: "single_line"
    margin_from_edge_mm: 3

variable_regions:
  - id: "VR-BUL-01"
    name: "issue_number"
    slot_type: "integer"
    position: { top_mm: 37, left_mm: 120, width_mm: 70, height_mm: 7 }
    format: "제 {value}호"
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.issue_number"
    validation: { min: 1, monotonically_increasing: true }

  - id: "VR-BUL-02"
    name: "bulletin_date"
    slot_type: "date"
    position: { top_mm: 37, left_mm: 0, width_mm: 110, height_mm: 7 }
    format: "{year}년 {month}월 {day}일 주일"
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.date"
    validation: { format: "YYYY-MM-DD", day_of_week: "sunday" }

  - id: "VR-BUL-03"
    name: "sermon_title"
    slot_type: "string"
    position: { top_mm: 50, left_mm: 0, width_pct: 100, height_mm: 12 }
    font: { family: "바탕체", size_pt: 16, weight: "bold", align: "center" }
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.sermon.title"
    validation: { min_length: 1, max_length: 60 }

  - id: "VR-BUL-04"
    name: "scripture_reference"
    slot_type: "string"
    position: { top_mm: 63, left_mm: 0, width_pct: 100, height_mm: 7 }
    font: { family: "굴림체", size_pt: 12, align: "center" }
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.sermon.scripture"
    validation: { min_length: 3, max_length: 40 }

  - id: "VR-BUL-05"
    name: "preacher_name"
    slot_type: "string"
    position: { top_mm: 71, left_mm: 0, width_pct: 100, height_mm: 7 }
    format: "설교 {value} 목사"
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.sermon.preacher"

  - id: "VR-BUL-06"
    name: "sermon_series"
    slot_type: "string"
    nullable: true
    position: { top_mm: 45, left_mm: 0, width_pct: 100, height_mm: 6 }
    format: "[ {value} ]"
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.sermon.series"

  - id: "VR-BUL-07"
    name: "worship_order"
    slot_type: "list[object]"
    position: { top_mm: 80, left_col: 0, width_col: 1, height_mm: 80 }
    item_height_mm: 8
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.worship_order"
    item_format: "{order}. {item}  {detail}  {performer}"
    validation: { min_items: 3 }

  - id: "VR-BUL-09"
    name: "announcements"
    slot_type: "list[object]"
    position: { top_mm: 165, left_col: 0, width_col: 2, height_mm: 60 }
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.announcements"
    item_format: "◆ {title}: {content}"
    filter: "priority != 'low' and expires >= bulletin.date"
    validation: { max_items: 8 }

  - id: "VR-BUL-10"
    name: "prayer_requests"
    slot_type: "list[object]"
    position: { top_mm: 230, left_col: 0, width_col: 2, height_mm: 40 }
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.prayer_requests"
    item_format: "• [{category}] {content}"
    validation: { min_items: 1 }

  - id: "VR-BUL-11"
    name: "birthday_members"
    slot_type: "list[string]"
    position: { top_mm: 165, left_col: 1, width_mm: 80, height_mm: 25 }
    data_source:
      file: "members.yaml"
      field: "members[*]"
      filter: "birth_date matches this_week_month_day and status == 'active'"
      transform: "mask_name_middle_char(name) + ' 성도 (' + format(birth_date, 'M월 d일') + ')'"
    nullable: true

  - id: "VR-BUL-12"
    name: "wedding_anniversaries"
    slot_type: "list[string]"
    position: { top_mm: 192, left_col: 1, width_mm: 80, height_mm: 20 }
    data_source:
      file: "members.yaml"
      field: "members[*]"
      filter: "family.relation == 'household_head' and family.wedding_anniversary matches this_week_month_day"
      transform: "family_display_names + ' 부부 (' + format(anniversary, 'M월 d일') + ')'"
    nullable: true

  - id: "VR-BUL-15"
    name: "offering_team"
    slot_type: "list[string]"
    position: { top_mm: 215, left_col: 1, width_mm: 80, height_mm: 15 }
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.offering_team"

output_format:
  type: "markdown"
  output_path_template: "bulletins/{date}-bulletin.md"
  pdf_ready: false  # PDF conversion deferred to Phase 2
```

#### Data Source Mapping

| Variable Slot | YAML File | Field Path | Transform | Validation |
|---------------|-----------|------------|-----------|------------|
| Issue Number | `bulletin-data.yaml` | `bulletin.issue_number` | Format as "제 N호" | integer ≥ 1, monotonically increasing |
| Date | `bulletin-data.yaml` | `bulletin.date` | Format as "YYYY년 MM월 DD일 주일" | YYYY-MM-DD, must be Sunday |
| Sermon Title | `bulletin-data.yaml` | `bulletin.sermon.title` | None | string, 1–60 chars |
| Scripture | `bulletin-data.yaml` | `bulletin.sermon.scripture` | None | string, 3–40 chars |
| Preacher | `bulletin-data.yaml` | `bulletin.sermon.preacher` | Append " 목사" | string |
| Series | `bulletin-data.yaml` | `bulletin.sermon.series` | Wrap in brackets | string, nullable |
| Worship Order | `bulletin-data.yaml` | `bulletin.worship_order[*]` | Format each item | list, min 3 items |
| Announcements | `bulletin-data.yaml` | `bulletin.announcements[*]` | Filter by priority, date | list, max 8 |
| Prayer Requests | `bulletin-data.yaml` | `bulletin.prayer_requests[*]` | Group by category | list, min 1 |
| Birthday Members | `members.yaml` | `members[*]` | Filter by birth month-day = this week; mask middle char of name | list, nullable |
| Wedding Anniversaries | `members.yaml` | `members[*].family` | Filter by anniversary month-day = this week | list, nullable |
| Offering Team | `bulletin-data.yaml` | `bulletin.offering_team[*]` | None | list[string] |

---

### 2.2 Receipt (헌금 영수증 — Tax Donation Receipt)

#### Overview

The 헌금 영수증 (tax donation receipt) is a legally significant document in Korea. Under 소득세법 시행령 §80①5호, churches are obligated to issue official donation receipts upon member request, which members use for year-end tax deductions. A typical mid-size church (250 members) issues 100–200 receipts per year, predominantly in a year-end bulk run (December–January).

The receipt must carry specific legally required fields: donor full name, donor ID number (or partial), church registration number, donation amount (in Korean 원 and in Korean numeral notation), the period, and the church official seal (직인). The scan-and-replicate template must accurately capture the seal position as a fixed anchor — AI generation must not place variable content over the seal zone.

#### Fixed Regions

| Region ID | Region Name | Korean Name | Position (typical) | Content Description |
|-----------|-------------|-------------|-------------------|---------------------|
| FR-RCP-01 | Receipt Title | 영수증 제목 | Top center | "기부금영수증" or "헌금영수증" in large font (바탕체, 20–24pt) |
| FR-RCP-02 | Church Name | 교회명 (발행기관) | Upper body | Full official church name as the issuing organization |
| FR-RCP-03 | Church Registration Number | 교회 등록번호 | Below church name | Government registration number (사업자등록번호 or 고유번호) |
| FR-RCP-04 | Church Address | 교회 주소 | Below registration | Full mailing address of the church |
| FR-RCP-05 | Representative Name | 대표자명 | Issuer block | Senior pastor's name as the legal representative |
| FR-RCP-06 | Seal Position Zone | 직인 위치 | Bottom-right of issuer block | Reserved zone for the official church seal (직인). No variable content allowed in this zone. |
| FR-RCP-07 | Receipt Type Label | 영수증 유형 라벨 | Header | "종교단체" (religious organization) category label |
| FR-RCP-08 | Legal Basis Text | 법적 근거 문구 | Footer | Standardized legal text referencing 소득세법 §34 and 시행령 §80 |
| FR-RCP-09 | Consecutive Number Label | 일련번호 라벨 | Header right | Fixed label "No." — the number itself is variable |

#### Variable Regions

| Region ID | Region Name | Korean Name | Slot Type | Notes |
|-----------|-------------|-------------|-----------|-------|
| VR-RCP-01 | Receipt Number | 영수증 번호 | string | Sequential: "YYYY-NNN" format |
| VR-RCP-02 | Issue Date | 발행일 | date | Date of receipt generation |
| VR-RCP-03 | Donor Full Name | 기부자 성명 | string | Full Korean name of the member |
| VR-RCP-04 | Donor ID Number | 주민등록번호 | string | Full 13-digit or masked "XXXXXX-X\*\*\*\*\*\*" for privacy |
| VR-RCP-05 | Donor Address | 기부자 주소 | string | Member's home address (nullable — some receipts omit) |
| VR-RCP-06 | Donation Period | 기부 기간 | date_range | "YYYY년 1월 1일 ~ YYYY년 12월 31일" for annual receipts |
| VR-RCP-07 | Donation Amount (numeric) | 기부금액 (숫자) | currency | Integer, KRW. Format: "₩1,234,000" or "1,234,000원" |
| VR-RCP-08 | Donation Amount (Korean numeral) | 기부금액 (한글) | string | Korean numeral form: "금 일백이십삼만사천원정" (법정 기재 방식) |
| VR-RCP-09 | Donation Category | 헌금 구분 | string | "십일조", "감사헌금", "일반헌금", or combined |
| VR-RCP-10 | Purpose Designation | 용도 지정 | string (nullable) | Specific purpose if designated gift |
| VR-RCP-11 | Representative Signature | 대표자 서명란 | string | "위와 같이 영수합니다. [이름] (인)" — the "(인)" marks seal placement |

#### YAML Template Schema

```yaml
# receipt-template.yaml
template_id: "receipt-v1"
document_type: "receipt"
version: "1.0"
scan_source: "inbox/templates/receipt-form.jpg"
confirmed_by: null
confirmed_date: null

paper:
  size: "A4"
  orientation: "portrait"
  pages: 1
  copies: 2    # donor copy + church archive copy (common practice)

legal:
  basis: "소득세법 제34조, 같은 법 시행령 제80조 제1항 제5호"
  issuer_type: "종교단체"
  registration_number_field: "church_state.church.registration_number"

fixed_regions:
  - id: "FR-RCP-01"
    name: "receipt_title"
    content: "기 부 금 영 수 증"
    font: { family: "바탕체", size_pt: 22, weight: "bold", align: "center" }
    position: { top_mm: 20, left_mm: 0, width_pct: 100, height_mm: 12 }

  - id: "FR-RCP-02"
    name: "church_name_issuer"
    content: "{{ church_state.church.name }}"
    font: { family: "바탕체", size_pt: 14, weight: "bold" }
    position: { top_mm: 38, left_mm: 15, width_mm: 120, height_mm: 8 }

  - id: "FR-RCP-03"
    name: "registration_number"
    content: "고유번호: {{ church_state.church.registration_number }}"
    font: { family: "굴림체", size_pt: 10 }
    position: { top_mm: 47, left_mm: 15, width_mm: 120, height_mm: 7 }

  - id: "FR-RCP-04"
    name: "church_address"
    content: "{{ church_state.church.address }}"
    font: { family: "굴림체", size_pt: 10 }
    position: { top_mm: 55, left_mm: 15, width_mm: 150, height_mm: 7 }

  - id: "FR-RCP-05"
    name: "representative_name_label"
    content: "대표자: {{ church_state.church.representative }}"
    font: { family: "굴림체", size_pt: 10 }
    position: { top_mm: 63, left_mm: 15, width_mm: 100, height_mm: 7 }

  - id: "FR-RCP-06"
    name: "seal_zone"
    content_type: "reserved_seal_zone"
    # CRITICAL: This zone must remain empty of variable content.
    # The physical church seal (직인) is affixed here during printing.
    position: { top_mm: 58, right_mm: 15, width_mm: 35, height_mm: 20 }
    guard: "NO_VARIABLE_CONTENT"

  - id: "FR-RCP-08"
    name: "legal_basis_footer"
    content: "위 금액을 {{ legal.basis }}에 의하여 기부금으로 영수합니다."
    font: { family: "굴림체", size_pt: 9 }
    position: { top_mm: 255, left_mm: 10, width_pct: 90, height_mm: 10 }

variable_regions:
  - id: "VR-RCP-01"
    name: "receipt_number"
    slot_type: "string"
    format: "No. {year}-{seq:03d}"
    data_source:
      derived: true
      rule: "YYYY + '-' + zero_padded_sequence_within_year"
    position: { top_mm: 20, right_mm: 15, width_mm: 60, height_mm: 7 }

  - id: "VR-RCP-02"
    name: "issue_date"
    slot_type: "date"
    format: "{year}년 {month}월 {day}일"
    data_source:
      derived: true
      rule: "generation_date"
    position: { top_mm: 28, right_mm: 15, width_mm: 80, height_mm: 7 }

  - id: "VR-RCP-03"
    name: "donor_name"
    slot_type: "string"
    data_source:
      file: "members.yaml"
      field: "members[id={member_id}].name"
    position: { top_mm: 90, left_mm: 50, width_mm: 80, height_mm: 8 }
    validation: { min_length: 2, max_length: 10 }

  - id: "VR-RCP-04"
    name: "donor_id_number"
    slot_type: "string"
    data_source:
      file: "members.yaml"
      field: "members[id={member_id}].resident_number"
    masking: "XXXXXX-X******"   # mask last 6 digits for privacy
    position: { top_mm: 90, left_mm: 140, width_mm: 60, height_mm: 8 }

  - id: "VR-RCP-06"
    name: "donation_period"
    slot_type: "date_range"
    format: "{year}년 1월 1일 ~ {year}년 12월 31일"
    data_source:
      derived: true
      rule: "fiscal_year start and end from finance.yaml.year"
    position: { top_mm: 110, left_mm: 50, width_mm: 140, height_mm: 8 }

  - id: "VR-RCP-07"
    name: "donation_amount_numeric"
    slot_type: "currency"
    format: "₩{amount:,}"
    data_source:
      file: "finance.yaml"
      field: "offerings[*]"
      filter: "member_id == {member_id} and year == {year} and void == false"
      aggregate: "sum(items[*].amount)"
    position: { top_mm: 130, left_mm: 100, width_mm: 90, height_mm: 10 }
    font: { family: "바탕체", size_pt: 14, weight: "bold" }
    validation: { min: 1, integer: true }

  - id: "VR-RCP-08"
    name: "donation_amount_korean_numeral"
    slot_type: "string"
    format: "금 {korean_numeral}원정"
    data_source:
      derived: true
      rule: "integer_to_korean_numeral(VR-RCP-07.value)"
    position: { top_mm: 142, left_mm: 30, width_mm: 160, height_mm: 8 }
    # Example: 1,234,000 → "금 일백이십삼만사천원정"

  - id: "VR-RCP-09"
    name: "donation_category"
    slot_type: "string"
    data_source:
      file: "finance.yaml"
      field: "offerings[*].type"
      filter: "member_id == {member_id} and year == {year} and void == false"
      transform: "unique_types joined by ', '"
    position: { top_mm: 155, left_mm: 50, width_mm: 140, height_mm: 8 }

output_format:
  type: "markdown"
  output_path_template: "certificates/receipts/{year}/{member_id}-receipt-{year}.md"
  bulk_generation: true   # generates one file per member in a single run
  batch_input:
    file: "members.yaml"
    filter: "status == 'active'"
    loop_field: "member_id"
```

#### Data Source Mapping

| Variable Slot | YAML File | Field Path | Transform | Legal Requirement |
|---------------|-----------|------------|-----------|-------------------|
| Receipt Number | derived | generation_date + sequence | Zero-padded year-sequence | Recommended for audit |
| Issue Date | derived | system date | Format as Korean date | Required |
| Donor Name | `members.yaml` | `members[id].name` | None | Required |
| Donor ID | `members.yaml` | `members[id].resident_number` | Mask last 6 digits | Required (partial OK) |
| Donation Period | `finance.yaml` | `year` | Full-year date range | Required |
| Amount (numeric) | `finance.yaml` | `offerings[*].items[*].amount` | Sum by member + year, KRW format | Required |
| Amount (Korean) | derived | integer_to_korean_numeral() | Korean numeral conversion | Required by legal convention |
| Category | `finance.yaml` | `offerings[*].type` | Unique types, comma-joined | Recommended |

---

### 2.3 Worship Order (예배 순서지 — Order of Worship Service)

#### Overview

The 예배 순서지 (order of worship service sheet) is often distributed separately from the main bulletin, or printed as the inside pages of a folded bulletin. It provides the step-by-step flow of the worship service, typically listing each liturgical element, the responsible participant (leader, deacon, choir), and associated hymn or song numbers. It is produced every Sunday and sometimes for midweek services.

Unlike the bulletin (which covers a whole week of information), the worship order is tightly focused on a single service. Its layout is typically a simple ordered list or a two-column table (left: order items; right: participant/detail).

#### Fixed Regions

| Region ID | Region Name | Korean Name | Content Description |
|-----------|-------------|-------------|---------------------|
| FR-WOR-01 | Church Name | 교회명 | Full official church name, top center |
| FR-WOR-02 | Service Type Label | 예배 종류 라벨 | Fixed text: "예배 순서" or specific service name like "주일 2부 예배 순서" |
| FR-WOR-03 | Denomination Header | 교단 명칭 | Denomination affiliation, smaller than church name |
| FR-WOR-04 | Section Headers | 섹션 구분 라벨 | Fixed labels: "예배에로의 부름" (Call to Worship), "말씀" (Word), "응답" (Response), "파송" (Sending) — varies by liturgical tradition |
| FR-WOR-05 | Footer | 푸터 | Church address + contact in small print |

#### Variable Regions

| Region ID | Region Name | Korean Name | Slot Type | Notes |
|-----------|-------------|-------------|-----------|-------|
| VR-WOR-01 | Service Date | 예배 날짜 | date | Full date with day of week |
| VR-WOR-02 | Service Time | 예배 시간 | time | HH:MM format, 24h |
| VR-WOR-03 | Service Name | 예배 이름 | string | e.g., "주일 1부 예배", "수요예배" |
| VR-WOR-04 | Liturgical Season | 절기 | string (nullable) | e.g., "사순절 제3주일", "대강절" |
| VR-WOR-05 | Order Items | 예배 순서 항목 | list[object] | Ordered list: sequence_number, item_name, detail, responsible_person |
| VR-WOR-06 | Preacher | 설교자 | string | Name + title |
| VR-WOR-07 | Sermon Title | 설교 제목 | string | This week's sermon title |
| VR-WOR-08 | Scripture | 성경 본문 | string | Book chapter:verse |
| VR-WOR-09 | Worship Leader | 찬양 인도자 | string (nullable) | Choir director or worship team lead |
| VR-WOR-10 | Representative Prayer Person | 대표기도자 | string | Member name leading congregational prayer |
| VR-WOR-11 | Offering Deacons | 헌금 위원 | list[string] | Names of deacons collecting offering |
| VR-WOR-12 | Benediction | 축도자 | string | Pastor pronouncing benediction (usually senior pastor) |

#### YAML Template Schema

```yaml
# worship-template.yaml
template_id: "worship-order-v1"
document_type: "worship_order"
version: "1.0"
scan_source: "inbox/templates/worship-order.jpg"
confirmed_by: null
confirmed_date: null

paper:
  size: "A5"         # worship orders often printed A5 (half A4) or as A4 folded
  orientation: "portrait"
  pages: 1

fixed_regions:
  - id: "FR-WOR-01"
    name: "church_name"
    content: "{{ church_state.church.name }}"
    font: { family: "바탕체", size_pt: 18, weight: "bold", align: "center" }
    position: { top_mm: 5, width_pct: 100, height_mm: 10 }

  - id: "FR-WOR-02"
    name: "service_type_label"
    content: "예  배  순  서"
    font: { family: "바탕체", size_pt: 13, weight: "bold", align: "center" }
    position: { top_mm: 16, width_pct: 100, height_mm: 8 }

  - id: "FR-WOR-03"
    name: "denomination_header"
    content: "{{ church_state.church.denomination }}"
    font: { family: "굴림체", size_pt: 8, align: "center" }
    position: { top_mm: 2, width_pct: 100, height_mm: 5 }

variable_regions:
  - id: "VR-WOR-01"
    name: "service_date"
    slot_type: "date"
    format: "{year}년 {month}월 {day}일 ({weekday})"
    data_source:
      file: "schedule.yaml"
      field: "regular_services[id={service_id}]"
      derive: "next_occurrence_date"
    position: { top_mm: 25, width_pct: 100, height_mm: 7 }

  - id: "VR-WOR-03"
    name: "service_name"
    slot_type: "string"
    data_source:
      file: "schedule.yaml"
      field: "regular_services[id={service_id}].name"
    position: { top_mm: 32, width_pct: 100, height_mm: 7 }

  - id: "VR-WOR-04"
    name: "liturgical_season"
    slot_type: "string"
    nullable: true
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.liturgical_season"
    position: { top_mm: 39, width_pct: 100, height_mm: 6 }

  - id: "VR-WOR-05"
    name: "order_items"
    slot_type: "list[object]"
    position: { top_mm: 46, width_pct: 95, height_mm: 120 }
    item_height_mm: 9
    columns:
      - { name: "order_num", width_mm: 10, align: "right" }
      - { name: "item_name", width_mm: 60, align: "left" }
      - { name: "detail", width_mm: 50, align: "left" }
      - { name: "responsible", width_mm: 30, align: "right" }
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.worship_order[*]"
    validation: { min_items: 5 }

  - id: "VR-WOR-06"
    name: "preacher"
    slot_type: "string"
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.sermon.preacher"

  - id: "VR-WOR-07"
    name: "sermon_title"
    slot_type: "string"
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.sermon.title"

  - id: "VR-WOR-08"
    name: "scripture"
    slot_type: "string"
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.sermon.scripture"

  - id: "VR-WOR-10"
    name: "representative_prayer_person"
    slot_type: "string"
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.worship_order[item='대표기도'].performer"
    fallback: "지정자"

  - id: "VR-WOR-11"
    name: "offering_deacons"
    slot_type: "list[string]"
    data_source:
      file: "bulletin-data.yaml"
      field: "bulletin.offering_team"

output_format:
  type: "markdown"
  output_path_template: "bulletins/{date}-worship-order.md"
```

#### Data Source Mapping

| Variable Slot | YAML File | Field Path | Notes |
|---------------|-----------|------------|-------|
| Service Date | `schedule.yaml` | `regular_services[id].next_occurrence` | Derived from recurrence rule |
| Service Name | `schedule.yaml` | `regular_services[id].name` | |
| Liturgical Season | `bulletin-data.yaml` | `bulletin.liturgical_season` | Optional field |
| Order Items | `bulletin-data.yaml` | `bulletin.worship_order[*]` | Full list |
| Preacher | `bulletin-data.yaml` | `bulletin.sermon.preacher` | |
| Sermon Title | `bulletin-data.yaml` | `bulletin.sermon.title` | |
| Scripture | `bulletin-data.yaml` | `bulletin.sermon.scripture` | |
| Prayer Person | `bulletin-data.yaml` | `bulletin.worship_order[item='대표기도'].performer` | |
| Offering Deacons | `bulletin-data.yaml` | `bulletin.offering_team[*]` | |

---

### 2.4 Official Letter (공문 — Church Official Correspondence)

#### Overview

공문 (official letter) is the formal written communication channel through which a Korean church communicates with other churches, the presbytery (노회), general assembly (총회), government offices, or other organizations. Every public communication that carries the church's legal authority must take the form of a 공문.

The 공문 has a highly standardized format governed by Korean administrative convention. The church seal (직인 — official stamp) is mandatory; a 공문 without the seal has no official standing. The denomination header must match the church's exact official denominational affiliation. Numbering follows a sequential system reset annually (e.g., "제 2026-001호").

공문 are issued for: membership transfer requests (이명), denominational report submission, presbytery communications, cooperation requests between churches, and formal notifications to government bodies.

#### Fixed Regions

| Region ID | Region Name | Korean Name | Content Description |
|-----------|-------------|-------------|---------------------|
| FR-LET-01 | Denomination Header | 교단 명칭 헤더 | Denomination affiliation, top center, formal typography |
| FR-LET-02 | Church Name (Issuer) | 발신 교회명 | Issuing church's full official name |
| FR-LET-03 | Document Type Label | 문서 종류 라벨 | Fixed text "공  문" in large bold font, centered |
| FR-LET-04 | Issuer Block | 발신처 블록 | Church name, address, phone, fax, registration number — right-aligned block |
| FR-LET-05 | Seal Zone | 직인 위치 | Reserved zone at bottom of issuer block OR at the signature line. Mandatory. |
| FR-LET-06 | Form Fields Labels | 양식 필드 라벨 | Fixed labels in a table: "문서번호:", "수신:", "참조:", "발신:", "제목:", "내용:" |
| FR-LET-07 | Footer Policy Text | 푸터 정책 문구 | Sometimes includes "이 문서를 받으신 분께서는..." handling instructions |

#### Variable Regions

| Region ID | Region Name | Korean Name | Slot Type | Notes |
|-----------|-------------|-------------|-----------|-------|
| VR-LET-01 | Document Number | 문서 번호 | string | Format: "제 YYYY-NNN호". Reset annually. |
| VR-LET-02 | Date | 날짜 | date | Issue date of the letter |
| VR-LET-03 | Recipient (수신) | 수신처 | string | Receiving party: church name, organization, or individual with title |
| VR-LET-04 | Reference (참조) | 참조 | string (nullable) | Secondary recipient or reference person, usually a role title |
| VR-LET-05 | Sender (발신) | 발신자 | string | "XXX교회 담임목사 [이름]" |
| VR-LET-06 | Subject | 제목 | string | Letter subject line. Should be concise (15–40 characters) |
| VR-LET-07 | Body Content | 내용 | text | Main letter body. May span multiple paragraphs. Standard opening: "위와 같이 알려드립니다" or formal greeting |
| VR-LET-08 | Attached Documents | 붙임 (첨부) | list[string] (nullable) | Attached document list, labeled "붙임" |
| VR-LET-09 | Representative Signature | 대표자 서명 | string | "위와 같이 공문을 발송합니다. [교회명] 담임목사 [이름] (인)" |

#### YAML Template Schema

```yaml
# letter-template.yaml
template_id: "official-letter-v1"
document_type: "official_letter"
version: "1.0"
scan_source: "inbox/templates/letter-sample.jpg"
confirmed_by: null
confirmed_date: null

paper:
  size: "A4"
  orientation: "portrait"
  pages: 1    # single-page standard; multi-page for lengthy content

numbering:
  system: "annual_sequential"
  format: "제 {year}-{seq:03d}호"
  counter_file: "church-state.yaml"
  counter_field: "documents.official_letter.last_number"

fixed_regions:
  - id: "FR-LET-01"
    name: "denomination_header"
    content: "{{ church_state.church.denomination_full_name }}"
    font: { family: "바탕체", size_pt: 11, weight: "bold", align: "center" }
    position: { top_mm: 8, width_pct: 100, height_mm: 7 }

  - id: "FR-LET-03"
    name: "document_type_label"
    content: "공      문"
    font: { family: "바탕체", size_pt: 24, weight: "bold", align: "center" }
    position: { top_mm: 18, width_pct: 100, height_mm: 14 }

  - id: "FR-LET-04"
    name: "issuer_block"
    content_type: "structured_block"
    position: { top_mm: 35, right_mm: 15, width_mm: 80, height_mm: 35 }
    fields:
      - "{{ church_state.church.name }}"
      - "{{ church_state.church.address }}"
      - "TEL: {{ church_state.church.phone }}"
      - "등록번호: {{ church_state.church.registration_number }}"
    font: { family: "굴림체", size_pt: 9, align: "right" }

  - id: "FR-LET-05"
    name: "seal_zone"
    content_type: "reserved_seal_zone"
    position: { top_mm: 60, right_mm: 15, width_mm: 30, height_mm: 18 }
    guard: "NO_VARIABLE_CONTENT"
    annotation: "직인 위치 — 물리적 직인 날인 필수"

  - id: "FR-LET-06"
    name: "form_field_labels"
    content_type: "table_with_fixed_labels"
    position: { top_mm: 75, left_mm: 15, width_mm: 180, height_mm: 60 }
    rows:
      - label: "문서번호"
        slot: "VR-LET-01"
      - label: "수    신"
        slot: "VR-LET-03"
      - label: "참    조"
        slot: "VR-LET-04"
        optional: true
      - label: "발    신"
        slot: "VR-LET-05"
      - label: "제    목"
        slot: "VR-LET-06"

variable_regions:
  - id: "VR-LET-01"
    name: "document_number"
    slot_type: "string"
    data_source:
      derived: true
      rule: "annual_sequential_from_church_state"
    format: "제 {year}-{seq:03d}호"

  - id: "VR-LET-02"
    name: "letter_date"
    slot_type: "date"
    format: "{year}년 {month}월 {day}일"
    data_source:
      derived: true
      rule: "generation_date"
    position: { top_mm: 35, left_mm: 15, width_mm: 80, height_mm: 7 }

  - id: "VR-LET-03"
    name: "recipient"
    slot_type: "string"
    data_source:
      file: "church-state.yaml"
      field: "documents.current_letter.recipient"
    # OR from members.yaml for inter-member correspondence

  - id: "VR-LET-05"
    name: "sender"
    slot_type: "string"
    format: "{church_name} 담임목사 {pastor_name}"
    data_source:
      file: "church-state.yaml"
      fields:
        - "church.name"
        - "church.representative"

  - id: "VR-LET-06"
    name: "subject"
    slot_type: "string"
    data_source:
      file: "church-state.yaml"
      field: "documents.current_letter.subject"
    validation: { min_length: 5, max_length: 60 }

  - id: "VR-LET-07"
    name: "body_content"
    slot_type: "text"
    data_source:
      file: "church-state.yaml"
      field: "documents.current_letter.body"
    position: { top_mm: 140, left_mm: 15, width_mm: 180, height_mm: 100 }
    font: { family: "바탕체", size_pt: 11, line_spacing: 1.8 }

  - id: "VR-LET-08"
    name: "attachments"
    slot_type: "list[string]"
    nullable: true
    data_source:
      file: "church-state.yaml"
      field: "documents.current_letter.attachments"
    format_prefix: "붙  임: "
    item_format: "{seq}. {attachment_name}"

output_format:
  type: "markdown"
  output_path_template: "reports/letters/{year}/{date}-{seq:03d}-official-letter.md"
```

#### Data Source Mapping

| Variable Slot | YAML File | Field Path | Notes |
|---------------|-----------|------------|-------|
| Document Number | `church-state.yaml` | `documents.official_letter.last_number` | Auto-increment, annual reset |
| Date | derived | system date | Korean date format |
| Recipient | `church-state.yaml` | `documents.current_letter.recipient` | Or from members.yaml for known members |
| Reference | `church-state.yaml` | `documents.current_letter.reference` | Optional |
| Sender | `church-state.yaml` | `church.name` + `church.representative` | Composed |
| Subject | `church-state.yaml` | `documents.current_letter.subject` | |
| Body | `church-state.yaml` | `documents.current_letter.body` | Pre-composed text |
| Attachments | `church-state.yaml` | `documents.current_letter.attachments` | List, nullable |

---

### 2.5 Meeting Minutes (당회/제직회 회의록 — Session/Deacons' Meeting Minutes)

#### Overview

Korean churches hold two primary governance meetings:
- **당회 (Session)**: Composed of the senior pastor (당회장) and all ordained elders (장로). Holds final authority on church governance, finance approval, ordinance administration, and personnel decisions. Typically monthly.
- **제직회 (Deacons' Meeting)**: All ordained officers — pastor, elders, deacons (집사), and deaconesses (권사). Administrative body for implementing session decisions. Monthly or quarterly.

Meeting minutes (회의록) are legally significant in Korean church governance. They serve as the official record of decisions made. In the Presbyterian system, session minutes must be submitted to the presbytery (노회) annually. The minutes must include quorum verification, agenda items, motions, votes, and outcomes.

A critical formatting convention: minutes use formal honorifics and third-person reportorial style throughout ("○○ 장로가 제안하여 전원 가결하다").

#### Fixed Regions

| Region ID | Region Name | Korean Name | Content Description |
|-----------|-------------|-------------|---------------------|
| FR-MIN-01 | Document Title | 회의록 제목 | "제 ○○차 당회 회의록" or "제 ○○차 제직회 회의록" — the meeting body is fixed per template type |
| FR-MIN-02 | Church Name | 교회명 | Full official church name |
| FR-MIN-03 | Denomination Header | 교단 명칭 | Required for presbyterial accountability |
| FR-MIN-04 | Standard Opening Text | 표준 개회 문구 | Fixed phrase: "위와 같이 폐회를 선언하다" or formal parliamentary opening/closing language |
| FR-MIN-05 | Signature Block Labels | 서명란 라벨 | Fixed labels: "서기:", "당회장:" (for 당회) or "회장:", "서기:" (for 제직회) |
| FR-MIN-06 | Seal Zone | 직인 위치 | Seal affixed near signature block |

#### Variable Regions

| Region ID | Region Name | Korean Name | Slot Type | Notes |
|-----------|-------------|-------------|-----------|-------|
| VR-MIN-01 | Meeting Number | 회의 차수 | integer | Sequential within the year: "제 N차" |
| VR-MIN-02 | Meeting Date | 회의 날짜 | date | Full date including day of week |
| VR-MIN-03 | Meeting Time | 회의 시간 | time | Start time HH:MM |
| VR-MIN-04 | Meeting Location | 회의 장소 | string | Usually "본 교회 당회실" or a specific room |
| VR-MIN-05 | Attendees List | 참석자 명단 | list[object] | Name + role for each attendee |
| VR-MIN-06 | Quorum Verification | 정족수 확인 | object | Total eligible + present + quorum met boolean |
| VR-MIN-07 | Presiding Officer | 의장 | string | Name + title of the person presiding |
| VR-MIN-08 | Secretary | 서기 | string | Name + title of the secretary recording minutes |
| VR-MIN-09 | Opening Prayer Person | 개회기도자 | string | Name of person who opened with prayer |
| VR-MIN-10 | Agenda Items | 안건 목록 | list[object] | Each agenda item: number, title, discussion summary, decision, vote |
| VR-MIN-11 | Special Reports | 특별 보고 | list[object] (nullable) | Committee reports or special items |
| VR-MIN-12 | Next Meeting Date | 다음 회의 예정일 | date (nullable) | If agreed in meeting |
| VR-MIN-13 | Closing Prayer Person | 폐회기도자 | string | Name of person who closed with prayer |
| VR-MIN-14 | Presider Signature | 의장 서명 | string | Name for the signature line |
| VR-MIN-15 | Secretary Signature | 서기 서명 | string | Name for the secretary signature line |

#### YAML Template Schema

```yaml
# minutes-template.yaml
template_id: "meeting-minutes-v1"
document_type: "meeting_minutes"
version: "1.0"
scan_source: "inbox/templates/meeting-minutes.jpg"
confirmed_by: null
confirmed_date: null

variants:
  - id: "danghoae"       # 당회
    name: "당회 회의록"
    presider_role: "당회장"
    quorum_rule: "total_elders * 0.5 + 1"
  - id: "jejikhoae"      # 제직회
    name: "제직회 회의록"
    presider_role: "회장"
    quorum_rule: "total_officers * 0.5 + 1"

paper:
  size: "A4"
  orientation: "portrait"
  pages: "variable"    # 2–6 pages depending on agenda length

fixed_regions:
  - id: "FR-MIN-01"
    name: "document_title"
    content: "제 {meeting_number}차 {{ variant.name }}"
    font: { family: "바탕체", size_pt: 20, weight: "bold", align: "center" }
    position: { top_mm: 20, width_pct: 100, height_mm: 12 }
    note: "meeting_number is variable but 'variant.name' portion is fixed per template variant"

  - id: "FR-MIN-02"
    name: "church_name"
    content: "{{ church_state.church.name }}"
    font: { family: "바탕체", size_pt: 14, weight: "bold", align: "center" }
    position: { top_mm: 8, width_pct: 100, height_mm: 8 }

  - id: "FR-MIN-04"
    name: "standard_opening"
    content: "예수 그리스도의 이름으로 개회를 선언하다."
    font: { family: "바탕체", size_pt: 11 }
    position: "inline_after_opening_prayer"

  - id: "FR-MIN-05"
    name: "signature_block_labels"
    content_type: "signature_block"
    position: { bottom_mm: 30, left_mm: 15, width_pct: 90 }
    labels:
      - "서    기: _____________________ (인)"
      - "{{ variant.presider_role }}: _____________________ (인)"

variable_regions:
  - id: "VR-MIN-01"
    name: "meeting_number"
    slot_type: "integer"
    data_source:
      file: "church-state.yaml"
      field: "governance.session_meeting_count"   # for 당회
      # OR: "governance.deacons_meeting_count"     # for 제직회
    format: "제 {value}차"

  - id: "VR-MIN-02"
    name: "meeting_date"
    slot_type: "date"
    format: "{year}년 {month}월 {day}일 ({weekday})"
    data_source:
      file: "schedule.yaml"
      field: "special_events[type='session_meeting' OR type='deacons_meeting'].date"
      select: "most_recent_future_or_today"

  - id: "VR-MIN-03"
    name: "meeting_time"
    slot_type: "time"
    data_source:
      file: "schedule.yaml"
      field: "special_events[type='session_meeting'].time"

  - id: "VR-MIN-04"
    name: "meeting_location"
    slot_type: "string"
    data_source:
      file: "schedule.yaml"
      field: "special_events[type='session_meeting'].location"
    default: "본 교회 당회실"

  - id: "VR-MIN-05"
    name: "attendees_list"
    slot_type: "list[object]"
    data_source:
      file: "members.yaml"
      field: "members[*]"
      filter: "church.role in ['장로', '목사'] and status == 'active'"    # for 당회
      # filter: "church.role in ['목사','장로','집사','권사'] and status == 'active'"  # for 제직회
      transform: "sort by role_rank then name; format as '{name} {role}'"
    format: "출석: {name} {role}"

  - id: "VR-MIN-06"
    name: "quorum_verification"
    slot_type: "object"
    data_source:
      derived: true
      rule: "count(attendees) vs quorum_rule(variant)"
    format: "재적 {total}인, 출석 {present}인 — 정족수 {quorum_met}"

  - id: "VR-MIN-10"
    name: "agenda_items"
    slot_type: "list[object]"
    data_source:
      file: "church-state.yaml"
      field: "governance.pending_agenda_items"
    item_format: |
      제{seq}안건 {title}
      [토의 내용] {discussion}
      [결의] {decision}
      [투표] 찬성 {yes}표, 반대 {no}표, 기권 {abstain}표 → {outcome}

output_format:
  type: "markdown"
  output_path_template: "reports/minutes/{year}/{date}-{variant}-minutes.md"
```

#### Data Source Mapping

| Variable Slot | YAML File | Field Path | Notes |
|---------------|-----------|------------|-------|
| Meeting Number | `church-state.yaml` | `governance.session_meeting_count` | Auto-increment |
| Meeting Date | `schedule.yaml` | `special_events[type='session_meeting'].date` | |
| Meeting Time | `schedule.yaml` | `special_events[type='session_meeting'].time` | |
| Meeting Location | `schedule.yaml` | `special_events[type='session_meeting'].location` | |
| Attendees | `members.yaml` | `members[church.role in elders].name + role` | Filter by role |
| Quorum | derived | count(attendees) vs quorum rule | Computed |
| Agenda Items | `church-state.yaml` | `governance.pending_agenda_items` | Pre-populated by secretary |
| Presider | `members.yaml` | `members[church.role=='목사'].name` | Senior pastor |
| Secretary | `members.yaml` | `members[church.role=='장로' and serving_area contains '서기'].name` | |

---

### 2.6 Certificate (세례증서/이명증서 — Baptism / Transfer Certificate)

#### Overview

The 세례증서 (baptism certificate) and 이명증서 (membership transfer certificate) are the most formally significant individual documents a Korean church produces. They have legal and ecclesiastical standing:

- **세례증서**: Certifies that a person has received baptism (세례) on a specific date under a specific pastor. Used for membership confirmation, other church membership transfer, and personal records. The senior pastor's signature and the church seal are both mandatory.
- **이명증서**: Certifies that a church member is formally transferring their membership (교적) to another church. Required by the receiving church. Contains the member's complete ecclesiastical record: baptism date, admission date, conduct record.

Both documents use more formal and decorative layouts than operational documents. Some churches use embossed letterhead or pre-printed certificate stock. The seal (직인) placement is prominent and central (not tucked in a corner as with letters).

#### Fixed Regions

| Region ID | Region Name | Korean Name | Content Description |
|-----------|-------------|-------------|---------------------|
| FR-CRT-01 | Certificate Title | 증서 제목 | "세 례 증 서" or "이 명 증 서" in large formal typography (28–36pt) |
| FR-CRT-02 | Denomination Header | 교단 명칭 | Full denomination name, often with the 교단 emblem/logo |
| FR-CRT-03 | Church Name | 교회명 | Issuing church's full name, formally styled |
| FR-CRT-04 | Decorative Frame | 장식 테두리 | Ornamental border — common in certificates. Double-line, scroll, or religious motif. |
| FR-CRT-05 | Biblical Verse | 성경 구절 | A fixed verse relating to baptism (e.g., 마태복음 28:19) or membership. Different per church, but fixed for that church. |
| FR-CRT-06 | Seal Zone (Central) | 직인 위치 (중앙) | Prominent seal zone, often centered below the body text or at the bottom center. |
| FR-CRT-07 | Signature Line Labels | 서명란 라벨 | "담임목사:" or "당회장:" label with blank line |
| FR-CRT-08 | Issue Authority Block | 발행 기관 블록 | Full church name + address + registration number |

#### Variable Regions — 세례증서 (Baptism Certificate)

| Region ID | Region Name | Korean Name | Slot Type | Notes |
|-----------|-------------|-------------|-----------|-------|
| VR-CRT-01 | Certificate Number | 증서 번호 | string | Sequential within year. Some churches omit. |
| VR-CRT-02 | Issue Date | 발행일 | date | |
| VR-CRT-03 | Recipient Name | 수여자 성명 | string | Full name of the baptized person |
| VR-CRT-04 | Recipient Birth Date | 생년월일 | date | Birth date in Korean format |
| VR-CRT-05 | Baptism Date | 세례 시행일 | date | Date when baptism was administered |
| VR-CRT-06 | Baptism Type | 세례 종류 | enum | "세례" (adult) or "입교" or "유아세례" (infant) |
| VR-CRT-07 | Officiating Pastor | 집례자 | string | Pastor who performed the baptism |
| VR-CRT-08 | Presiding Officer Signature | 서명자 | string | Senior pastor name for the signature line |

#### Variable Regions — 이명증서 (Transfer Certificate)

| Region ID | Region Name | Korean Name | Slot Type | Notes |
|-----------|-------------|-------------|-----------|-------|
| VR-CRT-T-01 | Certificate Number | 증서 번호 | string | |
| VR-CRT-T-02 | Issue Date | 발행일 | date | |
| VR-CRT-T-03 | Member Name | 교인 성명 | string | Full name of the transferring member |
| VR-CRT-T-04 | Member Birth Date | 생년월일 | date | |
| VR-CRT-T-05 | Registration Date | 본 교회 등록일 | date | Date registered at this church |
| VR-CRT-T-06 | Baptism Date | 세례일 | date | |
| VR-CRT-T-07 | Baptism Type | 세례 종류 | enum | |
| VR-CRT-T-08 | Receiving Church | 이명처 교회명 | string | Name of the destination church |
| VR-CRT-T-09 | Conduct Record | 행위 기록 | string | Standard phrase: "재직 중 행위가 단정하였음" (conduct was proper) |
| VR-CRT-T-10 | Presiding Officer | 서명자 | string | Senior pastor name |

#### YAML Template Schema

```yaml
# certificate-template.yaml
template_id: "certificate-v1"
document_type: "certificate"
version: "1.0"
scan_source: "inbox/templates/certificate-sample.jpg"
confirmed_by: null
confirmed_date: null

variants:
  - id: "baptism"
    name: "세례증서"
    title_display: "세  례  증  서"
    scripture: "마태복음 28:19 '그러므로 너희는 가서 모든 민족을 제자로 삼아...'"
  - id: "transfer"
    name: "이명증서"
    title_display: "이  명  증  서"
    scripture: "히브리서 10:25 '모이기를 폐하는 어떤 사람들의 습관과 같이...'"
  - id: "infant_baptism"
    name: "유아세례증서"
    title_display: "유  아  세  례  증  서"

paper:
  size: "A4"
  orientation: "portrait"
  pages: 1
  stock: "certificate"   # hint for physical printing: use certificate paper stock

fixed_regions:
  - id: "FR-CRT-01"
    name: "certificate_title"
    content: "{{ variant.title_display }}"
    font: { family: "바탕체", size_pt: 32, weight: "bold", align: "center" }
    position: { top_mm: 40, width_pct: 100, height_mm: 18 }

  - id: "FR-CRT-04"
    name: "decorative_frame"
    type: "border"
    style: "ornamental_double"
    margin_from_edge_mm: 8

  - id: "FR-CRT-05"
    name: "biblical_verse"
    content: "{{ variant.scripture }}"
    font: { family: "바탕체", size_pt: 9, style: "italic", align: "center" }
    position: { top_mm: 60, width_pct: 80, height_mm: 8 }

  - id: "FR-CRT-06"
    name: "seal_zone_central"
    content_type: "reserved_seal_zone"
    position: { top_mm: 195, left_mm: 80, width_mm: 50, height_mm: 30 }
    guard: "NO_VARIABLE_CONTENT"
    annotation: "직인 위치 — 날인 필수 (세례증서/이명증서 법적 유효성 요건)"

  - id: "FR-CRT-07"
    name: "signature_line"
    content: "{{ variant.presider_label }}: _____________________  (인)"
    font: { family: "바탕체", size_pt: 12 }
    position: { top_mm: 210, left_mm: 50, width_mm: 110, height_mm: 10 }

variable_regions:
  - id: "VR-CRT-03"
    name: "recipient_name"
    slot_type: "string"
    data_source:
      file: "members.yaml"
      field: "members[id={member_id}].name"
    font: { family: "바탕체", size_pt: 18, weight: "bold", align: "center" }
    position: { top_mm: 80, width_pct: 100, height_mm: 12 }
    format: "성  명:  {value}"

  - id: "VR-CRT-04"
    name: "recipient_birth_date"
    slot_type: "date"
    data_source:
      file: "members.yaml"
      field: "members[id={member_id}].birth_date"
    format: "생년월일:  {year}년 {month}월 {day}일"
    position: { top_mm: 95, width_pct: 80, height_mm: 8 }

  - id: "VR-CRT-05"
    name: "baptism_date"
    slot_type: "date"
    data_source:
      file: "members.yaml"
      field: "members[id={member_id}].church.baptism_date"
    format: "세례일:  {year}년 {month}월 {day}일"
    position: { top_mm: 105, width_pct: 80, height_mm: 8 }

  - id: "VR-CRT-T-08"    # transfer only
    name: "receiving_church"
    slot_type: "string"
    nullable_for_variant: ["baptism", "infant_baptism"]
    data_source:
      file: "church-state.yaml"
      field: "documents.current_transfer.receiving_church"
    format: "이명처:  {value}"

  - id: "VR-CRT-08"
    name: "presider_signature"
    slot_type: "string"
    data_source:
      file: "members.yaml"
      field: "members[church.role=='목사' and status=='active'].name"
      select: "first"    # senior pastor
    format: "담임목사  {value}  (인)"
    position: { top_mm: 215, left_mm: 100, width_mm: 90, height_mm: 8 }

  - id: "VR-CRT-02"
    name: "issue_date"
    slot_type: "date"
    data_source:
      derived: true
      rule: "generation_date"
    format: "{year}년 {month}월 {day}일"
    position: { top_mm: 225, width_pct: 100, height_mm: 7 }

output_format:
  type: "markdown"
  output_path_template: "certificates/{variant}/{year}/{member_id}-{variant}.md"
```

#### Data Source Mapping

| Variable Slot | YAML File | Field Path | Notes |
|---------------|-----------|------------|-------|
| Recipient Name | `members.yaml` | `members[id].name` | |
| Birth Date | `members.yaml` | `members[id].birth_date` | |
| Baptism Date | `members.yaml` | `members[id].church.baptism_date` | |
| Baptism Type | `members.yaml` | `members[id].church.baptism_type` | enum: adult/infant |
| Registration Date | `members.yaml` | `members[id].church.registration_date` | for transfer cert |
| Receiving Church | `church-state.yaml` | `documents.current_transfer.receiving_church` | for transfer cert |
| Conduct Record | derived | Standard phrase | "재직 중 행위가 단정하였음" |
| Officiating Pastor | `members.yaml` | `members[role=='목사'].name` | Senior pastor |
| Issue Date | derived | system date | Korean date format |

---

### 2.7 Invitation (초청장 — Event Invitation)

#### Overview

The 초청장 (event invitation) is used for special church events: revival meetings (부흥회), dedication services (헌당예배), anniversary services (창립기념예배), community outreach events, and inter-church gatherings. The design is less standardized than other document types — each invitation reflects the specific event's branding and formality level. However, a typical Korean church invitation retains several fixed structural elements.

Invitations may be print (A5 or custom size) or digital (image file for social media/KakaoTalk sharing). The scan-and-replicate template primarily targets the print format. Digital output (image generation) is a Phase 2 feature.

#### Fixed Regions

| Region ID | Region Name | Korean Name | Content Description |
|-----------|-------------|-------------|---------------------|
| FR-INV-01 | Church Name | 주최 교회명 | Hosting church's name |
| FR-INV-02 | Denomination Header | 교단 명칭 | Usually included for formal events |
| FR-INV-03 | Invitation Label | 초청 라벨 | "초 청 장" or "INVITATION" or specific event type label |
| FR-INV-04 | Church Logo | 교회 로고 | Church logo or cross symbol |
| FR-INV-05 | Footer Contact | 연락처 | Church phone + address in footer |

#### Variable Regions

| Region ID | Region Name | Korean Name | Slot Type | Notes |
|-----------|-------------|-------------|-----------|-------|
| VR-INV-01 | Event Name | 행사명 | string | Full name of the event |
| VR-INV-02 | Event Date | 행사 날짜 | date | Full date with day of week |
| VR-INV-03 | Event Time | 행사 시간 | time | Start time (and end time if known) |
| VR-INV-04 | Event Venue | 장소 | string | Full venue name and address |
| VR-INV-05 | Special Guest | 특별 강사/초청 인사 | string (nullable) | Name + title of guest speaker or performer |
| VR-INV-06 | Event Theme | 주제 | string (nullable) | Theme or subtitle of the event |
| VR-INV-07 | Program Outline | 프로그램 개요 | list[string] (nullable) | Key program items |
| VR-INV-08 | RSVP Information | 참석 문의 | string (nullable) | Contact for RSVP |
| VR-INV-09 | Host Organization | 주최 | string | Full hosting organization name |
| VR-INV-10 | Co-host Organizations | 후원/주관 | list[string] (nullable) | Co-organizing churches or ministries |
| VR-INV-11 | Greeting Message | 인사말 | text (nullable) | Short message from the pastor or event leader |
| VR-INV-12 | Recipient Name | 수신인 | string (nullable) | Specific person the invitation is addressed to (for personal invitations) |

#### YAML Template Schema

```yaml
# invitation-template.yaml
template_id: "invitation-v1"
document_type: "invitation"
version: "1.0"
scan_source: "inbox/templates/invitation-sample.jpg"
confirmed_by: null
confirmed_date: null

paper:
  size: "A5"         # A5 common for invitations; some use custom sizes
  orientation: "portrait"
  pages: 2           # front (cover) + back (program details)

fixed_regions:
  - id: "FR-INV-01"
    name: "hosting_church_name"
    content: "{{ church_state.church.name }}"
    font: { family: "바탕체", size_pt: 14, weight: "bold", align: "center" }
    position: { top_mm: 3, width_pct: 100, height_mm: 8 }

  - id: "FR-INV-03"
    name: "invitation_label"
    content: "초  청  장"
    font: { family: "바탕체", size_pt: 22, weight: "bold", align: "center" }
    position: { top_mm: 20, width_pct: 100, height_mm: 12 }

  - id: "FR-INV-04"
    name: "church_logo"
    content_type: "image"
    image_path: "assets/church-logo.png"
    position: { top_mm: 3, right_mm: 5, width_mm: 20, height_mm: 20 }

  - id: "FR-INV-05"
    name: "footer_contact"
    content: "{{ church_state.church.name }} | {{ church_state.church.phone }}"
    font: { family: "굴림체", size_pt: 8, align: "center" }
    position: { bottom_mm: 3, width_pct: 100, height_mm: 6 }

variable_regions:
  - id: "VR-INV-01"
    name: "event_name"
    slot_type: "string"
    data_source:
      file: "schedule.yaml"
      field: "special_events[id={event_id}].name"
    font: { family: "바탕체", size_pt: 18, weight: "bold", align: "center" }
    position: { top_mm: 35, width_pct: 90, height_mm: 12 }

  - id: "VR-INV-02"
    name: "event_date"
    slot_type: "date"
    data_source:
      file: "schedule.yaml"
      field: "special_events[id={event_id}].date"
    format: "{year}년 {month}월 {day}일 ({weekday})"
    position: { top_mm: 50, width_pct: 90, height_mm: 8 }

  - id: "VR-INV-03"
    name: "event_time"
    slot_type: "time"
    data_source:
      file: "schedule.yaml"
      field: "special_events[id={event_id}].time"
    format: "오전/오후 {hour}시 {minute}분"
    position: { top_mm: 59, width_pct: 90, height_mm: 7 }

  - id: "VR-INV-04"
    name: "event_venue"
    slot_type: "string"
    data_source:
      file: "schedule.yaml"
      field: "special_events[id={event_id}].location"
    position: { top_mm: 67, width_pct: 90, height_mm: 7 }

  - id: "VR-INV-05"
    name: "special_guest"
    slot_type: "string"
    nullable: true
    data_source:
      file: "schedule.yaml"
      field: "special_events[id={event_id}].preacher"
    format: "강  사: {value}"

  - id: "VR-INV-06"
    name: "event_theme"
    slot_type: "string"
    nullable: true
    data_source:
      file: "schedule.yaml"
      field: "special_events[id={event_id}].description"
    format: "주  제: {value}"

  - id: "VR-INV-07"
    name: "program_outline"
    slot_type: "list[string]"
    nullable: true
    data_source:
      file: "schedule.yaml"
      field: "special_events[id={event_id}].preparation"
      transform: "filter items that match program item pattern"

  - id: "VR-INV-11"
    name: "greeting_message"
    slot_type: "text"
    nullable: true
    data_source:
      file: "church-state.yaml"
      field: "documents.current_invitation.greeting_message"
    font: { family: "바탕체", size_pt: 10, line_spacing: 1.8 }

  - id: "VR-INV-12"
    name: "recipient_name"
    slot_type: "string"
    nullable: true
    data_source:
      file: "members.yaml"
      field: "members[id={member_id}].name"
    format: "{value} 귀하"
    note: "Used when generating personalized invitations for specific members"

output_format:
  type: "markdown"
  output_path_template: "reports/invitations/{event_id}-invitation.md"
  personalized_mode:
    enabled: false   # when true, generates one file per recipient
    batch_input:
      file: "members.yaml"
      filter: "status == 'active'"
```

#### Data Source Mapping

| Variable Slot | YAML File | Field Path | Notes |
|---------------|-----------|------------|-------|
| Event Name | `schedule.yaml` | `special_events[id].name` | |
| Event Date | `schedule.yaml` | `special_events[id].date` | |
| Event Time | `schedule.yaml` | `special_events[id].time` | |
| Venue | `schedule.yaml` | `special_events[id].location` | |
| Special Guest | `schedule.yaml` | `special_events[id].preacher` | nullable |
| Program | `schedule.yaml` | `special_events[id].preparation` | filtered list |
| Greeting | `church-state.yaml` | `documents.current_invitation.greeting_message` | pre-composed |
| Recipient | `members.yaml` | `members[id].name` | for personalized mode |

---

## 3. Korean Church Formatting Conventions

Understanding Korean church document formatting conventions is essential for the template scanner to correctly classify regions as fixed vs variable, and for the template generator to produce culturally and functionally correct output.

### 3.1 Paper Size Conventions

| Document Type | Primary Size | Secondary Options | Notes |
|---------------|-------------|-------------------|-------|
| Bulletin (주보) | A4 (210×297mm) | B5 folded (4-page booklet), A5 | B5 used in traditional/formal churches; A4 most common |
| Receipt (영수증) | A4 | None | Legal documents always A4 |
| Worship Order (순서지) | A5 or A4 folded | Half of A4 | Often printed inside the bulletin |
| Official Letter (공문) | A4 | None | Standardized to A4 in Korean administrative tradition |
| Meeting Minutes (회의록) | A4 | None | Always A4; may be multi-page |
| Certificate (증서) | A4 | Custom certificate stock | Often printed on heavier paper (160–200gsm) |
| Invitation (초청장) | A5 | DL envelope size, custom | Smaller formats common for formal invitations |

### 3.2 Font Conventions

Korean church documents use two dominant typefaces, both included in standard Korean office software (HWP, MS Word Korean version):

| Typeface | Korean Name | Characteristics | Typical Usage in Church Docs |
|----------|-------------|-----------------|-------------------------------|
| **Batang** | 바탕체 | Serif, traditional, formal. Resembles Ming/Song typefaces. | Document titles, sermon titles, certificate body text, official letters. Formal documents. |
| **Gulim** | 굴림체 | Sans-serif, clean, modern. | Contact information, addresses, captions, smaller body text. Informational sections. |
| **Gungseo** | 궁서체 | Highly formal, calligraphic serif. | Certificate titles in very formal contexts. Rare in standard bulletins. |
| **Dotum** | 돋움체 | Sans-serif, similar to Gulim. | Secondary body text, modern-style bulletins. |

**Font Size Conventions**:
- Document title: 20–36pt (바탕체, bold)
- Main headings: 14–18pt
- Body text: 10–12pt
- Captions, addresses, legal text: 8–9pt
- Certificate names: 18–24pt (바탕체, bold)

### 3.3 Seal (직인) Placement Rules

The 직인 (official seal/stamp) is one of the most critical elements in Korean church documents. Incorrect placement or absence invalidates the document's official standing.

**Seal Types**:
- **직인 (職印)**: The church's official institutional seal. Round or rectangular. Contains church name + Korean 印 character.
- **인감 (印鑑)**: The personal seal of the authorized signatory (pastor). Small, round.

**Placement Rules by Document Type**:

| Document Type | Seal Type | Placement Zone | Position Description |
|---------------|-----------|----------------|----------------------|
| Official Letter (공문) | 직인 | FR-LET-05: Bottom-right of issuer block | Overlaps the representative's name/signature line, stamped after signing |
| Meeting Minutes (회의록) | 직인 | FR-MIN-06: Bottom of signature block | Stamped over or adjacent to the presider's signature line |
| Certificate (세례증서/이명증서) | 직인 + 인감 | FR-CRT-06: Central/prominent position | Stamped in a visually prominent position below body text |
| Receipt (영수증) | 직인 | FR-RCP-06: Bottom-right of issuer block | Required for legal validity of tax donation receipts |
| Bulletin (주보) | None | N/A | Bulletins do not require a seal |
| Worship Order (순서지) | None | N/A | No seal required |
| Invitation (초청장) | Optional | Bottom center or issuer block | Some formal invitations include a seal for gravitas |

**Critical Rule for Template Scanner**: When detecting the seal zone during template scanning, the scanner must:
1. Identify the circular or rectangular seal impression in the sample scan
2. Record the zone coordinates as a `reserved_seal_zone` fixed region
3. Mark the zone with `guard: "NO_VARIABLE_CONTENT"` to prevent any variable data from being placed in that zone during generation

### 3.4 Denomination Header Patterns

The denomination header appears at the top of formal documents (공문, certificates, meeting minutes) and identifies the ecclesiastical authority under which the church operates. The exact format varies by denomination:

| Denomination | Korean Name | Typical Header Text | Abbreviation Used |
|-------------|-------------|---------------------|-------------------|
| 예장통합 | 대한예수교장로회 (통합) | "대한예수교장로회 [○○노회]" | PCK |
| 예장합동 | 대한예수교장로회 (합동) | "대한예수교장로회합동 [○○노회]" | PROK |
| 기독교대한감리회 | 기독교대한감리회 (기감) | "기독교대한감리회 [○○연회]" | KMC |
| 한국기독교장로회 | 한국기독교장로회 (기장) | "한국기독교장로회 [○○노회]" | PCKK |
| 기독교대한성결교회 | 기독교대한성결교회 | "기독교대한성결교회 [○○지방회]" | KHC |
| 기독교한국루터회 | 기독교한국루터회 | "기독교한국루터회" | KLC |

**Scan-and-Replicate Note**: The denomination header, once extracted from the first scan, becomes a fixed region for all subsequent documents. The scanner must capture the exact denomination string including the presbytery (노회) or district (연회/지방회) name, which is part of the church's official affiliation.

### 3.5 Vertical Text Areas

Some Korean church documents, particularly certificates and formal invitations, use vertical text (세로쓰기/종서) in decorative or header sections. This is a traditional East Asian typography convention.

**Detection Rules for Template Scanner**:
- Vertical text areas are identified by character height > character width in the bounding box
- Characters flow top-to-bottom, right-to-left
- Typically used for: certificate titles, formal headings, names in very formal certificates

**Template Representation**:
```yaml
text_direction: "vertical"    # "horizontal" (default) or "vertical"
vertical_flow: "top_to_bottom_right_to_left"   # traditional Korean vertical
```

**Practical Note**: The Markdown output format (used in this system) does not natively support vertical text rendering. Vertical text areas are captured as metadata in the template YAML but rendered as horizontal text in Markdown output. PDF conversion (Phase 2) would handle actual vertical text rendering.

### 3.6 Honorific and Formal Language Conventions

Korean church documents use formal registers (높임말) throughout. Key conventions:

**For meeting minutes (회의록)**:
- Third-person reportorial: "○○ 장로가 동의하고 ○○ 장로가 재청하여 가결하다."
- Passive declarative: "[의안]이 상정되어 논의 후 원안대로 통과되다."
- No contractions, no casual particles

**For official letters (공문)**:
- Opening: "귀 [수신처] 교회(기관)의 무궁한 발전을 기원합니다."
- Body: Formal verb endings (-습니다, -하겠습니다)
- Closing: "위와 같이 알려드립니다." or "위와 같이 공문을 발송합니다."

**For certificates (증서)**:
- Present-tense declarative: "위 사람은 [year]년 [month]월 [day]일 본 교회에서 세례를 받았음을 증명합니다."
- Formal assertion: Never casual

These conventions are encoded as `style_guidelines` in each template and are referenced by the template-generator agent when composing variable content.

### 3.7 Korean Date and Number Formatting

| Format Type | Pattern | Example |
|-------------|---------|---------|
| Standard date | YYYY년 MM월 DD일 | 2026년 3월 1일 |
| Date with weekday | YYYY년 MM월 DD일 (요일) | 2026년 3월 1일 (주일) |
| Formal date (certificates) | YYYY년 MM월 DD일 | 2026년 03월 01일 (no leading zero optional) |
| Currency (numeric) | \₩X,XXX,XXX 또는 X,XXX,XXX원 | ₩1,234,000 또는 1,234,000원 |
| Currency (Korean numeral) | 금 [한글수량]원정 | 금 일백이십삼만사천원정 |
| Document number | 제 YYYY-NNN호 | 제 2026-001호 |
| Time | 오전/오후 H시 MM분 | 오전 11시 00분 |
| Ordinal meeting | 제 N차 | 제 3차 |

---

## 4. Priority Classification

Based on PRD §5.1 F-06 and §8.1, document types are classified into three implementation tiers.

### 4.1 Tier A — Immediate Implementation (즉시 — M1 Milestone)

**Criterion**: High frequency (weekly or annual bulk), direct M1 feature requirements, highest ROI for time savings.

| Document Type | Frequency | Annual Volume | Time Saved/Instance | M1 Reason |
|---------------|-----------|---------------|----------------------|-----------|
| **Bulletin (주보)** | Weekly | 52/year | ~2.5 hours | Core MVP feature (F-01). 52× annual repetition makes template ROI highest of all document types. |
| **Receipt (헌금 영수증)** | Annual bulk | 100–200/year | ~25 min/receipt | Legal obligation + year-end bulk generation (T1-03). High pain point for finance deacon. |
| **Worship Order (예배 순서지)** | Weekly | 52/year | ~30 min | Often combined with bulletin; 52× repetition; closely coupled to bulletin data sources. |

**Implementation Priority within Tier A**:
1. Bulletin (주보) — highest frequency, foundation for worship order
2. Worship Order (예배 순서지) — shares 80% of data sources with bulletin
3. Receipt (헌금 영수증) — highest legal significance, can batch-generate at year-end

### 4.2 Tier B — Phase 1 Extended (M2 Milestone)

**Criterion**: Medium frequency (monthly to a few times per year), important but not daily-operation-critical, complexity manageable after Tier A infrastructure is established.

| Document Type | Frequency | Annual Volume | M2 Reason |
|---------------|-----------|---------------|-----------|
| **Official Letter (공문)** | 2–5/month | 24–60/year | T1-05 feature. Uses established member + schedule data. Template simpler than certificate. |
| **Meeting Minutes (당회/제직회 회의록)** | 1–4/month | 12–48/year | Requires member roster data (already in M1 infrastructure). Governance records compliance need. |
| **Certificate (세례증서, 이명증서)** | 2–4/year | 2–20/year | T1-02 feature. Low frequency but high legal significance. Depends on M1 member management infrastructure. |

### 4.3 Tier C — Phase 2 / M3 Deferred

**Criterion**: Low frequency, high design variability (harder to standardize), or dependent on features not yet in M1/M2.

| Document Type | Frequency | Reason for Deferral |
|---------------|-----------|---------------------|
| **Denomination Report (교단 보고서)** | Annual | High complexity: aggregates all data sources, format dictated by denomination HQ, requires manual verification. Deferred to T2-03. |
| **Newsletter (교회 소식지)** | Monthly | Variable design, mixed content types, not yet in PRD scope as scan-and-replicate target. |
| **Personalized Invitation (개인별 초청장)** | Ad-hoc | Invitation generation is Tier C; bulk personalized invitations (per-member) require batch loop infrastructure not yet designed. |

**Note on Invitation (초청장)**:
- Standard (single) invitations: Tier B capability using existing schedule.yaml data
- Bulk personalized invitations (one per member): Tier C, requires M2 batch infrastructure
- PRD lists invitation as Tier C in F-06; this analysis concurs for bulk personalized mode

---

## 5. Denomination Variations

Korean church document formatting varies meaningfully between denominations. The scan-and-replicate system must accommodate denomination-specific variations without requiring per-denomination code changes.

### 5.1 Presbyterian (예장통합 / 예장합동)

The two largest Presbyterian denominations share similar governance structures but differ in some document conventions.

| Aspect | 예장통합 (PCK) | 예장합동 (PROK) | Notes |
|--------|--------------|--------------|-------|
| Denomination header | "대한예수교장로회 [노회명]" | "대한예수교장로회합동 [노회명]" | Must match exactly |
| Session authority | 당회 (Session) is supreme | Same | |
| Minutes submission | Annual to 노회 | Annual to 노회 | Different 노회 |
| Baptism form | Adult + infant | Adult + infant | Similar format |
| Transfer cert | 이명증서 issued by 당회 | Same | |
| Official letter numbering | Sequential annual | Sequential annual | |
| Seal requirement | 직인 mandatory | 직인 mandatory | |
| 공동의회 report | Required annually | Required annually | Different form templates |

### 5.2 Methodist (기독교대한감리회 — 기감)

The Methodist structure differs significantly from Presbyterian in governance hierarchy.

| Aspect | 기감 (KMC) | Presbyterian Comparison |
|--------|-----------|------------------------|
| Denomination header | "기독교대한감리회 [연회명]" | 노회 → 연회 (district conference) |
| Governing body | 교구회 (Circuit meeting) not 당회 | Different body name |
| Minutes | 교구회 회의록 | 당회록 → 교구회록 |
| Transfer cert | 이명증서 (same name, different authority) | Issued by 교구회 not 당회 |
| Annual report | 연회 보고서 | Different form than presbyterian 노회 |
| Baptism form | Similar to Presbyterian | Minor wording differences |

### 5.3 Template Denomination Parameter

To handle denomination variations without duplicate templates, each template includes a `denomination` parameter that drives conditional rendering:

```yaml
# In each template:
denomination_config:
  source: "church-state.yaml"
  field: "church.denomination_code"
  # Values: "PCK", "PROK", "KMC", "PCKK", "KHC", etc.

conditional_content:
  - condition: "denomination_code in ['PCK', 'PROK']"
    overrides:
      governing_body_name: "당회"
      minutes_type: "당회록"
      presbytery_level: "노회"

  - condition: "denomination_code == 'KMC'"
    overrides:
      governing_body_name: "교구회"
      minutes_type: "교구회록"
      presbytery_level: "연회"
```

### 5.4 Scan Priority by Denomination

For the initial implementation (M1), the scan-and-replicate system prioritizes:
1. **예장통합 (PCK)**: Largest denomination, ~30% of Korean Protestant churches
2. **예장합동 (PROK)**: Second largest, ~25%
3. **기감 (KMC)**: Third largest, ~15%

Combined coverage: ~70% of Korean Protestant churches with 3 denomination configurations.

---

## 6. Pipeline Integration Requirements

This section defines the technical requirements for integrating the 7 template schemas into the Step 5 pipeline design.

### 6.1 Template Schema Registry

All 7 templates must be registered in a central schema registry accessible to the pipeline:

```yaml
# templates/registry.yaml (generated during template scanning)
schema_registry:
  version: "1.0"
  last_updated: "2026-02-28"
  templates:
    - id: "bulletin-v1"
      file: "templates/bulletin-template.yaml"
      document_type: "bulletin"
      priority_tier: "A"
      confirmed: false
      primary_data_sources:
        - "data/bulletin-data.yaml"
        - "data/schedule.yaml"
        - "data/members.yaml"
      output_path_pattern: "bulletins/{date}-bulletin.md"
      generation_trigger: "weekly_monday"

    - id: "receipt-v1"
      file: "templates/receipt-template.yaml"
      document_type: "receipt"
      priority_tier: "A"
      confirmed: false
      primary_data_sources:
        - "data/finance.yaml"
        - "data/members.yaml"
      output_path_pattern: "certificates/receipts/{year}/{member_id}-receipt-{year}.md"
      generation_trigger: "annual_year_end"
      bulk_mode: true

    - id: "worship-order-v1"
      file: "templates/worship-template.yaml"
      document_type: "worship_order"
      priority_tier: "A"
      confirmed: false
      primary_data_sources:
        - "data/schedule.yaml"
        - "data/bulletin-data.yaml"
      output_path_pattern: "bulletins/{date}-worship-order.md"
      generation_trigger: "weekly_monday"

    - id: "official-letter-v1"
      file: "templates/letter-template.yaml"
      document_type: "official_letter"
      priority_tier: "B"
      confirmed: false
      primary_data_sources:
        - "data/members.yaml"
        - "data/schedule.yaml"
        - "church-state.yaml"
      output_path_pattern: "reports/letters/{year}/{date}-{seq:03d}-official-letter.md"
      generation_trigger: "on_demand"

    - id: "meeting-minutes-v1"
      file: "templates/minutes-template.yaml"
      document_type: "meeting_minutes"
      priority_tier: "B"
      confirmed: false
      primary_data_sources:
        - "data/members.yaml"
        - "data/schedule.yaml"
        - "church-state.yaml"
      output_path_pattern: "reports/minutes/{year}/{date}-{variant}-minutes.md"
      generation_trigger: "on_demand"

    - id: "certificate-v1"
      file: "templates/certificate-template.yaml"
      document_type: "certificate"
      priority_tier: "B"
      confirmed: false
      primary_data_sources:
        - "data/members.yaml"
      output_path_pattern: "certificates/{variant}/{year}/{member_id}-{variant}.md"
      generation_trigger: "on_demand"

    - id: "invitation-v1"
      file: "templates/invitation-template.yaml"
      document_type: "invitation"
      priority_tier: "C"
      confirmed: false
      primary_data_sources:
        - "data/schedule.yaml"
        - "data/members.yaml"
      output_path_pattern: "reports/invitations/{event_id}-invitation.md"
      generation_trigger: "on_demand"
```

### 6.2 Variable Slot Type System

The pipeline's data injection engine must support these slot types with corresponding validation:

| Slot Type | YAML Representation | Validation Rules | Transform Functions |
|-----------|---------------------|------------------|---------------------|
| `string` | `str` | min_length, max_length, non_empty | mask_name, format_title |
| `integer` | `int` | min, max, monotonically_increasing | format_with_unit |
| `date` | `str` (YYYY-MM-DD) | valid date, day_of_week constraints | korean_date_format, korean_weekday |
| `time` | `str` (HH:MM) | valid time, 24h | korean_time_format (오전/오후) |
| `date_range` | `object` {start, end} | end > start | korean_date_range_format |
| `currency` | `int` (KRW) | > 0, integer (no cents) | krw_format (₩X,XXX), korean_numeral |
| `text` | `str` (multiline) | non_empty | line_wrap, honorific_check |
| `list[string]` | `list[str]` | min_items, max_items | join, numbered_list |
| `list[object]` | `list[dict]` | item schema validation | table_format, item_template |
| `enum` | `str` | allowed_values | display_name lookup |

### 6.3 Data Source Access Pattern

Every variable slot accesses data through a standardized pattern:

```python
# Pseudo-code for data injection engine
def inject_slot(slot_config, data_context):
    source = slot_config['data_source']

    if source.get('derived'):
        value = evaluate_derived_rule(source['rule'], data_context)
    else:
        yaml_data = load_yaml(source['file'])
        value = navigate_path(yaml_data, source['field'])

        if 'filter' in source:
            value = apply_filter(value, source['filter'], data_context)

        if 'aggregate' in source:
            value = apply_aggregate(value, source['aggregate'])

        if 'transform' in source:
            value = apply_transform(value, source['transform'])

    if slot_config.get('nullable') and value is None:
        return None

    validate_slot(value, slot_config)
    return format_slot(value, slot_config)
```

### 6.4 Seal Zone Protection Rule

The seal zone is a critical pipeline safety constraint. The generation engine must enforce:

```python
def check_seal_zone_protection(template, generated_content):
    """
    P1 guard: No generated content (variable or computed) may overlap
    with any region marked guard='NO_VARIABLE_CONTENT'.
    """
    seal_zones = [r for r in template['fixed_regions']
                  if r.get('content_type') == 'reserved_seal_zone']

    for zone in seal_zones:
        for content_block in generated_content:
            if regions_overlap(zone['position'], content_block['position']):
                raise SealZoneViolationError(
                    f"Generated content {content_block['id']} overlaps seal zone {zone['id']}"
                )
    return True
```

### 6.5 Human Confirmation Gate

Before any template is used for automated generation, the confirmation gate must be passed:

```yaml
# In template YAML:
confirmed_by: null      # null = not yet confirmed
confirmed_date: null    # null = not yet confirmed

# Confirmation triggers:
# 1. template-scanner agent generates template
# 2. System presents extracted structure to human for review
# 3. Human approves or corrects slot assignments
# 4. confirmed_by and confirmed_date are set
# 5. Template is unlocked for automated generation
```

**Confirmation checklist** (presented to human reviewer):
- [ ] All fixed regions correctly identified (no variable content misclassified as fixed)
- [ ] All variable regions correctly identified (no fixed content misclassified as variable)
- [ ] Seal zone correctly marked and protected
- [ ] Data source mappings are accurate (each slot points to the correct YAML field)
- [ ] Paper size and layout parameters match the physical document
- [ ] Denomination header content is correct

### 6.6 Output Path Conventions

All generated documents follow a consistent path structure:

```
{output_root}/
├── bulletins/
│   ├── {YYYY-MM-DD}-bulletin.md
│   └── {YYYY-MM-DD}-worship-order.md
├── certificates/
│   ├── receipts/
│   │   └── {year}/
│   │       └── {member_id}-receipt-{year}.md
│   ├── baptism/
│   │   └── {year}/
│   │       └── {member_id}-baptism.md
│   └── transfer/
│       └── {year}/
│           └── {member_id}-transfer.md
├── reports/
│   ├── letters/
│   │   └── {year}/
│   │       └── {YYYY-MM-DD}-{seq:03d}-official-letter.md
│   ├── minutes/
│   │   └── {year}/
│   │       └── {YYYY-MM-DD}-{danghoae|jejikhoae}-minutes.md
│   └── invitations/
│       └── {event_id}-invitation.md
```

### 6.7 Cross-Document Data Dependencies

The pipeline must resolve cross-document dependencies before generation:

```
Bulletin generation requires:
  ← bulletin-data.yaml (sermon, worship order, announcements, prayer, offering team)
  ← schedule.yaml (service times, upcoming events)
  ← members.yaml (birthday/anniversary filter for this week)

Worship Order generation requires:
  ← bulletin-data.yaml (worship order items, sermon title/scripture/preacher)
  ← schedule.yaml (service name, date, time)

Receipt generation requires:
  ← finance.yaml (annual sum by member, categories, verification status)
  ← members.yaml (name, resident number, address)

Meeting Minutes generation requires:
  ← members.yaml (attendee list filtered by role)
  ← schedule.yaml (meeting date, time, location)
  ← church-state.yaml (agenda items, meeting number counter)

Certificate generation requires:
  ← members.yaml (name, birth date, baptism date, registration date)
  ← church-state.yaml (representative name for signature)

Official Letter generation requires:
  ← church-state.yaml (letter content, recipient, document number counter)
  ← members.yaml (for member-specific letters)

Invitation generation requires:
  ← schedule.yaml (event name, date, time, location, preacher)
  ← church-state.yaml (greeting message)
  ← members.yaml (for personalized mode only)
```

### 6.8 Validation Integration Points

Each template generation must pass through P1 validation checkpoints:

| Checkpoint | Validation Rule | Tool |
|------------|----------------|------|
| Pre-generation | All required data sources exist and are non-empty | `validate_members.py`, `validate_finance.py`, `validate_schedule.py` |
| Slot injection | Each variable slot value passes its type + constraint validation | Template engine internal |
| Seal zone guard | No content overlaps with seal zones | `check_seal_zone_protection()` |
| Output size | Generated document is ≥ 100 bytes (L0 Anti-Skip Guard) | `validate_step_output()` |
| Financial arithmetic | Receipt amounts: member sum == KRW total (tolerance 0) | `validate_finance.py` F1-F5 |
| Korean numeral | Korean numeral representation matches numeric amount exactly | `verify_korean_numeral()` |
| Date consistency | All dates in a document are internally consistent | Template engine internal |

---

## Appendix A: Slot Type Quick Reference

| Slot Type | Example Value | Korean Format Example | Source Type |
|-----------|--------------|----------------------|-------------|
| string | "김철수" | N/A | members.yaml name field |
| integer | 523 | "제 523호" | bulletin-data.yaml issue_number |
| date | "2026-03-01" | "2026년 3월 1일 주일" | bulletin-data.yaml date |
| time | "11:00" | "오전 11시 00분" | schedule.yaml time |
| date_range | {start: "2026-01-01", end: "2026-12-31"} | "2026년 1월 1일 ~ 2026년 12월 31일" | derived from finance.yaml year |
| currency | 1234000 | "₩1,234,000" / "금 일백이십삼만사천원정" | finance.yaml aggregate sum |
| text | "위와 같이..." | multiline paragraph | church-state.yaml body field |
| list[string] | ["김철수", "이영희"] | "1. 김철수\n2. 이영희" | members.yaml filtered list |
| list[object] | [{order:1, item:"묵도", detail:"", performer:"일동"}] | formatted table row | bulletin-data.yaml worship_order |
| enum | "adult" | "세례" | members.yaml baptism_type |

---

## Appendix B: Template File Naming Convention

| Document Type | Template File | Sample Input | Confirmed Output |
|---------------|---------------|--------------|------------------|
| Bulletin | `templates/bulletin-template.yaml` | `inbox/templates/bulletin-sample.jpg` | `templates/bulletin-output.md` |
| Receipt | `templates/receipt-template.yaml` | `inbox/templates/receipt-form.jpg` | `templates/receipt-output.md` |
| Worship Order | `templates/worship-template.yaml` | `inbox/templates/worship-order.jpg` | `templates/worship-output.md` |
| Official Letter | `templates/letter-template.yaml` | `inbox/templates/letter-sample.jpg` | `templates/letter-output.md` |
| Meeting Minutes | `templates/minutes-template.yaml` | `inbox/templates/meeting-minutes.jpg` | `templates/minutes-output.md` |
| Certificate | `templates/certificate-template.yaml` | `inbox/templates/certificate-sample.jpg` | `templates/certificate-output.md` |
| Invitation | `templates/invitation-template.yaml` | `inbox/templates/invitation-sample.jpg` | `templates/invitation-output.md` |

---

## Appendix C: Data Source YAML Files Cross-Reference

| YAML File | Used By Templates | Key Fields Referenced |
|-----------|------------------|-----------------------|
| `data/members.yaml` | Bulletin, Receipt, Minutes, Certificate, Invitation | name, birth_date, baptism_date, church.role, status, family.* |
| `data/finance.yaml` | Receipt | offerings[*].items[*].amount, offerings[*].type, year |
| `data/schedule.yaml` | Worship Order, Official Letter, Minutes, Invitation | regular_services[*], special_events[*] |
| `data/bulletin-data.yaml` | Bulletin, Worship Order | bulletin.*, worship_order[*], announcements[*], prayer_requests[*] |
| `church-state.yaml` | All (for church identity) + Official Letter, Minutes | church.name, church.denomination, church.representative, governance.* |

---

*End of Template Analysis — Total document types analyzed: 7 / Total verification criteria satisfied: 5*
