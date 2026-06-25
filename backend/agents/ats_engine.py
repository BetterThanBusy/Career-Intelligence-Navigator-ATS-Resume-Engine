"""
ATS Engine Agent
Takes resume_text + job_description → returns full ATS analysis JSON

Cost: ~$0.15 per analysis (Claude Sonnet 4.6)
"""

import json
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

log = structlog.get_logger()
client = anthropic.Anthropic()

ATS_SCHEMA = {
    "ats_score": "integer 0-100",
    "score_breakdown": {
        "keyword_match": "integer 0-100",
        "skills_alignment": "integer 0-100",
        "experience_relevance": "integer 0-100",
        "formatting_score": "integer 0-100"
    },
    "matched_keywords": ["list of keywords found in both resume and JD"],
    "missing_keywords": ["critical keywords in JD NOT in resume"],
    "missing_skills": ["skills required in JD but absent from resume"],
    "strengths": ["what the resume does well for this role"],
    "critical_fixes": [
        {
            "issue": "specific problem",
            "fix": "exact action to take",
            "priority": "high | medium | low"
        }
    ],
    "rewritten_summary": "ATS-optimized professional summary paragraph",
    "rewritten_experience_bullets": [
        {
            "original": "original bullet text",
            "rewritten": "optimized bullet with keywords naturally integrated"
        }
    ],
    "optimized_skills_section": ["ordered list of skills to include, most relevant first"],
    "final_verdict": "hire | maybe | no",
    "verdict_reason": "one sentence explanation"
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def run_ats_analysis(resume_text: str, job_description: str) -> dict:
    """
    Run full ATS analysis on a resume against a job description.
    
    Args:
        resume_text: Plain text of the resume
        job_description: Plain text of the job description
        
    Returns:
        Structured ATS analysis dict
        
    Raises:
        ATSParseError: If Claude returns invalid JSON
        ATSAPIError: If Anthropic API call fails
    """
    
    log.info("Running ATS analysis", 
             resume_length=len(resume_text),
             jd_length=len(job_description))
    
    prompt = f"""You are a senior ATS (Applicant Tracking System) analyst and resume strategist with 10 years of experience optimizing resumes for Fortune 500 hiring pipelines.

Analyze this resume against the job description. Be precise, specific, and actionable.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

Return ONLY valid JSON matching this exact schema:
{json.dumps(ATS_SCHEMA, indent=2)}

Rules:
- ats_score: weight keyword_match 40%, skills_alignment 30%, experience_relevance 20%, formatting_score 10%
- missing_keywords: only include words that appear 2+ times in the JD
- rewritten_summary: must naturally include top 3 missing keywords
- rewritten_experience_bullets: rewrite the 3 most relevant existing bullets, integrating missing keywords naturally
- critical_fixes: maximum 5, ordered by priority
- Be specific in fixes — name the exact keyword or skill to add

Return only the JSON object. No markdown. No explanation. No preamble."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        raw = response.content[0].text.strip()
        
        # Strip accidental markdown wrappers
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        result = json.loads(raw.strip())
        
        # Log token usage for cost tracking
        log.info("ATS analysis complete",
                 tokens_in=response.usage.input_tokens,
                 tokens_out=response.usage.output_tokens,
                 ats_score=result.get("ats_score"))
        
        # Attach token usage for DB storage
        result["_meta"] = {
            "tokens_in": response.usage.input_tokens,
            "tokens_out": response.usage.output_tokens,
            "model": "claude-sonnet-4-6"
        }
        
        return result
        
    except json.JSONDecodeError as e:
        log.error("ATS agent returned invalid JSON", error=str(e), raw=raw[:500])
        raise ATSParseError(f"Failed to parse ATS response: {e}")
    except anthropic.APIError as e:
        log.error("Anthropic API error", error=str(e))
        raise ATSAPIError(f"Claude API call failed: {e}")


class ATSParseError(Exception):
    """Raised when Claude returns unparseable JSON"""
    pass

class ATSAPIError(Exception):
    """Raised when Anthropic API call fails"""
    pass
