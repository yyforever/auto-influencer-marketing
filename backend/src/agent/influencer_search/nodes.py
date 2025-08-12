"""
Node implementations for influencer search workflow.

Contains all LangGraph node functions that implement the core business logic
for the influencer search agent. Each node has a single responsibility
following LangGraph best practices.
"""

import logging
import asyncio
from typing import Dict, Any, Literal
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage, get_buffer_string
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END

# Import local modules
from .state import InfluencerSearchState
from .schemas import (
    ClarifyWithUser, InfluencerResearchBrief, 
    SupervisorState, ConductInfluencerResearch, InfluencerResearchComplete,
    ResearchComplete, ResearcherState, ResearcherInputState, ResearcherOutputState
)
from .prompts import (
    CLARIFY_WITH_USER_INSTRUCTIONS,
    TRANSFORM_MESSAGES_INTO_INFLUENCER_RESEARCH_BRIEF_PROMPT,
    INFLUENCER_RESEARCH_SUPERVISOR_PROMPT,
    FINAL_REPORT_GENERATION_PROMPT,
    get_today_str,
    think_tool,
    get_notes_from_tool_calls,
    get_api_key_for_model,
    is_token_limit_exceeded,
    get_model_token_limit,
    filter_messages,
    remove_up_to_last_ai_message,
    openai_websearch_called,
    anthropic_websearch_called
)
from ..configuration import Configuration

# Setup logging
logger = logging.getLogger(__name__)

