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

# No legacy schema imports needed


class InfluencerSearchInputState(MessagesState):
    """
    Input state for influencer search agent.
    
    Following LangGraph pattern: InputState contains only 'messages'
    for communication with parent graph or external callers.
    """
    pass


class InfluencerSearchState(MessagesState):
    """
    Complete state for influencer marketing research workflow.
    
    Extends MessagesState to maintain conversation history while adding
    research-specific state fields for the streamlined research-oriented workflow.
    """
    
    # Research Brief Workflow Fields
    research_brief: Optional[str] = None
    """Generated research brief for influencer marketing campaign"""
    
    research_metadata: Optional[dict] = None
    """Structured metadata from research brief generation"""
    
    supervisor_messages: Annotated[List[BaseMessage], operator.add] = []
    """Messages for supervisor conversation (accumulated)"""
    
    supervisor_active: bool = False
    """Flag indicating if research supervisor is active"""
    
    # Research Results and Notes
    notes: Annotated[List[str], operator.add] = []
    """Research findings and notes collected during the workflow"""
    
    # Final Report Generation
    final_report: Optional[str] = None
    """Final comprehensive research report"""
    
    report_completed: bool = False
    """Flag indicating if final report has been generated"""
    
    # Error Handling
    last_error: Optional[str] = None
    """Last error message if any step failed"""


# Type aliases for cleaner imports
SearchInputState = InfluencerSearchInputState
SearchState = InfluencerSearchState