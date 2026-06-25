# Deployment Guide

## Backend → Railway

### Step 1: Install Railway CLI
```bash
npm install -g @railway/cli
```

### Step 2: Login and initialize
```bash
railway login
cd backend
railway init
# Select: Create new project → Name it "career-intelligence-navigator"
```

### Step 3: Add PostgreSQL
```bash
railway add
# Select: PostgreSQL
# Railway auto-sets DATABASE_URL in your environment
```

### Step 4: Run database schema
```bash
# Get your DATABASE_URL from Railway dashboard
psql $DATABASE_URL -f db/schema.sql
```

### Step 5: Set environment variables
```bash
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set PERPLEXITY_API_KEY=pplx-...
railway variables set CLERK_SECRET_KEY=sk_live_...
railway variables set CLERK_JWT_ISSUER=https://your-instance.clerk.accounts.dev
railway variables set STRIPE_SECRET_KEY=sk_live_...
railway variables set STRIPE_WEBHOOK_SECRET=whsec_...
railway variables set RESEND_API_KEY=re_...
railway variables set EMAIL_FROM=hello@yourdomain.com
railway variables set APP_ENV=production
railway variables set FRONTEND_URL=https://your-app.vercel.app
```

### Step 6: Create railway.toml
```bash
# Already exists at root of backend/
# Verify it has the correct start command
```

### Step 7: Deploy
```bash
railway up
```

### Step 8: Verify
```bash
# Get your Railway URL from dashboard
curl https://your-app.railway.app/health
# Should return: {"status": "ok", "version": "1.0.0"}
```

---

## Frontend → Vercel

### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

### Step 2: Deploy
```bash
cd frontend
vercel
# Follow prompts: link to existing project or create new
```

### Step 3: Set environment variables in Vercel dashboard
```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
STRIPE_SECRET_KEY=sk_live_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### Step 4: Deploy to production
```bash
vercel --prod
```

---

## Stripe Webhook Setup

1. Go to Stripe Dashboard → Webhooks
2. Add endpoint: `https://your-backend.railway.app/api/webhooks/stripe`
3. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy webhook secret → set as `STRIPE_WEBHOOK_SECRET` in Railway

---

## Custom Domain (Optional)

Railway: Settings → Domains → Add custom domain  
Vercel: Settings → Domains → Add domain  
Both support automatic SSL.

---

## Monitoring

Add Sentry (free tier) for error tracking:

```bash
pip install sentry-sdk[fastapi]
```

```python
# In main.py, add at top:
import sentry_sdk
sentry_sdk.init(dsn="https://your-sentry-dsn", traces_sample_rate=0.1)
```

---

## Rollback

```bash
# Railway keeps last 5 deployments
railway rollback
```
