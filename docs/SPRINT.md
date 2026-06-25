# 2-Week Deployment Sprint

**Goal:** Ship Career Intelligence Navigator (ATS + Career Gap) to production  
**Deadline:** 2 weeks from start  
**Status:** 🔄 Week 1 In Progress

---

## Week 1: Backend + Core Agents

| Day | Task | Status | Notes |
|---|---|---|---|
| 1 | Railway project setup + PostgreSQL + run schema.sql | ⬜ | |
| 1 | Set all environment variables in Railway | ⬜ | |
| 1 | Verify FastAPI health check deploys successfully | ⬜ | |
| 2 | Port existing ATS engine into `ats_engine.py` | ⬜ | You already built this in 1hr |
| 2 | Test ATS engine with 5 real resumes + JDs | ⬜ | Aim for consistent JSON output |
| 2 | Add Pydantic validation to ATS output | ⬜ | |
| 3 | Build and test `resume_parser.py` | ⬜ | Test with 3 diverse resume types |
| 3 | Build and test `market_agent.py` (Perplexity) | ⬜ | Verify live data is returning |
| 4 | Build and test `gap_analyzer.py` | ⬜ | Run end-to-end: parser → market → gap |
| 4 | Build and test `learning_path.py` | ⬜ | Verify with budget=free constraint |
| 5 | Wire all agents into `/api/career/analyze` route | ⬜ | Full chain test |
| 5 | Test full career analysis end-to-end via curl | ⬜ | |
| 6 | Add Clerk auth + `get_current_user` middleware | ⬜ | |
| 6 | Add usage limit checks (free: 2 ATS, 1 career) | ⬜ | |
| 6 | Add `save_analysis` + `check_usage_limit` DB queries | ⬜ | |
| 7 | Add PDF upload + text extraction (`pdf_parser.py`) | ⬜ | |
| 7 | End-to-end backend test: auth → analyze → save | ⬜ | |
| 7 | Deploy backend to Railway, verify in production | ⬜ | |

**Week 1 Done When:**
- [ ] `/health` returns 200 on Railway
- [ ] ATS analysis returns valid JSON in <10 seconds
- [ ] Career analysis returns valid JSON in <30 seconds
- [ ] Auth works — unauthenticated requests return 401
- [ ] Usage limits enforce correctly
- [ ] Results save to PostgreSQL

---

## Week 2: Frontend + Auth + Payments + Launch

| Day | Task | Status | Notes |
|---|---|---|---|
| 8 | Next.js 14 scaffold with Clerk provider | ⬜ | |
| 8 | Dashboard layout + navigation shell | ⬜ | |
| 8 | Connect frontend to Railway backend URL | ⬜ | |
| 9 | ATS tool page: paste resume + JD → results | ⬜ | Show score, keywords, rewrites |
| 9 | ATS results: score breakdown chart | ⬜ | Simple bar chart, Recharts |
| 9 | PDF upload on ATS page | ⬜ | |
| 10 | Career intelligence page: resume paste → full report | ⬜ | |
| 10 | Career results: gap score, automation risk, 6-month plan | ⬜ | |
| 10 | Learning path display: week-by-week roadmap | ⬜ | |
| 11 | Stripe: upgrade page with Pro + Teams pricing | ⬜ | |
| 11 | Stripe webhook → update user plan in DB | ⬜ | |
| 11 | Paywall: show upgrade prompt when limit reached | ⬜ | |
| 12 | Deploy frontend to Vercel | ⬜ | |
| 12 | Set all Vercel environment variables | ⬜ | |
| 12 | End-to-end test: sign up → analyze → upgrade → unlimited | ⬜ | |
| 13 | 10 beta users: send access, collect feedback | ⬜ | Use existing network |
| 13 | Fix critical bugs from beta feedback | ⬜ | |
| 14 | Write LinkedIn launch post | ⬜ | "I built this in 2 weeks" |
| 14 | Go live 🚀 | ⬜ | |

**Week 2 Done When:**
- [ ] User can sign up, run ATS analysis, see results
- [ ] User can run career analysis, see full report
- [ ] Free limits enforce with upgrade prompt
- [ ] Stripe checkout works end-to-end
- [ ] 10 beta users tested and gave feedback
- [ ] Live on production URL

---

## Launch Checklist

### Before Going Live
- [ ] Privacy policy page (use a generator)
- [ ] Terms of service page
- [ ] Error monitoring (Sentry free tier — 10 min setup)
- [ ] Remove all test API keys, use production keys
- [ ] HTTPS on both domains (automatic on Railway + Vercel)
- [ ] Test Stripe in live mode (not test mode)

### Day of Launch
- [ ] LinkedIn post: "I built Career Intelligence Navigator in 2 weeks. Here's what it does."
- [ ] Post ATS tool screenshot + 1 example analysis result
- [ ] DM 20 people in your network who fit the ICP
- [ ] Reply to every comment in first 2 hours

---

## API Keys Needed Before Day 1

| Key | Where to Get | Time to Get |
|---|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com | 5 minutes |
| `PERPLEXITY_API_KEY` | perplexity.ai/api | 5 minutes |
| `CLERK_SECRET_KEY` | dashboard.clerk.com | 10 minutes |
| `STRIPE_SECRET_KEY` | dashboard.stripe.com | 10 minutes |
| `RESEND_API_KEY` | resend.com | 5 minutes |
| `RAILWAY_TOKEN` | railway.app | 5 minutes |

**Total setup time: ~40 minutes**

---

## Cost Tracker

| Item | Monthly Cost |
|---|---|
| Railway (backend + DB) | $5.00 |
| Vercel (frontend) | $0.00 |
| Anthropic API | Pay per use |
| Perplexity API | Pay per use |
| Clerk | $0.00 |
| Resend | $0.00 |
| **Fixed monthly total** | **~$5.00** |
