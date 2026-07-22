"""
Resume vs Job Description Skill-Gap Analyzer Service (Phase 7).

Sends resume text and job description text to Groq (llama-3.3-70b-versatile)
to identify matched skills, missing skill gaps, and a step-by-step learning roadmap.
"""

import json
import logging
import re
from app.adapters.groq_adapter import groq_adapter
from app.schemas.resume import ResumeAnalyzeResponse

logger = logging.getLogger(__name__)

RESUME_ANALYSIS_SYSTEM_PROMPT = """You are StudyMate AI — an expert technical career strategist and skill gap analyst.
Your task is to analyze a candidate's resume text against a target job description text.

You must:
1. Extract technical skills, tools, methodologies, and requirements from both inputs.
2. Identify "matched_skills" (skills present in both the candidate's resume and the job description).
3. Identify "missing_skills" (critical skills required by the job description that are absent or under-represented in the candidate's resume).
4. Build a concise, actionable 4-6 step "roadmap" to help the candidate acquire the missing skills and improve their fit.

Respond ONLY with a single valid JSON object in this exact schema (no markdown explanations outside the JSON):
{
  "matched_skills": ["Skill 1", "Skill 2"],
  "missing_skills": ["Missing Skill 1", "Missing Skill 2"],
  "roadmap": ["Step 1: ...", "Step 2: ...", "Step 3: ...", "Step 4: ..."]
}"""


async def analyze_resume_gap(resume_text: str, job_description_text: str) -> ResumeAnalyzeResponse:
    """
    Call Groq LLM to compute skill match, gaps, and roadmap.
    Parses response defensively with fallback error handling.
    """
    user_prompt = (
        "CANDIDATE RESUME TEXT:\n"
        f"{resume_text.strip()[:4000]}\n\n"
        "TARGET JOB DESCRIPTION TEXT:\n"
        f"{job_description_text.strip()[:4000]}\n\n"
        "Analyze the overlap and gaps, and output the required JSON schema."
    )

    try:
        raw_reply = await groq_adapter.generate(
            prompt=user_prompt,
            system_prompt=RESUME_ANALYSIS_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=1500,
        )

        # Extract JSON object using regex fallback
        json_match = re.search(r"\{.*\}", raw_reply, re.DOTALL)
        if not json_match:
            logger.warning("No JSON structure found in Groq resume analysis output.")
            return _fallback_response(resume_text, job_description_text)

        data = json.loads(json_match.group())

        matched = [str(s).strip() for s in data.get("matched_skills", []) if s]
        missing = [str(s).strip() for s in data.get("missing_skills", []) if s]
        roadmap = [str(r).strip() for r in data.get("roadmap", []) if r]

        if not matched and not missing:
            return _fallback_response(resume_text, job_description_text)

        return ResumeAnalyzeResponse(
            matched_skills=matched,
            missing_skills=missing,
            roadmap=roadmap,
        )

    except Exception as exc:
        logger.error(f"Error performing LLM resume analysis: {exc}")
        return _fallback_response(resume_text, job_description_text)


def _fallback_response(resume_text: str, job_description_text: str) -> ResumeAnalyzeResponse:
    """Fallback keyword matching analysis when LLM output cannot be parsed."""
    logger.info("Using fallback keyword matching for resume gap analysis.")
    # Extract simple word tokens
    resume_words = set(re.findall(r"\b[A-Za-z0-9+#.-]{3,}\b", resume_text.lower()))
    jd_words = set(re.findall(r"\b[A-Za-z0-9+#.-]{3,}\b", job_description_text.lower()))

    # Common tech terms filter
    common_tech = {
        "python", "java", "javascript", "typescript", "react", "node", "sql", "postgres",
        "aws", "docker", "git", "rest", "api", "html", "css", "c++", "data", "structures",
        "algorithms", "agile", "devops", "linux", "cloud", "security"
    }

    jd_tech = jd_words.intersection(common_tech)
    matched = list(jd_tech.intersection(resume_words))
    missing = list(jd_tech - set(matched))

    if not matched and not missing:
        matched = ["General Problem Solving", "Technical Communication"]
        missing = ["Targeted Framework Proficiency", "System Architecture"]

    roadmap = [
        f"1. Deepen hands-on practice in missing skills: {', '.join(missing[:3]) if missing else 'Advanced Concepts'}.",
        "2. Build 1-2 practical portfolio projects demonstrating these competencies.",
        "3. Document project architecture and source code on GitHub.",
        "4. Highlight project outcomes and metric impacts directly on your resume."
    ]

    return ResumeAnalyzeResponse(
        matched_skills=[s.title() for s in matched],
        missing_skills=[s.title() for s in missing],
        roadmap=roadmap,
    )
