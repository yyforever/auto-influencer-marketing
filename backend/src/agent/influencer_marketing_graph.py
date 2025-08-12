"""
Auto Influencer Marketing Graph - Main orchestration graph.

This is the main entry point for the influencer marketing campaign agent.
It orchestrates the 7-phase campaign workflow using LangGraph subgraphs.
"""

import os
import logging
from typing import Any, Dict, Literal
from agent.schemas.campaigns import CampaignBasicInfo, CalarifyCampaignInfoWithHuman
from devtools import pprint
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, get_buffer_string
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt
from langchain.chat_models import init_chat_model

# Import state management
from agent.state.states import AgentInputState, AgentState, CampaignState
from agent.configuration import Configuration
from agent.prompts.instructions import campaign_info_extraction_instructions, clarify_campaign_info_with_human_instructions, caliry_questions_template

# Import utilities
from agent.utils import setup_campaign_logging, log_phase_transition

# Load environment variables
load_dotenv()

# Initialize configurable model
def create_model(model_name: str, max_tokens: int = 4000, temperature: float = 0.0):
    """Create a model instance with proper provider detection."""
    api_key = get_api_key_for_model(model_name)
    
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

def get_api_key_for_model(model_name: str) -> str:
    """Get appropriate API key for the specified model."""
    # For GPT models (including GPT-5), use the OPENAI_API_KEY
    if "gpt" in model_name.lower():
        return os.getenv("OPENAI_API_KEY", "")
    
    # For Gemini models, use the GEMINI_API_KEY
    if "gemini" in model_name.lower():
        return os.getenv("GEMINI_API_KEY", "")
    
    # Default to OpenAI for unknown models
    return os.getenv("OPENAI_API_KEY", "")

# Setup logging
logger = logging.getLogger(__name__)

