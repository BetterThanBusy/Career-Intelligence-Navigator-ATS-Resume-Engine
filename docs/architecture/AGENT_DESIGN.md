# Agent Design

## Philosophy

Every agent in this system follows three rules:

1. **Structured output only** — all agents return JSON, never prose
2. **Single responsibility** — each agent does one thing well
3. **Fail loudly** — agents raise clear errors rather than returning partial data

---

## Agent Inventory

### 1. ATS Engine (`ats_engine.py`)

**Purpose:** Score a resume against a job description. Rewrite resume elements for ATS optimization.

**Input:**
```json
{
  "resume_text": "string",
  "job_description": "string"
}
```

**Output:**
```json
{
  "ats_score": 72,
  "score_breakdown": {
    "keyword_match": 65,
    "skills_alignment": 80,
    "experience_relevance": 75,
    "formatting_score": 70
  },
  "matched_keywords": ["Python", "data analysis", "stakeholder management"],
  "missing_keywords": ["SQL", "Tableau", "A/B testing"],
  "missing_skills": ["statistical modeling", "dashboard design"],
  "strengths": ["Strong leadership narrative", "Quantified achievements"],
  "critical_fixes": [
    {
      "issue": "Missing SQL — appears 7x in JD",
      "fix": "Add SQL to skills. Rewrite data bullet to mention SQL queries.",
      "priority": "high"
    }
  ],
  "rewritten_summary": "...",
  "rewritten_experience_bullets": [
    { "original": "...", "rewritten": "..." }
  ],
  "optimized_skills_section": ["SQL", "Python", "Tableau", "..."],
  "final_verdict": "maybe",
  "verdict_reason": "Strong experience but missing 3 critical technical keywords"
}
```

**Model:** Claude Sonnet 4.6  
**Avg tokens:** ~1,200 input / ~800 output  
**Avg cost:** ~$0.15 per analysis

---

### 2. Resume Parser (`resume_parser.py`)

**Purpose:** Extract structured profile data from raw resume text.

**Input:** `resume_text: str`

**Output:**
```json
{
  "current_role": "Senior Marketing Manager",
  "years_experience": 8,
  "skills": ["Google Analytics", "SQL", "Campaign Management"],
  "industries": ["SaaS", "E-commerce"],
  "education": ["MBA - Marketing", "BSc - Business"],
  "notable_achievements": ["Grew MQL pipeline by 40%"],
  "inferred_strengths": ["Data-driven decision making", "Cross-functional leadership"],
  "potential_gaps": ["AI/ML tools", "Marketing automation platforms"]
}
```

**Model:** Claude Sonnet 4.6  
**Avg tokens:** ~800 input / ~400 output  
**Avg cost:** ~$0.05 per parse

---

### 3. Market Agent (`market_agent.py`)

**Purpose:** Pull real-time job market intelligence for a given role and skill set.

**Input:**
```json
{
  "role": "Marketing Manager",
  "skills": ["Google Analytics", "SQL", "Campaign Management"]
}
```

**Output:**
```json
{
  "in_demand_skills": ["AI literacy", "Marketing automation", "Predictive analytics"],
  "skills_at_risk": ["Manual reporting", "Basic copywriting"],
  "salary_range": { "low": 85000, "mid": 105000, "high": 135000, "currency": "USD" },
  "target_job_titles": ["Growth Marketing Manager", "Director of Demand Gen"],
  "growing_adjacent_roles": ["Revenue Operations Manager", "AI Marketing Strategist"],
  "market_summary": "Marketing roles increasingly require AI tool proficiency...",
  "data_sources": ["LinkedIn Jobs", "Indeed", "Glassdoor", "recent industry reports"],
  "retrieved_at": "2026-06-25T10:00:00Z"
}
```

**Model:** Perplexity `llama-3.1-sonar-large-128k-online`  
**Avg tokens:** ~400 input / ~600 output  
**Avg cost:** ~$0.05–0.10 per query  
**Key advantage:** Live web search — no stale training data

---

### 4. Gap Analyzer (`gap_analyzer.py`)

**Purpose:** Compare user profile against market data to produce actionable gap intelligence.

**Input:** `user_profile: dict` + `market_data: dict`

**Output:**
```json
{
  "gap_score": 58,
  "critical_gaps": [
    { "skill": "AI literacy", "urgency": "high", "reason": "Appears in 73% of senior marketing JDs" },
    { "skill": "Marketing automation", "urgency": "high", "reason": "HubSpot/Marketo in 60% of JDs" }
  ],
  "strengths_to_leverage": ["Analytical background", "Cross-industry experience"],
  "automation_risk_score": 35,
  "recommended_pivot": {
    "target_role": "AI Marketing Strategist",
    "rationale": "Bridges existing marketing expertise with emerging AI demand",
    "time_to_qualify": "4-6 months"
  },
  "quick_wins": ["Complete HubSpot certification (free, 2 weeks)", "AI for Marketing course"],
  "six_month_plan": [
    "Month 1: HubSpot Marketing Automation certification",
    "Month 2-3: Build one AI-powered marketing workflow",
    "Month 4-5: Document results, publish on LinkedIn",
    "Month 6: Apply for AI-adjacent marketing roles"
  ]
}
```

**Model:** Claude Sonnet 4.6  
**Avg tokens:** ~1,000 input / ~600 output  
**Avg cost:** ~$0.10 per analysis

---

### 5. Learning Path Agent (`learning_path.py`)

**Purpose:** Generate a personalized, resource-specific learning roadmap.

**Input:** `gap_analysis: dict` + `constraints: dict`

```json
{
  "hours_per_week": 5,
  "budget": "free",
  "learning_style": "video",
  "timeline_months": 3
}
```

**Output:**
```json
{
  "roadmap": [
    {
      "week": 1,
      "focus": "HubSpot Marketing Automation Fundamentals",
      "resources": [
        {
          "name": "HubSpot Marketing Hub Certification",
          "url": "https://academy.hubspot.com",
          "type": "course",
          "cost": "free",
          "time_hours": 6
        }
      ],
      "milestone": "Complete HubSpot certification"
    }
  ],
  "total_weeks": 12,
  "estimated_outcome": "Qualified for AI Marketing Strategist roles with 40% higher earning potential"
}
```

**Model:** Claude Sonnet 4.6  
**Avg tokens:** ~800 input / ~1,200 output  
**Avg cost:** ~$0.12 per roadmap

---

## Agent Orchestration

For **ATS analysis**, agents run sequentially in a single API call:
```
Request → ATS Engine → DB Write → Response
```

For **Career Intelligence**, agents chain with data passing:
```
Request → Resume Parser → Market Agent → Gap Analyzer → Learning Path → DB Write → Response
```

Total cost per Career Intelligence analysis: **~$0.32–0.42**

---

## Error Handling Pattern

All agents use this pattern:

```python
def run_agent(input_data):
    try:
        response = call_claude(input_data)
        raw = response.content[0].text.strip()
        
        # Strip markdown if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        result = json.loads(raw.strip())
        validate_schema(result)  # Pydantic
        return result
        
    except json.JSONDecodeError as e:
        raise AgentParseError(f"Agent returned invalid JSON: {e}")
    except ValidationError as e:
        raise AgentSchemaError(f"Agent output failed schema validation: {e}")
    except anthropic.APIError as e:
        raise AgentAPIError(f"Claude API error: {e}")
```
