"""
Resume Parser Agent
Extracts structured profile data from raw resume text.

Cost: ~$0.05 per parse (Claude Sonnet 4.6)
"""

import json
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

log = structlog.get_logger()
client = anthropic.Anthropic()

RESUME_SCHEMA = {
    "current_role": "most recent job title as a string",
    "years_experience": "total years of professional experience as integer",
    "skills": ["list of all technical and soft skills mentioned"],
    "industries": ["list of industries the person has worked in"],
    "education": ["list of degrees and certifications"],
    "companies": ["list of companies worked at"],
    "notable_achievements": ["list of quantified accomplishments if any"],
    "inferred_strengths": ["3-5 key strengths inferred from the resume"],
    "potential_gaps": ["areas that seem underdeveloped based on the experience level"]
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def parse_resume(resume_text: str) -> dict:
    """
    Parse a resume into structured profile data.
    
    Args:
        resume_text: Plain text of the resume
        
    Returns:
        Structured profile dict
    """
    
    log.info("Parsing resume", resume_length=len(resume_text))
    
    prompt = f"""Extract structured data from this resume. Be thorough and accurate.

RESUME:
{resume_text}

Return ONLY valid JSON matching this exact schema:
{json.dumps(RESUME_SCHEMA, indent=2)}

Rules:
- skills: include ALL mentioned skills, tools, technologies, and methodologies
- years_experience: calculate total, not just most recent role
- potential_gaps: infer based on role level (e.g. senior manager with no strategy mentions is a gap)
- Be factual — only include what's actually in the resume

Return only the JSON. No markdown. No explanation."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
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
    
    log.info("Resume parsed", role=result.get("current_role"), skills_count=len(result.get("skills", [])))
    return result
