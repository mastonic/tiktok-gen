from pydantic import BaseModel, Field
from typing import List, Optional

class VisualPrompts(BaseModel):
    prompts: List[str] = Field(..., description="Exactly 15 cinematically consistent image prompts.")
    style: str = Field("Raw cinematic shot, 35mm film grain, hyper-realistic", description="Overall visual style.")

class TikTokMetadata(BaseModel):
    caption: str = Field(..., description="Viral TikTok description including hooks.")
    hashtags: List[str] = Field(..., description="Strategic viral hashtags.")
    hook_type: str = Field("Aggressive", description="Type of hook used (e.g., Question, Shocking fact).")

class AgentOutcome(BaseModel):
    title: str = Field(..., description="Title of the content.")
    script: str = Field(..., description="Final 90s+ script.")
    mots_cles: str = Field(..., description="3 impact keywords in UPPERCASE.")
    score_roi: int = Field(..., description="Monetization score out of 100.")
    image_prompts: List[str] = Field(..., description="The 15 prompts for image generation.")
    tiktok_caption: Optional[str] = Field(None, description="TikTok specific metadata.")
    statut_validation: bool = Field(True, description="Ready for production.")
    top_5_concepts: List[dict] = Field([], description="Related concepts for the blog.")
