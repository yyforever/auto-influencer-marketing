"""
Node implementations for influencer search workflow.

Contains all LangGraph node functions that implement the core business logic
for the influencer search agent. Each node has a single responsibility
following LangGraph best practices.
"""

import os
import logging
import time
from typing import Dict, List, Any, Literal
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, get_buffer_string
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.types import Command
from langgraph.graph import END

# Import local modules
from .state import InfluencerSearchState
from .schemas import InfluencerSearchQuery, InfluencerProfile, SearchResult, ClarifyWithUser, InfluencerResearchBrief
from .prompts import (
    format_search_query_prompt,
    format_results_summary_prompt,
    format_no_results_prompt,
    format_error_recovery_prompt,
    CLARIFY_WITH_USER_INSTRUCTIONS,
    TRANSFORM_MESSAGES_INTO_INFLUENCER_RESEARCH_BRIEF_PROMPT,
    INFLUENCER_RESEARCH_SUPERVISOR_PROMPT,
    get_today_str
)
from ..configuration import Configuration

# Setup logging
logger = logging.getLogger(__name__)


def parse_search_request(
    state: InfluencerSearchState, 
    config: RunnableConfig
) -> Dict[str, Any]:
    """
    Node 1: Parse user messages to extract structured search parameters.
    
    Purpose: Convert natural language requests into structured InfluencerSearchQuery
    Input: User messages from state
    Output: search_query field populated in state
    """
    logger.info("🔍 Starting search request parsing")
    
    try:
        # Get configuration
        configurable = Configuration.from_runnable_config(config)
        
        # Extract user messages
        user_messages = get_buffer_string(state["messages"])
        logger.info(f"Processing user messages: {user_messages[:200]}...")
        
        # Initialize LLM with structured output
        llm = ChatGoogleGenerativeAI(
            model=configurable.query_generator_model,
            temperature=0.1,
            max_retries=2,
            timeout=60,
            api_key=os.getenv("GEMINI_API_KEY"),
        )
        
        # Use structured output for query extraction
        structured_llm = llm.with_structured_output(InfluencerSearchQuery)
        
        # Format prompt and extract query
        formatted_prompt = format_search_query_prompt(user_messages)
        search_query = structured_llm.invoke(formatted_prompt)
        
        logger.info(f"🔍 Successfully parsed search query: {search_query}")
        
        return {
            "search_query": search_query,
            "query_parsed": True,
            "last_error": None
        }
        
    except Exception as e:
        logger.error(f"Error parsing search request: {e}")
        return {
            "last_error": f"Failed to parse search request: {str(e)}",
            "query_parsed": False,
            "messages": [AIMessage(content=format_error_recovery_prompt(
                str(e), 
                get_buffer_string(state["messages"])
            ))]
        }


def search_influencers(
    state: InfluencerSearchState,
    config: RunnableConfig
) -> Dict[str, Any]:
    """
    Node 2: Execute influencer search based on parsed query parameters.
    
    Purpose: Perform the actual search and return mock influencer results
    Input: search_query from state
    Output: search_results and search_metadata populated
    
    Note: This is a demo implementation with mock data
    In production, this would integrate with real influencer APIs
    """
    logger.info("🔍 Starting influencer search execution")
    start_time = time.time()
    
    try:
        # Validate input
        search_query = state.get("search_query")
        if not search_query:
            raise ValueError("No search query found in state")
        
        logger.info(f"Searching for influencers with query: {search_query}")
        
        # Mock search implementation
        # In production, this would call real APIs like:
        # - Instagram Basic Display API
        # - TikTok Creator API  
        # - YouTube Data API
        # - Third-party influencer platforms (AspireIQ, Klear, etc.)
        
        mock_influencers = _generate_mock_influencers(search_query)
        
        # Create search metadata
        execution_time = int((time.time() - start_time) * 1000)
        search_metadata = SearchResult(
            query=search_query,
            total_found=len(mock_influencers) + 50,  # Simulate larger pool
            results_returned=len(mock_influencers),
            search_duration_ms=execution_time,
            filters_applied=["authenticity_check", "engagement_filter", "niche_match"]
        )
        
        logger.info(f"🔍 Found {len(mock_influencers)} influencers in {execution_time}ms")
        
        # Generate result summary
        if mock_influencers:
            result_message = _generate_results_summary(search_query, mock_influencers, search_metadata)
        else:
            result_message = format_no_results_prompt(search_query.model_dump())
        
        return {
            "search_results": mock_influencers,
            "search_metadata": search_metadata,
            "search_completed": True,
            "applied_filters": search_metadata.filters_applied,
            "last_error": None,
            "messages": [AIMessage(content=result_message)]
        }
        
    except Exception as e:
        logger.error(f"Error during influencer search: {e}")
        return {
            "last_error": f"Search execution failed: {str(e)}",
            "search_completed": False,
            "messages": [AIMessage(content=format_error_recovery_prompt(
                str(e),
                f"Search query: {state.get('search_query', 'Unknown')}"
            ))]
        }


