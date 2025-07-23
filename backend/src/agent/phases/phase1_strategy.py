"""
Phase 1: Strategy Planning - Campaign objective and budget definition.
"""

import logging
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END

from agent.state import CampaignState, StrategyState
from agent.tools import InfluencityAPI
from agent.utils import create_hitl_node

logger = logging.getLogger(__name__)


def init_goal(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Initialize campaign goal from user brief.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with parsed objective and KPIs
    """
    logger.info(f"🎯 Initializing campaign goal, state: {state}")
    
    # Simulate parsing user brief
    user_brief = state.get("user_brief", "Brand awareness campaign for lifestyle brand")
    
    # Parse objective
    objective = f"Parsed objective: {user_brief}"
    
    # Generate KPIs based on objective
    kpi = {
        "target_reach": 100000,
        "target_engagement_rate": 0.03,
        "target_cpm": 5.0,
        "target_roas": 3.0
    }
    
    # Define target audience
    target_audience = {
        "age_range": "18-34",
        "gender": "mixed",
        "interests": ["lifestyle", "fashion", "wellness"],
        "location": "US, CA, UK"
    }
    
    logger.info(f"✅ Goal initialized: {objective}")
    logger.info(f"📊 KPIs: {kpi}")
    logger.info(f"👥 Target audience: {target_audience}")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append("Campaign goal initialized")
    logger.info(f"🎯 Initializing campaign goal END, state: {state}")
    return {
        "objective": objective,
        "kpi": kpi,
        "target_audience": target_audience,
        "logs": logs
    }


def budget_predictor(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Predict budget requirements using Influencity API.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with budget prediction
    """
    logger.info(f"💰 Predicting budget requirements, state: {state}")
    
    # Get campaign details
    objective = state.get("objective", "")
    kpi = state.get("kpi", {})
    
    # Use Influencity API for prediction
    api = InfluencityAPI("demo_key")
    
    # Calculate initial budget estimate
    initial_budget = 10000.0  # Base budget
    
    # Get ROI prediction
    roi_prediction = api.predict_roi.invoke(
        {
            "objective": objective,
            "initial_budget": initial_budget,
            "kpi": kpi
        }
    )
    
    # Adjust budget based on prediction
    predicted_budget = initial_budget * roi_prediction.get("predicted_roas", 1.0)
    
    logger.info(f"📈 ROI prediction: {roi_prediction}")
    logger.info(f"💵 Predicted budget: ${predicted_budget:.2f}")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Budget predicted: ${predicted_budget:.2f}")
    
    logger.info(f"💰 Predicting budget requirements END, state: {state}")
    return {
        "budget": predicted_budget,
        "logs": logs
    }


def finish_phase1(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Complete Phase 1 and transition to Phase 2.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with phase transition
    """
    logger.info("🏁 Completing Phase 1: Strategy")
    
    # Update phase
    phase = 2
    
    # Add completion log
    logs = state.get("logs", [])
    logs.append("Phase 1 (Strategy) completed")
    logs.append("Transitioning to Phase 2 (Discovery)")
    
    logger.info("✅ Phase 1 completed successfully")
    logger.info("➡️ Moving to Phase 2: Discovery")
    
    return {
        "phase": phase,
        "logs": logs
    }


def create_strategy_subgraph() -> StateGraph:
    """
    Create the Strategy phase subgraph.
    
    Returns:
        Compiled strategy subgraph
    """
    logger.info("🏗️ Creating Strategy subgraph")
    
    # Create subgraph
    builder = StateGraph(CampaignState)
    
    # Add nodes
    builder.add_node("init_goal", init_goal)
    builder.add_node("budget_predictor", budget_predictor)
    builder.add_node("HITL_review", create_hitl_node("strategy"))
    builder.add_node("finish_p1", finish_phase1)
    
    # Add edges
    builder.add_edge(START, "init_goal")
    builder.add_edge("init_goal", "budget_predictor")
    builder.add_edge("budget_predictor", "HITL_review")
    builder.add_edge("HITL_review", "finish_p1")
    builder.add_edge("finish_p1", END)
    
    # Compile subgraph
    subgraph = builder.compile(name="strategy-phase")
    
    logger.info("✅ Strategy subgraph created")
    return subgraph


# Export as toolified agent
def create_strategy_tool():
    """
    Create toolified version of strategy subgraph.
    
    Returns:
        Strategy tool for external use
    """
    from langchain_core.tools import tool
    
    @tool
    def strategy_planning_tool(user_brief: str, initial_budget: float = None) -> Dict[str, Any]:
        """
        Execute campaign strategy planning.
        
        Args:
            user_brief: Campaign brief from user
            initial_budget: Optional initial budget hint
            
        Returns:
            Strategy planning results
        """
        logger.info("🔧 Strategy tool activated")
        
        # Create initial state
        state = CampaignState(
            user_brief=user_brief,
            budget=initial_budget or 0,
            phase=1,
            logs=[]
        )
        
        # Execute strategy subgraph
        subgraph = create_strategy_subgraph()
        result = subgraph.invoke(state)
        
        logger.info("✅ Strategy tool completed")
        return result
    
    return strategy_planning_tool