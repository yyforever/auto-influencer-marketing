"""
Phase 5: Publish & Boost - Multi-platform content publishing and amplification.
"""

import logging
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from agent.state import CampaignState, PublishState
from agent.tools import InfluencityAPI, SocialMediaTools
from agent.state.models import PostLink

logger = logging.getLogger(__name__)


def schedule_post_tiktok(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Schedule posts for TikTok platform.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with TikTok scheduling results
    """
    logger.info("📱 Scheduling TikTok posts")
    
    # Get approved scripts
    scripts = state.get("scripts", [])
    tiktok_scripts = [s for s in scripts if s.platform.lower() == "tiktok"]
    
    # Use Influencity API for scheduling
    api = InfluencityAPI("demo_key")
    
    # Schedule posts
    scheduled_posts = []
    for script in tiktok_scripts:
        post_data = {
            "platform": "tiktok",
            "creator_id": script.creator_id,
            "content": script.content,
            "scheduled_time": "2024-01-16T10:00:00Z"
        }
        
        result = api.schedule_cross_platform_post(post_data)
        tiktok_id = result.get("tiktok")
        
        if tiktok_id:
            post_link = PostLink(
                id=f"tiktok_{tiktok_id}",
                creator_id=script.creator_id,
                platform="tiktok",
                url=f"https://tiktok.com/post/{tiktok_id}",
                published_at="2024-01-16T10:00:00Z",
                content_type="video",
                status="scheduled"
            )
            scheduled_posts.append(post_link)
    
    logger.info(f"✅ Scheduled {len(scheduled_posts)} TikTok posts")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"TikTok posts scheduled: {len(scheduled_posts)}")
    
    return {
        "posts": scheduled_posts,
        "logs": logs
    }


def schedule_post_instagram(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Schedule posts for Instagram platform.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with Instagram scheduling results
    """
    logger.info("📸 Scheduling Instagram posts")
    
    # Get approved scripts
    scripts = state.get("scripts", [])
    instagram_scripts = [s for s in scripts if "instagram" in s.platform.lower()]
    
    # Use Influencity API for scheduling
    api = InfluencityAPI("demo_key")
    
    # Schedule posts
    scheduled_posts = []
    for script in instagram_scripts:
        post_data = {
            "platform": "instagram",
            "creator_id": script.creator_id,
            "content": script.content,
            "scheduled_time": "2024-01-16T12:00:00Z"
        }
        
        result = api.schedule_cross_platform_post(post_data)
        instagram_id = result.get("instagram")
        
        if instagram_id:
            # Determine content type from script
            content_type = "post" if "post" in script.id else "story"
            
            post_link = PostLink(
                id=f"instagram_{instagram_id}",
                creator_id=script.creator_id,
                platform="instagram",
                url=f"https://instagram.com/p/{instagram_id}",
                published_at="2024-01-16T12:00:00Z",
                content_type=content_type,
                status="scheduled"
            )
            scheduled_posts.append(post_link)
    
    logger.info(f"✅ Scheduled {len(scheduled_posts)} Instagram posts")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Instagram posts scheduled: {len(scheduled_posts)}")
    
    return {
        "posts": scheduled_posts,
        "logs": logs
    }


def schedule_post_youtube(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Schedule posts for YouTube platform.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with YouTube scheduling results
    """
    logger.info("🎥 Scheduling YouTube posts")
    
    # Get approved scripts
    scripts = state.get("scripts", [])
    youtube_scripts = [s for s in scripts if s.platform.lower() == "youtube"]
    
    # Use Influencity API for scheduling
    api = InfluencityAPI("demo_key")
    
    # Schedule posts
    scheduled_posts = []
    for script in youtube_scripts:
        post_data = {
            "platform": "youtube",
            "creator_id": script.creator_id,
            "content": script.content,
            "scheduled_time": "2024-01-16T14:00:00Z"
        }
        
        result = api.schedule_cross_platform_post(post_data)
        youtube_id = result.get("youtube")
        
        if youtube_id:
            post_link = PostLink(
                id=f"youtube_{youtube_id}",
                creator_id=script.creator_id,
                platform="youtube",
                url=f"https://youtube.com/watch?v={youtube_id}",
                published_at="2024-01-16T14:00:00Z",
                content_type="video",
                status="scheduled"
            )
            scheduled_posts.append(post_link)
    
    logger.info(f"✅ Scheduled {len(scheduled_posts)} YouTube posts")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"YouTube posts scheduled: {len(scheduled_posts)}")
    
    return {
        "posts": scheduled_posts,
        "logs": logs
    }


def start_parallel_publishing(state: CampaignState) -> List[Send]:
    """
    Start parallel publishing across platforms.
    
    Args:
        state: Current campaign state
        
    Returns:
        List of Send objects for parallel execution
    """
    logger.info("🚀 Starting parallel publishing across platforms")
    
    # Create parallel publishing tasks
    return [
        Send("schedule_post_tiktok", state),
        Send("schedule_post_instagram", state),
        Send("schedule_post_youtube", state)
    ]


def wait_all_publish(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Wait for all publishing tasks to complete and aggregate results.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with aggregated publishing results
    """
    logger.info("⏳ Waiting for all publishing tasks to complete")
    
    # All posts should be accumulated in state by now
    posts = state.get("posts", [])
    
    # Group posts by platform
    platform_counts = {}
    for post in posts:
        platform = post.platform
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    logger.info(f"📊 Publishing summary: {platform_counts}")
    
    # Check if we have posts scheduled
    if not posts:
        logger.warning("⚠️ No posts were scheduled")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"All platform publishing completed: {len(posts)} posts scheduled")
    
    return {
        "logs": logs
    }


def setup_boost_campaigns(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Set up paid boost campaigns for scheduled posts.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with boost campaign setup
    """
    logger.info("🚀 Setting up paid boost campaigns")
    
    # Get published posts
    posts = state.get("posts", [])
    budget = state.get("budget", 0)
    
    # Calculate boost budget allocation
    boost_budget_per_post = min(budget * 0.2 / len(posts), 500) if posts else 0
    
    # Initialize social media tools
    social_tools = SocialMediaTools({
        "instagram": {"api_key": "demo_key"},
        "tiktok": {"api_key": "demo_key"},
        "youtube": {"api_key": "demo_key"}
    })
    
    # Set up boost campaigns
    boost_campaigns = []
    for post in posts:
        boost_config = {
            "budget": boost_budget_per_post,
            "duration": 7,  # 7 days
            "target_audience": state.get("target_audience", {}),
            "objective": "engagement"
        }
        
        post_data = {
            "id": post.id,
            "url": post.url,
            "platform": post.platform
        }
        
        result = social_tools.schedule_boost_campaign(post_data, boost_config)
        boost_campaigns.append(result)
    
    logger.info(f"✅ Set up {len(boost_campaigns)} boost campaigns")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Boost campaigns set up: {len(boost_campaigns)}")
    
    return {
        "logs": logs
    }


def finish_phase5(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Complete Phase 5 and transition to Phase 6.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with phase transition
    """
    logger.info("🏁 Completing Phase 5: Publish & Boost")
    
    # Update phase
    phase = 6
    
    # Add completion log
    logs = state.get("logs", [])
    logs.append("Phase 5 (Publish & Boost) completed")
    logs.append("Transitioning to Phase 6 (Monitor & Optimize)")
    
    logger.info("✅ Phase 5 completed successfully")
    logger.info("➡️ Moving to Phase 6: Monitor & Optimize")
    
    return {
        "phase": phase,
        "logs": logs
    }


def create_publish_subgraph() -> StateGraph:
    """
    Create the Publish & Boost phase subgraph.
    
    Returns:
        Compiled publish subgraph
    """
    logger.info("🏗️ Creating Publish & Boost subgraph")
    
    # Create subgraph
    builder = StateGraph(CampaignState)
    
    # Add nodes
    builder.add_node("schedule_post_tiktok", schedule_post_tiktok)
    builder.add_node("schedule_post_instagram", schedule_post_instagram)
    builder.add_node("schedule_post_youtube", schedule_post_youtube)
    builder.add_node("wait_all_publish", wait_all_publish)
    builder.add_node("setup_boost_campaigns", setup_boost_campaigns)
    builder.add_node("finish_p5", finish_phase5)
    
    # Add edges - parallel fan-out and fan-in pattern
    builder.add_conditional_edges(START, start_parallel_publishing, ["schedule_post_tiktok", "schedule_post_instagram", "schedule_post_youtube"])
    builder.add_edge("schedule_post_tiktok", "wait_all_publish")
    builder.add_edge("schedule_post_instagram", "wait_all_publish")
    builder.add_edge("schedule_post_youtube", "wait_all_publish")
    builder.add_edge("wait_all_publish", "setup_boost_campaigns")
    builder.add_edge("setup_boost_campaigns", "finish_p5")
    builder.add_edge("finish_p5", END)
    
    # Compile subgraph
    subgraph = builder.compile(name="publish-phase")
    
    logger.info("✅ Publish & Boost subgraph created")
    return subgraph


# Export as toolified agent
def create_publish_tool():
    """
    Create toolified version of publish subgraph.
    
    Returns:
        Publish tool for external use
    """
    from langchain_core.tools import tool
    
    @tool
    def publish_boost_tool(
        scripts: List[Dict[str, Any]], 
        budget: float,
        target_audience: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute content publishing and boost process.
        
        Args:
            scripts: List of approved scripts
            budget: Available budget for boosts
            target_audience: Target audience for boost campaigns
            
        Returns:
            Publishing results with scheduled posts and boost campaigns
        """
        logger.info("🔧 Publish & Boost tool activated")
        
        # Convert scripts to Script objects
        from agent.state.models import Script
        from datetime import datetime
        
        script_objects = [
            Script(
                id=s.get("id", ""),
                creator_id=s.get("creator_id", ""),
                platform=s.get("platform", ""),
                content=s.get("content", ""),
                brand_story=s.get("brand_story", ""),
                compliance_status=s.get("compliance_status", "approved"),
                version=s.get("version", 1),
                created_at=datetime.now().isoformat()
            )
            for s in scripts
        ]
        
        # Create initial state
        state = CampaignState(
            scripts=script_objects,
            budget=budget,
            target_audience=target_audience,
            phase=5,
            logs=[],
            posts=[]
        )
        
        # Execute publish subgraph
        subgraph = create_publish_subgraph()
        result = subgraph.invoke(state)
        
        logger.info("✅ Publish & Boost tool completed")
        return result
    
    return publish_boost_tool