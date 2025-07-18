"""
Auto Influencer Marketing Graph - Main orchestration graph.

This is the main entry point for the influencer marketing campaign agent.
It orchestrates the 7-phase campaign workflow using LangGraph subgraphs.
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END

# Import state management
from agent.state import CampaignState
from agent.configuration import Configuration

# Import all phase subgraphs
from agent.phases import (
    create_strategy_subgraph,
    create_discovery_subgraph,
    create_outreach_subgraph,
    create_cocreation_subgraph,
    create_publish_subgraph,
    create_monitor_subgraph,
    create_settle_subgraph
)

# Import utilities
from agent.utils import setup_campaign_logging, log_phase_transition

# Load environment variables
load_dotenv()

# Validate required environment variables
if os.getenv("GEMINI_API_KEY") is None:
    raise ValueError("GEMINI_API_KEY is not set")

# Setup logging
logger = logging.getLogger(__name__)


def initialize_campaign(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Initialize a new influencer marketing campaign.
    
    Args:
        state: Initial campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with campaign initialization
    """
    logger.info("🚀 Initializing Influencer Marketing Campaign")
    
    # Generate campaign ID if not provided
    campaign_id = state.get("campaign_id", f"campaign_{int(os.urandom(4).hex(), 16)}")
    
    # Initialize campaign metadata
    brand_name = state.get("brand_name", "Demo Brand")
    
    # Setup campaign logging
    campaign_logger = setup_campaign_logging(campaign_id)
    
    # Initialize state with defaults
    initial_state = {
        "campaign_id": campaign_id,
        "brand_name": brand_name,
        "phase": 1,
        "iteration_count": {},
        "logs": [f"Campaign initialized: {campaign_id}"],
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    }
    
    # Add any missing required fields
    if not state.get("candidates"):
        initial_state["candidates"] = []
    if not state.get("contracts"):
        initial_state["contracts"] = []
    if not state.get("scripts"):
        initial_state["scripts"] = []
    if not state.get("posts"):
        initial_state["posts"] = []
    if not state.get("settlements"):
        initial_state["settlements"] = []
    if not state.get("approvals"):
        initial_state["approvals"] = {}
    
    campaign_logger.info(f"✅ Campaign initialized: {campaign_id}")
    campaign_logger.info(f"🏢 Brand: {brand_name}")
    
    return initial_state


def phase_router(state: CampaignState, config: RunnableConfig) -> str:
    """
    Route to the appropriate phase based on current state.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Next phase name
    """
    current_phase = state.get("phase", 1)
    
    phase_map = {
        1: "phase1_strategy",
        2: "phase2_discovery", 
        3: "phase3_outreach",
        4: "phase4_cocreation",
        5: "phase5_publish",
        6: "phase6_monitor",
        7: "phase7_settle"
    }
    
    next_phase = phase_map.get(current_phase, "phase1_strategy")
    
    logger.info(f"🔀 Routing to {next_phase} (phase {current_phase})")
    
    return next_phase


