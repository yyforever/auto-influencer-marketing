"""
Pydantic schemas for influencer search functionality.

Defines structured data models for influencer search queries, results,
and related data structures used throughout the search workflow.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, PositiveInt, validator


class InfluencerSearchQuery(BaseModel):
    """Schema for structured influencer search query generation"""
    
    platform: str = Field(
        description="Social media platform (instagram, tiktok, youtube, etc.)",
        examples=["instagram", "tiktok", "youtube", "twitter"]
    )
    niche: str = Field(
        description="Content niche or category",
        examples=["fitness", "beauty", "tech", "food", "travel"]
    )
    min_followers: PositiveInt = Field(
        description="Minimum follower count",
        ge=1000,
        default=10000
    )
    max_followers: PositiveInt = Field(
        description="Maximum follower count", 
        le=10000000,
        default=1000000
    )
    location: Optional[str] = Field(
        default=None,
        description="Geographic location preference",
        examples=["US", "China", "Global", "Europe"]
    )
    keywords: List[str] = Field(
        description="Keywords related to content or brand",
        min_items=1,
        examples=[["fitness", "workout"], ["beauty", "makeup"], ["tech", "gadgets"]]
    )
    
    @validator('max_followers')
    def validate_follower_range(cls, v, values):
        if 'min_followers' in values and v < values['min_followers']:
            raise ValueError('max_followers must be greater than min_followers')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "platform": "instagram",
                "niche": "fitness",
                "min_followers": 50000,
                "max_followers": 500000,
                "location": "US",
                "keywords": ["fitness", "workout", "health"]
            }
        }


class InfluencerProfile(BaseModel):
    """Schema for influencer profile data"""
    
    id: str = Field(description="Unique influencer identifier")
    username: str = Field(description="Social media username")
    platform: str = Field(description="Primary platform")
    display_name: Optional[str] = Field(default=None, description="Display name")
    
    # Metrics
    followers: PositiveInt = Field(description="Current follower count")
    engagement_rate: float = Field(
        description="Average engagement rate percentage",
        ge=0.0,
        le=100.0
    )
    
    # Profile Information  
    niche: str = Field(description="Content niche/category")
    bio: Optional[str] = Field(default=None, description="Profile bio/description")
    verified: bool = Field(default=False, description="Account verification status")
    
    # Demographics & Audience
    audience_demographics: dict = Field(
        default_factory=dict,
        description="Audience demographic breakdown"
    )
    location: Optional[str] = Field(default=None, description="Primary location")
    
    # Contact & Business
    contact_email: Optional[str] = Field(default=None, description="Business email")
    contact_info: Optional[str] = Field(default=None, description="Other contact info")
    
    # Performance Metrics
    historical_performance: dict = Field(
        default_factory=dict,
        description="Historical performance metrics"
    )
    
    # Quality Scores
    authenticity_score: float = Field(
        default=0.0,
        description="Authenticity/fraud detection score (0-1, higher is better)",
        ge=0.0,
        le=1.0
    )
    match_score: float = Field(
        default=0.0,
        description="Match score for search criteria (0-1)",
        ge=0.0,
        le=1.0
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "inf_001",
                "username": "@fitness_creator_1", 
                "platform": "instagram",
                "display_name": "Fitness Creator",
                "followers": 50000,
                "engagement_rate": 3.5,
                "niche": "fitness",
                "bio": "Certified personal trainer sharing daily workouts",
                "verified": True,
                "audience_demographics": {
                    "age_group": "18-34", 
                    "gender": "mixed",
                    "top_locations": ["US", "UK", "Canada"]
                },
                "location": "Los Angeles, CA",
                "contact_email": "business@creator.com",
                "historical_performance": {
                    "avg_likes": 1750,
                    "avg_comments": 87,
                    "avg_shares": 15
                },
                "authenticity_score": 0.9,
                "match_score": 0.85
            }
        }


class SearchResult(BaseModel):
    """Schema for search result metadata"""
    
    query: InfluencerSearchQuery = Field(description="Original search query")
    total_found: int = Field(description="Total number of influencers found")
    results_returned: int = Field(description="Number of results returned")
    search_duration_ms: Optional[int] = Field(
        default=None,
        description="Search execution time in milliseconds"
    )
    filters_applied: List[str] = Field(
        default_factory=list,
        description="List of filters that were applied"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": {
                    "platform": "instagram",
                    "niche": "fitness", 
                    "min_followers": 10000,
                    "max_followers": 100000,
                    "keywords": ["fitness", "workout"]
                },
                "total_found": 150,
                "results_returned": 3,
                "search_duration_ms": 1250,
                "filters_applied": ["authenticity_check", "engagement_filter"]
            }
        }


class ClarifyWithUser(BaseModel):
    """Model for user clarification requests in influencer search context."""
    
    need_clarification: bool = Field(
        description="Whether the user needs to be asked a clarifying question.",
    )
    question: str = Field(
        description="A question to ask the user to clarify the search scope",
    )
    verification: str = Field(
        description="Verification message that we will start search after the user has provided the necessary information.",
    )


class InfluencerResearchBrief(BaseModel):
    """Structured research brief for influencer marketing campaigns."""
    
    research_brief: str = Field(
        description="A comprehensive research brief that will guide the influencer marketing research and strategy development.",
        min_length=100
    )
    target_platforms: List[str] = Field(
        description="Social media platforms to focus on (e.g., Instagram, TikTok, YouTube, LinkedIn)",
        examples=[["Instagram", "TikTok"], ["YouTube"], ["LinkedIn", "Twitter"]]
    )
    niche_focus: str = Field(
        description="Primary content niche or industry vertical",
        examples=["fitness", "beauty", "technology", "food", "travel", "business"]
    )
    geographic_focus: Optional[str] = Field(
        description="Geographic targeting for influencers",
        default=None,
        examples=["US", "Europe", "Global", "Asia-Pacific"]
    )
    follower_range: Optional[str] = Field(
        description="Desired influencer tier based on follower count",
        default=None,
        examples=["micro (1K-100K)", "mid-tier (100K-1M)", "macro (1M+)", "mixed"]
    )
    campaign_objectives: List[str] = Field(
        description="Primary marketing objectives for the campaign",
        examples=[["brand awareness", "product launch"], ["engagement boost"], ["sales conversion"]]
    )
    budget_considerations: Optional[str] = Field(
        description="Budget constraints or investment level",
        default=None,
        examples=["startup budget ($1K-5K)", "enterprise level ($50K+)", "mid-market ($5K-50K)"]
    )
    content_preferences: Optional[List[str]] = Field(
        description="Preferred content formats and styles",
        default=None,
        examples=[["video reviews", "unboxing"], ["tutorials", "lifestyle integration"], ["stories", "reels"]]
    )
    timeline: Optional[str] = Field(
        description="Campaign timeline and urgency",
        default=None,
        examples=["immediate launch", "Q2 2024", "ongoing partnership", "seasonal campaign"]
    )