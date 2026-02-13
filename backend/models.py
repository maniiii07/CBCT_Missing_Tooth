from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ToothStatus(str, Enum):
    PRESENT = "present"
    MISSING = "missing"
    UNCERTAIN = "uncertain"


class QuadrantAnalysis(BaseModel):
    quadrant_number: int = Field(..., ge=1, le=4, description="Dental quadrant (1-4)")
    missing_teeth: list[int] = Field(default_factory=list, description="List of missing tooth numbers in this quadrant")
    present_teeth: list[int] = Field(default_factory=list, description="List of present tooth numbers in this quadrant")
    impacted_teeth: list[int] = Field(default_factory=list, description="List of impacted tooth numbers in this quadrant")
    not_visualized_teeth: list[int] = Field(default_factory=list, description="List of teeth not visualized in this quadrant")
    notes: Optional[str] = Field(None, description="Additional observations")


class ModelAnalysisResult(BaseModel):
    model_name: str = Field(..., description="Name of the AI model")
    quadrant_1: QuadrantAnalysis = Field(..., description="Upper Right quadrant (teeth 11-18)")
    quadrant_2: QuadrantAnalysis = Field(..., description="Upper Left quadrant (teeth 21-28)")
    quadrant_3: QuadrantAnalysis = Field(..., description="Lower Left quadrant (teeth 31-38)")
    quadrant_4: QuadrantAnalysis = Field(..., description="Lower Right quadrant (teeth 41-48)")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence score")
    raw_response: Optional[str] = Field(None, description="Raw response from the model")


class DecidingModelResult(BaseModel):
    selected_model: Optional[str] = Field(None, description="Model selected as most accurate, or None if deciding model made own decision")
    final_analysis: ModelAnalysisResult = Field(..., description="Final analysis result")
    reasoning: str = Field(..., description="Explanation for the decision")
    agreement_score: float = Field(..., ge=0, le=1, description="How much the models agreed with each other")


class DentalAnalysisResponse(BaseModel):
    gpt4o_result: ModelAnalysisResult
    gemini_result: ModelAnalysisResult
    anthropic_result: ModelAnalysisResult
    final_decision: DecidingModelResult
    image_filename: str


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
