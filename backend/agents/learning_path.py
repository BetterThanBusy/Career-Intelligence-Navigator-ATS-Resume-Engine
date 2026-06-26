import json
import os
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_learning_path(gap_analysis: dict, constraints: dict) -> dict:

    print("Generating learning path")

    clean_gaps = {k: v for k, v in gap_analysis.items() if not k.startswith("_")}

    hours_per_week = constraints.get("hours_per_week", 5)
    budget = constraints.get("budget", "free")
    learning_style = constraints.get("learning_style", "mixed")
    timeline_months = constraints.get("timeline_months", 3)
    total_weeks = timeline_months * 4

    budget_instruction = {
        "free": "ONLY recommend free resources.",
        "low": "Prefer free, max $50 total.",
        "any": "Recommend best resources regardless of cost."
    }.get(budget, "Prefer free resources.")

    prompt = f"""You are a career education strategist. Create a week-by-week learning roadmap.

GAP ANALYSIS:
{json.dumps(clean_gaps, indent=2)}

CONSTRAINTS:
- Hours per week: {hours_per_week}
- Budget: {budget} — {budget_instruction}
- Learning style: {learning_style}
- Timeline: {timeline_months} months ({total_weeks} weeks)

Return ONLY valid JSON, no markdown, no explanation:
{{
    "roadmap": [
        {{
            "week": 1,
            "focus": "topic for this week",
            "resources": [
                {{
                    "name": "resource name",
                    "url": "https://actual-url.com",
                    "type": "course",
                    "platform": "Coursera",
                    "cost": "free",
                    "time_hours": 5,
                    "why": "why this resource"
                }}
            ],
            "milestone": "what they achieve by end of week"
        }}
    ],
    "total_weeks": {total_weeks},
    "total_cost_usd": 0,
    "estimated_outcome": "what roles they qualify for after completion",
    "key_projects_to_build": ["project1", "project2", "project3"],
    "communities_to_join": ["community1", "community2"],
    "metrics_to_track": ["metric1", "metric2"]
}}

Generate {min(total_weeks, 8)} weeks of roadmap. Return only JSON."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        print("Learning path Claude response received")

        raw = response.content[0].text.strip()
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                try:
                    return json.loads(part)
                except:
                    continue

        result = json.loads(raw)
        print(f"Learning path generated: {result.get('total_weeks')} weeks")
        return result

    except Exception as e:
        print(f"Learning path error: {type(e).__name__}: {str(e)}")
        raise Exception(f"Learning path failed: {type(e).__name__}: {str(e)}")
