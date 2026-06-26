import json
import os
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def parse_resume(resume_text: str) -> dict:

    print("Parsing resume")

    prompt = f"""Extract structured data from this resume. Be thorough and accurate.

RESUME:
{resume_text}

Return ONLY valid JSON, no markdown, no explanation:
{{
    "current_role": "most recent job title",
    "years_experience": 9,
    "skills": ["skill1", "skill2", "skill3"],
    "industries": ["industry1", "industry2"],
    "education": ["degree1", "degree2"],
    "companies": ["company1", "company2"],
    "notable_achievements": ["achievement1", "achievement2"],
    "inferred_strengths": ["strength1", "strength2", "strength3"],
    "potential_gaps": ["gap1", "gap2"]
}}

Return only JSON."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        print("Resume parser Claude response received")

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
        print(f"Resume parsed: {result.get('current_role')}")
        return result

    except Exception as e:
        print(f"Resume parser error: {type(e).__name__}: {str(e)}")
        raise Exception(f"Resume parser failed: {type(e).__name__}: {str(e)}")
