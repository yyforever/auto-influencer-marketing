"""
Supervisor subgraph implementation for influencer search workflow.

Contains the supervisor logic that manages research delegation and coordination
for the influencer marketing research agent. Separated from main nodes.py
for better code organization and maintainability.
"""

import logging
import asyncio
from typing import Literal
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END

# Import local modules
from .state import SupervisorState
from .schemas import ConductInfluencerResearch, InfluencerResearchComplete
from .prompts import (
    get_notes_from_tool_calls,
    is_token_limit_exceeded,
    think_tool
)
from ..configuration import Configuration

# Setup logging
logger = logging.getLogger(__name__)


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
    
    # Available tools: research delegation, completion signaling, and strategic thinking
    lead_researcher_tools = [ConductInfluencerResearch, InfluencerResearchComplete, think_tool]
    
    # Simple model initialization with tool binding
    # Pass API key explicitly for Google GenAI to avoid default credentials lookup
    model_kwargs = {
        "model": configurable.default_model,
        "temperature": 0.0,
    }
    
    # Add API key for Google GenAI models
    if "google_genai" in configurable.default_model:
        import os
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            model_kwargs["api_key"] = api_key
    
    research_model = (
        init_chat_model(**model_kwargs)
        .bind_tools(lead_researcher_tools)
        .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
    )
    
    # Step 2: Generate supervisor response based on current context
    supervisor_messages = state.get("supervisor_messages", [])
    logger.info(f"🔍 DEBUG - Supervisor messages: {supervisor_messages}")
    response = await research_model.ainvoke(supervisor_messages)
    
    logger.info(f"🎯 Supervisor generated response with {len(response.tool_calls) if response.tool_calls else 0} tool calls, response={response}")
    
    # Step 3: Update state and proceed to tool execution
    return Command(
        goto="supervisor_tools",
        update={
            "supervisor_messages": [response],
            "research_iterations": state.get("research_iterations", 0) + 1
        }
    )


def _should_end_research(state: SupervisorState, config: RunnableConfig) -> tuple[bool, dict]:
    """Check if research phase should end based on exit conditions.
    
    Returns:
        Tuple of (should_end, update_dict)
    """
    configurable = Configuration.from_runnable_config(config)
    supervisor_messages = state.get("supervisor_messages", [])
    research_iterations = state.get("research_iterations", 0)
    most_recent_message = supervisor_messages[-1] if supervisor_messages else None
    
    # Check basic validation
    if not most_recent_message or not hasattr(most_recent_message, 'tool_calls'):
        logger.warning("No recent message or tool calls found, ending research")
        return True, {
            "notes": get_notes_from_tool_calls(supervisor_messages),
            "research_brief": state.get("research_brief", "")
        }
    
    # Check exit criteria
    exceeded_iterations = research_iterations > configurable.max_researcher_iterations
    no_tool_calls = not most_recent_message.tool_calls
    research_complete = any(
        tool_call.get("name") == "InfluencerResearchComplete" 
        for tool_call in most_recent_message.tool_calls
    )
    
    if exceeded_iterations or no_tool_calls or research_complete:
        logger.info(f"🏁 Ending research - iterations: {research_iterations}, complete: {research_complete}")
        return True, {
            "notes": get_notes_from_tool_calls(supervisor_messages),
            "research_brief": state.get("research_brief", "")
        }
    
    return False, {}

def _process_think_tools(tool_calls: list) -> list[ToolMessage]:
    """Process think_tool calls and return corresponding tool messages.
    
    Args:
        tool_calls: List of tool calls to process
        
    Returns:
        List of ToolMessage objects for think_tool calls
    """
    think_messages = []
    think_tool_calls = [tc for tc in tool_calls if tc.get("name") == "think_tool"]
    
    for tool_call in think_tool_calls:
        reflection_content = tool_call["args"]["reflection"]
        think_messages.append(ToolMessage(
            content=f"Strategic reflection recorded: {reflection_content}",
            name="think_tool",
            tool_call_id=tool_call["id"]
        ))
        logger.info(f"💭 Processed strategic reflection: {reflection_content[:100]}...")
    
    return think_messages

