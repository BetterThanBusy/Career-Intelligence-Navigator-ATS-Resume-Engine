import json
import os
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def analyze_skill_gap(user_profile: dict, market_data: dict) -> dict:

    print("Running gap analysis")

    clean_profile = {k: v for k, v in user_profile.items() if not k.startswith("_")}
    clean_market = {k: v for k, v in market_data.items() if not k.startswith("_")}

    prompt = f"""You are a senior career strategist. Analyze the gap between this professional's profile and market demands.

USER PROFILE:
{json.dumps(clean_profile, indent=2)}

MARKET INTELLIGENCE:
{json.dumps(clean_market, indent=2)}

Return ONLY valid JSON, no markdown, no explanation:
{{
    "gap_score": 45,
    "critical_gaps": [
        {{
            "skill": "skill name",
            "urgency": "high",
            "reason": "why this gap matters",
            "time_to_learn": "4 weeks"
        }}
    ],
    "strengths_to_leverage": ["strength1", "strength2", "strength3"],
    "automation_risk_score": 25,
    "automation_risk_breakdown": ["task1 at risk", "task2 at risk"],
    "recommended_pivot": {{
        "target_role": "specific job title",
        "rationale": "why this is optimal",
        "time_to_qualify": "3 months",
        "salary_upside": "20%"
    }},
    "quick_wins": ["certification1 in 2 weeks", "skill2 in 1 week"],
    "six_month_plan": [
        {{
            "month": "1",
            "focus": "primary focus",
            "goal": "measurable milestone"
        }}
    ],
    "competitive_advantage": "what makes this person uniquely valuable"
}}

Be specific and honest. Return only JSON."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        print("Gap analysis Claude response received")

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
        print(f"Gap score: {result.get('gap_score')}")
        return result

    except Exception as e:
        print(f"Gap analyzer error: {type(e).__name__}: {str(e)}")
        raise Exception(f"Gap analyzer failed: {type(e).__name__}: {str(e)}")
