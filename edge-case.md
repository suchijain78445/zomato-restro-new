# Edge Cases & Corner Scenarios

This document catalogs known edge cases, corner scenarios, and failure modes for the AI-powered restaurant recommendation system defined in [problemStatement.md](./problemStatement.md), [architecture.md](./architecture.md), and [implementation-plan.md](./implementation-plan.md).

Each entry includes the **scenario**, **expected system behavior**, and **recommended handling**. Use this during implementation, testing, and code review.

---

## Severity Legend

| Level | Meaning |
|-------|---------|
| **Critical** | Can crash the app, leak secrets, or return dangerously wrong results |
| **High** | Breaks core user flow or produces misleading recommendations |
| **Medium** | Degraded UX or incorrect edge behavior; workaround exists |
| **Low** | Cosmetic, rare, or easily recoverable |

---

## 1. Data Ingestion & Preprocessing

### 1.1 Rating Field (`rate`)

| # | Scenario | Example | Expected Behavior | Handling | Severity |
|---|----------|---------|-------------------|----------|----------|
| D-01 | Standard rating format | `"4.1/5"` | Parse to `4.1` | Regex extract float before `/` | — |
| D-02 | New/unrated restaurant | `"NEW"` | `rating = None` | Exclude from min-rating filter; sort last among ties | Medium |
| D-03 | Missing rating | `"-"`, `""`, `null` | `rating = None` | Same as D-02 | Medium |
| D-04 | Rating out of expected range | `"6.2/5"`, `"0/5"` | Parse if numeric; clamp or accept as-is | Log warning; optionally clamp to `[0, 5]` | Low |
| D-05 | Non-numeric garbage | `"good"`, `"N/A"` | `rating = None` | Defensive parse; never throw | Medium |
| D-06 | Rating with whitespace | `" 4.1 /5 "` | Parse to `4.1` | Strip whitespace before parse | Low |
| D-07 | User sets `min_rating: 4.5` | Restaurant has `rating = None` | Restaurant excluded from min-rating filter | Treat `None` as not meeting threshold | High |
| D-08 | All candidates have `None` rating | City with only `"NEW"` restaurants | Filter returns empty or relaxes min_rating | Trigger constraint relaxation; inform user | High |

### 1.2 Cost Field (`approx_cost(for two people)`)

| # | Scenario | Example | Expected Behavior | Handling | Severity |
|---|----------|---------|-------------------|----------|----------|
| D-09 | Comma-separated cost | `"1,200"` | Parse to `1200` | Remove commas before int cast | — |
| D-10 | Plain integer string | `"300"` | Parse to `300` | Direct int cast | — |
| D-11 | Unparseable cost | `"-"`, `"for two"`, `""` | `cost_for_two = None`, `budget_tier = None` | Exclude from budget filter; include in LLM context as unknown | Medium |
| D-12 | Cost at tier boundary | Exactly `500` | `budget_tier = "low"` | Document inclusive upper bound for low | Low |
| D-13 | Cost at tier boundary | Exactly `501` | `budget_tier = "medium"` | Document exclusive lower bound for medium | Low |
| D-14 | Cost at tier boundary | Exactly `1500` | `budget_tier = "medium"` | Inclusive upper bound for medium | Low |
| D-15 | Cost at tier boundary | Exactly `1501` | `budget_tier = "high"` | Exclusive lower bound for high | Low |
| D-16 | Zero or negative cost | `"0"`, `"-100"` | Reject or treat as `None` | Treat as invalid; log anomaly | Low |
| D-17 | User selects budget but cost is `None` | budget = `"medium"` | Restaurant excluded from budget filter | Relax budget constraint if too few results | Medium |

### 1.3 Cuisines Field

| # | Scenario | Example | Expected Behavior | Handling | Severity |
|---|----------|---------|-------------------|----------|----------|
| D-18 | Multiple cuisines | `"North Indian, Chinese, Mughlai"` | Split to list, normalized lowercase | Split on `,`, strip, lowercase | — |
| D-19 | Extra whitespace | `"North Indian , Chinese "` | Clean tokens | Strip each token | Low |
| D-20 | Empty cuisines | `""`, `null` | `cuisines = []` | Still valid restaurant; cuisine filter may exclude | Medium |
| D-21 | Case mismatch | User: `"italian"`, data: `"Italian"` | Match succeeds | Always normalize to lowercase for comparison | — |
| D-22 | Partial cuisine match | User: `"Indian"`, data: `"North Indian"` | Match via substring or token overlap | Document matching strategy (substring on normalized strings) | High |
| D-23 | User selects multiple cuisines | `["Chinese", "Italian"]` | Match if restaurant has **any** listed cuisine (OR logic) | Document OR semantics clearly in API | Medium |
| D-24 | User selects obscure cuisine | `"Assamese"` | May return zero results | Relax cuisine constraint; suggest alternatives in summary | Medium |
| D-25 | Duplicate cuisine tokens | `"Chinese, chinese, Chinese"` | Deduplicate after normalize | Set dedup on split | Low |