async def _process_research_tasks(tool_calls: list, config: RunnableConfig) -> tuple[list[ToolMessage], dict]:
    """Process ConductInfluencerResearch calls with concurrent execution.
    
    Args:
        tool_calls: List of tool calls to process
        config: Runtime configuration
        
    Returns:
        Tuple of (tool_messages, update_payload)
    """
    research_calls = [tc for tc in tool_calls if tc.get("name") == "ConductInfluencerResearch"]
    if not research_calls:
        return [], {}
    
    configurable = Configuration.from_runnable_config(config)
    logger.info(f"🔍 Processing {len(research_calls)} research delegation requests")
    
    # Apply concurrency limits
    allowed_calls = research_calls[:configurable.max_concurrent_research_units]
    overflow_calls = research_calls[configurable.max_concurrent_research_units:]
    
    try:
        # Execute research tasks concurrently
        from .nodes import researcher_subgraph
        
        research_tasks = [
            researcher_subgraph.ainvoke({
                "researcher_messages": [HumanMessage(content=tc["args"]["research_topic"])],
                "research_topic": tc["args"]["research_topic"],
                "tool_call_iterations": 0
            }, config) 
            for tc in allowed_calls
        ]
        
        logger.info(f"🚀 Executing {len(research_tasks)} research tasks concurrently")
        tool_results = await asyncio.gather(*research_tasks)
        logger.info(f"✅ Completed {len(tool_results)} concurrent research tasks")
        
        # Create tool messages from results
        tool_messages = []
        for observation, tool_call in zip(tool_results, allowed_calls):
            tool_messages.append(ToolMessage(
                content=observation.get("compressed_research", "Error synthesizing research report: Maximum retries exceeded"),
                name=tool_call.get("name", "ConductInfluencerResearch"),
                tool_call_id=tool_call["id"]
            ))
        
        # Handle overflow calls
        for overflow_call in overflow_calls:
            tool_messages.append(ToolMessage(
                content=f"Error: Did not run this research as you have already exceeded the maximum number of concurrent research units. Please try again with {configurable.max_concurrent_research_units} or fewer research units.",
                name="ConductInfluencerResearch",
                tool_call_id=overflow_call["id"]
            ))
        
        # Aggregate raw notes
        raw_notes = "\n".join([
            "\n".join(observation.get("raw_notes", [])) 
            for observation in tool_results
        ])
        
        update_payload = {"raw_notes": [raw_notes]} if raw_notes else {}
        return tool_messages, update_payload
        
    except Exception as e:
        logger.error(f"Error executing concurrent research: {e}")
        return _handle_research_error(e, allowed_calls, config)


def _handle_research_error(error: Exception, failed_calls: list, config: RunnableConfig) -> tuple[list[ToolMessage], dict]:
    """Handle research execution errors with appropriate recovery strategy.
    
    Args:
        error: The exception that occurred
        failed_calls: List of tool calls that failed
        config: Runtime configuration
        
    Returns:
        Tuple of (error_tool_messages, update_payload)
    """
    configurable = Configuration.from_runnable_config(config)
    
    if is_token_limit_exceeded(error, configurable.default_model):
        logger.warning("Token limit exceeded during research execution")
        # Return empty to trigger research phase end
        raise error
    
    # For other errors, create error messages and continue
    logger.warning(f"Research execution partially failed: {error}")
    error_messages = [
        ToolMessage(
            content=f"Error executing research: {str(error)}",
            name=tool_call.get("name", "ConductInfluencerResearch"),
            tool_call_id=tool_call["id"]
        )
        for tool_call in failed_calls
    ]
    
    return error_messages, {}


async def supervisor_tools(state: SupervisorState, config: RunnableConfig) -> Command[Literal["supervisor", "__end__"]]:
    """Execute tools called by the supervisor with clean separation of concerns.
    
    Handles think_tool (strategic reflection) and ConductInfluencerResearch (task delegation)
    with proper error handling and resource management.
    
    Args:
        state: Current supervisor state with messages and iteration count
        config: Runtime configuration with research limits and model settings
        
    Returns:
        Command to either continue supervision loop or end research phase
    """
    logger.info("🔧 Executing supervisor tools")
    
    # Check if research should end
    should_end, end_update = _should_end_research(state, config)
    if should_end:
        return Command(goto=END, update=end_update)
    
    # Get tool calls from most recent message
    supervisor_messages = state.get("supervisor_messages", [])
    most_recent_message = supervisor_messages[-1]
    tool_calls = most_recent_message.tool_calls
    
    try:
        # Process different tool types
        think_messages = _process_think_tools(tool_calls)
        research_messages, research_update = await _process_research_tasks(tool_calls, config)
        
        # Combine all tool messages and updates
        all_tool_messages = think_messages + research_messages
        update_payload = {"supervisor_messages": all_tool_messages}
        update_payload.update(research_update)
        
        logger.info(f"✅ Processed {len(all_tool_messages)} tool messages, continuing supervision")
        return Command(goto="supervisor", update=update_payload)
        
    except Exception as e:
        # Handle critical errors (like token limit exceeded)
        if is_token_limit_exceeded(e, Configuration.from_runnable_config(config).default_model):
            logger.warning("Token limit exceeded, ending research phase")
            return Command(goto=END, update=end_update)
        
        # Re-raise other critical errors
        raise


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

logger.info("🎯 Supervisor subgraph compiled successfully")