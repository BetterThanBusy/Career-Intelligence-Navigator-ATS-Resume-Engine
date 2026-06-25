# System Architecture

## Overview

Career Intelligence Navigator is a two-feature AI platform:

1. **ATS Resume Engine** — Scores a resume against a job description, identifies gaps, rewrites bullets
2. **Career Intelligence Agent** — Analyzes career trajectory against real-time market data, generates learning paths

Both features share the same auth, database, billing, and agent infrastructure.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│                    Next.js 14 / Vercel                          │
│   ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐  │
│   │   ATS    │  │   Career     │  │Dashboard │  │ Upgrade  │  │
│   │  Scorer  │  │Intelligence  │  │          │  │  Stripe  │  │
│   └────┬─────┘  └──────┬───────┘  └────┬─────┘  └────┬─────┘  │
└────────┼───────────────┼───────────────┼──────────────┼────────┘
         │               │               │              │
         └───────────────┼───────────────┘              │
                         │ HTTPS / REST                 │ Stripe Webhook
                         ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FASTAPI BACKEND                           │
│                       Railway / Docker                          │
│                                                                 │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│   │  /api/ats    │    │ /api/career  │    │  /api/user   │     │
│   │  analyze     │    │  analyze     │    │  webhooks    │     │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘     │
│          │                   │                   │             │
│          └─────────┬─────────┘                   │             │
│                    ▼                             ▼             │
│   ┌─────────────────────────────┐  ┌─────────────────────┐    │
│   │        AGENT LAYER          │  │    MIDDLEWARE        │    │
│   │                             │  │  - Auth (Clerk JWT)  │    │
│   │  ┌─────────────────────┐   │  │  - Usage limits      │    │
│   │  │   ATS Engine        │   │  │  - Rate limiting      │    │
│   │  │   resume_parser     │   │  │  - Error handling     │    │
│   │  │   gap_analyzer      │   │  └─────────────────────┘    │
│   │  │   market_agent      │   │                             │
│   │  │   learning_path     │   │                             │
│   │  └─────────────────────┘   │                             │
│   └──────────────┬──────────────┘                             │
└──────────────────┼─────────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌───────────────┐    ┌─────────────────────────────────┐
│  PostgreSQL   │    │         EXTERNAL APIS            │
│  (Railway)    │    │                                  │
│               │    │  ┌────────────┐ ┌─────────────┐ │
│  users        │    │  │  Claude    │ │ Perplexity  │ │
│  analyses     │    │  │  Sonnet4.6 │ │   Online    │ │
│  digests      │    │  │            │ │   Search    │ │
│               │    │  └────────────┘ └─────────────┘ │
└───────────────┘    │                                  │
                     │  ┌────────────┐ ┌─────────────┐ │
                     │  │   Stripe   │ │   Resend    │ │
                     │  │ (payments) │ │   (email)   │ │
                     │  └────────────┘ └─────────────┘ │
                     └─────────────────────────────────┘
```

---

## Agent Data Flow

### ATS Analysis Flow

```
User Input
  resume_text (string or PDF upload)
  job_description (string)
       │
       ▼
[PDF Parser] ──if PDF──▶ extract text ──▶ resume_text (string)
       │
       ▼
[ATS Engine Agent] ── Claude Sonnet 4.6 ──▶ structured JSON output
  - ats_score (0-100)
  - score_breakdown
  - matched_keywords
  - missing_keywords
  - critical_fixes
  - rewritten_summary
  - rewritten_experience_bullets
  - optimized_skills_section
       │
       ▼
[DB Write] ── save to analyses table
       │
       ▼
[API Response] ── return to frontend
```

### Career Intelligence Flow

```
User Input
  resume_text
  target_role (optional)
  constraints (hours/week, budget, timeline)
       │
       ▼
[Resume Parser] ── Claude ──▶ structured profile JSON
  - current_role, years_experience
  - skills[], industries[], education[]
  - inferred_strengths[], potential_gaps[]
       │
       ▼
[Market Agent] ── Perplexity Online ──▶ live market data JSON
  - in_demand_skills[]
  - automation_risk_skills[]
  - salary_range
  - target_job_titles[]
  - growing_adjacent_roles[]
       │
       ▼
[Gap Analyzer] ── Claude ──▶ gap analysis JSON
  - gap_score (0-100)
  - critical_gaps[]
  - automation_risk_score
  - recommended_pivot
  - six_month_plan[]
       │
       ▼
[Learning Path Agent] ── Claude ──▶ learning roadmap JSON
  - roadmap[{week, focus, resources[], milestone}]
  - total_weeks
  - estimated_outcome
       │
       ▼
[DB Write] ── save full result
       │
       ▼
[API Response]
```

---

## Token Optimization Strategy

Every agent uses **structured JSON output** to minimize token usage:

```
Conversational prompt  →  ~800 tokens input, ~600 tokens output
JSON schema prompt     →  ~400 tokens input, ~300 tokens output
Savings per analysis   →  ~40% reduction in token costs
```

Rules enforced across all agents:
1. Always end system prompt with: `"Return only valid JSON. No explanation. No markdown."`
2. Define exact schema in the prompt
3. Strip any accidental markdown wrappers before `json.loads()`
4. Validate with Pydantic before writing to DB

---

## Database Schema

See [`../db/schema.sql`](../db/schema.sql) for full schema.

Core tables:
- `users` — plan, usage limits, Clerk ID mapping
- `analyses` — all ATS and career analyses (JSONB result column)
- `market_digests` — weekly digest records per user

---

## Scaling Plan

| Stage | Users | Changes |
|---|---|---|
| MVP | 0–100 | Single Railway instance, synchronous API calls |
| Growth | 100–1000 | Add Redis queue for async analysis jobs |
| Scale | 1000+ | Separate worker service, CDN for results, caching |

Current architecture handles ~100 concurrent users without changes.

---

## Cost Model

| Item | Cost | Notes |
|---|---|---|
| Railway backend | ~$5/mo | Includes PostgreSQL |
| Vercel frontend | Free | Free tier sufficient |
| Claude API | ~$0.20–0.30/analysis | Sonnet 4.6 pricing |
| Perplexity API | ~$0.05–0.10/query | Online search model |
| Resend email | Free | Up to 3k emails/mo |
| Cloudflare R2 | Free | Up to 10GB storage |
| **Total at 0 users** | **~$5/mo** | |
| **Total at 100 Pro users** | **~$35–50/mo** | Revenue: ~$2,900/mo |
