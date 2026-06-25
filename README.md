# Career Intelligence Navigator

> **Work Smarter. Build Faster. Think Better.**  
> An AI-powered platform that analyzes your resume against real job market data, scores it against ATS systems, identifies skill gaps, and generates a personalized learning path to close them.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)
[![Vercel](https://img.shields.io/badge/Frontend-Vercel-black)](https://vercel.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What This Does

| Feature | Description |
|---|---|
| **ATS Resume Scorer** | Upload your resume + job description. Get a score, missing keywords, rewritten bullets, and an optimized summary. |
| **Career Gap Analyzer** | Compares your experience against live job market data. Returns a gap score, automation risk, and pivot recommendations. |
| **Learning Path Generator** | Builds a week-by-week roadmap with real resources to close your skill gaps. |
| **Weekly Market Digest** | Automated email with trending skills, salary movements, and role demand shifts for your target role. |

---

## Tech Stack

```
Frontend    Next.js 14 (App Router)      → Vercel (free)
Backend     FastAPI (Python)             → Railway (~$5/mo)
Database    PostgreSQL                   → Railway (included)
Auth        Clerk                        → Free tier
Payments    Stripe                       → Pay-per-transaction
AI          Claude Sonnet 4.6            → Anthropic API
Search      Perplexity API               → Real-time job market data
Email       Resend                       → Free tier (3k/mo)
Storage     Cloudflare R2                → PDF uploads (free)
```

**Total fixed infra cost: ~$5–10/month**  
**Cost per analysis: ~$0.30–0.50**

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (or Railway account)
- API keys: Anthropic, Perplexity, Clerk, Stripe, Resend

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Fill in your API keys
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local  # Fill in your keys
npm run dev
```

### Database Setup

```bash
cd backend
python scripts/init_db.py
```

---

## Project Structure

```
career-intelligence-navigator/
├── backend/
│   ├── agents/              # AI agent logic
│   │   ├── ats_engine.py         # ATS analysis + resume rewrite
│   │   ├── resume_parser.py      # Structured resume extraction
│   │   ├── market_agent.py       # Perplexity job market intelligence
│   │   ├── gap_analyzer.py       # Gap analysis engine
│   │   └── learning_path.py      # Learning path generator
│   ├── api/
│   │   └── routes/
│   │       ├── ats.py            # POST /api/ats/analyze
│   │       ├── career.py         # POST /api/career/analyze
│   │       └── user.py           # User management
│   ├── db/
│   │   ├── connection.py         # PostgreSQL connection
│   │   ├── queries.py            # DB operations
│   │   └── schema.sql            # Full DB schema
│   ├── utils/
│   │   ├── pdf_parser.py         # PDF → text extraction
│   │   └── token_counter.py      # API cost tracking
│   ├── main.py                   # FastAPI entry point
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── dashboard/            # Main user dashboard
│   │   ├── ats/                  # ATS scorer UI
│   │   ├── career/               # Career intelligence UI
│   │   └── upgrade/              # Stripe paywall
│   ├── components/
│   │   ├── ui/                   # Reusable UI components
│   │   └── charts/               # Data visualizations
│   └── lib/
│       ├── api.ts                # API client
│       └── utils.ts
├── docs/
│   ├── architecture/
│   │   ├── SYSTEM_ARCHITECTURE.md
│   │   ├── DATA_FLOW.md
│   │   └── AGENT_DESIGN.md
│   ├── api/
│   │   └── API_REFERENCE.md
│   └── decisions/
│       └── ADR_001_stack_selection.md
├── scripts/
│   ├── init_db.py
│   └── seed_data.py
└── .github/
    ├── workflows/
    │   ├── deploy-backend.yml
    │   └── deploy-frontend.yml
    └── ISSUE_TEMPLATE/
        ├── bug_report.md
        └── feature_request.md
```

---

## Monetization

| Plan | Price | ATS Analyses | Career Analyses | Weekly Digest |
|---|---|---|---|---|
| Free | $0 | 2/month | 1/month | ✗ |
| Pro | $29/mo | Unlimited | Unlimited | ✓ |
| Teams | $79/mo | Unlimited × 5 seats | Unlimited × 5 seats | ✓ + HR Dashboard |

---

## Deployment

### Backend (Railway)
```bash
railway login
railway init
railway variables set ANTHROPIC_API_KEY=...
railway up
```

### Frontend (Vercel)
```bash
vercel --prod
```

Full deployment guide: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)

---

## Build Log

This project is being built in public as part of [Better Than Busy](https://betterthanbusy.com).

| Week | Milestone | Status |
|---|---|---|
| Week 1 | Backend agents + API routes | 🔄 In Progress |
| Week 2 | Frontend + auth + payments + deploy | ⬜ Planned |

Follow the journey on [LinkedIn](#) and [YouTube](#).

---

## Contributing

This is an active production build. Issues and PRs welcome after v1.0 launch.

---

## License

MIT — built by [Better Than Busy](https://betterthanbusy.com)
