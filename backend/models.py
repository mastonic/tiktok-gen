from pydantic import BaseModel, Field
from typing import List, Optional

class VisualPrompts(BaseModel):
    prompts: List[str] = Field(..., description="Exactly 18 cinematically consistent image prompts.")
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
    image_prompts: List[str] = Field(..., description="The 18 prompts for image generation.")
    tiktok_caption: Optional[str] = Field(None, description="TikTok specific metadata.")
    statut_validation: bool = Field(True, description="Ready for production.")
    top_5_concepts: List[dict] = Field([], description="Related concepts for the blog.")

class ToolItem(BaseModel):
    id: str = Field(..., description="Tool ID (e.g., tool_1, tool_2)")
    name: str = Field(..., description="Tool name")
    category: str = Field(..., description="Tool category")
    description: str = Field(..., description="Short 1-line description")
    cta: str = Field(..., description="Call to action text")
    affiliate_link_placeholder: str = Field(..., description="Placeholder link")
    gradient: str = Field(..., description="Tailwind gradient classes")
    relevance_score: int = Field(..., description="Score out of 100")

class BentoBoxData(BaseModel):
    article_title: str = Field(..., description="Full title of the article")
    article_slug: str = Field(..., description="Slug of the article")
    seo_tags: List[str] = Field(..., description="3-5 SEO tags")
    tools: List[ToolItem] = Field(..., description="List of 2 exactly matched tools")
