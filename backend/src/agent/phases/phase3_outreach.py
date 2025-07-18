"""
Phase 3: Outreach - Influencer communication and contract negotiation.
"""

import logging
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END

from agent.state import CampaignState, OutreachState
from agent.tools import EmailAutomation
from agent.state.models import Contract
from agent.utils import create_hitl_node

logger = logging.getLogger(__name__)


def generate_email(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Generate personalized outreach emails for candidates.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with email templates
    """
    logger.info("✍️ Generating personalized outreach emails")
    
    # Get candidates and brand info
    candidates = state.get("candidates", [])
    objective = state.get("objective", "")
    brand_name = state.get("brand_name", "Our Brand")
    
    # Brand information
    brand_info = {
        "name": brand_name,
        "contact_name": "Marketing Team",
        "campaign_type": "lifestyle collaboration",
        "compensation_range": "$500-2000"
    }
    
    # Initialize email automation
    email_automation = EmailAutomation({"smtp_server": "smtp.gmail.com"})
    
    # Generate emails for top candidates
    email_templates = []
    for candidate in candidates[:10]:  # Top 10 candidates
        
        # Create influencer profile for template generation
        influencer_profile = {
            "username": candidate.username,
            "niche": candidate.niche,
            "followers": candidate.followers,
            "engagement_rate": candidate.engagement_rate
        }
        
        # Generate personalized template
        template = email_automation.generate_personalized_template(
            influencer_profile, brand_info
        )
        
        email_templates.append({
            "candidate_id": candidate.id,
            "template": template,
            "status": "draft"
        })
    
    logger.info(f"✅ Generated {len(email_templates)} email templates")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Email templates generated for {len(email_templates)} candidates")
    
    return {
        "current_negotiations": email_templates,
        "logs": logs
    }


def send_and_track(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Send emails and track responses.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with email tracking results
    """
    logger.info("📧 Sending emails and tracking responses")
    
    # Get email templates
    email_templates = state.get("current_negotiations", [])
    candidates = state.get("candidates", [])
    
    # Create candidate lookup
    candidate_lookup = {c.id: c for c in candidates}
    
    # Initialize email automation
    email_automation = EmailAutomation({"smtp_server": "smtp.gmail.com"})
    
    # Send emails
    email_results = []
    email_ids = []
    
    for template_data in email_templates:
        candidate_id = template_data["candidate_id"]
        template = template_data["template"]
        
        # Get candidate data
        candidate = candidate_lookup.get(candidate_id)
        if not candidate:
            continue
            
        # Prepare influencer data
        influencer_data = {
            "id": candidate.id,
            "username": candidate.username,
            "email": candidate.contact_info or f"{candidate.username}@example.com"
        }
        
        # Send email
        send_result = email_automation.send_cold_outreach(influencer_data, template)
        email_results.append(send_result)
        email_ids.append(send_result["email_id"])
    
    # Track responses
    tracking_results = email_automation.track_email_responses(email_ids)
    
    # Update negotiation status
    updated_negotiations = []
    for template_data in email_templates:
        candidate_id = template_data["candidate_id"]
        email_id = f"email_{candidate_id}"
        
        tracking_data = tracking_results.get(email_id, {})
        
        updated_negotiations.append({
            **template_data,
            "email_id": email_id,
            "status": tracking_data.get("status", "sent"),
            "responded": tracking_data.get("replied", False),
            "response_content": tracking_data.get("reply_content")
        })
    
    logger.info(f"✅ Sent {len(email_results)} emails")
    logger.info(f"📊 Tracking {len(tracking_results)} responses")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Emails sent: {len(email_results)}")
    logs.append(f"Responses tracked: {len(tracking_results)}")
    
    return {
        "current_negotiations": updated_negotiations,
        "logs": logs
    }


def negotiate_contract(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Negotiate contracts with responding influencers.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with contract negotiations
    """
    logger.info("🤝 Negotiating contracts with responding influencers")
    
    # Get negotiations
    negotiations = state.get("current_negotiations", [])
    budget = state.get("budget", 0)
    
    # Find responding influencers
    responding_negotiations = [n for n in negotiations if n.get("responded", False)]
    
    logger.info(f"💬 Found {len(responding_negotiations)} responding influencers")
    
    # Create contracts for responding influencers
    contracts = []
    candidates = state.get("candidates", [])
    candidate_lookup = {c.id: c for c in candidates}
    
    for negotiation in responding_negotiations:
        candidate_id = negotiation["candidate_id"]
        candidate = candidate_lookup.get(candidate_id)
        
        if not candidate:
            continue
        
        # Calculate compensation based on follower count and engagement
        base_compensation = 500  # Base rate
        follower_bonus = min(candidate.followers / 10000, 10) * 50  # Max $500 bonus
        engagement_bonus = candidate.engagement_rate * 1000  # Engagement bonus
        
        compensation = base_compensation + follower_bonus + engagement_bonus
        
        # Create contract
        contract = Contract(
            id=f"contract_{candidate_id}",
            creator_id=candidate_id,
            terms={
                "content_type": "instagram_post",
                "deliverables": ["1 feed post", "3 stories"],
                "usage_rights": "6 months",
                "exclusivity": "30 days"
            },
            compensation=compensation,
            deliverables=["1 feed post", "3 stories"],
            timeline={
                "content_due": "2024-02-01",
                "revision_deadline": "2024-02-03",
                "go_live": "2024-02-05"
            },
            status="draft"
        )
        
        contracts.append(contract)
    
    logger.info(f"✅ Created {len(contracts)} contract drafts")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Contract negotiations started: {len(contracts)} drafts")
    
    return {
        "contracts": contracts,
        "logs": logs
    }


def route_negotiation_response(state: CampaignState) -> str:
    """
    Route based on negotiation responses.
    
    Args:
        state: Current campaign state
        
    Returns:
        Next node name
    """
    negotiations = state.get("current_negotiations", [])
    
    # Check if we have any responses
    responding_count = sum(1 for n in negotiations if n.get("responded", False))
    
    if responding_count > 0:
        logger.info(f"📈 {responding_count} influencers responded - proceeding to contract negotiation")
        return "negotiate_contract"
    else:
        logger.info("📭 No responses yet - sending follow-up emails")
        return "send_followup"


def send_followup(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Send follow-up emails to non-responding influencers.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with follow-up results
    """
    logger.info("🔄 Sending follow-up emails")
    
    # Get non-responding negotiations
    negotiations = state.get("current_negotiations", [])
    non_responding = [n for n in negotiations if not n.get("responded", False)]
    
    # Initialize email automation
    email_automation = EmailAutomation({"smtp_server": "smtp.gmail.com"})
    
    # Send follow-ups
    followup_results = []
    for negotiation in non_responding:
        email_data = {
            "email_id": negotiation.get("email_id"),
            "candidate_id": negotiation.get("candidate_id")
        }
        
        result = email_automation.auto_followup(email_data)
        followup_results.append(result)
    
    # Update iteration count
    iteration_count = state.get("iteration_count", {})
    iteration_count["outreach"] = iteration_count.get("outreach", 0) + 1
    
    logger.info(f"✅ Sent {len(followup_results)} follow-up emails")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Follow-up emails sent: {len(followup_results)}")
    
    return {
        "iteration_count": iteration_count,
        "logs": logs
    }


def check_iteration_limit(state: CampaignState) -> str:
    """
    Check if we've reached the iteration limit for outreach.
    
    Args:
        state: Current campaign state
        
    Returns:
        Next node name
    """
    # Get iteration count
    iteration_count = state.get("iteration_count", {})
    outreach_iterations = iteration_count.get("outreach", 0)
    
    max_iterations = 3  # Maximum outreach attempts
    
    if outreach_iterations >= max_iterations:
        logger.info(f"⏱️ Reached maximum outreach iterations ({max_iterations})")
        return "negotiate_contract"
    else:
        logger.info(f"🔄 Outreach iteration {outreach_iterations + 1}/{max_iterations}")
        return "send_and_track"


def finish_phase3(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Complete Phase 3 and transition to Phase 4.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with phase transition
    """
    logger.info("🏁 Completing Phase 3: Outreach")
    
    # Update phase
    phase = 4
    
    # Clear temporary negotiation data
    current_negotiations = []
    
    # Add completion log
    logs = state.get("logs", [])
    logs.append("Phase 3 (Outreach) completed")
    logs.append("Transitioning to Phase 4 (Co-creation)")
    
    logger.info("✅ Phase 3 completed successfully")
    logger.info("➡️ Moving to Phase 4: Co-creation")
    
    return {
        "phase": phase,
        "current_negotiations": current_negotiations,
        "logs": logs
    }


def create_outreach_subgraph() -> StateGraph:
    """
    Create the Outreach phase subgraph.
    
    Returns:
        Compiled outreach subgraph
    """
    logger.info("🏗️ Creating Outreach subgraph")
    
    # Create subgraph
    builder = StateGraph(CampaignState)
    
    # Add nodes
    builder.add_node("generate_email", generate_email)
    builder.add_node("send_and_track", send_and_track)
    builder.add_node("send_followup", send_followup)
    builder.add_node("negotiate_contract", negotiate_contract)
    builder.add_node("HITL_contract_review", create_hitl_node("contract"))
    builder.add_node("finish_p3", finish_phase3)
    
    # Add edges with conditional routing
    builder.add_edge(START, "generate_email")
    builder.add_edge("generate_email", "send_and_track")
    builder.add_conditional_edges("send_and_track", route_negotiation_response, ["negotiate_contract", "send_followup"])
    builder.add_conditional_edges("send_followup", check_iteration_limit, ["send_and_track", "negotiate_contract"])
    builder.add_edge("negotiate_contract", "HITL_contract_review")
    builder.add_edge("HITL_contract_review", "finish_p3")
    builder.add_edge("finish_p3", END)
    
    # Compile subgraph
    subgraph = builder.compile(name="outreach-phase")
    
    logger.info("✅ Outreach subgraph created")
    return subgraph


# Export as toolified agent
def create_outreach_tool():
    """
    Create toolified version of outreach subgraph.
    
    Returns:
        Outreach tool for external use
    """
    from langchain_core.tools import tool
    
    @tool
    def outreach_tool(
        candidates: List[Dict[str, Any]], 
        brand_info: Dict[str, Any],
        budget: float
    ) -> Dict[str, Any]:
        """
        Execute influencer outreach process.
        
        Args:
            candidates: List of candidate influencers
            brand_info: Brand information for personalization
            budget: Available budget for contracts
            
        Returns:
            Outreach results with signed contracts
        """
        logger.info("🔧 Outreach tool activated")
        
        # Convert candidates to Creator objects
        from agent.state.models import Creator
        creator_candidates = [
            Creator(
                id=c.get("id", ""),
                username=c.get("username", ""),
                platform=c.get("platform", ""),
                followers=c.get("followers", 0),
                engagement_rate=c.get("engagement_rate", 0),
                niche=c.get("niche", ""),
                audience_demographics=c.get("audience_demographics", {}),
                contact_info=c.get("contact_info", ""),
                historical_performance=c.get("historical_performance", {}),
                fraud_score=c.get("fraud_score", 0),
                match_score=c.get("match_score", 0)
            )
            for c in candidates
        ]
        
        # Create initial state
        state = CampaignState(
            candidates=creator_candidates,
            brand_name=brand_info.get("name", "Brand"),
            budget=budget,
            phase=3,
            logs=[],
            contracts=[]
        )
        
        # Execute outreach subgraph
        subgraph = create_outreach_subgraph()
        result = subgraph.invoke(state)
        
        logger.info("✅ Outreach tool completed")
        return result
    
    return outreach_tool