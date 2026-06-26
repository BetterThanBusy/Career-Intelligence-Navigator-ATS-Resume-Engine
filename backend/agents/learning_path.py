import json
import os
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _call_claude(prompt: str, max_tokens: int = 1500) -> dict:
    """Single reusable Claude caller with robust JSON parsing."""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text.strip()
    print(f"Claude response length: {len(raw)}")

    # Strip markdown
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{") or part.startswith("["):
                try:
                    return json.loads(part)
                except:
                    continue

    return json.loads(raw)


def _agent_learning_priorities(critical_gaps: list, target_role: str) -> list:
    """Agent 1: Decide WHAT to learn and in what order."""
    print("Agent 1: Learning priorities")
    prompt = f"""You are a senior career strategist.

Target role: {target_role}
Critical gaps: {json.dumps(critical_gaps)}

Return ONLY a JSON array of learning priorities in order:
[
    {{
        "priority": 1,
        "skill": "skill name",
        "why": "one sentence business reason",
        "urgency": "high",
        "weeks_needed": 2
    }}
]

Maximum 5 priorities. Return only the JSON array."""
    return _call_claude(prompt, 800)


def _agent_certifications(target_role: str, priorities: list) -> list:
    """Agent 2: Find the best certifications with ROI."""
    print("Agent 2: Certifications")
    prompt = f"""You are a professional certification advisor.

Target role: {target_role}
Skills to certify in: {json.dumps([p.get("skill") for p in priorities[:3]])}

Return ONLY a JSON array:
[
    {{
        "name": "exact certification name",
        "provider": "AWS / Google / Microsoft / Coursera etc",
        "url": "https://actual-url.com",
        "cost": "free or $X",
        "duration_weeks": 2,
        "salary_uplift": "estimated % uplift",
        "employer_recognition": "high / medium / low",
        "why": "one sentence on why this cert for this role"
    }}
]

Maximum 4 certifications. Only real certifications with real URLs. Return only JSON array."""
    return _call_claude(prompt, 800)


def _agent_weekly_schedule(
    priorities: list,
    hours_per_week: int,
    timeline_months: int,
    budget: str
) -> list:
    """Agent 3: Build week by week schedule."""
    print("Agent 3: Weekly schedule")
    total_weeks = min(timeline_months * 4, 8)
    prompt = f"""You are a learning schedule designer.

Priorities: {json.dumps(priorities)}
Hours per week: {hours_per_week}
Weeks available: {total_weeks}
Budget: {budget}

Return ONLY a JSON array of {total_weeks} weeks:
[
    {{
        "week": 1,
        "focus": "specific topic",
        "primary_resource": {{
            "name": "resource name",
            "url": "https://real-url.com",
            "platform": "platform name",
            "cost": "free",
            "hours": {hours_per_week}
        }},
        "milestone": "exactly what they can DO by end of week"
    }}
]

{"Only free resources." if budget == "free" else "Mix free and paid."}
Use real resources from Coursera, DeepLearning.AI, YouTube, Microsoft Learn, Google, DataCamp.
Return only JSON array."""
    return _call_claude(prompt, 1500)


def _agent_portfolio_projects(target_role: str, priorities: list) -> list:
    """Agent 4: Design specific GitHub portfolio projects."""
    print("Agent 4: Portfolio projects")
    prompt = f"""You are a technical portfolio strategist.

Target role: {target_role}
Skills to demonstrate: {json.dumps([p.get("skill") for p in priorities[:4]])}

Design 3 specific GitHub projects that prove these skills to a hiring manager.

Return ONLY a JSON array:
[
    {{
        "project_name": "specific project name",
        "description": "2 sentence description of what it does",
        "skills_demonstrated": ["skill1", "skill2"],
        "tech_stack": ["Python", "tool2"],
        "dataset": "where to get the data",
        "deliverable": "what the README should show",
        "interview_talking_point": "how to explain this in an interview",
        "difficulty": "beginner / intermediate / advanced",
        "time_to_build": "X hours"
    }}
]

Return only JSON array."""
    return _call_claude(prompt, 1000)


def _agent_thought_leadership(target_role: str, priorities: list) -> list:
    """Agent 5: LinkedIn content strategy to build authority."""
    print("Agent 5: Thought leadership")
    prompt = f"""You are a personal branding strategist for senior professionals.

Target role: {target_role}
Skills being developed: {json.dumps([p.get("skill") for p in priorities[:3]])}

Create a 4-week LinkedIn content plan to build authority while learning.

Return ONLY a JSON array:
[
    {{
        "week": 1,
        "content_type": "post / article / carousel",
        "hook": "exact opening line of the post",
        "topic": "what to write about",
        "why_this_works": "why this builds credibility for target role"
    }}
]

Return only JSON array."""
    return _call_claude(prompt, 800)


def _agent_interview_prep(target_role: str, critical_gaps: list) -> dict:
    """Agent 6: Interview intelligence for this specific role."""
    print("Agent 6: Interview prep")
    prompt = f"""You are an executive interview coach.

Target role: {target_role}
Candidate gaps: {json.dumps(critical_gaps[:3])}

Return ONLY this JSON:
{{
    "likely_questions": [
        {{
            "question": "exact interview question",
            "why_asked": "what the interviewer is testing",
            "star_framework": "how to structure the answer"
        }}
    ],
    "gap_handling": [
        {{
            "gap": "skill gap name",
            "how_to_address": "exactly how to answer when asked about this gap"
        }}
    ],
    "salary_range": {{
        "market_low": 0,
        "market_mid": 0,
        "market_high": 0,
        "negotiation_tip": "one specific tip"
    }}
}}

Maximum 4 questions. Return only JSON."""
    return _call_claude(prompt, 1000)


def generate_learning_path(gap_analysis: dict, constraints: dict) -> dict:
    """
    Orchestrates 6 focused agents to produce an intelligence-grade career roadmap.
    Each agent is small, focused, and reliable.
    """

    print("Starting multi-agent learning path generation")

    hours_per_week = constraints.get("hours_per_week", 5)
    budget = constraints.get("budget", "free")
    learning_style = constraints.get("learning_style", "mixed")
    timeline_months = constraints.get("timeline_months", 3)

    critical_gaps = gap_analysis.get("critical_gaps", [])[:5]
    quick_wins = gap_analysis.get("quick_wins", [])[:3]
    target_role = gap_analysis.get("recommended_pivot", {}).get("target_role", "Senior AI Professional")

    try:
        # Agent 1: What to learn
        priorities = _agent_learning_priorities(critical_gaps, target_role)
        if isinstance(priorities, dict):
            priorities = [priorities]

        # Agent 2: Certifications
        certifications = _agent_certifications(target_role, priorities)
        if isinstance(certifications, dict):
            certifications = [certifications]

        # Agent 3: Weekly schedule
        weekly_schedule = _agent_weekly_schedule(
            priorities, hours_per_week, timeline_months, budget
        )
        if isinstance(weekly_schedule, dict):
            weekly_schedule = [weekly_schedule]

        # Agent 4: Portfolio projects
        portfolio_projects = _agent_portfolio_projects(target_role, priorities)
        if isinstance(portfolio_projects, dict):
            portfolio_projects = [portfolio_projects]

        # Agent 5: Thought leadership
        content_plan = _agent_thought_leadership(target_role, priorities)
        if isinstance(content_plan, dict):
            content_plan = [content_plan]

        # Agent 6: Interview prep
        interview_prep = _agent_interview_prep(target_role, critical_gaps)

        # Compose final result
        result = {
            "target_role": target_role,
            "timeline_months": timeline_months,
            "hours_per_week": hours_per_week,
            "learning_priorities": priorities,
            "certifications": certifications,
            "weekly_schedule": weekly_schedule,
            "portfolio_projects": portfolio_projects,
            "thought_leadership_plan": content_plan,
            "interview_prep": interview_prep,
            "quick_wins": quick_wins,
            "total_weeks": min(timeline_months * 4, 8),
            "total_cost_usd": 0 if budget == "free" else "varies"
        }

        print("Multi-agent learning path complete")
        return result

    except Exception as e:
        print(f"Learning path agent error: {type(e).__name__}: {str(e)}")
        raise Exception(f"Learning path failed: {type(e).__name__}: {str(e)}")
