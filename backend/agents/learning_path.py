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

Return ONLY valid JSON.

{{
    "roadmap": [
        {{
            "week": 1,
            "focus": "topic",
            "resources": [
                {{
                    "name": "resource",
                    "url": "https://example.com",
                    "type": "course",
                    "platform": "Coursera",
                    "cost": "free",
                    "time_hours": {hours_per_week},
                    "why": "reason"
                }}
            ],
            "milestone": "achievement"
        }}
    ],
    "total_weeks": 4,
    "total_cost_usd": 0,
    "estimated_outcome": "target outcome",
    "key_projects_to_build": [],
    "communities_to_join": [],
    "metrics_to_track": []
}}

{"Only free resources." if budget == "free" else "Mix free and paid resources."}

Return ONLY the JSON object.
"""

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

            if getattr(block, "type", "") == "text":
                print(block.text)
                text_parts.append(block.text)

            else:
                print(block)

        raw = "\n".join(text_parts).strip()

        print("\n=========== RAW TEXT ===========")
        print(raw)
        print("=========== END RAW ===========\n")

        print("Raw Length:", len(raw))

        if not raw:
            raise Exception("Claude returned an empty response.")

        result = json.loads(raw)

        print("Learning path parsed successfully")

        return result

    except json.JSONDecodeError as e:

        print("JSON Decode Error")
        print(raw)

        raise Exception(f"Learning path failed: JSONDecodeError: {e}")

    except Exception as e:

        print("Learning path error:", type(e).__name__, str(e))

        raise Exception(f"Learning path failed: {type(e).__name__}: {e}")
