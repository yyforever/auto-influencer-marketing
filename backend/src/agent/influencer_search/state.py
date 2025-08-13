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

def override_reducer(current_value, new_value):
    """Reducer function that allows overriding values in state."""
    if isinstance(new_value, dict) and new_value.get("type") == "override":
        return new_value.get("value", new_value)
    else:
        return operator.add(current_value, new_value)


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
    
    supervisor_messages: Annotated[List[BaseMessage], override_reducer] = []
    """Messages for supervisor conversation (accumulated)"""
    
    supervisor_active: bool = False
    """Flag indicating if research supervisor is active"""
    
    # Research Results and Notes
    notes: Annotated[List[str], override_reducer] = []
    """Research findings and notes collected during the workflow"""
    
    # Final Report Generation
    final_report: Optional[str] = None
    """Final comprehensive research report"""
    
    report_completed: bool = False
    """Flag indicating if final report has been generated"""
    
    # Error Handling
    last_error: Optional[str] = None
    """Last error message if any step failed"""


# Supervisor State for Research Coordination
# ==========================================

class SupervisorState(TypedDict):
    """State for the influencer marketing research supervisor."""
    
    supervisor_messages: Annotated[List[BaseMessage], override_reducer]
    research_brief: str
    notes: Annotated[List[str], override_reducer]
    research_iterations: int
    raw_notes: Annotated[List[str], override_reducer]


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


# Type aliases for cleaner imports
SearchInputState = InfluencerSearchInputState
SearchState = InfluencerSearchState