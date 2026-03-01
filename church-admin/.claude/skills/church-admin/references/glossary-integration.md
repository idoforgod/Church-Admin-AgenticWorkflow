# Glossary Integration Guide

How the NL interface uses `data/church-glossary.yaml` for Korean term normalization.

## Glossary Structure

```yaml
# data/church-glossary.yaml structure:
terms:
  - korean: "목사"
    english: "pastor"
    category: "roles"
    system_key: "pastor"

  - korean: "십일조"
    english: "tithe"
    category: "finance"
    system_key: "tithe"
```

## Term Categories

| Category | Count | Usage |
|----------|-------|-------|
| `roles` (직분) | ~10 | Member role assignment, search filters |
| `governance` (치리) | ~6 | Meeting types, resolution documents |
| `worship` (예배) | ~8 | Bulletin generation, service scheduling |
| `finance` (재정) | ~7 | Offering categorization, receipt generation |
| `sacraments` (성례) | ~5 | Certificate types, member milestones |
| `newcomer` (새신자) | ~6 | Pipeline stage names, welcome messages |
| `documents` (문서) | ~5 | Document type identification |
| `departments` (부서) | ~8 | Organizational filtering |

## Lookup Protocol

### 1. Exact Match (Primary)

```
Input: "집사 김철수의 헌금 내역"
       ^^^^ exact match in glossary

Result: role=deacon, operation=offering_history, name_filter="김철수"
```

### 2. Compound Term Resolution

Some Korean church terms are compound expressions:

```
"유아세례"      → infant_baptism (not "infant" + "baptism" separately)
"감사헌금"      → thanksgiving_offering (not "thanks" + "offering")
"건축헌금"      → building_fund_offering
"기부금영수증"   → donation_receipt
```

### 3. Honorific Handling

Korean honorifics must be stripped before glossary lookup:

```
"목사님"   → "목사"   → pastor
"장로님"   → "장로"   → elder
"권사님"   → "권사"   → kwonsa (senior deaconess)
"집사님"   → "집사"   → deacon
```

### 4. Denomination-Specific Terms

PCK (대한예수교장로회) specific terminology:

```
"노회"     → presbytery (PCK governance)
"총회"     → general_assembly
"당회"     → session (local church governing body)
"시찰"     → visitation_committee
```

## Integration Points

### NL Interface (SKILL.md)

The NL skill uses the glossary for:
1. **Command parsing**: Extract roles and types from Korean input
2. **Response generation**: Use correct Korean terms in output
3. **Search queries**: Normalize member role/department filters

### Agent Operations

Agents reference the glossary for:
1. **Data validation**: Verify that role/type values match glossary terms
2. **Document generation**: Use proper Korean terminology in certificates and letters
3. **Welcome messages**: Use culturally appropriate church terminology

### Glossary Maintenance

- The glossary is **append-only** — new terms can be added by ANY agent
- Existing terms should NEVER be deleted or modified (breaking change risk)
- New terms require both `korean` and `english` fields plus a `category`
- The `system_key` field must be unique across all terms