# Initialize a configurable model that we will use throughout the agent
def create_model(model_name: str, max_tokens: int = 4000, temperature: float = 0.0):
    """Create a model instance with proper provider detection."""
    import os
    
    api_key = get_api_key_for_model(model_name, None)
    
    if "gpt" in model_name.lower():
        return init_chat_model(
            model=model_name,
            model_provider="openai",
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL"),
            max_tokens=max_tokens,
            temperature=temperature,
        )
    elif "gemini" in model_name.lower():
        return init_chat_model(
            model=model_name,
            model_provider="google-genai",
            api_key=api_key,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    else:
        # Default to OpenAI
        return init_chat_model(
            model=model_name,
            model_provider="openai",
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL"),
            max_tokens=max_tokens,
            temperature=temperature,
        )



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
    logger.info(f"Configurable: {configurable}")
    if not configurable.allow_clarification:
        # Skip clarification step and proceed directly to research brief generation
        logger.info("Clarification disabled, proceeding to research brief generation")
        return Command(goto="write_research_brief")
    
    # Step 2: Prepare the model for structured clarification analysis
    messages = state["messages"]
    
    # Configure model with structured output and retry logic
    base_model = create_model(
        configurable.query_generator_model,
        max_tokens=configurable.research_model_max_tokens,
        temperature=0.0
    )
    clarification_model = (
        base_model
        .with_structured_output(ClarifyWithUser)
        .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
    )
    
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
        
        # Configure model for structured research brief generation
        base_model = create_model(
            configurable.research_model,
            max_tokens=configurable.research_model_max_tokens,
            temperature=0.0
        )
        research_model = (
            base_model
            .with_structured_output(InfluencerResearchBrief)
            .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
        )
        
        # Step 2: Generate structured research brief from user messages
        prompt_content = TRANSFORM_MESSAGES_INTO_INFLUENCER_RESEARCH_BRIEF_PROMPT.format(
            messages=get_buffer_string(state.get("messages", [])),
            date=get_today_str()
        )
        
        logger.info("🤖 Generating influencer structured research brief...")
        response = await research_model.ainvoke([HumanMessage(content=prompt_content)])
        
        # Step 3: Initialize supervisor with research brief and instructions
        supervisor_system_prompt = INFLUENCER_RESEARCH_SUPERVISOR_PROMPT.format(
            date=get_today_str(),
            max_concurrent_research_units=configurable.max_concurrent_research_units,
            max_researcher_iterations=configurable.max_researcher_iterations
        )
        
        logger.info("✅ Influencer research brief generated successfully")
        logger.info(f"Structured influencer research brief: {response}")
        
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
                    "budget": response.budget,
                    "content_requirements": response.content_requirements,
                    # timeline removed from schema; no longer included
                },
                "supervisor_messages": {
                    "type": "override",
                    "value": [
                        SystemMessage(content=supervisor_system_prompt),
                        HumanMessage(content=response.research_brief)
                    ]
                },
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
    base_model = create_model(
        configurable.research_model,
        max_tokens=configurable.research_model_max_tokens,
        temperature=0.0
    )
    research_model = (
        base_model
        .bind_tools(lead_researcher_tools)
        .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
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
            
            # Execute research tasks in parallel using researcher_subgraph
            research_tasks = [
                researcher_subgraph.ainvoke({
                    "researcher_messages": [
                        HumanMessage(content=tool_call["args"]["research_topic"])
                    ],
                    "research_topic": tool_call["args"]["research_topic"],
                    "tool_call_iterations": 0
                }, config) 
                for tool_call in allowed_conduct_research_calls
            ]
            
            logger.info(f"🚀 Executing {len(research_tasks)} research tasks concurrently")
            tool_results = await asyncio.gather(*research_tasks)
            logger.info(f"✅ Completed {len(tool_results)} concurrent research tasks")
            
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
            logger.error(f"Error executing concurrent research: {e}")
            # Handle research execution errors
            if is_token_limit_exceeded(e, configurable.research_model):
                # Token limit exceeded - end research phase
                logger.warning("Token limit exceeded during research execution, ending research phase")
                return Command(
                    goto=END,
                    update={
                        "notes": get_notes_from_tool_calls(supervisor_messages),
                        "research_brief": state.get("research_brief", "")
                    }
                )
            else:
                # Other errors - continue with partial results
                logger.warning(f"Research execution partially failed: {e}")
                # Create error messages for failed research calls
                for tool_call in allowed_conduct_research_calls:
                    all_tool_messages.append(ToolMessage(
                        content=f"Error executing research: {str(e)}",
                        name=tool_call.get("name", "ConductInfluencerResearch"),
                        tool_call_id=tool_call["id"]
                    ))
    
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


## Deprecated bridge function removed after wiring subgraph directly in the main graph


async def final_report_generation(state: InfluencerSearchState, config: RunnableConfig) -> Dict[str, Any]:
    """Generate the final comprehensive influencer marketing research report with retry logic for token limits.
    
    This function takes all collected research findings and synthesizes them into a 
    well-structured, comprehensive final report using the configured report generation model.
    
    Args:
        state: Agent state containing research findings and context
        config: Runtime configuration with model settings and API keys
        
    Returns:
        Dictionary containing the final report and updated state
    """
    logger.info("📝 Starting final report generation")
    
    try:
        # Step 1: Extract research findings and configuration
        configurable = Configuration.from_runnable_config(config)
        
        # Check if final report generation is enabled
        if not configurable.enable_final_report:
            logger.info("Final report generation is disabled, skipping")
            return {
                "messages": [AIMessage(content="🎯 影响者营销研究已完成，未生成最终报告（已禁用）")],
                "report_completed": False
            }
        
        # Get research findings from notes
        notes = state.get("notes", [])
        findings = "\n".join(notes)
        
        if not findings.strip():
            logger.warning("No research findings available for report generation")
            return {
                "final_report": "⚠️ 无法生成报告：未找到研究发现和数据",
                "messages": [AIMessage(content="⚠️ 无法生成最终报告：缺少研究数据")],
                "report_completed": False
            }
        
        # Step 2: Configure the final report generation model
        writer_model_config = {
            "model": configurable.final_report_model,
            "max_tokens": configurable.final_report_model_max_tokens,
            "api_key": get_api_key_for_model(configurable.final_report_model, config),
            "tags": ["langsmith:nostream"]
        }
        
        logger.info(f"🤖 Using model {configurable.final_report_model} for report generation")
        
        # Step 3: Attempt report generation with token limit retry logic
        max_retries = 3
        current_retry = 0
        findings_token_limit = None
        
        while current_retry <= max_retries:
            try:
                # Create comprehensive prompt with all research context
                final_report_prompt = FINAL_REPORT_GENERATION_PROMPT.format(
                    research_brief=state.get("research_brief", ""),
                    messages=get_buffer_string(state.get("messages", [])),
                    findings=findings,
                    date=get_today_str()
                )
                
                logger.info(f"🚀 Generating final report (attempt {current_retry + 1}/{max_retries + 1})")
                
                # Generate the final report
                writer_model = create_model(
                    configurable.final_report_model,
                    max_tokens=configurable.final_report_model_max_tokens,
                    temperature=0.0
                )
                final_report = await writer_model.ainvoke([
                    HumanMessage(content=final_report_prompt)
                ])
                
                logger.info("✅ Final report generated successfully")
                
                # Return successful report generation
                return {
                    "final_report": final_report.content, 
                    "messages": [final_report],
                    "report_completed": True,
                    "notes": []  # Clear notes after report generation
                }
                
            except Exception as e:
                # Handle token limit exceeded errors with progressive truncation
                if is_token_limit_exceeded(e, configurable.final_report_model):
                    current_retry += 1
                    logger.warning(f"Token limit exceeded, attempting retry {current_retry}/{max_retries}")
                    
                    if current_retry == 1:
                        # First retry: determine initial truncation limit
                        model_token_limit = get_model_token_limit(configurable.final_report_model)
                        if not model_token_limit:
                            logger.error("Could not determine model token limit")
                            return {
                                "final_report": f"❌ 报告生成错误：Token限制超出，但无法确定模型的最大上下文长度。请检查模型配置。错误：{e}",
                                "messages": [AIMessage(content="⚠️ 报告生成因token限制失败")],
                                "report_completed": False
                            }
                        # Use 4x token limit as character approximation for truncation
                        findings_token_limit = model_token_limit * 4
                    else:
                        # Subsequent retries: reduce by 10% each time
                        findings_token_limit = int(findings_token_limit * 0.9)
                    
                    # Truncate findings and retry
                    findings = findings[:findings_token_limit]
                    logger.info(f"Truncated findings to {len(findings)} characters")
                    continue
                else:
                    # Non-token-limit error: return error immediately
                    logger.error(f"Report generation error: {e}")
                    return {
                        "final_report": f"❌ 报告生成错误：{str(e)}",
                        "messages": [AIMessage(content="⚠️ 报告生成过程中发生错误")],
                        "report_completed": False
                    }
        
        # Step 4: Return failure result if all retries exhausted
        logger.error("Report generation failed after maximum retries")
        return {
            "final_report": "❌ 报告生成错误：已达到最大重试次数",
            "messages": [AIMessage(content="⚠️ 报告生成多次重试后失败")],
            "report_completed": False
        }
        
    except Exception as e:
        logger.error(f"Critical error in final_report_generation: {e}")
        # Fallback result
        return {
            "final_report": f"❌ 报告生成关键错误：{str(e)}",
            "messages": [AIMessage(content="⚠️ 报告生成系统遇到严重错误")],
            "report_completed": False
        }


# Individual Researcher Node Functions
# ====================================

async def researcher(state, config: RunnableConfig) -> Command[Literal["researcher_tools"]]:
    """Individual researcher that conducts focused research on specific topics.
    
    This researcher is given a specific research topic by the supervisor and uses
    available tools (search, think_tool, MCP tools) to gather comprehensive information.
    It can use think_tool for strategic planning between searches.
    
    Args:
        state: Current researcher state with messages and topic context
        config: Runtime configuration with model settings and tool availability
        
    Returns:
        Command to proceed to researcher_tools for tool execution
    """
    logger.info("🔬 Individual researcher activated")
    
    try:
        # Step 1: Load configuration and validate tool availability
        configurable = Configuration.from_runnable_config(config)
        researcher_messages = state.get("researcher_messages", [])
        
        # Get all available research tools (search, MCP, think_tool)
        tools = await get_all_tools(config)
        if len(tools) == 0:
            raise ValueError(
                "No tools found to conduct research: Please configure either your "
                "search API or add MCP tools to your configuration."
            )
        
        logger.info(f"📦 Available research tools: {[tool.name if hasattr(tool, 'name') else 'web_search' for tool in tools]}")
        
        # Step 2: Configure the researcher model with tools
        research_model_config = {
            "model": configurable.research_model,
            "max_tokens": configurable.research_model_max_tokens,
            "api_key": get_api_key_for_model(configurable.research_model, config),
            "tags": ["langsmith:nostream"]
        }
        
        # Prepare system prompt with MCP context if available
        from .prompts import research_system_prompt
        researcher_prompt = research_system_prompt.format(
            mcp_prompt=configurable.mcp_prompt or "", 
            date=get_today_str()
        )
        
        # Configure model with tools, retry logic, and settings
        base_model = create_model(
            configurable.research_model,
            max_tokens=configurable.research_model_max_tokens,
            temperature=0.0
        )
        research_model = (
            base_model
            .bind_tools(tools)
            .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
        )
        
        # Step 3: Generate researcher response with system context
        messages = [SystemMessage(content=researcher_prompt)] + researcher_messages
        response = await research_model.ainvoke(messages)
        
        logger.info(f"🎯 Researcher generated response with {len(response.tool_calls) if response.tool_calls else 0} tool calls")
        
        # Step 4: Update state and proceed to tool execution
        return Command(
            goto="researcher_tools",
            update={
                "researcher_messages": [response],
                "tool_call_iterations": state.get("tool_call_iterations", 0) + 1
            }
        )
        
    except Exception as e:
        logger.error(f"Error in researcher node: {e}")
        # Return error state - will be handled by compression
        return Command(
            goto="compress_research",
            update={
                "researcher_messages": [AIMessage(content=f"Research error: {str(e)}")]
            }
        )


async def researcher_tools(state, config: RunnableConfig) -> Command[Literal["researcher", "compress_research"]]:
    """Execute tools called by the researcher, including search tools and strategic thinking.
    
    This function handles various types of researcher tool calls:
    1. think_tool - Strategic reflection that continues the research conversation
    2. Search tools (tavily_search, web_search) - Information gathering
    3. MCP tools - External tool integrations
    4. ResearchComplete - Signals completion of individual research task
    
    Args:
        state: Current researcher state with messages and iteration count
        config: Runtime configuration with research limits and tool settings
        
    Returns:
        Command to either continue research loop or proceed to compression
    """
    logger.info("🔧 Executing researcher tools")
    
    try:
        # Step 1: Extract current state and check early exit conditions
        configurable = Configuration.from_runnable_config(config)
        researcher_messages = state.get("researcher_messages", [])
        most_recent_message = researcher_messages[-1] if researcher_messages else None
        
        if not most_recent_message:
            logger.warning("No recent message found, proceeding to compression")
            return Command(goto="compress_research")
        
        # Early exit if no tool calls were made (including native web search)
        has_tool_calls = bool(most_recent_message.tool_calls)
        has_native_search = (
            openai_websearch_called(most_recent_message) or 
            anthropic_websearch_called(most_recent_message)
        )
        
        if not has_tool_calls and not has_native_search:
            logger.info("No tool calls found, proceeding to compression")
            return Command(goto="compress_research")
        
        # Step 2: Handle tool calls if they exist
        all_tool_messages = []
        
        if has_tool_calls:
            # Get all available research tools
            tools = await get_all_tools(config)
            tools_by_name = {
                tool.name if hasattr(tool, "name") else tool.get("name", "web_search"): tool 
                for tool in tools
            }
            
            # Execute all tool calls in parallel
            tool_calls = most_recent_message.tool_calls
            logger.info(f"🔧 Executing {len(tool_calls)} tool calls in parallel")
            
            tool_execution_tasks = [
                execute_tool_safely(tools_by_name.get(tool_call["name"]), tool_call["args"], config) 
                for tool_call in tool_calls
                if tool_call["name"] in tools_by_name
            ]
            
            if tool_execution_tasks:
                observations = await asyncio.gather(*tool_execution_tasks)
                
                # Create tool messages from execution results
                all_tool_messages = [
                    ToolMessage(
                        content=str(observation),
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"]
                    ) 
                    for observation, tool_call in zip(observations, tool_calls)
                    if tool_call["name"] in tools_by_name
                ]
                
                logger.info(f"✅ Processed {len(all_tool_messages)} tool executions")
        
        # Step 3: Check late exit conditions (after processing tools)
        exceeded_iterations = state.get("tool_call_iterations", 0) >= configurable.max_react_tool_calls
        research_complete_called = any(
            tool_call["name"] == "ResearchComplete" 
            for tool_call in most_recent_message.tool_calls
        ) if has_tool_calls else False
        
        if exceeded_iterations or research_complete_called:
            # End research and proceed to compression
            logger.info(f"🏁 Ending research - iterations: {state.get('tool_call_iterations', 0)}, complete: {research_complete_called}")
            return Command(
                goto="compress_research",
                update={"researcher_messages": all_tool_messages} if all_tool_messages else {}
            )
        
        # Continue research loop with tool results
        logger.info("🔄 Continuing research loop")
        return Command(
            goto="researcher",
            update={"researcher_messages": all_tool_messages} if all_tool_messages else {}
        )
        
    except Exception as e:
        logger.error(f"Error in researcher_tools: {e}")
        # On error, proceed to compression
        return Command(
            goto="compress_research",
            update={"researcher_messages": [AIMessage(content=f"Tool execution error: {str(e)}")]}
        )


async def compress_research(state, config: RunnableConfig):
    """Compress and synthesize research findings into a concise, structured summary.
    
    This function takes all the research findings, tool outputs, and AI messages from
    a researcher's work and distills them into a clean, comprehensive summary while
    preserving all important information and findings.
    
    Args:
        state: Current researcher state with accumulated research messages
        config: Runtime configuration with compression model settings
        
    Returns:
        Dictionary containing compressed research summary and raw notes
    """
    logger.info("🗜️ Starting research compression")
    
    try:
        # Step 1: Configure the compression model
        configurable = Configuration.from_runnable_config(config)
        compression_model_name = (configurable.compression_model 
                                if hasattr(configurable, 'compression_model') and configurable.compression_model
                                else configurable.research_model)
        compression_max_tokens = (configurable.compression_model_max_tokens 
                                if hasattr(configurable, 'compression_model_max_tokens') and configurable.compression_model_max_tokens
                                else configurable.research_model_max_tokens)
        
        synthesizer_model = create_model(
            compression_model_name,
            max_tokens=compression_max_tokens,
            temperature=0.0
        )
        
        # Step 2: Prepare messages for compression
        researcher_messages = state.get("researcher_messages", [])
        
        # Add instruction to switch from research mode to compression mode
        from .prompts import compress_research_simple_human_message
        researcher_messages.append(HumanMessage(content=compress_research_simple_human_message))
        
        # Step 3: Attempt compression with retry logic for token limit issues
        synthesis_attempts = 0
        max_attempts = 3
        
        while synthesis_attempts < max_attempts:
            try:
                # Create system prompt focused on compression task
                from .prompts import compress_research_system_prompt
                compression_prompt = compress_research_system_prompt.format(date=get_today_str())
                messages = [SystemMessage(content=compression_prompt)] + researcher_messages
                
                # Execute compression
                logger.info("🤖 Generating compressed research summary...")
                response = await synthesizer_model.ainvoke(messages)
                
                # Extract raw notes from all tool and AI messages
                raw_notes_content = "\n".join([
                    str(message.content) 
                    for message in filter_messages(researcher_messages, include_types=["tool", "ai"])
                ])
                
                logger.info("✅ Research compression completed successfully")
                
                # Return successful compression result
                return {
                    "compressed_research": str(response.content),
                    "raw_notes": [raw_notes_content]
                }
                
            except Exception as e:
                synthesis_attempts += 1
                logger.warning(f"Compression attempt {synthesis_attempts} failed: {e}")
                
                # Handle token limit exceeded by removing older messages
                if is_token_limit_exceeded(e, configurable.research_model):
                    researcher_messages = remove_up_to_last_ai_message(researcher_messages)
                    logger.info("Reduced message history due to token limit")
                    continue
                
                # For other errors, continue retrying
                continue
        
        # Step 4: Return error result if all attempts failed
        raw_notes_content = "\n".join([
            str(message.content) 
            for message in filter_messages(researcher_messages, include_types=["tool", "ai"])
        ])
        
        logger.error("Research compression failed after maximum retries")
        return {
            "compressed_research": "Error synthesizing research report: Maximum retries exceeded",
            "raw_notes": [raw_notes_content]
        }
        
    except Exception as e:
        logger.error(f"Critical error in compress_research: {e}")
        # Fallback result
        return {
            "compressed_research": f"Error in research compression: {str(e)}",
            "raw_notes": [f"Error processing research data: {str(e)}"]
        }


# Tool Management and Search Integration
# ======================================

# Mock SearchAPI for now - replace with actual implementation
class SearchAPI:
    """Mock SearchAPI class for development."""
    def __init__(self, api_type: str):
        self.api_type = api_type

    def __str__(self):
        return f"SearchAPI({self.api_type})"


def get_config_value(value):
    """Get configuration value with fallback."""
    return value if value is not None else "mock_search"


async def get_search_tool(search_api: SearchAPI):
    """Get search tools based on configured API."""
    # Mock search tool implementation
    from langchain_core.tools import tool
    
    @tool(description="Search for information on the internet")
    def tavily_search(query: str) -> str:
        """Mock search function for development."""
        return f"Mock search results for: {query}\n\nThis is a mock implementation. Real search results would appear here with relevant information about influencer marketing based on the query."
    
    return [tavily_search]


async def load_mcp_tools(config, existing_tool_names):
    """Load MCP tools if configured."""
    # Mock MCP tool loading - replace with actual MCP integration
    mcp_tools = []
    
    # For now, return empty list since we don't have MCP configured
    return mcp_tools


async def get_all_tools(config: RunnableConfig):
    """Assemble complete toolkit including research, search, and MCP tools.
    
    Args:
        config: Runtime configuration specifying search API and MCP settings
        
    Returns:
        List of all configured and available tools for research operations
    """
    from langchain_core.tools import tool
    
    # Start with core research tools
    tools = [tool(ResearchComplete), think_tool]
    
    # Add configured search tools
    configurable = Configuration.from_runnable_config(config)
    search_api = SearchAPI(get_config_value(configurable.search_api if hasattr(configurable, 'search_api') else 'mock'))
    search_tools = await get_search_tool(search_api)
    tools.extend(search_tools)
    
    # Track existing tool names to prevent conflicts
    existing_tool_names = {
        tool.name if hasattr(tool, "name") else tool.get("name", "web_search") 
        for tool in tools
    }
    
    # Add MCP tools if configured
    mcp_tools = await load_mcp_tools(config, existing_tool_names)
    tools.extend(mcp_tools)
    
    logger.info(f"🔧 Assembled {len(tools)} research tools: {[tool.name if hasattr(tool, 'name') else 'web_search' for tool in tools]}")
    
    return tools


async def execute_tool_safely(tool, args, config):
    """Safely execute a tool with error handling."""
    try:
        if tool is None:
            return "Error: Tool not found or not configured"
        
        logger.info(f"🔧 Executing tool: {tool.name if hasattr(tool, 'name') else 'unknown'}")
        
        if hasattr(tool, 'ainvoke'):
            result = await tool.ainvoke(args, config)
        elif hasattr(tool, 'invoke'):
            result = tool.invoke(args)
        elif callable(tool):
            result = tool(**args)
        else:
            return f"Error: Tool {tool} is not callable"
        
        logger.info(f"✅ Tool execution completed")
        return result
        
    except Exception as e:
        logger.error(f"❌ Tool execution failed: {e}")
        return f"Error executing tool: {str(e)}"


# Researcher Subgraph Construction
# ================================

# Creates individual researcher workflow for conducting focused research on specific topics
researcher_builder = StateGraph(
    ResearcherState, 
    input=ResearcherInputState,
    output=ResearcherOutputState, 
    config_schema=Configuration
)

# Add researcher nodes for research execution and compression
researcher_builder.add_node("researcher", researcher)                 # Main researcher logic
researcher_builder.add_node("researcher_tools", researcher_tools)     # Tool execution handler  
researcher_builder.add_node("compress_research", compress_research)   # Research compression

# Define researcher workflow edges
researcher_builder.add_edge(START, "researcher")           # Entry point to researcher
researcher_builder.add_edge("compress_research", END)      # Exit point after compression

# Compile researcher subgraph for parallel execution by supervisor
researcher_subgraph = researcher_builder.compile()
logger.info("🔬 Researcher subgraph compiled successfully")