def refine_search(
    state: InfluencerSearchState,
    config: RunnableConfig
) -> Dict[str, Any]:
    """
    Node 3 (Optional): Refine search results based on additional criteria.
    
    Purpose: Apply additional filtering, ranking, or refinement
    Input: search_results from previous search
    Output: refined search_results
    
    This node can be used for:
    - Advanced filtering
    - Custom ranking algorithms
    - Quality score adjustments
    """
    logger.info("🔍 Refining search results")
    
    try:
        search_results = state.get("search_results", [])
        search_query = state.get("search_query")
        
        if not search_results:
            logger.warning("No search results to refine")
            return {"last_error": None}
        
        # Apply refinement logic
        refined_results = _apply_refinement_logic(search_results, search_query)
        
        logger.info(f"🔍 Refined {len(search_results)} -> {len(refined_results)} results")
        
        return {
            "search_results": refined_results,
            "applied_filters": ["quality_refinement", "relevance_boost"],
            "last_error": None
        }
        
    except Exception as e:
        logger.error(f"Error during search refinement: {e}")
        return {
            "last_error": f"Search refinement failed: {str(e)}"
        }


# Private helper functions

def _generate_mock_influencers(query: InfluencerSearchQuery) -> List[InfluencerProfile]:
    """Generate mock influencer profiles based on search query"""
    
    mock_profiles = []
    base_profiles = [
        {
            "username_suffix": "creator_1",
            "followers": 50000,
            "engagement_rate": 3.5,
            "authenticity_score": 0.9,
            "match_score": 0.85,
            "email": "business@creator1.com"
        },
        {
            "username_suffix": "creator_2", 
            "followers": 75000,
            "engagement_rate": 4.2,
            "authenticity_score": 0.95,
            "match_score": 0.92,
            "email": "collabs@creator2.com"
        },
        {
            "username_suffix": "creator_3",
            "followers": 32000,
            "engagement_rate": 5.8,
            "authenticity_score": 0.88,
            "match_score": 0.78,
            "email": "partnerships@creator3.com"
        }
    ]
    
    for i, profile_data in enumerate(base_profiles):
        # Skip if follower count is outside range
        if (profile_data["followers"] < query.min_followers or 
            profile_data["followers"] > query.max_followers):
            continue
            
        profile = InfluencerProfile(
            id=f"inf_{i+1:03d}",
            username=f"@{query.niche}_{profile_data['username_suffix']}",
            platform=query.platform,
            display_name=f"{query.niche.title()} Creator {i+1}",
            followers=profile_data["followers"],
            engagement_rate=profile_data["engagement_rate"],
            niche=query.niche,
            bio=f"Certified {query.niche} expert sharing daily {query.keywords[0] if query.keywords else 'content'}",
            verified=profile_data["followers"] > 40000,
            audience_demographics={
                "age_group": "18-34" if profile_data["followers"] < 60000 else "25-45",
                "gender": "mixed",
                "top_locations": [query.location] if query.location else ["US", "UK", "Canada"]
            },
            location=query.location or "Global",
            contact_email=profile_data["email"],
            historical_performance={
                "avg_likes": int(profile_data["followers"] * profile_data["engagement_rate"] / 100 * 0.7),
                "avg_comments": int(profile_data["followers"] * profile_data["engagement_rate"] / 100 * 0.05),
                "avg_shares": int(profile_data["followers"] * profile_data["engagement_rate"] / 100 * 0.01)
            },
            authenticity_score=profile_data["authenticity_score"],
            match_score=profile_data["match_score"]
        )
        mock_profiles.append(profile)
    
    return mock_profiles


def _apply_refinement_logic(
    results: List[InfluencerProfile], 
    query: InfluencerSearchQuery
) -> List[InfluencerProfile]:
    """Apply refinement and ranking logic to search results"""
    
    # Sort by match score and authenticity
    refined_results = sorted(
        results,
        key=lambda x: (x.match_score * 0.6 + x.authenticity_score * 0.4),
        reverse=True
    )
    
    # Apply additional quality filters
    refined_results = [
        profile for profile in refined_results
        if profile.authenticity_score > 0.7 and profile.engagement_rate > 2.0
    ]
    
    return refined_results