def finalize_campaign(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Finalize the campaign and generate summary.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Final campaign state
    """
    logger.info("🏁 Finalizing Influencer Marketing Campaign")
    
    # Get campaign summary
    from agent.utils.logging import create_campaign_summary
    campaign_summary = create_campaign_summary(state)
    
    # Update final state
    final_logs = state.get("logs", [])
    final_logs.append("Campaign completed successfully")
    
    logger.info(f"✅ Campaign completed: {state.get('campaign_id')}")
    logger.info(f"📊 Final metrics: {campaign_summary['metrics']}")
    
    return {
        "logs": final_logs,
        "campaign_summary": campaign_summary,
        "updated_at": "2024-01-20T18:00:00Z"
    }


def create_influencer_marketing_graph() -> StateGraph:
    """
    Create the main influencer marketing campaign graph.
    
    Returns:
        Compiled main campaign graph
    """
    logger.info("🏗️ Creating Influencer Marketing Graph")
    
    # Create main graph
    builder = StateGraph(CampaignState)
    
    # Add initialization node
    builder.add_node("initialize_campaign", initialize_campaign)
    
    # Add all phase subgraphs as nodes
    builder.add_node("phase1_strategy", create_strategy_subgraph())
    builder.add_node("phase2_discovery", create_discovery_subgraph())
    builder.add_node("phase3_outreach", create_outreach_subgraph())
    builder.add_node("phase4_cocreation", create_cocreation_subgraph())
    builder.add_node("phase5_publish", create_publish_subgraph())
    builder.add_node("phase6_monitor", create_monitor_subgraph())
    builder.add_node("phase7_settle", create_settle_subgraph())
    
    # Add finalization node
    builder.add_node("finalize_campaign", finalize_campaign)
    
    # Define the main workflow edges
    builder.add_edge(START, "initialize_campaign")
    builder.add_edge("initialize_campaign", "phase1_strategy")
    builder.add_edge("phase1_strategy", "phase2_discovery")
    builder.add_edge("phase2_discovery", "phase3_outreach")
    builder.add_edge("phase3_outreach", "phase4_cocreation")
    builder.add_edge("phase4_cocreation", "phase5_publish")
    builder.add_edge("phase5_publish", "phase6_monitor")
    builder.add_edge("phase6_monitor", "phase7_settle")
    builder.add_edge("phase7_settle", "finalize_campaign")
    builder.add_edge("finalize_campaign", END)
    
    # Compile the graph
    graph = builder.compile(name="influencer-marketing-campaign")
    
    logger.info("✅ Influencer Marketing Graph created successfully")
    
    return graph


# Create the main graph instance
graph = create_influencer_marketing_graph()


def run_campaign(
    objective: str,
    budget: float,
    target_audience: Dict[str, Any],
    brand_name: str = "Demo Brand",
    **kwargs
) -> Dict[str, Any]:
    """
    Run a complete influencer marketing campaign.
    
    Args:
        objective: Campaign objective
        budget: Campaign budget
        target_audience: Target audience definition
        brand_name: Brand name
        **kwargs: Additional campaign parameters
        
    Returns:
        Campaign results
    """
    logger.info(f"🎯 Starting influencer marketing campaign: {objective}")
    
    # Create initial state
    initial_state = CampaignState(
        objective=objective,
        budget=budget,
        target_audience=target_audience,
        brand_name=brand_name,
        **kwargs
    )
    
    # Run the campaign
    result = graph.invoke(initial_state)
    
    logger.info("🎉 Campaign completed successfully")
    
    return result


# Export toolified agents for external use
def create_toolified_agents():
    """
    Create toolified versions of all phase agents.
    
    Returns:
        Dictionary of toolified agents
    """
    from agent.phases.phase1_strategy import create_strategy_tool
    from agent.phases.phase2_discovery import create_discovery_tool
    from agent.phases.phase3_outreach import create_outreach_tool
    from agent.phases.phase4_cocreation import create_cocreation_tool
    from agent.phases.phase5_publish import create_publish_tool
    from agent.phases.phase6_monitor import create_monitor_tool
    from agent.phases.phase7_settle import create_settle_tool
    
    return {
        "strategy_tool": create_strategy_tool(),
        "discovery_tool": create_discovery_tool(),
        "outreach_tool": create_outreach_tool(),
        "cocreation_tool": create_cocreation_tool(),
        "publish_tool": create_publish_tool(),
        "monitor_tool": create_monitor_tool(),
        "settle_tool": create_settle_tool()
    }


# Example usage
if __name__ == "__main__":
    # Demo campaign parameters
    demo_objective = "Brand awareness campaign for sustainable lifestyle products"
    demo_budget = 15000.0
    demo_target_audience = {
        "age_range": "25-40",
        "gender": "mixed",
        "interests": ["sustainability", "lifestyle", "wellness"],
        "location": "US, CA, UK"
    }
    
    # Run demo campaign
    logger.info("🚀 Running demo campaign")
    result = run_campaign(
        objective=demo_objective,
        budget=demo_budget,
        target_audience=demo_target_audience,
        brand_name="EcoLife"
    )
    
    logger.info("🎉 Demo campaign completed")
    logger.info(f"📊 Results: {result.get('campaign_summary', {})}")
