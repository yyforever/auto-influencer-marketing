"""
Phase 2: Discovery - Influencer search and validation with parallel processing.
"""

import logging
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from agent.state import CampaignState, DiscoveryState
from agent.tools import InfluencityAPI
from agent.state.models import Creator

logger = logging.getLogger(__name__)


def search_by_topic(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Search for influencers by topic/niche.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with topic-based search results
    """
    logger.info("🔍 Searching influencers by topic")
    
    # Get search criteria
    objective = state.get("objective", "")
    target_audience = state.get("target_audience", {})
    
    # Extract topic from objective
    topic = "lifestyle"  # Simplified extraction
    
    # Create search filters
    filters = {
        "platform": "instagram",
        "min_followers": 10000,
        "max_followers": 500000,
        "min_engagement_rate": 0.02,
        "location": target_audience.get("location", "US")
    }
    
    # Use Influencity API
    api = InfluencityAPI("demo_key")
    search_results = api.search_influencers_by_topic(topic, filters)
    
    logger.info(f"✅ Found {len(search_results)} topic-based influencers")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Topic search completed: {len(search_results)} results")
    
    return {
        "current_search_results": search_results,
        "logs": logs
    }


def search_by_audience(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Search for influencers by audience demographics.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with audience-based search results
    """
    logger.info("👥 Searching influencers by audience")
    
    # Get audience criteria
    target_audience = state.get("target_audience", {})
    
    # Use Influencity API
    api = InfluencityAPI("demo_key")
    search_results = api.search_by_audience(target_audience)
    
    logger.info(f"✅ Found {len(search_results)} audience-matched influencers")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Audience search completed: {len(search_results)} results")
    
    return {
        "current_search_results": search_results,
        "logs": logs
    }


def lookalike_search(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Find similar influencers using lookalike algorithm.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with lookalike search results
    """
    logger.info("🔄 Performing lookalike search")
    
    # Use reference influencer (simplified)
    reference_influencer = "top_performer_123"
    
    # Use Influencity API
    api = InfluencityAPI("demo_key")
    search_results = api.lookalike_search(reference_influencer)
    
    logger.info(f"✅ Found {len(search_results)} lookalike influencers")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Lookalike search completed: {len(search_results)} results")
    
    return {
        "current_search_results": search_results,
        "logs": logs
    }


def start_parallel_search(state: CampaignState) -> List[Send]:
    """
    Start parallel search operations.
    
    Args:
        state: Current campaign state
        
    Returns:
        List of Send objects for parallel execution
    """
    logger.info("🚀 Starting parallel influencer search")
    
    # Create parallel search tasks
    return [
        Send("search_by_topic", state),
        Send("search_by_audience", state),
        Send("lookalike_search", state)
    ]


def fraud_check(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Check for fraud indicators in search results.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with fraud check results
    """
    logger.info("🛡️ Running fraud detection")
    
    # Get search results
    search_results = state.get("current_search_results", [])
    
    # Extract influencer IDs
    influencer_ids = [result.get("id") for result in search_results]
    
    # Use Influencity API for fraud detection
    api = InfluencityAPI("demo_key")
    fraud_results = api.fraud_detection(influencer_ids)
    
    # Filter out high-risk influencers
    safe_results = []
    for result in search_results:
        inf_id = result.get("id")
        fraud_score = fraud_results.get(inf_id, {}).get("fraud_score", 0)
        
        if fraud_score < 0.3:  # Low fraud risk threshold
            result["fraud_score"] = fraud_score
            safe_results.append(result)
    
    logger.info(f"✅ Fraud check completed: {len(safe_results)} safe influencers")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Fraud check completed: {len(safe_results)} safe influencers")
    
    return {
        "current_search_results": safe_results,
        "logs": logs
    }


def merge_candidates(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Merge and deduplicate candidates from parallel searches.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with merged candidates
    """
    logger.info("🔄 Merging candidate results")
    
    # Get all search results (accumulated from parallel branches)
    all_results = state.get("current_search_results", [])
    
    # Deduplicate by ID
    unique_candidates = {}
    for result in all_results:
        inf_id = result.get("id")
        if inf_id not in unique_candidates:
            unique_candidates[inf_id] = result
    
    # Convert to Creator objects
    creators = []
    for result in unique_candidates.values():
        creator = Creator(
            id=result.get("id", ""),
            username=result.get("username", ""),
            platform=result.get("platform", ""),
            followers=result.get("followers", 0),
            engagement_rate=result.get("engagement_rate", 0),
            niche=result.get("niche", ""),
            audience_demographics=result.get("audience_demographics", {}),
            contact_info=result.get("contact_info", ""),
            historical_performance=result.get("historical_performance", {}),
            fraud_score=result.get("fraud_score", 0),
            match_score=result.get("match_score", 0)
        )
        creators.append(creator)
    
    logger.info(f"✅ Merged {len(creators)} unique candidates")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Candidates merged: {len(creators)} unique influencers")
    
    return {
        "candidates": creators,
        "logs": logs
    }


def rank_score(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Rank and score candidates based on multiple criteria.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with ranked candidates
    """
    logger.info("📊 Ranking and scoring candidates")
    
    candidates = state.get("candidates", [])
    
    # Score candidates based on multiple factors
    for candidate in candidates:
        # Calculate composite score
        engagement_score = min(candidate.engagement_rate * 100, 10)  # Max 10 points
        follower_score = min(candidate.followers / 50000, 5)  # Max 5 points
        fraud_score = (1 - candidate.fraud_score) * 5  # Max 5 points (inverted)
        
        candidate.match_score = engagement_score + follower_score + fraud_score
    
    # Sort by match score
    candidates.sort(key=lambda x: x.match_score, reverse=True)
    
    logger.info(f"✅ Ranked {len(candidates)} candidates")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Candidates ranked by match score")
    
    return {
        "candidates": candidates,
        "logs": logs
    }


def finish_phase2(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Complete Phase 2 and transition to Phase 3.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with phase transition
    """
    logger.info("🏁 Completing Phase 2: Discovery")
    
    # Update phase
    phase = 3
    
    # Clear temporary search data
    current_search_results = []
    
    # Add completion log
    logs = state.get("logs", [])
    logs.append("Phase 2 (Discovery) completed")
    logs.append("Transitioning to Phase 3 (Outreach)")
    
    logger.info("✅ Phase 2 completed successfully")
    logger.info("➡️ Moving to Phase 3: Outreach")
    
    return {
        "phase": phase,
        "current_search_results": current_search_results,
        "logs": logs
    }


def create_discovery_subgraph() -> StateGraph:
    """
    Create the Discovery phase subgraph.
    
    Returns:
        Compiled discovery subgraph
    """
    logger.info("🏗️ Creating Discovery subgraph")
    
    # Create subgraph
    builder = StateGraph(CampaignState)
    
    # Add nodes
    builder.add_node("search_by_topic", search_by_topic)
    builder.add_node("search_by_audience", search_by_audience)
    builder.add_node("lookalike_search", lookalike_search)
    builder.add_node("fraud_check", fraud_check)
    builder.add_node("merge_candidates", merge_candidates)
    builder.add_node("rank_score", rank_score)
    builder.add_node("finish_p2", finish_phase2)
    
    # Add edges - parallel fan-out and fan-in pattern
    builder.add_conditional_edges(START, start_parallel_search, ["search_by_topic", "search_by_audience", "lookalike_search"])
    builder.add_edge("search_by_topic", "fraud_check")
    builder.add_edge("search_by_audience", "fraud_check")
    builder.add_edge("lookalike_search", "fraud_check")
    builder.add_edge("fraud_check", "merge_candidates")
    builder.add_edge("merge_candidates", "rank_score")
    builder.add_edge("rank_score", "finish_p2")
    builder.add_edge("finish_p2", END)
    
    # Compile subgraph
    subgraph = builder.compile(name="discovery-phase")
    
    logger.info("✅ Discovery subgraph created")
    return subgraph


# Export as toolified agent
def create_discovery_tool():
    """
    Create toolified version of discovery subgraph.
    
    Returns:
        Discovery tool for external use
    """
    from langchain_core.tools import tool
    
    @tool
    def discover_creators_tool(
        objective: str, 
        target_audience: Dict[str, Any],
        budget: float
    ) -> Dict[str, Any]:
        """
        Execute influencer discovery process.
        
        Args:
            objective: Campaign objective
            target_audience: Target audience criteria
            budget: Available budget
            
        Returns:
            Discovery results with ranked candidates
        """
        logger.info("🔧 Discovery tool activated")
        
        # Create initial state
        state = CampaignState(
            objective=objective,
            target_audience=target_audience,
            budget=budget,
            phase=2,
            logs=[],
            candidates=[]
        )
        
        # Execute discovery subgraph
        subgraph = create_discovery_subgraph()
        result = subgraph.invoke(state)
        
        logger.info("✅ Discovery tool completed")
        return result
    
    return discover_creators_tool