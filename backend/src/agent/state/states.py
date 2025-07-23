"""
Campaign state definition for Influencer Marketing Agent.
"""

from typing import Dict, List, Literal, Optional, Any
from typing_extensions import TypedDict, Annotated
import operator

from langgraph.graph import add_messages

from .models import Creator, Contract, Script, PostLink, Metric, Invoice


# class OverallState(TypedDict):
#     """
#     Overall state for influencer marketing campaign.
#     """
#     messages: Annotated[list, add_messages]
#     user_query: Annotated[list, operator.add]

class CampaignState(TypedDict, total=False):
    """
    Global state for influencer marketing campaign.
    """
    messages: Annotated[list, add_messages]
    
    # Campaign Definition
    objective: str                              # Campaign goal (brand awareness, sales, etc.)
    budget: float                              # Available budget
    kpi: Dict[str, float]                      # Key metrics: CPM, CPA, ROAS, etc.
    target_audience: Dict[str, Any]            # Demographics, interests, etc.
    
    # Campaign Assets
    candidates: Annotated[List[Creator], operator.add]         # Potential influencers
    contracts: Annotated[List[Contract], operator.add]         # Signed contracts
    scripts: Annotated[List[Script], operator.add]             # Content scripts
    posts: Annotated[List[PostLink], operator.add]             # Published posts
    performance: Dict[str, Metric]                             # Real-time metrics
    settlements: Annotated[List[Invoice], operator.add]        # Payment records
    
    # Campaign Flow Control
    phase: Literal[1, 2, 3, 4, 5, 6, 7]       # Current phase
    iteration_count: Dict[str, int]            # Loop counters for each phase
    
    # Audit Trail
    logs: Annotated[List[str], operator.add]   # Event logs
    approvals: Dict[str, str]                  # HITL approval records
    
    # Temporary Working Data (cleaned between phases)
    current_search_results: List[Dict[str, Any]]
    current_negotiations: List[Dict[str, Any]]
    current_drafts: List[Dict[str, Any]]
    
    # Campaign Metadata
    campaign_id: str
    brand_name: str
    created_at: str
    updated_at: str


# Specialized state types for specific subgraphs
# Following LangGraph best practices: "为每个子图声明自己的专用 State"

class StrategyState(TypedDict, total=False):
    """State for Phase 1: Strategy Planning subgraph"""
    user_brief: str
    parsed_objective: str
    predicted_budget: float
    roi_forecast: Dict[str, float]
    target_audience: Dict[str, Any]
    kpi: Dict[str, float]


class DiscoveryState(TypedDict, total=False):
    """State for Phase 2: Discovery subgraph"""
    search_criteria: Dict[str, Any]
    current_search_results: Annotated[List[Dict[str, Any]], operator.add]
    candidates: Annotated[List[Creator], operator.add]
    fraud_check_results: List[Dict[str, Any]]


class OutreachState(TypedDict, total=False):
    """State for Phase 3: Outreach subgraph"""
    current_negotiations: Annotated[List[Dict[str, Any]], operator.add]
    contracts: Annotated[List[Contract], operator.add]
    email_templates: List[Dict[str, str]]
    iteration_count: Dict[str, int]


class CocreationState(TypedDict, total=False):
    """State for Phase 4: Co-creation subgraph"""
    current_drafts: Annotated[List[Dict[str, Any]], operator.add]
    scripts: Annotated[List[Script], operator.add]
    brand_guidelines: Dict[str, Any]
    compliance_results: List[Dict[str, Any]]


class PublishState(TypedDict, total=False):
    """State for Phase 5: Publish subgraph"""
    posts: Annotated[List[PostLink], operator.add]
    publishing_schedule: Dict[str, Any]
    platform_results: Dict[str, Any]
    boost_campaigns: List[Dict[str, Any]]


class MonitorState(TypedDict, total=False):
    """State for Phase 6: Monitor subgraph"""
    performance: Dict[str, Metric]
    optimization_decisions: Annotated[List[Dict[str, Any]], operator.add]
    metrics_data: Dict[str, Any]
    iteration_count: Dict[str, int]


class SettleState(TypedDict, total=False):
    """State for Phase 7: Settle subgraph"""
    settlements: Annotated[List[Invoice], operator.add]
    payment_calculations: Dict[str, Any]
    archive_manifest: List[Dict[str, Any]]
    final_report: Dict[str, Any]