def _generate_results_summary(
    query: InfluencerSearchQuery,
    results: List[InfluencerProfile], 
    metadata: SearchResult
) -> str:
    """Generate formatted summary of search results"""
    
    # Create influencer list string
    influencer_list = ""
    for i, profile in enumerate(results, 1):
        influencer_list += f"""
{i}. {profile.username}
   • 粉丝数: {profile.followers:,}
   • 互动率: {profile.engagement_rate}%
   • 匹配度: {profile.match_score:.0%}
   • 真实度: {profile.authenticity_score:.0%}
   • 联系方式: {profile.contact_email or 'N/A'}
"""
    
    return format_results_summary_prompt(
        search_query=query.model_dump(),
        total_results=metadata.total_found,
        returned_results=metadata.results_returned,
        influencer_list=influencer_list
    )


async def clarify_with_user(state: InfluencerSearchState, config: RunnableConfig) -> Command[Literal["write_research_brief", "parse_search_request", "__end__"]]:
    """Analyze user messages and ask clarifying questions if the search scope is unclear.
    
    This function determines whether the user's request needs clarification before proceeding
    with influencer search. If clarification is disabled or not needed, it proceeds directly to search.
    
    Args:
        state: Current agent state containing user messages
        config: Runtime configuration with model settings and preferences
        
    Returns:
        Command to either end with a clarifying question or proceed to search parsing
    """
    logger.info("🔍 Starting clarification analysis")
    
    # Step 1: Check if clarification is enabled in configuration
    configurable = Configuration.from_runnable_config(config)
    if not configurable.allow_clarification:
        # Skip clarification step and proceed directly to research brief generation
        logger.info("Clarification disabled, proceeding to research brief generation")
        return Command(goto="write_research_brief")
    
    # Step 2: Prepare the model for structured clarification analysis
    messages = state["messages"]
    
    # Initialize LLM with Gemini
    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,  # Use same model as query generation
        temperature=0.1,  # Lower temperature for consistent analysis
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
    # Configure model with structured output
    clarification_model = llm.with_structured_output(ClarifyWithUser)
    
    # Step 3: Analyze whether clarification is needed
    prompt_content = CLARIFY_WITH_USER_INSTRUCTIONS.format(
        messages=get_buffer_string(messages), 
        date=get_today_str()
    )
    
    try:
        response = await clarification_model.ainvoke([HumanMessage(content=prompt_content)])
        logger.info(f"Clarification analysis result: need_clarification={response.need_clarification}")
        
        # Step 4: Route based on clarification analysis
        if response.need_clarification:
            # End with clarifying question for user
            logger.info(f"Asking clarification question: {response.question}")
            return Command(
                goto=END, 
                update={"messages": [AIMessage(content=response.question)]}
            )
        else:
            # Proceed to research brief generation with verification message
            logger.info(f"No clarification needed, proceeding with verification: {response.verification}")
            return Command(
                goto="write_research_brief", 
                update={"messages": [AIMessage(content=response.verification)]}
            )
            
    except Exception as e:
        logger.error(f"Error in clarification analysis: {e}")
        # On error, proceed to search parsing to avoid blocking
        return Command(
            goto="parse_search_request",
            update={
                "last_error": f"Clarification analysis failed: {str(e)}",
                "messages": [AIMessage(content="继续进行影响者搜索分析...")]
            }
        )


