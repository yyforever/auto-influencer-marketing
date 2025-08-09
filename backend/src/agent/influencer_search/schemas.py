"""
Pydantic schemas for influencer search functionality.

Defines structured data models for influencer search queries, results,
and related data structures used throughout the search workflow.
"""

from typing import List, Optional, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import operator

from langchain_core.messages import BaseMessage


# Legacy schemas removed - using research-oriented workflow only


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


# Supervisor State and Tools for Research Coordination
# ====================================================

def override_reducer(existing_value: list, new_value: list) -> list:
    """Reducer that replaces the existing value with the new value."""
    # pylint: disable=unused-argument
    return new_value

class SupervisorState(TypedDict):
    """State for the influencer marketing research supervisor."""
    
    supervisor_messages: Annotated[List[BaseMessage], override_reducer]
    research_brief: str
    notes: Annotated[List[str], override_reducer]
    research_iterations: int
    raw_notes: Annotated[List[str], override_reducer]


class ConductInfluencerResearch(BaseModel):
    """Tool for delegating influencer marketing research to specialized researchers."""
    
    research_topic: str = Field(
        description="""The specific influencer marketing research topic to investigate. 
        Should be a single focused topic described in high detail (at least a paragraph).
        
        Examples:
        - "Research top fitness influencers on Instagram with 100K-1M followers who focus on home workouts and have high engagement rates with female audiences aged 25-35"
        - "Analyze TikTok beauty influencers who have successfully promoted skincare products, focusing on their content styles, engagement patterns, and collaboration approaches"
        - "Investigate micro-influencers in the tech space who review mobile apps, particularly those with authentic audiences and strong conversion rates for app downloads"
        """
    )


class InfluencerResearchComplete(BaseModel):
    """Tool to signal completion of influencer marketing research phase."""
    
    pass  # No parameters needed - completion signal only