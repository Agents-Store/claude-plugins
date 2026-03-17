---
name: report-generation
description: Report templates and generation guidelines — Executive Summary, Deep Research Report, and Comparison Table formats with methodology and citation rules. Use when formatting research results into structured reports.
---

# Report Generation

3 шаблона отчётов с правилами цитирования и обязательной секцией Methodology.

## Template Selection

| Тип исследования | Primary шаблон | Alternative |
|-----------------|---------------|-------------|
| Competitive Analysis | Comparison Table | Deep Research Report |
| Market Research | Deep Research Report | Executive Summary |
| Technical Audit | Deep Research Report | — |
| Person/Company Lookup | Executive Summary | — |
| Topic Deep Dive | Deep Research Report | — |
| News & Trends | Executive Summary | Deep Research Report |

## Template 1: Executive Summary

Краткий формат для быстрых исследований и фактических запросов.

```markdown
# {Topic} — Executive Summary

**Date:** {YYYY-MM-DD}
**Research Depth:** {quick | standard | deep}

## Key Findings

- Finding 1 [Source](url)
- Finding 2 [Source](url)
- Finding 3 [Source](url)

## Overview

{2-3 параграфа с основными выводами}

## Key Data Points

| Metric | Value | Source |
|--------|-------|--------|
| {metric} | {value} | [Source](url) |

## Recommendations

1. {Рекомендация 1}
2. {Рекомендация 2}

## Sources

1. [{Title}]({url}) — accessed {YYYY-MM-DD}
2. [{Title}]({url}) — accessed {YYYY-MM-DD}

## Methodology

- **Research type:** {type}
- **Tools used:** {list of tools with providers}
- **Queries executed:** {count}
- **Pages analyzed:** {count}
- **Date range:** {if applicable}
```

## Template 2: Deep Research Report

Полный формат для глубоких исследований.

```markdown
# {Topic} — Deep Research Report

**Date:** {YYYY-MM-DD}
**Research Depth:** {quick | standard | deep}

## Executive Summary

{3-5 предложений с ключевыми выводами}

## Background

{Контекст: почему это важно, текущая ситуация}

## Findings

### {Section 1: Aspect/Angle}

{Детальные находки с inline-цитатами [Source](url)}

### {Section 2: Aspect/Angle}

{Детальные находки}

### {Section 3: Aspect/Angle}

{Детальные находки}

## Analysis

{Кросс-анализ источников: паттерны, тренды, противоречия}

## Data & Metrics

| Metric | Value | Source | Confidence |
|--------|-------|--------|------------|
| {metric} | {value} | [Source](url) | High/Medium/Low |

## Key Quotes

> "{Цитата}" — {Author/Source}, [{Link}]({url})

## Gaps & Limitations

- {Что не удалось найти}
- {Противоречивые данные}
- {Ограничения исследования}

## Recommendations

1. {Рекомендация 1} — обоснование
2. {Рекомендация 2} — обоснование

## Sources

1. [{Title}]({url}) — accessed {YYYY-MM-DD}
2. [{Title}]({url}) — accessed {YYYY-MM-DD}

## Methodology

- **Research type:** {type}
- **Tools used:** {list with providers}
- **Search queries:**
  1. "{query 1}"
  2. "{query 2}"
  3. "{query 3}"
- **Pages analyzed:** {count}
- **Date of research:** {YYYY-MM-DD}
- **Limitations:** {any access issues, paywalls, blocked content}
```

## Template 3: Comparison Table

Формат для сравнительного анализа (Competitive Analysis).

```markdown
# {Item A} vs {Item B} vs {Item C} — Comparative Analysis

**Date:** {YYYY-MM-DD}

## Summary

{Краткий обзор сравнения, 2-3 предложения}

## Feature Comparison

| Feature | {Item A} | {Item B} | {Item C} |
|---------|----------|----------|----------|
| **Price** | {value} | {value} | {value} |
| **{Feature 1}** | {value} | {value} | {value} |
| **{Feature 2}** | {value} | {value} | {value} |
| **{Feature 3}** | {value} | {value} | {value} |

## Detailed Analysis

### {Item A}

**Strengths:**
- {strength 1} [Source](url)
- {strength 2}

**Weaknesses:**
- {weakness 1}

**Best for:** {use case}

### {Item B}

**Strengths:**
- {strength 1} [Source](url)

**Weaknesses:**
- {weakness 1}

**Best for:** {use case}

### {Item C}

**Strengths / Weaknesses / Best for...**

## Verdict

{Рекомендация в зависимости от use case:}
- **Для {use case 1}:** выбрать {Item}
- **Для {use case 2}:** выбрать {Item}

## Sources

1. [{Title}]({url}) — accessed {YYYY-MM-DD}

## Methodology

- **Research type:** Competitive Analysis
- **Tools used:** {list}
- **Items compared:** {count}
- **Criteria evaluated:** {count}
- **Pages analyzed:** {count}
```

## Methodology Section — обязательные поля

Каждый отчёт ДОЛЖЕН содержать секцию Methodology с:

1. **Research type** — один из 6 типов
2. **Tools used** — какие инструменты и от каких провайдеров
3. **Search queries** — список использованных запросов
4. **Pages analyzed** — количество прочитанных страниц
5. **Date of research** — дата проведения
6. **Limitations** — ограничения (paywalls, blocked content, missing data)

## Citation Format

### Inline цитирование
```
Размер рынка AI code assistants составляет $5.2B [Gartner](https://gartner.com/report)
```

### Список источников
```
1. [Gartner: AI Code Assistant Market Report](https://gartner.com/report) — accessed 2026-03-16
2. [TechCrunch: The Rise of AI Coding Tools](https://techcrunch.com/article) — accessed 2026-03-16
```

### Уровни уверенности
| Уровень | Критерий | Использование |
|---------|---------|--------------|
| **High** | 3+ независимых источника подтверждают | Для фактов и цифр |
| **Medium** | 2 источника подтверждают | Для оценок и прогнозов |
| **Low** | 1 источник или противоречивые данные | Обязательно отметить в тексте |

## Best Practices

1. **Каждый факт — с URL** — без исключений
2. **Cross-check цифры** — данные из одного источника помечать как Low confidence
3. **Gaps обязательны** — честно указывать что не найдено
4. **Дата в каждом отчёте** — исследования устаревают
5. **Methodology прозрачна** — читатель должен понимать как проводилось исследование
6. **Таблицы для данных** — числовые сравнения всегда в таблицах
7. **Quotes для подкрепления** — прямые цитаты повышают достоверность
