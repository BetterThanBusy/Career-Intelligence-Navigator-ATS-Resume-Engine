# ADR 001: Stack Selection

**Date:** 2026-06-25  
**Status:** Accepted  
**Author:** Better Than Busy

---

## Context

We are building a career intelligence platform with two features:
1. ATS Resume Scorer
2. Career Gap Analyzer + Learning Path Generator

We need to choose a tech stack that is:
- Deployable in 2 weeks
- Costs under $10/month at launch
- Scalable to 1,000+ users without rewriting
- Maintainable by a solo technical founder

---

## Decisions

### Backend: FastAPI (Python) on Railway

**Chosen:** FastAPI + Python  
**Rejected:** Node.js/Express, Django

**Reasoning:**
- Anthropic and Perplexity SDKs have first-class Python support
- FastAPI is async-native, handles concurrent AI requests well
- Pydantic validation is perfect for JSON schema enforcement
- Python ecosystem for AI/data work is unmatched
- Railway is zero-config, handles Python Nixpacks builds automatically

### Frontend: Next.js 14 on Vercel

**Chosen:** Next.js 14 App Router  
**Rejected:** Create React App, Vite + React, SvelteKit

**Reasoning:**
- Vercel free tier is genuinely production-grade
- App Router enables server components for faster initial loads
- Next.js + Vercel is the lowest friction full-stack deploy path
- Large ecosystem of UI components (shadcn/ui)

### Auth: Clerk

**Chosen:** Clerk  
**Rejected:** NextAuth, Supabase Auth, Auth0, rolling our own

**Reasoning:**
- 10 minutes to implement vs days for alternatives
- Free tier covers 10,000 MAU — more than enough for launch
- Handles social login, magic links, JWT verification out of the box
- Webhook to sync users to our PostgreSQL on sign-up

### Database: PostgreSQL on Railway

**Chosen:** PostgreSQL  
**Rejected:** Supabase, PlanetScale, MongoDB, SQLite

**Reasoning:**
- JSONB column type handles our variable AI output perfectly
- Railway includes PostgreSQL in the $5/month plan — no separate cost
- GIN indexing on JSONB enables fast queries on analysis results
- Standard SQL — no vendor lock-in

### AI: Claude Sonnet 4.6 + Perplexity

**Chosen:** Claude Sonnet 4.6 for reasoning, Perplexity for live search  
**Rejected:** GPT-4o, Gemini Pro, single-model approach

**Reasoning:**
- Claude Sonnet 4.6 produces the most reliable structured JSON output
- Perplexity's online models pull live web data — critical for real-time market intelligence
- No other combination gives us both reasoning quality AND live data
- Cost: ~$0.30-0.50 per full analysis (acceptable margin at $29/mo Pro)

### Payments: Stripe

**Chosen:** Stripe  
**Rejected:** Paddle, LemonSqueezy, manual invoicing

**Reasoning:**
- Industry standard, no alternative evaluation needed
- Webhook → DB plan update pattern is well-documented
- 2.9% fee is acceptable at our price point

---

## Cost Model Validation

At 100 Pro users ($29/month):
- Revenue: $2,900/month
- Railway: $5/month
- Claude API (avg 20 analyses/user × $0.45): $900/month
- Perplexity API: ~$50/month
- Resend email: Free
- **Gross profit: ~$1,945/month (~67% margin)**

At 1,000 Pro users:
- Revenue: $29,000/month
- Infrastructure + API: ~$10,000/month
- **Gross profit: ~$19,000/month (~65% margin)**

Margins are healthy and stable due to per-use API pricing.

---

## What We Will Revisit at 500+ Users

1. **Redis queue** — async analysis jobs (currently synchronous, fine under 100 concurrent)
2. **CDN caching** — cache market intelligence results by role (same role = same Perplexity call)
3. **Fine-tuned model** — if Claude costs grow, consider fine-tuning a smaller model on our analysis patterns
4. **Separate worker service** — decouple analysis jobs from API server
