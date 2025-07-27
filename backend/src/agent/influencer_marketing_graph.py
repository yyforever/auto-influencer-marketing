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
from langchain_google_genai import ChatGoogleGenerativeAI

# Import state management
from agent.state.states import AgentInputState, AgentState, CampaignState
from agent.configuration import Configuration
from agent.prompts.instructions import campaign_info_extraction_instructions, clarify_campaign_info_with_human_instructions, caliry_questions_template

# Import utilities
from agent.utils import setup_campaign_logging, log_phase_transition

# Load environment variables
load_dotenv()

# Validate required environment variables
if os.getenv("GEMINI_API_KEY") is None:
    raise ValueError("GEMINI_API_KEY is not set")

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
    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,
        temperature=0.1,
        max_retries=2,
        timeout=60,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
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
    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
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


def request_human_review(state: AgentState, config: RunnableConfig) -> None:
    """
    Node 3: Trigger human review interrupt (HITL core node).
    
    Purpose: Pause execution and request human approval for campaign info
    Key Logic: interrupt() call MUST be last line - execution stops here
    Resume: Graph will restart from apply_human_review_result node
    """
    logger.info("🔍 Requesting human review")
    # logger.info(f"config: {config}")
    configurable = Configuration.from_runnable_config(config)
    
    # Idempotency check: Skip interrupt if already have human result
    if state.get("human_review_compagin_info_result") is not None:
        logger.info(f"🔍 request_human_review - Already reviewed, human_review_compagin_info_result is not None")
        return  # Already reviewed, will resume to next node
    
    # Configuration bypass: Skip review if configured to do so
    if configurable.allow_skip_human_review_campaign_info:
        logger.info(f"🔍 request_human_review - Skip review, allow_skip_human_review_campaign_info is True")
        return  # Skip review, next node will handle this case
    
    # CRITICAL: interrupt() pauses execution, waits for human input
    # No code should follow this line - execution stops here
    interrupt({
        "type": "human_review_request",
        "title": "请审核营销活动基本信息",
        # "message": "请审核营销活动基本信息。回复 'yes' 批准或 'no' 拒绝。",
        "content": "请审核营销活动基本信息。回复 'yes' 批准或 'no' 拒绝。\n 当前的营销活动基本信息如下：\n {campaign_basic_info}",
        # "campaign_basic_info": state["campaign_basic_info"]
    })


def apply_human_review_result(state: AgentState, config: RunnableConfig) -> Command[Literal["generate_campaign_plan", "__end__"]]:
    """
    Node 4: Process human review decision and route to next step.
    
    Purpose: Handle resume after interrupt, normalize response, make routing decision
    Key Logic: "yes" -> continue to plan generation, "no" -> end with feedback
    Resume Point: This runs when human provides input via Command(resume=...)
    """
    logger.info("🔍 Applying human review result")
    # logger.info(f"config: {config}")
    configurable = Configuration.from_runnable_config(config)
    
    # Configuration bypass: Auto-approve if skip is enabled
    if configurable.allow_skip_human_review_campaign_info:
        logger.info(f"🔍 apply_human_review_result - Skip review, allow_skip_human_review_campaign_info is True")
        return Command(
            goto="generate_campaign_plan",
            update={"human_review_compagin_info_result": "yes"}
        )
    
    # Get human review result from resume payload
    human_review_result = state.get("human_review_compagin_info_result")
    
    # Safety check: Handle missing review result
    if human_review_result is None:
        logger.info(f"🔍 apply_human_review_result - No human review result, will end flow")
        return Command(
            goto="__end__", 
            update={"messages": [AIMessage(content="审核超时或无效输入")]}
        )
    
    # Critical routing decision based on human approval
    if human_review_result:
        # Approved: Continue to campaign plan generation
        logger.info(f"🔍 apply_human_review_result - Human review result is True, will continue to generate campaign plan")
        return Command(goto="generate_campaign_plan")
    else:
        # Rejected: End flow with feedback message
        logger.info(f"🔍 apply_human_review_result - Human review result is False, will end flow")
        return Command(
            goto="__end__",
            update={"messages": [AIMessage(content="审核未通过，请补充或修改信息后重新提交")]}
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
    """Create graph with 3-node HITL pattern following LangGraph best practices."""
    builder = StateGraph(AgentState, input=AgentInputState, config_schema=Configuration)
    
    # Add nodes following single-responsibility principle
    builder.add_node("initialize_campaign_info", initialize_campaign_info)
    builder.add_node("auto_clarify_campaign_info", auto_clarify_campaign_info)
    builder.add_node("request_human_review", request_human_review)
    builder.add_node("apply_human_review_result", apply_human_review_result)
    builder.add_node("generate_campaign_plan", generate_campaign_plan)
    
    # Define flow: START -> init -> clarify -> review -> apply -> plan -> END
    builder.add_edge(START, "initialize_campaign_info")
    builder.add_edge("initialize_campaign_info", "auto_clarify_campaign_info")
    builder.add_edge("request_human_review", "apply_human_review_result")
    builder.add_edge("generate_campaign_plan", END)
    
    # LangGraph API automatically provides checkpointer for interrupts
    graph = builder.compile()
    
    logger.info("✅ Graph created with 3-node HITL pattern")
    return graph


# Create the main graph instance
graph = create_influencer_marketing_graph()