async def write_research_brief(state: InfluencerSearchState, config: RunnableConfig) -> Command[Literal["research_supervisor"]]:
    """Transform user messages into a structured influencer marketing research brief and initialize supervisor.
    
    This function analyzes the user's messages and generates a focused research brief
    that will guide the influencer marketing research supervisor. It also sets up the 
    initial supervisor context with appropriate prompts and instructions.
    
    Args:
        state: Current agent state containing user messages
        config: Runtime configuration with model settings
        
    Returns:
        Command to proceed to research supervisor with initialized context
    """
    logger.info("📝 Starting research brief generation")
    
    try:
        # Step 1: Set up the research model for structured output
        configurable = Configuration.from_runnable_config(config)
        
        # Initialize LLM with Gemini for structured research brief generation
        llm = ChatGoogleGenerativeAI(
            model=configurable.research_model,
            temperature=0.1,  # Lower temperature for consistent structured output
            max_tokens=configurable.research_model_max_tokens,
            max_retries=configurable.max_structured_output_retries,
            api_key=os.getenv("GEMINI_API_KEY"),
        )
        
        # Configure model for structured research brief generation
        research_model = llm.with_structured_output(InfluencerResearchBrief)
        
        # Step 2: Generate structured research brief from user messages
        prompt_content = TRANSFORM_MESSAGES_INTO_INFLUENCER_RESEARCH_BRIEF_PROMPT.format(
            messages=get_buffer_string(state.get("messages", [])),
            date=get_today_str()
        )
        
        logger.info("🤖 Generating structured research brief...")
        response = await research_model.ainvoke([HumanMessage(content=prompt_content)])
        
        # Step 3: Initialize supervisor with research brief and instructions
        supervisor_system_prompt = INFLUENCER_RESEARCH_SUPERVISOR_PROMPT.format(
            date=get_today_str(),
            max_concurrent_research_units=configurable.max_concurrent_research_units,
            max_researcher_iterations=configurable.max_researcher_iterations
        )
        
        logger.info("✅ Research brief generated successfully")
        logger.info(f"📊 Brief summary - Platforms: {response.target_platforms}, Niche: {response.niche_focus}")
        
        return Command(
            goto="research_supervisor", 
            update={
                "research_brief": response.research_brief,
                "research_metadata": {
                    "target_platforms": response.target_platforms,
                    "niche_focus": response.niche_focus,
                    "geographic_focus": response.geographic_focus,
                    "follower_range": response.follower_range,
                    "campaign_objectives": response.campaign_objectives,
                    "budget_considerations": response.budget_considerations,
                    "content_preferences": response.content_preferences,
                    "timeline": response.timeline
                },
                "supervisor_messages": [
                    SystemMessage(content=supervisor_system_prompt),
                    HumanMessage(content=response.research_brief)
                ],
                "messages": [AIMessage(content="🔍 已生成影响者营销研究摘要，正在启动研究监督程序...")]
            }
        )
        
    except Exception as e:
        logger.error(f"Error in research brief generation: {e}")
        # On error, fall back to simple search to avoid blocking
        error_message = f"Research brief generation failed: {str(e)}"
        return Command(
            goto="parse_search_request",
            update={
                "last_error": error_message,
                "messages": [AIMessage(content="⚠️ 研究摘要生成遇到问题，回退到简单搜索模式...")]
            }
        )


def research_supervisor(state: InfluencerSearchState, config: RunnableConfig) -> Dict[str, Any]:
    """Research supervisor placeholder node for future implementation.
    
    This is currently a placeholder node that acknowledges the research brief
    and provides a summary response. In the future, this will coordinate
    multiple research agents for comprehensive influencer marketing analysis.
    
    Args:
        state: Current agent state containing research brief and metadata
        config: Runtime configuration
        
    Returns:
        Updated state with supervisor response
    """
    logger.info("🎯 Research supervisor activated")
    
    # Extract research metadata if available
    research_metadata = state.get("research_metadata", {})
    research_brief = state.get("research_brief", "")
    
    # Generate supervisor response based on research brief
    if research_metadata:
        platforms = research_metadata.get("target_platforms", ["未指定"])
        niche = research_metadata.get("niche_focus", "未指定")
        objectives = research_metadata.get("campaign_objectives", ["待确定"])
        
        supervisor_response = f"""🎯 **影响者营销研究监督程序已启动**

📊 **研究摘要概览**:
• 目标平台: {', '.join(platforms)}  
• 内容领域: {niche}
• 营销目标: {', '.join(objectives)}

📋 **研究计划** (占位符):
1. 影响者发现与分析
2. 竞争对手策略研究  
3. 平台趋势分析
4. 受众洞察收集
5. 内容策略建议
6. 性能基准研究

✅ **当前状态**: 研究架构已就绪，等待完整研究功能实现

*注: 这是一个占位符节点，完整的研究协调功能正在开发中*"""
    else:
        supervisor_response = """🎯 **影响者营销研究监督程序已启动**

📋 **当前状态**: 正在分析研究需求...

*注: 这是一个占位符节点，完整的研究协调功能正在开发中*"""
    
    logger.info("✅ Supervisor placeholder response generated")
    
    return {
        "messages": [AIMessage(content=supervisor_response)],
        "search_completed": True,
        "supervisor_active": True
    }