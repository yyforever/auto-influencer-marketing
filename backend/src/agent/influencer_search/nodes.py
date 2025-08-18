"""
Node implementations for influencer search workflow.

Contains all LangGraph node functions that implement the core business logic
for the influencer search agent. Each node has a single responsibility
following LangGraph best practices.
"""

import logging
from typing import Dict, Any, Literal
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, get_buffer_string
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langgraph.graph import END

# Import local modules
from .state import InfluencerSearchState
from .schemas import ClarifyWithUser, InfluencerResearchBrief
from .supervisor import supervisor_subgraph
from .researcher import researcher_subgraph
from .prompts import (
    CLARIFY_WITH_USER_INSTRUCTIONS,
    TRANSFORM_MESSAGES_INTO_INFLUENCER_RESEARCH_BRIEF_PROMPT,
    INFLUENCER_RESEARCH_SUPERVISOR_PROMPT,
    FINAL_REPORT_GENERATION_PROMPT,
    get_today_str,
    is_token_limit_exceeded,
    get_model_token_limit
)
from ..configuration import Configuration

# Setup logging
logger = logging.getLogger(__name__)

# Simplified model initialization using init_chat_model best practices



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
    
    # Simple model initialization using init_chat_model best practices
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
    
    clarification_model = (
        init_chat_model(**model_kwargs)
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
        
        # DEBUG: Print configuration details
        logger.info(f"🔍 DEBUG - Model: {configurable.default_model}")
        
        # Simple model initialization for structured research brief generation
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
        
        base_model = init_chat_model(**model_kwargs)
        
        
        research_model = (
            base_model
            .with_structured_output(InfluencerResearchBrief)
            .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
        )
        
        # Step 2: Generate structured research brief from user messages
        prompt_content = TRANSFORM_MESSAGES_INTO_INFLUENCER_RESEARCH_BRIEF_PROMPT.format(
            messages=get_buffer_string(state.get("messages", []))
        )
        
        logger.info("🤖 Generating influencer structured research brief...")
        
        # Now try structured output - let it fail naturally if parsing fails
        response = await research_model.ainvoke([HumanMessage(content=prompt_content)])
        
        logger.info("✅ Influencer research brief generated successfully")
        logger.info(f"🔍 DEBUG - Structured response: {response}")
        
        # Step 3: Initialize supervisor with research brief and instructions
        supervisor_system_prompt = INFLUENCER_RESEARCH_SUPERVISOR_PROMPT.format(
            max_concurrent_research_units=configurable.max_concurrent_research_units,
            max_researcher_iterations=configurable.max_researcher_iterations
        )
        
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
                }
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
                
                # Simple model initialization for final report generation
                # Pass API key explicitly for Google GenAI to avoid default credentials lookup
                model_kwargs = {
                    "model": configurable.final_report_model,
                    "temperature": 0.0,
                }
                
                # Add API key for Google GenAI models
                if "google_genai" in configurable.final_report_model:
                    import os
                    api_key = os.getenv("GEMINI_API_KEY")
                    if api_key:
                        model_kwargs["api_key"] = api_key
                
                writer_model = init_chat_model(**model_kwargs)
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


