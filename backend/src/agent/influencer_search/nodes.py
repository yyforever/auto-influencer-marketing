"""
Node implementations for influencer search workflow.

Contains all LangGraph node functions that implement the core business logic
for the influencer search agent. Each node has a single responsibility
following LangGraph best practices.
"""

import os
import logging
import asyncio
from typing import Dict, Any, Literal
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage, get_buffer_string
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END

# Import local modules
from .state import InfluencerSearchState
from .schemas import (
    ClarifyWithUser, InfluencerResearchBrief, 
    SupervisorState, ConductInfluencerResearch, InfluencerResearchComplete
)
from .prompts import (
    CLARIFY_WITH_USER_INSTRUCTIONS,
    TRANSFORM_MESSAGES_INTO_INFLUENCER_RESEARCH_BRIEF_PROMPT,
    INFLUENCER_RESEARCH_SUPERVISOR_PROMPT,
    get_today_str,
    think_tool,
    get_notes_from_tool_calls,
    get_api_key_for_model,
    is_token_limit_exceeded,
    configurable_model
)
from ..configuration import Configuration

# Setup logging
logger = logging.getLogger(__name__)



async def clarify_with_user(state: InfluencerSearchState, config: RunnableConfig) -> Command[Literal["write_research_brief", "__end__"]]:
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
        # On error, proceed to research brief generation to avoid blocking
        return Command(
            goto="write_research_brief",
            update={
                "last_error": f"Clarification analysis failed: {str(e)}",
                "messages": [AIMessage(content="继续进行影响者研究分析...")]
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
        # On error, end workflow with error message
        error_message = f"Research brief generation failed: {str(e)}"
        return Command(
            goto=END,
            update={
                "last_error": error_message,
                "messages": [AIMessage(content="⚠️ 研究摘要生成遇到问题，无法继续处理请求。请重新描述您的需求。")]
            }
        )


async def supervisor(state: SupervisorState, config: RunnableConfig) -> Command[Literal["supervisor_tools"]]:
    """Lead influencer marketing research supervisor that plans research strategy and delegates to researchers.
    
    The supervisor analyzes the research brief and decides how to break down the influencer marketing research
    into manageable tasks. It can use think_tool for strategic planning, ConductInfluencerResearch
    to delegate tasks to sub-researchers, or InfluencerResearchComplete when satisfied with findings.
    
    Args:
        state: Current supervisor state with messages and research context
        config: Runtime configuration with model settings
        
    Returns:
        Command to proceed to supervisor_tools for tool execution
    """
    logger.info("🎯 Influencer marketing research supervisor activated")
    
    # Step 1: Configure the supervisor model with available tools
    configurable = Configuration.from_runnable_config(config)
    research_model_config = {
        "model": configurable.research_model,
        "max_tokens": configurable.research_model_max_tokens,
        "api_key": get_api_key_for_model(configurable.research_model, config),
        "tags": ["langsmith:nostream"]
    }
    
    # Available tools: research delegation, completion signaling, and strategic thinking
    lead_researcher_tools = [ConductInfluencerResearch, InfluencerResearchComplete, think_tool]
    
    # Configure model with tools, retry logic, and model settings
    research_model = (
        configurable_model()
        .bind_tools(lead_researcher_tools)
        .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
        .with_config(research_model_config)
    )
    
    # Step 2: Generate supervisor response based on current context
    supervisor_messages = state.get("supervisor_messages", [])
    response = await research_model.ainvoke(supervisor_messages)
    
    logger.info(f"🎯 Supervisor generated response with {len(response.tool_calls) if response.tool_calls else 0} tool calls")
    
    # Step 3: Update state and proceed to tool execution
    return Command(
        goto="supervisor_tools",
        update={
            "supervisor_messages": [response],
            "research_iterations": state.get("research_iterations", 0) + 1
        }
    )


async def supervisor_tools(state: SupervisorState, config: RunnableConfig) -> Command[Literal["supervisor", "__end__"]]:
    """Execute tools called by the supervisor, including research delegation and strategic thinking.
    
    This function handles three types of supervisor tool calls:
    1. think_tool - Strategic reflection that continues the conversation
    2. ConductInfluencerResearch - Delegates research tasks to sub-researchers
    3. InfluencerResearchComplete - Signals completion of research phase
    
    Args:
        state: Current supervisor state with messages and iteration count
        config: Runtime configuration with research limits and model settings
        
    Returns:
        Command to either continue supervision loop or end research phase
    """
    logger.info("🔧 Executing supervisor tools")
    
    # Step 1: Extract current state and check exit conditions
    configurable = Configuration.from_runnable_config(config)
    supervisor_messages = state.get("supervisor_messages", [])
    research_iterations = state.get("research_iterations", 0)
    most_recent_message = supervisor_messages[-1] if supervisor_messages else None
    
    if not most_recent_message or not hasattr(most_recent_message, 'tool_calls'):
        logger.warning("No recent message or tool calls found, ending research")
        return Command(
            goto=END,
            update={
                "notes": get_notes_from_tool_calls(supervisor_messages),
                "research_brief": state.get("research_brief", "")
            }
        )
    
    # Define exit criteria for research phase
    exceeded_allowed_iterations = research_iterations > configurable.max_researcher_iterations
    no_tool_calls = not most_recent_message.tool_calls
    research_complete_tool_call = any(
        tool_call.get("name") == "InfluencerResearchComplete" 
        for tool_call in most_recent_message.tool_calls
    )
    
    # Exit if any termination condition is met
    if exceeded_allowed_iterations or no_tool_calls or research_complete_tool_call:
        logger.info(f"🏁 Ending research phase - iterations: {research_iterations}, tools: {len(most_recent_message.tool_calls)}")
        return Command(
            goto=END,
            update={
                "notes": get_notes_from_tool_calls(supervisor_messages),
                "research_brief": state.get("research_brief", "")
            }
        )
    
    # Step 2: Process all tool calls together (both think_tool and ConductInfluencerResearch)
    all_tool_messages = []
    update_payload = {"supervisor_messages": []}
    
    # Handle think_tool calls (strategic reflection)
    think_tool_calls = [
        tool_call for tool_call in most_recent_message.tool_calls 
        if tool_call.get("name") == "think_tool"
    ]
    
    for tool_call in think_tool_calls:
        reflection_content = tool_call["args"]["reflection"]
        all_tool_messages.append(ToolMessage(
            content=f"Strategic reflection recorded: {reflection_content}",
            name="think_tool",
            tool_call_id=tool_call["id"]
        ))
        logger.info(f"💭 Processed strategic reflection: {reflection_content[:100]}...")
    
    # Handle ConductInfluencerResearch calls (research delegation)
    conduct_research_calls = [
        tool_call for tool_call in most_recent_message.tool_calls 
        if tool_call.get("name") == "ConductInfluencerResearch"
    ]
    
    if conduct_research_calls:
        logger.info(f"🔍 Processing {len(conduct_research_calls)} research delegation requests")
        try:
            # Limit concurrent research units to prevent resource exhaustion
            allowed_conduct_research_calls = conduct_research_calls[:configurable.max_concurrent_research_units]
            overflow_conduct_research_calls = conduct_research_calls[configurable.max_concurrent_research_units:]
            
            # For now, simulate research results since we don't have researcher_subgraph implementation
            tool_results = []
            for tool_call in allowed_conduct_research_calls:
                research_topic = tool_call["args"]["research_topic"]
                # Simulate research result
                mock_result = {
                    "compressed_research": f"研究结果: {research_topic} 的初步分析已完成。发现了相关的影响者营销机会和策略要点。",
                    "raw_notes": [f"Research note for: {research_topic}"]
                }
                tool_results.append(mock_result)
            
            # Create tool messages with research results
            for observation, tool_call in zip(tool_results, allowed_conduct_research_calls):
                all_tool_messages.append(ToolMessage(
                    content=observation.get("compressed_research", "Error synthesizing research report: Maximum retries exceeded"),
                    name=tool_call.get("name", "ConductInfluencerResearch"),
                    tool_call_id=tool_call["id"]
                ))
            
            # Handle overflow research calls with error messages
            for overflow_call in overflow_conduct_research_calls:
                all_tool_messages.append(ToolMessage(
                    content=f"Error: Did not run this research as you have already exceeded the maximum number of concurrent research units. Please try again with {configurable.max_concurrent_research_units} or fewer research units.",
                    name="ConductInfluencerResearch",
                    tool_call_id=overflow_call["id"]
                ))
            
            # Aggregate raw notes from all research results
            raw_notes_concat = "\n".join([
                "\n".join(observation.get("raw_notes", [])) 
                for observation in tool_results
            ])
            
            if raw_notes_concat:
                update_payload["raw_notes"] = [raw_notes_concat]
                
        except Exception as e:
            logger.error(f"Error executing research: {e}")
            # Handle research execution errors
            if is_token_limit_exceeded(e, configurable.research_model) or True:
                # Token limit exceeded or other error - end research phase
                logger.warning("Research execution failed, ending research phase")
                return Command(
                    goto=END,
                    update={
                        "notes": get_notes_from_tool_calls(supervisor_messages),
                        "research_brief": state.get("research_brief", "")
                    }
                )
    
    # Step 3: Return command with all tool results
    update_payload["supervisor_messages"] = all_tool_messages
    logger.info(f"✅ Processed {len(all_tool_messages)} tool messages, continuing supervision")
    return Command(
        goto="supervisor",
        update=update_payload
    )


# Supervisor Subgraph Construction
# Creates the supervisor workflow that manages research delegation and coordination
supervisor_builder = StateGraph(SupervisorState, config_schema=Configuration)

# Add supervisor nodes for research management
supervisor_builder.add_node("supervisor", supervisor)           # Main supervisor logic
supervisor_builder.add_node("supervisor_tools", supervisor_tools)  # Tool execution handler

# Define supervisor workflow edges
supervisor_builder.add_edge(START, "supervisor")  # Entry point to supervisor
# supervisor_tools routes back to supervisor or END based on tool results

# Compile supervisor subgraph for use in main workflow
supervisor_subgraph = supervisor_builder.compile()


def research_supervisor(state: InfluencerSearchState, config: RunnableConfig) -> Dict[str, Any]:
    """Research supervisor entry point that bridges main workflow to supervisor subgraph.
    
    This function serves as the integration point between the main influencer search workflow
    and the specialized supervisor subgraph. It transforms the main state into supervisor state
    and invokes the supervisor subgraph for comprehensive research coordination.
    
    Args:
        state: Main workflow state containing research brief and context
        config: Runtime configuration with model settings
        
    Returns:
        Updated main workflow state with supervisor results
    """
    logger.info("🎯 Research supervisor bridge activated")
    
    try:
        # Transform main state to supervisor state
        supervisor_state = {
            "supervisor_messages": state.get("supervisor_messages", []),
            "research_brief": state.get("research_brief", ""),
            "notes": [],
            "research_iterations": 0,
            "raw_notes": []
        }
        
        # Invoke supervisor subgraph
        logger.info("🚀 Invoking supervisor subgraph")
        result = supervisor_subgraph.invoke(supervisor_state, config)
        
        # Extract final notes and create summary response
        final_notes = result.get("notes", [])
        research_brief = result.get("research_brief", "")
        
        if final_notes:
            summary_response = f"""🎯 **影响者营销研究已完成**

📊 **研究发现**:
{chr(10).join(['• ' + note for note in final_notes[:5]])}

✅ **研究状态**: 综合分析完成，已准备好战略建议

📋 **研究摘要**: {research_brief[:200]}{'...' if len(research_brief) > 200 else ''}
"""
        else:
            summary_response = """🎯 **影响者营销研究监督程序已完成**

📋 **当前状态**: 研究协调已完成，正在准备最终报告...

✅ **下一步**: 基于研究发现制定影响者营销策略"""
        
        logger.info("✅ Supervisor subgraph completed successfully")
        
        return {
            "messages": [AIMessage(content=summary_response)],
            "search_completed": True,
            "supervisor_active": True,
            "research_brief": result.get("research_brief", state.get("research_brief", "")),
            "supervisor_messages": result.get("supervisor_messages", [])
        }
        
    except Exception as e:
        logger.error(f"Error in supervisor subgraph: {e}")
        # Fallback response on error
        error_response = f"""⚠️ **研究监督程序遇到问题**

错误信息: {str(e)}

🔄 **回退状态**: 将使用基础搜索功能继续处理请求"""
        
        return {
            "messages": [AIMessage(content=error_response)],
            "search_completed": True,
            "supervisor_active": False,
            "last_error": str(e)
        }