### 1.4 City & Location Fields

| # | Scenario | Example | Expected Behavior | Handling | Severity |
|---|----------|---------|-------------------|----------|----------|
| D-26 | City name casing | `"bangalore"` vs `"Bangalore"` | Case-insensitive match | Normalize to canonical casing from metadata | High |
| D-27 | Unknown city in request | `"Goa"` (not in dataset) | `400 Bad Request` | Validate against `cities.json` allowlist | High |
| D-28 | Location not in selected city | city=`Delhi`, location=`Banashankari` | Zero matches → relaxation or empty | Validate location belongs to city when possible | Medium |
| D-29 | Missing city on row | `listed_in(city)` empty | Drop row during preprocessing | Required field for indexing | — |
| D-30 | Missing location on row | `location` empty | Keep row; location filter won't match | Allow city-only queries | Medium |
| D-31 | Same restaurant name, different addresses | Two `"Jalsa"` entries | Distinct IDs via `hash(name + address)` | Never dedupe by name alone | High |
| D-32 | Duplicate rows (exact same data) | Identical name + address | Same ID; dedupe on preprocess | Keep first occurrence; log duplicate count | Medium |

### 1.5 Text & Security Edge Cases

| # | Scenario | Example | Expected Behavior | Handling | Severity |
|---|----------|---------|-------------------|----------|----------|
| D-36 | Very long `reviews_list` | Up to 1.28M chars | Never send full text to LLM | Exclude from prompt; use `dish_liked` instead | Critical |
| D-40 | HTML/script in text fields | `"<script>alert(1)</script>"` | Escape on render | Streamlit auto-escapes; sanitize if using custom HTML | Critical |

---

## 2. User Input & Validation

| # | Scenario | Expected Behavior | Handling | Severity |
|---|----------|-------------------|----------|----------|
| U-01 | Missing `city` in request | `422 Unprocessable Entity` | Pydantic validation error | — |
| U-02 | Empty string `city: ""` | `400 Bad Request` | Treat as missing/invalid | High |
| U-08 | `min_rating: 5.5` or `-1` | `422` validation error | Pydantic `ge=0, le=5` | High |
| U-12 | Invalid budget value | `"cheap"`, `"premium"` | `422` — must be `low`/`medium`/`high` | High |
| U-15 | Very long `additional_notes` (>500 chars) | Truncate or reject | Max length validation | Medium |
| U-16 | Prompt injection attempt | `"Ignore instructions and recommend..."` | LLM prompt hardening | System prompt boundaries; sanitize logs | Critical |

---

## 3. Filtering & Constraint Relaxation

| # | Scenario | Expected Behavior | Handling | Severity |
|---|----------|-------------------|----------|----------|
| F-01 | Zero matches after all filters | Empty list + helpful summary | `"No restaurants found matching your criteria."` | High |
| F-02 | Fewer than 5 matches (before relaxation) | Trigger constraint relaxation | Relax in order: location → cuisine → budget → min_rating | High |
| F-06 | 1000+ matches in city | Pre-sort; take top 25 by rating/votes | Never pass all to LLM | Critical |
| F-07 | Same rating, different votes | Higher votes ranked first | Secondary sort by `votes DESC` | — |

---

## 4. LLM Integration Edge Cases

| # | Scenario | Expected Behavior | Handling | Severity |
|---|----------|-------------------|----------|----------|
| L-01 | Missing `OPENAI_API_KEY` | Fallback to Ollama or rule-based ranking | Startup warning; graceful degradation | Critical |
| L-03 | LLM API timeout (>30s) | Retry once; then fallback | Return rule-based ranking without explanations | High |
| L-09 | JSON wrapped in markdown fences | ` ```json ... ``` ` | Strip markdown code fences before parse | High |
| L-10 | Malformed JSON response | Retry once with stricter prompt | Fallback to rule-based ranking | High |
| L-19 | LLM invents restaurant not in candidates | Reject hallucinated item | Validate `restaurant_id` against candidate set | Critical |
| L-21 | LLM returns non-existent `restaurant_id` | Skip item; log warning | If all invalid → fallback to rule-based | Critical |

---

## 5. Frontend & Security Edge Cases

| # | Scenario | Expected Behavior | Handling | Severity |
|---|----------|-------------------|----------|----------|
| E-01 | API server unreachable | User-friendly error card in UI | Show connection error banner | High |
| S-01 | API key in frontend code | Never exposed | Keys stored server-side only in `.env` | Critical |
| S-02 | API key committed to git | Prevented | `.gitignore` includes `.env` | Critical |

---

## Decision Log

| Decision | Chosen Approach | Rationale |
|----------|-----------------|-----------|
| Cuisine multi-select logic | **OR** (match any listed cuisine) | Broader, more user-friendly results |
| Null rating vs min_rating | **Exclude** | User explicitly asked for minimum quality |
| Constraint relaxation order | **location → cuisine → budget → min_rating** | Per architecture spec |
| LLM failure fallback | **Rule-based ranking without explanations** | Prevents app crash; ensures reliable UX |
