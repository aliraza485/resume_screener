from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ScreeningResponse(BaseModel):
    candidate_name: Optional[str] = Field(None, description="Extracted name of the candidate")
    match_score: int = Field(..., ge=0, le=100, description="Match score from 0 to 100 based on the job description")
    matching_skills: List[str] = Field(..., description="List of relevant skills found in the resume matching the job description")
    missing_skills: List[str] = Field(..., description="Key skills required by the job description that are missing from the resume")
    summary_reasoning: str = Field(..., description="Detailed explanation of why the candidate is a strong or weak match")
    recommendation: str = Field(..., description="Hiring recommendation (e.g., 'Strong Hire', 'Interview', 'Reject')")

class ScreeningRecord(ScreeningResponse):
    id: int
    filename: str
    created_at: datetime

    class Config:
        from_attributes = True