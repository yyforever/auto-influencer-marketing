"""
LangGraph construction and compilation for influencer search agent.

Defines the graph structure, node connections, and control flow
for the influencer search workflow using LangGraph patterns.
"""

import logging

from langgraph.graph import StateGraph, START, END

# Import local modules
from agent.influencer_search.state import InfluencerSearchState, InfluencerSearchInputState
from agent.influencer_search.nodes import clarify_with_user, write_research_brief, research_supervisor
from agent.configuration import Configuration

# Setup logging
logger = logging.getLogger(__name__)


def create_influencer_search_graph() -> StateGraph:
    """
    Create and compile the influencer search graph.
    
    Graph Flow:
    START -> clarify_with_user -> write_research_brief -> research_supervisor -> END
    
    This is a streamlined research-oriented workflow that:
    1. Optionally clarifies user requirements (skippable via configuration)
    2. Generates a structured research brief from user messages
    3. Invokes the research supervisor for comprehensive analysis
    
    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("🏗️ Creating influencer search graph")
    
    # Initialize graph builder with state schemas
    builder = StateGraph(
        InfluencerSearchState,
        input=InfluencerSearchInputState,
        config_schema=Configuration
    )
    
    # Add nodes for the research-oriented workflow
    builder.add_node("clarify_with_user", clarify_with_user)
    builder.add_node("write_research_brief", write_research_brief)
    builder.add_node("research_supervisor", research_supervisor)
    
    # Define linear graph flow
    builder.add_edge(START, "clarify_with_user")
    # clarify_with_user uses Command to route to either write_research_brief or END
    # write_research_brief uses Command to route to research_supervisor
    builder.add_edge("research_supervisor", END)
    
    # Compile the graph
    graph = builder.compile()
    
    logger.info("✅ Influencer search graph compiled successfully")
    return graph

# Export the main graph instance
graph = create_influencer_search_graph()