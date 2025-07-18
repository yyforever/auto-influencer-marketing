"""
Phase 6: Monitor & Optimize - Performance tracking and budget optimization.
"""

import logging
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END

from agent.state import CampaignState, MonitorState
from agent.tools import SocialMediaTools
from agent.state.models import Metric
from agent.utils import create_hitl_node

logger = logging.getLogger(__name__)


def pull_metrics(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Pull performance metrics from social media platforms.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with performance metrics
    """
    logger.info("📊 Pulling performance metrics")
    
    # Get published posts
    posts = state.get("posts", [])
    post_urls = [post.url for post in posts]
    
    if not post_urls:
        logger.warning("⚠️ No posts found to monitor")
        return {"logs": state.get("logs", []) + ["No posts to monitor"]}
    
    # Initialize social media tools
    social_tools = SocialMediaTools({
        "instagram": {"api_key": "demo_key"},
        "tiktok": {"api_key": "demo_key"},
        "youtube": {"api_key": "demo_key"}
    })
    
    # Pull metrics for all posts
    metrics_data = social_tools.pull_post_metrics(post_urls)
    
    # Convert to Metric objects
    performance_metrics = {}
    for post in posts:
        post_metrics = metrics_data.get(post.url, {})
        
        if post_metrics:
            metric = Metric(
                post_id=post.id,
                views=post_metrics.get("views", 0),
                likes=post_metrics.get("likes", 0),
                shares=post_metrics.get("shares", 0),
                comments=post_metrics.get("comments", 0),
                engagement_rate=post_metrics.get("engagement_rate", 0),
                cpm=post_metrics.get("cpm", 0),
                cpa=post_metrics.get("cpa", 0),
                roas=post_metrics.get("roas", 0),
                timestamp=post_metrics.get("last_updated", "2024-01-16T15:00:00Z")
            )
            performance_metrics[post.id] = metric
    
    logger.info(f"✅ Pulled metrics for {len(performance_metrics)} posts")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Performance metrics pulled: {len(performance_metrics)} posts")
    
    return {
        "performance": performance_metrics,
        "logs": logs
    }


def detect_winner(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Detect high-performing (viral) content and make budget recommendations.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with winner detection results
    """
    logger.info("🔥 Detecting viral content and winners")
    
    # Get performance metrics
    performance_metrics = state.get("performance", {})
    
    if not performance_metrics:
        logger.warning("⚠️ No performance metrics available")
        return {"logs": state.get("logs", []) + ["No metrics available for winner detection"]}
    
    # Initialize social media tools
    social_tools = SocialMediaTools({
        "instagram": {"api_key": "demo_key"},
        "tiktok": {"api_key": "demo_key"},
        "youtube": {"api_key": "demo_key"}
    })
    
    # Prepare metrics data for analysis
    metrics_data = {}
    for post_id, metric in performance_metrics.items():
        # Find corresponding post
        posts = state.get("posts", [])
        post = next((p for p in posts if p.id == post_id), None)
        
        if post:
            metrics_data[post.url] = {
                "views": metric.views,
                "likes": metric.likes,
                "shares": metric.shares,
                "comments": metric.comments,
                "engagement_rate": metric.engagement_rate,
                "cpm": metric.cpm,
                "cpa": metric.cpa,
                "roas": metric.roas
            }
    
    # Detect viral content
    viral_detection = social_tools.detect_viral_content(metrics_data)
    
    # Calculate recommended budget adjustment
    viral_posts = viral_detection.get("viral_posts", [])
    suggested_budget_increase = viral_detection.get("suggested_budget_increase", 0)
    
    # Create optimization decisions
    optimization_decisions = []
    
    for viral_post in viral_posts:
        decision = {
            "post_url": viral_post["url"],
            "viral_score": viral_post["viral_score"],
            "action": "increase_budget",
            "recommended_budget": suggested_budget_increase / len(viral_posts) if viral_posts else 0,
            "reason": viral_post["reason"]
        }
        optimization_decisions.append(decision)
    
    logger.info(f"✅ Detected {len(viral_posts)} viral posts")
    logger.info(f"💰 Suggested budget increase: ${suggested_budget_increase}")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Winner detection completed: {len(viral_posts)} viral posts")
    
    return {
        "optimization_decisions": optimization_decisions,
        "logs": logs
    }


def adjust_budget(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Adjust budget based on performance insights.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with budget adjustments
    """
    logger.info("💰 Adjusting budget based on performance")
    
    # Get optimization decisions
    optimization_decisions = state.get("optimization_decisions", [])
    current_budget = state.get("budget", 0)
    
    # Calculate total budget adjustment
    total_increase = sum(
        decision.get("recommended_budget", 0) 
        for decision in optimization_decisions
    )
    
    # Apply budget adjustment
    new_budget = current_budget + total_increase
    
    # Initialize social media tools
    social_tools = SocialMediaTools({
        "instagram": {"api_key": "demo_key"},
        "tiktok": {"api_key": "demo_key"},
        "youtube": {"api_key": "demo_key"}
    })
    
    # Set up additional boost campaigns for viral posts
    boost_results = []
    for decision in optimization_decisions:
        if decision["action"] == "increase_budget":
            post_data = {
                "url": decision["post_url"],
                "viral_score": decision["viral_score"]
            }
            
            boost_config = {
                "budget": decision["recommended_budget"],
                "duration": 5,  # Extended boost duration
                "objective": "reach"
            }
            
            result = social_tools.schedule_boost_campaign(post_data, boost_config)
            boost_results.append(result)
    
    logger.info(f"✅ Budget adjusted: ${current_budget} → ${new_budget}")
    logger.info(f"🚀 Set up {len(boost_results)} additional boost campaigns")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Budget adjusted: ${current_budget:.2f} → ${new_budget:.2f}")
    logs.append(f"Additional boost campaigns: {len(boost_results)}")
    
    return {
        "budget": new_budget,
        "logs": logs
    }


def check_budget_threshold(state: CampaignState) -> str:
    """
    Check if budget increase requires HITL approval.
    
    Args:
        state: Current campaign state
        
    Returns:
        Next node name
    """
    optimization_decisions = state.get("optimization_decisions", [])
    
    # Calculate total budget increase
    total_increase = sum(
        decision.get("recommended_budget", 0) 
        for decision in optimization_decisions
    )
    
    # Set threshold for HITL approval
    threshold = 1000  # $1000 threshold
    
    if total_increase > threshold:
        logger.info(f"💸 Budget increase ${total_increase} exceeds threshold - requiring HITL approval")
        return "HITL_budget_guard"
    else:
        logger.info(f"💰 Budget increase ${total_increase} within threshold - proceeding automatically")
        return "loop_or_finish"


def update_monitor_iteration(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Update monitoring iteration count.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with iteration count
    """
    logger.info("🔄 Updating monitoring iteration count")
    
    # Update iteration count
    iteration_count = state.get("iteration_count", {})
    iteration_count["monitor"] = iteration_count.get("monitor", 0) + 1
    
    return {
        "iteration_count": iteration_count
    }


def loop_or_finish(state: CampaignState, config: RunnableConfig) -> str:
    """
    Decide whether to continue monitoring or finish the phase.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Next node name
    """
    logger.info("🔄 Evaluating monitoring loop continuation")
    
    # Get current performance
    performance_metrics = state.get("performance", {})
    kpi = state.get("kpi", {})
    
    # Check if KPIs are met
    if performance_metrics:
        # Calculate overall performance
        total_engagement = sum(metric.likes + metric.shares + metric.comments for metric in performance_metrics.values())
        average_engagement_rate = sum(metric.engagement_rate for metric in performance_metrics.values()) / len(performance_metrics)
        
        target_engagement_rate = kpi.get("target_engagement_rate", 0.03)
        
        if average_engagement_rate >= target_engagement_rate:
            logger.info(f"🎯 KPI achieved: {average_engagement_rate:.3f} >= {target_engagement_rate:.3f}")
            return "finish_p6"
    
    # Check iteration limit
    iteration_count = state.get("iteration_count", {})
    monitor_iterations = iteration_count.get("monitor", 0)
    max_iterations = 5  # Maximum monitoring cycles
    
    if monitor_iterations >= max_iterations:
        logger.info(f"⏱️ Reached maximum monitoring iterations ({max_iterations})")
        return "finish_p6"
    
    # Continue monitoring
    logger.info(f"🔄 Continuing monitoring: iteration {monitor_iterations + 1}/{max_iterations}")
    
    return "update_monitor_iteration"


def finish_phase6(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Complete Phase 6 and transition to Phase 7.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with phase transition
    """
    logger.info("🏁 Completing Phase 6: Monitor & Optimize")
    
    # Update phase
    phase = 7
    
    # Add completion log
    logs = state.get("logs", [])
    logs.append("Phase 6 (Monitor & Optimize) completed")
    logs.append("Transitioning to Phase 7 (Settle & Archive)")
    
    logger.info("✅ Phase 6 completed successfully")
    logger.info("➡️ Moving to Phase 7: Settle & Archive")
    
    return {
        "phase": phase,
        "logs": logs
    }


def create_monitor_subgraph() -> StateGraph:
    """
    Create the Monitor & Optimize phase subgraph.
    
    Returns:
        Compiled monitor subgraph
    """
    logger.info("🏗️ Creating Monitor & Optimize subgraph")
    
    # Create subgraph
    builder = StateGraph(CampaignState)
    
    # Add nodes
    builder.add_node("pull_metrics", pull_metrics)
    builder.add_node("detect_winner", detect_winner)
    builder.add_node("adjust_budget", adjust_budget)
    builder.add_node("update_monitor_iteration", update_monitor_iteration)
    builder.add_node("HITL_budget_guard", create_hitl_node("budget"))
    builder.add_node("loop_or_finish", loop_or_finish)
    builder.add_node("finish_p6", finish_phase6)
    
    # Add edges with conditional routing and loops
    builder.add_edge(START, "pull_metrics")
    builder.add_edge("pull_metrics", "detect_winner")
    builder.add_edge("detect_winner", "adjust_budget")
    builder.add_conditional_edges("adjust_budget", check_budget_threshold, ["HITL_budget_guard", "loop_or_finish"])
    builder.add_edge("HITL_budget_guard", "loop_or_finish")
    builder.add_conditional_edges("loop_or_finish", loop_or_finish, ["update_monitor_iteration", "finish_p6"])
    builder.add_edge("update_monitor_iteration", "pull_metrics")
    builder.add_edge("finish_p6", END)
    
    # Compile subgraph
    subgraph = builder.compile(name="monitor-phase")
    
    logger.info("✅ Monitor & Optimize subgraph created")
    return subgraph


# Export as toolified agent
def create_monitor_tool():
    """
    Create toolified version of monitor subgraph.
    
    Returns:
        Performance dashboard tool for external use
    """
    from langchain_core.tools import tool
    
    @tool
    def performance_dashboard_tool(
        posts: List[Dict[str, Any]], 
        budget: float,
        kpi: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute performance monitoring and optimization.
        
        Args:
            posts: List of published posts to monitor
            budget: Current campaign budget
            kpi: Key performance indicators
            
        Returns:
            Monitoring results with performance metrics and optimizations
        """
        logger.info("🔧 Performance dashboard tool activated")
        
        # Convert posts to PostLink objects
        from agent.state.models import PostLink
        from datetime import datetime
        
        post_objects = [
            PostLink(
                id=p.get("id", ""),
                creator_id=p.get("creator_id", ""),
                platform=p.get("platform", ""),
                url=p.get("url", ""),
                published_at=p.get("published_at", datetime.now().isoformat()),
                content_type=p.get("content_type", "post"),
                status=p.get("status", "published")
            )
            for p in posts
        ]
        
        # Create initial state
        state = CampaignState(
            posts=post_objects,
            budget=budget,
            kpi=kpi,
            phase=6,
            logs=[],
            performance={}
        )
        
        # Execute monitor subgraph
        subgraph = create_monitor_subgraph()
        result = subgraph.invoke(state)
        
        logger.info("✅ Performance dashboard tool completed")
        return result
    
    return performance_dashboard_tool