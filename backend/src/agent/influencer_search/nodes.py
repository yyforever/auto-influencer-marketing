"""
Node implementations for influencer search workflow.

Contains all LangGraph node functions that implement the core business logic
for the influencer search agent. Each node has a single responsibility
following LangGraph best practices.
"""

import os
import logging
import time
from typing import Dict, List, Any
from langchain_core.messages import AIMessage, get_buffer_string
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI

# Import local modules
from .state import InfluencerSearchState
from .schemas import InfluencerSearchQuery, InfluencerProfile, SearchResult
from .prompts import (
    format_search_query_prompt,
    format_results_summary_prompt,
    format_no_results_prompt,
    format_error_recovery_prompt
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
            result_message = format_no_results_prompt(search_query.dict())
        
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
        search_query=query.dict(),
        total_results=metadata.total_found,
        returned_results=metadata.results_returned,
        influencer_list=influencer_list
    )