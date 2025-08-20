"""
Researcher subgraph implementation for influencer search workflow.

Contains individual researcher logic that conducts focused research on specific topics,
including tool management, search integration, and research compression functionality.
Separated from main nodes.py for better code organization and maintainability.
"""

import logging
import asyncio
from typing import Literal
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END

# Import local modules
from .state import ResearcherState, ResearcherInputState, ResearcherOutputState
from .schemas import InfluencerResearchComplete
from .prompts import (
    get_today_str,
    think_tool,
    influencer_search_tool,
    is_token_limit_exceeded,
    filter_messages,
    remove_up_to_last_ai_message,
    openai_websearch_called,
    anthropic_websearch_called
)
from ..configuration import Configuration

# Setup logging
logger = logging.getLogger(__name__)


# Individual Researcher Node Functions
# ====================================

async def researcher(state: ResearcherState, config: RunnableConfig) -> Command[Literal["researcher_tools"]]:
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
        # Prepare system prompt with MCP context if available
        from .prompts import research_system_prompt
        researcher_prompt = research_system_prompt.format(
            mcp_prompt=configurable.mcp_prompt or "", 
            date=get_today_str()
        )
        
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


async def researcher_tools(state: ResearcherState, config: RunnableConfig) -> Command[Literal["researcher", "compress_research"]]:
    """Execute tools called by the researcher, including search tools and strategic thinking.
    
    This function handles various types of researcher tool calls:
    1. think_tool - Strategic reflection that continues the research conversation
    2. influencer_search_tool - Influencer search
    3. ResearchComplete - Signals completion of individual research task
    
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
        
        # Early exit if no tool calls were made
        has_tool_calls = bool(most_recent_message.tool_calls)
        
        if not has_tool_calls:
            logger.info("No tool calls found, proceeding to compression")
            return Command(goto="compress_research")
        
        # Step 2: Handle tool calls if they exist
        all_tool_messages = []
        
        if has_tool_calls:
            # Get all available research tools
            available_tools = await get_all_tools(config)
            tools_by_name = {
                tool.name if hasattr(tool, "name") else tool.get("name", "web_search"): tool 
                for tool in available_tools
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


async def compress_research(state: ResearcherState, config: RunnableConfig):
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
    
    # 直接跳过压缩逻辑 - 极简实现，不调用大模型
    try:
        researcher_messages = state.get("researcher_messages", [])
        
        # 使用相同的逻辑提取原始内容
        raw_notes_content = "\n".join([
            str(message.content) 
            for message in filter_messages(researcher_messages, include_types=["tool", "ai"])
        ])
        
        # 直接拼装简单的研究摘要，不调用大模型
        tool_call_count = len([m for m in researcher_messages if hasattr(m, 'tool_calls') and m.tool_calls])
        compressed_summary = f"Research completed with {tool_call_count} tool executions."
        
        if raw_notes_content.strip():
            # 取前500字符作为简要摘要
            preview = raw_notes_content.strip()[:500]
            if len(raw_notes_content) > 500:
                preview += "..."
            compressed_summary += f"\n\nFindings:\n{preview}"
        
        logger.info("✅ Research compression bypassed - returning direct results")
        
        # 返回与其他节点匹配的格式
        return {
            "compressed_research": compressed_summary,
            "raw_notes": [raw_notes_content]
        }
        
    except Exception:
        # 如果极简实现失败，继续执行原压缩逻辑
        logger.error("Research compression bypassed failed")
        pass
    
    try:
        # Step 1: Simple compression model configuration
        configurable = Configuration.from_runnable_config(config)
        
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
        
        synthesizer_model = init_chat_model(**model_kwargs)
        
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
                if is_token_limit_exceeded(e, configurable.default_model):
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

async def get_all_tools(config: RunnableConfig):
    """Assemble complete toolkit including research, search, and MCP tools.
    
    Args:
        config: Runtime configuration specifying search API and MCP settings
        
    Returns:
        List of all configured and available tools for research operations
    """
    from langchain_core.tools import tool
    
    # Start with core research tools
    tools = [tool(InfluencerResearchComplete), think_tool]
    
    tools.extend([influencer_search_tool])
   
    logger.info(f"🔧 Assembled {len(tools)} research tools: {[tool.name if hasattr(tool, 'name') else 'unkown tool' for tool in tools]}")
    
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