"""
LangGraph state management for influencer search workflow.

Defines the state schema and data flow for the influencer search agent,
following LangGraph best practices for subgraph state management.
"""

from typing import List, Optional
from typing_extensions import TypedDict, Annotated
import operator

from langgraph.graph import MessagesState
from langchain_core.messages import BaseMessage

from .schemas import InfluencerSearchQuery, InfluencerProfile, SearchResult


class InfluencerSearchInputState(MessagesState):
    """
    Input state for influencer search agent.
    
    Following LangGraph pattern: InputState contains only 'messages'
    for communication with parent graph or external callers.
    """
    pass


class InfluencerSearchState(MessagesState):
    """
    Complete state for influencer search workflow.
    
    Extends MessagesState to maintain conversation history while adding
    search-specific state fields. Uses Annotated types for proper
    LangGraph state management and accumulation patterns.
    """
    
    # Search Parameters
    search_query: Optional[InfluencerSearchQuery] = None
    """Parsed and structured search query"""
    
    # Search Results & Metadata
    search_results: Annotated[List[InfluencerProfile], operator.add] = []
    """List of found influencer profiles (accumulated)"""
    
    search_metadata: Optional[SearchResult] = None
    """Metadata about the search execution"""
    
    # Workflow Control
    search_completed: bool = False
    """Flag indicating if search workflow is complete"""
    
    query_parsed: bool = False
    """Flag indicating if user query has been parsed"""
    
    # Error Handling
    last_error: Optional[str] = None
    """Last error message if any step failed"""
    
    # Optional: Filtering and Ranking
    applied_filters: Annotated[List[str], operator.add] = []
    """List of filters applied during search (accumulated)"""
    
    ranking_criteria: Optional[dict] = None
    """Criteria used for ranking results"""
    
    # Research Brief Workflow Fields
    research_brief: Optional[str] = None
    """Generated research brief for influencer marketing campaign"""
    
    research_metadata: Optional[dict] = None
    """Structured metadata from research brief generation"""
    
    supervisor_messages: Annotated[List[BaseMessage], operator.add] = []
    """Messages for supervisor conversation (accumulated)"""
    
    supervisor_active: bool = False
    """Flag indicating if research supervisor is active"""


class InfluencerSearchWorkingState(TypedDict, total=False):
    """
    Working state for intermediate calculations.
    
    This state is used for temporary data that doesn't need to be
    persisted across the entire workflow. Useful for passing data
    between closely related nodes.
    """
    
    raw_search_results: List[dict]
    """Raw API results before transformation to InfluencerProfile"""
    
    filtering_stats: dict
    """Statistics about filtering process"""
    
    ranking_scores: dict
    """Detailed ranking scores for debugging"""
    
    api_response_time: int
    """API response time in milliseconds"""


# Type aliases for cleaner imports
SearchInputState = InfluencerSearchInputState
SearchState = InfluencerSearchState
WorkingState = InfluencerSearchWorkingState