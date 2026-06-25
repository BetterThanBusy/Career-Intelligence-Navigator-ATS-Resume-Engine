"""
Learning Path Agent
Generates a personalized, resource-specific learning roadmap.

Cost: ~$0.12 per roadmap (Claude Sonnet 4.6)
"""

import json
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

log = structlog.get_logger()
client = anthropic.Anthropic()

LEARNING_PATH_SCHEMA = {
    "roadmap": [
        {
            "week": "integer",
            "focus": "primary topic for this week",
            "resources": [
                {
                    "name": "resource name",
                    "url": "actual URL if known",
                    "type": "course | book | project | certification | community",
                    "platform": "Coursera | YouTube | DataCamp | Kaggle | LinkedIn Learning | free | etc",
                    "cost": "free | $X",
                    "time_hours": "estimated hours this week",
                    "why": "one sentence on why this resource for this gap"
                }
            ],
            "milestone": "measurable outcome by end of week"
        }
    ],
    "total_weeks": "integer",
    "total_cost_usd": "estimated total cost across all paid resources",
    "estimated_outcome": "what the person will be capable of and what roles they'll qualify for",
    "key_projects_to_build": ["3-5 portfolio projects to demonstrate new skills"],
    "communities_to_join": ["relevant communities, Slack groups, subreddits"],
    "metrics_to_track": ["how to measure learning progress week by week"]
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_learning_path(gap_analysis: dict, constraints: dict) -> dict:
    """
    Generate a personalized learning roadmap based on gap analysis.
    
    Args:
        gap_analysis: Output from gap_analyzer
        constraints: User learning preferences
            {
                "hours_per_week": int,      # How many hours available (default: 5)
                "budget": str,              # "free" | "low" ($0-50) | "any"
                "learning_style": str,      # "video" | "reading" | "projects" | "mixed"
                "timeline_months": int      # Target timeline (default: 3)
            }
            
    Returns:
        Structured learning roadmap
    """
    
    log.info("Generating learning path",
             gap_score=gap_analysis.get("gap_score"),
             hours_per_week=constraints.get("hours_per_week", 5),
             budget=constraints.get("budget", "free"))
    
    clean_gaps = {k: v for k, v in gap_analysis.items() if not k.startswith("_")}
    
    hours_per_week = constraints.get("hours_per_week", 5)
    budget = constraints.get("budget", "free")
    learning_style = constraints.get("learning_style", "mixed")
    timeline_months = constraints.get("timeline_months", 3)
    total_weeks = timeline_months * 4
    
    budget_instruction = {
        "free": "ONLY recommend free resources. Coursera audit, YouTube, free tiers, open-source.",
        "low": "Prefer free resources. Paid options max $50 total budget.",
        "any": "Recommend best resources regardless of cost. Note pricing."
    }.get(budget, "Prefer free resources.")
    
    prompt = f"""You are a career education strategist who designs learning systems for busy professionals.

Create a week-by-week learning roadmap to close these specific skill gaps.

GAP ANALYSIS:
{json.dumps(clean_gaps, indent=2)}

USER CONSTRAINTS:
- Available hours per week: {hours_per_week}
- Budget: {budget} — {budget_instruction}
- Learning style: {learning_style}
- Timeline: {timeline_months} months ({total_weeks} weeks)

Return ONLY valid JSON matching this schema:
{json.dumps(LEARNING_PATH_SCHEMA, indent=2)}

Rules:
- Total hours per week across all resources must equal {hours_per_week} hours
- Address critical_gaps first, quick_wins in week 1
- Include real, existing resources with real URLs where possible
- key_projects_to_build: must be portfolio-worthy and demonstrable on GitHub
- Sequence matters: foundational skills before advanced ones
- Each week must have exactly ONE clear milestone

Return only the JSON. No markdown. No explanation."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    result = json.loads(raw.strip())
    result["_meta"] = {
        "tokens_in": response.usage.input_tokens,
        "tokens_out": response.usage.output_tokens,
        "model": "claude-sonnet-4-6"
    }
    
    log.info("Learning path generated",
             total_weeks=result.get("total_weeks"),
             total_cost=result.get("total_cost_usd"))
    
    return result
