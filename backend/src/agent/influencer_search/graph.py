"""
LangGraph construction and compilation for influencer search agent.

Defines the graph structure, node connections, and control flow
for the influencer search workflow using LangGraph patterns.
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

# Import local modules
from agent.influencer_search.state import InfluencerSearchState, InfluencerSearchInputState
from agent.influencer_search.nodes import parse_search_request, search_influencers, refine_search
from agent.configuration import Configuration

# Setup logging
logger = logging.getLogger(__name__)


def should_refine_results(state: InfluencerSearchState) -> Literal["refine_search", "__end__"]:
    """
    Conditional edge: Determine if search results need refinement.
    
    Decision logic:
    - If no results found -> end (will show no results guidance)
    - If too many results (>10) -> refine to narrow down
    - If results look good -> end
    """
    search_results = state.get("search_results", [])
    search_query = state.get("search_query")
    
    # No results - end immediately
    if not search_results:
        logger.info("No results found, ending workflow")
        return "__end__"
    
    # Too many results - refine
    if len(search_results) > 10:
        logger.info(f"Found {len(search_results)} results, applying refinement")
        return "refine_search"
    
    # Check if results need quality improvement
    avg_match_score = sum(r.match_score for r in search_results) / len(search_results)
    if avg_match_score < 0.7:
        logger.info(f"Average match score {avg_match_score:.2f} is low, applying refinement")
        return "refine_search"
    
    # Results are good, end workflow
    logger.info(f"Found {len(search_results)} good quality results, ending workflow")
    return "__end__"


def create_influencer_search_graph() -> StateGraph:
    """
    Create and compile the influencer search graph.
    
    Graph Flow:
    START -> parse_search_request -> search_influencers -> [conditional] -> refine_search -> END
                                                        -> [conditional] -> END
    
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
    
    # Add nodes with single responsibilities
    builder.add_node("parse_search_request", parse_search_request)
    builder.add_node("search_influencers", search_influencers)  
    builder.add_node("refine_search", refine_search)
    
    # Define graph flow
    builder.add_edge(START, "parse_search_request")
    builder.add_edge("parse_search_request", "search_influencers")
    
    # Conditional routing after search
    builder.add_conditional_edges(
        "search_influencers",
        should_refine_results,
        {
            "refine_search": "refine_search",
            "__end__": END
        }
    )
    
    # End after refinement
    builder.add_edge("refine_search", END)
    
    # Compile the graph
    graph = builder.compile()
    
    logger.info("✅ Influencer search graph compiled successfully")
    return graph

# Export the main graph instance
graph = create_influencer_search_graph()