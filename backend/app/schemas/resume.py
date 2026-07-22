"""Pydantic schemas for Phase 7 Resume vs Job Description Skill-Gap Analyzer."""
from pydantic import BaseModel, Field


class ResumeAnalyzeRequest(BaseModel):
    resume_text: str = Field(..., min_length=10, description="Plain text content of the candidate's resume.")
    job_description_text: str = Field(..., min_length=10, description="Plain text of the target job description.")


class ResumeAnalyzeResponse(BaseModel):
    matched_skills: list[str] = Field(default_factory=list, description="Skills present in both resume and job description.")
    missing_skills: list[str] = Field(default_factory=list, description="Skills required by job description but missing from resume.")
    roadmap: list[str] = Field(default_factory=list, description="Step-by-step learning roadmap to bridge the skill gap.")