def initialize_campaign_info(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    Node 1: Extract structured campaign information from user messages.
    
    Purpose: Parse user input and extract core campaign data (objective, budget, KPIs, etc.)
    Schema: Uses CampaignBasicInfo for structured data extraction
    """
    logger.info("🔍 Initializing campaign info")
    logger.info(f"config: {config}")
    configurable = Configuration.from_runnable_config(config)
    
    # Get user messages for extraction
    user_messages = get_buffer_string(state["messages"])
    
    # Initialize LLM with structured output for information extraction
    llm = create_model(configurable.query_generator_model, max_tokens=4000, temperature=0.1)
    
    # Use CampaignBasicInfo for information extraction
    structured_llm = llm.with_structured_output(CampaignBasicInfo)
    formatted_prompt = campaign_info_extraction_instructions.format(messages=user_messages)
    campaign_basic_info = structured_llm.invoke(formatted_prompt)
    
    logger.info(f"🔍 Campaign Basic Info Extracted: {campaign_basic_info}")
    
    return {
        "campaign_basic_info": campaign_basic_info
    }

def auto_clarify_campaign_info(state: AgentState, config: RunnableConfig) -> Command[Literal["request_human_review", "__end__"]]:
    """
    Node 2: AI determines if extracted info needs clarification from user.
    
    Purpose: Analyze campaign_basic_info and decide if more details needed
    Schema: Uses CalarifyCampaignInfoWithHuman for clarification logic
    Key Logic: If need_clarification=True, return questions to user and end flow 
    """
    logger.info("🔍 Auto clarifying campaign info")
    # logger.info(f"config: {config}")
    configurable = Configuration.from_runnable_config(config)
    
    # Idempotency check: Skip if already determined clarification status
    # if state.get("need_clarification") is not None:
    #     return Command(goto="request_human_review")
    
    # Initialize LLM for clarification assessment
    llm = create_model(configurable.query_generator_model, max_tokens=4000, temperature=0.0)
    
    # Use CalarifyCampaignInfoWithHuman for clarification judgment
    structured_llm = llm.with_structured_output(CalarifyCampaignInfoWithHuman)
    formatted_prompt = clarify_campaign_info_with_human_instructions.format(
        messages=get_buffer_string(state["messages"]),
        campaign_basic_info=state["campaign_basic_info"],
    )
    clarify_campaign_info_with_human = structured_llm.invoke(formatted_prompt)
    logger.info(f"🔍 auto_clarify_campaign_info - clarify_campaign_info_with_human response: {clarify_campaign_info_with_human}")
    # Critical Decision: Does AI think clarification is needed?
    if clarify_campaign_info_with_human.need_clarification:
        # End flow with clarification questions for user
        logger.info(f"🔍 auto_clarify_campaign_info - Need clarification: {clarify_campaign_info_with_human.questions}")
        return Command(
            goto="__end__",
            update={
                "messages": [AIMessage(content=caliry_questions_template.format(
                    questions=clarify_campaign_info_with_human.questions,
                    campaign_basic_info=state["campaign_basic_info"])),
                ],
                "need_clarification": True
            }
        )
    else:
        logger.info(f"🔍 auto_clarify_campaign_info - No clarification needed")
        return Command(
            goto="request_human_review",
            update={"need_clarification": False}
        )


def request_human_review(state: AgentState, config: RunnableConfig) -> Command[Literal["generate_campaign_plan", "__end__"]]:
    """
    Node 3: Trigger human review interrupt and process result (HITL core node).
    
    Purpose: Pause execution, request human approval, and route based on decision
    Key Logic: interrupt() returns the resume value directly
    Resume: Command(resume=decision) value becomes interrupt() return value
    """
    logger.info("🔍 Requesting human review")
    configurable = Configuration.from_runnable_config(config)
    
    # Idempotency check: Skip interrupt if already have human result
    if state.get("human_review_compagin_info_result") is not None:
        logger.info(f"🔍 request_human_review - Already reviewed, human_review_compagin_info_result is not None")
        # Already reviewed, route based on previous result
        return Command(goto="generate_campaign_plan" if state["human_review_compagin_info_result"] else "__end__")
    
    # Configuration bypass: Auto-approve if skip is enabled
    if configurable.allow_skip_human_review_campaign_info:
        logger.info(f"🔍 request_human_review - Skip review, allow_skip_human_review_campaign_info is True")
        return Command(
            goto="generate_campaign_plan",
            update={"human_review_compagin_info_result": True}
        )
    
    # CRITICAL: interrupt() pauses execution and returns resume value
    logger.info(f"🔍 request_human_review - Calling interrupt, waiting for human input...")
    human_decision = interrupt({
        "type": "human_review_request",
        "title": "请审核营销活动基本信息",
        "content": f"请审核营销活动基本信息。回复 'yes' 批准或 'no' 拒绝。\n\n当前的营销活动基本信息如下：\n{state['campaign_basic_info']}",
        "campaign_info": state["campaign_basic_info"]  # 提供结构化数据给前端
    })
    
    logger.info(f"🔍 request_human_review - Human decision received: {human_decision}")
    
    # Process the human decision directly from interrupt() return value
    if human_decision:
        # Approved: Continue to campaign plan generation
        logger.info(f"🔍 request_human_review - Human approved, continuing to generate campaign plan")
        return Command(
            goto="generate_campaign_plan",
            update={"human_review_compagin_info_result": True}
        )
    else:
        # Rejected: End flow with feedback message
        logger.info(f"🔍 request_human_review - Human rejected, ending flow")
        return Command(
            goto="__end__",
            update={
                "human_review_compagin_info_result": False,
                "messages": [AIMessage(content="人工审核未通过，请告诉AI应该如何执行？")]
            }
        )

def generate_campaign_plan(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    Node 5: Generate final campaign plan based on approved information.
    
    Purpose: Create actionable campaign plan from validated campaign_basic_info
    Key Logic: Transform approved info into executable campaign strategy
    Final Step: Returns final state, leads to END
    """
    logger.info("🔍 Generating campaign plan based on approved info")
    # logger.info(f"config: {config}")
    
    # TODO: Implement actual campaign plan generation logic
    # For now, return current state (approved info is preserved)
    return state

def create_influencer_marketing_graph() -> StateGraph:
    """Create graph with simplified HITL pattern following LangGraph best practices."""
    builder = StateGraph(AgentState, input=AgentInputState, config_schema=Configuration)
    
    # Add nodes following single-responsibility principle
    builder.add_node("initialize_campaign_info", initialize_campaign_info)
    builder.add_node("auto_clarify_campaign_info", auto_clarify_campaign_info)
    builder.add_node("request_human_review", request_human_review)
    builder.add_node("generate_campaign_plan", generate_campaign_plan)
    
    # Define flow: START -> init -> clarify -> review -> plan -> END
    builder.add_edge(START, "initialize_campaign_info")
    builder.add_edge("initialize_campaign_info", "auto_clarify_campaign_info")
    # request_human_review now handles routing directly using Command(goto=...)
    builder.add_edge("generate_campaign_plan", END)
    
    # LangGraph API automatically provides checkpointer for interrupts
    graph = builder.compile()
    
    logger.info("✅ Graph created with simplified HITL pattern")
    return graph


# Create the main graph instance
graph = create_influencer_marketing_graph()
