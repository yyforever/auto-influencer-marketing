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
        description="A comprehensive research brief that will guide the influencer marketing research and strategy development. Brief should include all key information for influencer marketing research."
    )
    # Core campaign context (aligned to test case)
    brand_name: Optional[str] = Field(
        description="Brand name for the campaign (e.g., 'HeyGears')",
        default=None,
        examples=["HeyGears"]
    )
    product_names: Optional[List[str]] = Field(
        description="Product names involved in the campaign (e.g., 'UltraCraft 3D Printer', 'U1 Custom Earbuds')",
        default=None,
        examples=[["UltraCraft 3D Printer", "U1 Custom Earbuds"]]
    )
    product_type: Optional[str] = Field(
        description="Product type/category (e.g., 'Physical Product').",
        default=None,
        examples=["Physical Product"]
    )
    product_links: Optional[List[str]] = Field(
        description="Relevant product or landing page URLs to reference in research and content.",
        default=None,
        examples=[["https://store.heygears.com/collections/3d-printers"]]
    )
    product_summary: Optional[str] = Field(
        description="Product overview including price notes and key description (free-form).",
        default=None,
        examples=["$979-$1,399; 系统 $1,749；定制耳机定价。高精度DLP 3D打印机，25μm 精度，TI DLP 技术，适用于牙科/消费电子/珠宝/工程原型等，支持量产"]
    )
    target_platforms: List[str] = Field(
        description="Social media platforms to focus on (e.g., Instagram, TikTok, YouTube, LinkedIn)",
        examples=[["Instagram", "TikTok"], ["YouTube"], ["LinkedIn"]]
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
    languages: Optional[List[str]] = Field(
        description="Primary content or audience languages (e.g., ['English']).",
        default=None,
        examples=[["English"]]
    )
    follower_range: Optional[str] = Field(
        description="Desired influencer tier based on follower count",
        default=None,
        examples=["micro (1K-100K)", "mid-tier (100K-1M)", "macro (1M+)", "mixed"]
    )
    influencer_count_target: Optional[str] = Field(
        description="Target number of influencers to collaborate with (e.g., '25-30').",
        default=None,
        examples=["25-30"]
    )
    expected_impressions: Optional[str] = Field(
        description="Target or expected total impressions across campaign (e.g., '2,000,000').",
        default=None,
        examples=["2,000,000"]
    )
    campaign_objectives: List[str] = Field(
        description="Primary marketing objectives for the campaign",
        examples=[["brand awareness", "product launch"], ["engagement boost"], ["sales conversion"]]
    )
    budget: Optional[str] = Field(
        description="Total budget and any constraints/notes (free-form, e.g., '$15,000').",
        default=None,
        examples=["$15,000"]
    )
    content_requirements: Optional[List[str]] = Field(
        description="Content formats and mandatory elements combined (e.g., YouTube长视频+精度对比、应用场景、技术参数、ROI等)。",
        default=None
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


class ResearchComplete(BaseModel):
    """Tool to signal completion of individual research task."""
    
    pass  # No parameters needed - completion signal only


# Researcher State Management for Individual Research Tasks
# ========================================================

class ResearcherInputState(TypedDict):
    """Input state for individual researcher agents."""
    researcher_messages: Annotated[List[BaseMessage], override_reducer]
    research_topic: str


class ResearcherState(TypedDict):
    """Complete state for individual researcher workflow."""
    researcher_messages: Annotated[List[BaseMessage], override_reducer]
    research_topic: str
    tool_call_iterations: int


class ResearcherOutputState(TypedDict):
    """Output state from researcher with compressed results."""
    compressed_research: str
    raw_notes: Annotated[List[str], override_reducer]