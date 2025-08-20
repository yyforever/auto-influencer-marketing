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
from agent.influencer_search.state import InfluencerSearchState
from agent.influencer_search.schemas import ClarifyWithUser, InfluencerResearchBrief
from agent.influencer_search.prompts import (
    CLARIFY_WITH_USER_INSTRUCTIONS,
    TRANSFORM_MESSAGES_INTO_INFLUENCER_RESEARCH_BRIEF_PROMPT,
    INFLUENCER_RESEARCH_SUPERVISOR_PROMPT,
    FINAL_REPORT_GENERATION_PROMPT,
    get_today_str,
    is_token_limit_exceeded,
    get_model_token_limit
)
from agent.configuration import Configuration

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
    """Generate the final comprehensive influencer marketing research report with retry logic.
    
    Robust report generation from research findings with detailed error logging and retry mechanism.
    
    Args:
        state: Agent state containing research findings
        config: Runtime configuration with model settings
        
    Returns:
        Dictionary containing the final report and updated state
    """
    import asyncio
    
    logger.info("📝 Starting final report generation")
    
    # Extract research findings
    notes = state.get("notes", [])
    findings = "\n".join(notes)
    
    if not findings.strip():
        logger.warning("No research findings available")
        return {
            "final_report": "⚠️ 无法生成报告：未找到研究数据",
            "messages": [AIMessage(content="⚠️ 无法生成最终报告：缺少研究数据")],
            "report_completed": False,
            "notes": {"type": "override", "value": []}
        }
    
    # Configure model
    configurable = Configuration.from_runnable_config(config)
    logger.info(f"🤖 Using model {configurable.final_report_model} for report generation")
    
    # Prepare comprehensive prompt
    final_report_prompt = FINAL_REPORT_GENERATION_PROMPT.format(
        research_brief=state.get("research_brief", ""),
        messages=get_buffer_string(state.get("messages", [])),
        findings=findings,
        date=get_today_str()
    )
    
    # Initialize model with API key
    model_kwargs = {
        "model": configurable.final_report_model,
        "temperature": 0.0,
    }
    
    if "google_genai" in configurable.final_report_model:
        import os
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            model_kwargs["api_key"] = api_key
    
    writer_model = init_chat_model(**model_kwargs)
    
    # Retry logic with detailed error logging
    max_retries = 3
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"🚀 Generating final report (attempt {attempt + 1}/{max_retries + 1})")
            
            final_report = await writer_model.ainvoke([
                HumanMessage(content=final_report_prompt)
            ])
            
            logger.info("✅ Final report generated successfully")
            
            return {
                "final_report": final_report.content, 
                "messages": [final_report],
                "report_completed": True,
                "notes": {"type": "override", "value": []}  # Clear notes after successful generation
            }
            
        except Exception as e:
            # Detailed error logging
            logger.error(f"报告生成失败 - 尝试次数: {attempt + 1}/{max_retries + 1}")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"错误详情: {str(e)}")
            logger.error(f"研究数据长度: {len(findings)} 字符")
            logger.error(f"使用模型: {configurable.final_report_model}")
            
            if attempt < max_retries:
                logger.warning(f"第{attempt + 1}次尝试失败，1秒后重试...")
                await asyncio.sleep(1)  # 1秒延迟避免API限流
                continue
            else:
                logger.error(f"报告生成在{max_retries + 1}次尝试后最终失败")
                return {
                    "final_report": f"❌ 报告生成失败：{str(e)}",
                    "messages": [AIMessage(content="⚠️ 报告生成在多次重试后失败，请检查配置和网络连接")],
                    "report_completed": False,
                    "notes": {"type": "override", "value": []}
                }


