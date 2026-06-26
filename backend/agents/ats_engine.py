import json
import os
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def run_ats_analysis(resume_text: str, job_description: str) -> dict:

    print("Running ATS analysis")

    prompt = f"""You are an ATS analyst. Analyze this resume against the job description.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

Return ONLY valid JSON with these exact fields:
{{
    "ats_score": 72,
    "matched_keywords": ["keyword1", "keyword2"],
    "missing_keywords": ["missing1", "missing2"],
    "missing_skills": ["skill1"],
    "strengths": ["strength1"],
    "critical_fixes": [
        {{"issue": "issue here", "fix": "fix here", "priority": "high"}}
    ],
    "rewritten_summary": "optimized summary here",
    "rewritten_experience_bullets": [
        {{"original": "original bullet", "rewritten": "rewritten bullet"}}
    ],
    "optimized_skills_section": ["SQL", "HubSpot"],
    "final_verdict": "maybe",
    "verdict_reason": "reason here",
    "score_breakdown": {{
        "keyword_match": 65,
        "skills_alignment": 75,
        "experience_relevance": 80,
        "formatting_score": 70
    }}
}}

Return only JSON. No markdown. No explanation."""

    try:
        print("Calling Claude API")
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        print("Claude responded")

        raw = response.content[0].text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw.strip())
        result["_meta"] = {
            "tokens_in": response.usage.input_tokens,
            "tokens_out": response.usage.output_tokens
        }
        return result

    except Exception as e:
        print(f"ATS engine error: {type(e).__name__}: {str(e)}")
        raise Exception(f"ATS engine failed: {type(e).__name__}: {str(e)}")


class ATSParseError(Exception):
    pass

class ATSAPIError(Exception):
    pass
