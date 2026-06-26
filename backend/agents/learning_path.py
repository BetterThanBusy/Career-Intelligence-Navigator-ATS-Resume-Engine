import json
import os
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_learning_path(gap_analysis: dict, constraints: dict) -> dict:

    print("Generating learning path")

    hours_per_week = constraints.get("hours_per_week", 5)
    budget = constraints.get("budget", "free")
    timeline_months = constraints.get("timeline_months", 3)

    # Send only the critical fields to keep prompt small
    critical_gaps = gap_analysis.get("critical_gaps", [])[:3]
    quick_wins = gap_analysis.get("quick_wins", [])[:3]
    target_role = gap_analysis.get("recommended_pivot", {}).get("target_role", "target role")

    prompt = f"""Create a {timeline_months}-month learning roadmap for someone targeting {target_role}.

Critical gaps to address: {json.dumps(critical_gaps)}
Quick wins available: {json.dumps(quick_wins)}
Hours available per week: {hours_per_week}
Budget: {budget}

Return ONLY this JSON, no markdown, no text before or after:
{{
    "roadmap": [
        {{
            "week": 1,
            "focus": "topic",
            "resources": [
                {{
                    "name": "resource name",
                    "url": "https://url.com",
                    "type": "course",
                    "platform": "platform name",
                    "cost": "free",
                    "time_hours": {hours_per_week},
                    "why": "reason"
                }}
            ],
            "milestone": "what they achieve"
        }},
        {{
            "week": 2,
            "focus": "topic",
            "resources": [
                {{
                    "name": "resource name",
                    "url": "https://url.com",
                    "type": "course",
                    "platform": "platform name",
                    "cost": "free",
                    "time_hours": {hours_per_week},
                    "why": "reason"
                }}
            ],
            "milestone": "what they achieve"
        }},
        {{
            "week": 3,
            "focus": "topic",
            "resources": [
                {{
                    "name": "resource name",
                    "url": "https://url.com",
                    "type": "course",
                    "platform": "platform name",
                    "cost": "free",
                    "time_hours": {hours_per_week},
                    "why": "reason"
                }}
            ],
            "milestone": "what they achieve"
        }},
        {{
            "week": 4,
            "focus": "topic",
            "resources": [
                {{
                    "name": "resource name",
                    "url": "https://url.com",
                    "type": "course",
                    "platform": "platform name",
                    "cost": "free",
                    "time_hours": {hours_per_week},
                    "why": "reason"
                }}
            ],
            "milestone": "what they achieve"
        }}
    ],
    "total_weeks": 4,
    "total_cost_usd": 0,
    "estimated_outcome": "what roles they qualify for",
    "key_projects_to_build": ["project1", "project2"],
    "communities_to_join": ["community1", "community2"],
    "metrics_to_track": ["metric1", "metric2"]
}}

Fill in ALL fields with real specific content for {target_role}.
{"Only free resources." if budget == "free" else "Mix of free and paid resources."}
Return only the JSON object. Nothing else."""

   try:
    response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4000,
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

print("\n================ CLAUDE RESPONSE ================\n")
print(response)
print("\n===============================================\n")

print("Stop Reason:", response.stop_reason)
print("Model:", response.model)

print("\n=========== CONTENT BLOCKS ===========\n")

text_parts = []

for i, block in enumerate(response.content):
    print(f"\n--- Block {i} ---")
    print("Type:", type(block))

    if hasattr(block, "text"):
        print(block.text)
        text_parts.append(block.text)

raw = "\n".join(text_parts).strip()

print("\n=========== RAW TEXT ===========")
print(raw)
print("=========== END RAW ===========\n")

print("Raw Length:", len(raw))

result = json.loads(raw)

return result

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {str(e)}, raw: {raw[:500] if raw else 'EMPTY'}")
        raise Exception(f"Learning path failed: JSONDecodeError: {str(e)}")
    except Exception as e:
        print(f"Learning path error: {type(e).__name__}: {str(e)}")
        raise Exception(f"Learning path failed: {type(e).__name__}: {str(e)}")
