"""Resume vs Job Description Skill-Gap Analyzer router (Phase 7)."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas.resume import ResumeAnalyzeRequest, ResumeAnalyzeResponse
from app.services import resume_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=ResumeAnalyzeResponse, status_code=status.HTTP_200_OK)
async def analyze_resume_gap(
    body: ResumeAnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Protected route to analyze resume text against job description text.
    Returns matched skills, missing skills, and learning roadmap.
    """
    if not body.resume_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume text cannot be empty."
        )

    if not body.job_description_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text cannot be empty."
        )

    try:
        result = await resume_service.analyze_resume_gap(
            body.resume_text.strip(),
            body.job_description_text.strip(),
        )
        return result
    except Exception as exc:
        logger.error(f"Resume analysis router exception: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze skill gap. Please try again."
        )
