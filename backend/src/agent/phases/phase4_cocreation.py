"""
Phase 4: Co-creation - Content script creation and compliance review.
"""

import logging
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END

from agent.state import CampaignState, CocreationState
from agent.state.models import Script
from agent.utils import create_hitl_node

logger = logging.getLogger(__name__)


def draft_script(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Draft content scripts for contracted influencers.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with script drafts
    """
    logger.info("✍️ Drafting content scripts for influencers")
    
    # Get contracts and campaign info
    contracts = state.get("contracts", [])
    objective = state.get("objective", "")
    brand_name = state.get("brand_name", "Brand")
    
    # Brand guidelines
    brand_guidelines = {
        "tone": "friendly and authentic",
        "key_messages": [
            "Quality products for modern lifestyle",
            "Sustainable and ethical practices",
            "Community-focused brand values"
        ],
        "brand_story": f"{brand_name} is committed to creating products that enhance everyday life while supporting sustainable practices.",
        "do_not_mention": ["competitors", "price comparisons", "medical claims"],
        "required_hashtags": [f"#{brand_name.lower()}", "#lifestyle", "#sustainable"]
    }
    
    # Create scripts for each contract
    scripts = []
    for contract in contracts:
        # Get deliverables from contract
        deliverables = contract.deliverables
        
        for deliverable in deliverables:
            # Determine content type
            if "post" in deliverable.lower():
                content_type = "instagram_post"
                platform = "instagram"
            elif "story" in deliverable.lower():
                content_type = "instagram_story"
                platform = "instagram"
            else:
                content_type = "general"
                platform = "instagram"
            
            # Generate script content
            script_content = f"""
            Brand Story Integration:
            {brand_guidelines['brand_story']}
            
            Key Messages to Include:
            {', '.join(brand_guidelines['key_messages'])}
            
            Tone & Voice:
            {brand_guidelines['tone']}
            
            Content Guidelines:
            - Show product in natural, everyday setting
            - Share personal experience with the product
            - Highlight sustainability aspect
            - Include call-to-action for followers
            
            Required Hashtags:
            {' '.join(brand_guidelines['required_hashtags'])}
            
            Content Structure:
            1. Hook: Personal story or relatable situation
            2. Product introduction naturally
            3. Benefits and personal experience
            4. Call-to-action
            5. Hashtags
            
            Compliance Notes:
            - Must include #ad or #sponsored disclosure
            - Cannot make medical or health claims
            - Must follow platform community guidelines
            """.strip()
            
            # Create script object
            script = Script(
                id=f"script_{contract.id}_{content_type}",
                creator_id=contract.creator_id,
                platform=platform,
                content=script_content,
                brand_story=brand_guidelines['brand_story'],
                compliance_status="pending",
                version=1,
                created_at="2024-01-15T16:00:00Z"
            )
            
            scripts.append(script)
    
    logger.info(f"✅ Created {len(scripts)} script drafts")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Script drafts created: {len(scripts)}")
    
    return {
        "scripts": scripts,
        "current_drafts": [
            {
                "script_id": s.id,
                "creator_id": s.creator_id,
                "platform": s.platform,
                "content_length": len(s.content),
                "version": s.version
            }
            for s in scripts
        ],
        "logs": logs
    }


def compliance_scan(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Scan scripts for compliance issues using AI.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with compliance scan results
    """
    logger.info("🛡️ Scanning scripts for compliance issues")
    
    # Get scripts
    scripts = state.get("scripts", [])
    
    # Compliance rules
    compliance_rules = {
        "required_disclosures": ["#ad", "#sponsored", "#partnership"],
        "prohibited_words": ["guaranteed", "miracle", "cure", "instant"],
        "required_elements": ["call-to-action", "hashtags"],
        "platform_guidelines": {
            "instagram": {
                "max_hashtags": 30,
                "disclosure_placement": "beginning"
            }
        }
    }
    
    # Scan each script
    compliance_results = []
    updated_scripts = []
    
    for script in scripts:
        issues = []
        warnings = []
        
        # Check for required disclosures
        has_disclosure = any(
            disclosure in script.content.lower()
            for disclosure in compliance_rules["required_disclosures"]
        )
        
        if not has_disclosure:
            issues.append("Missing required disclosure (#ad, #sponsored, or #partnership)")
        
        # Check for prohibited words
        prohibited_found = [
            word for word in compliance_rules["prohibited_words"]
            if word in script.content.lower()
        ]
        
        if prohibited_found:
            issues.append(f"Contains prohibited words: {', '.join(prohibited_found)}")
        
        # Check for required elements
        if "#" not in script.content:
            warnings.append("No hashtags found")
        
        if "call-to-action" not in script.content.lower():
            warnings.append("No clear call-to-action identified")
        
        # Determine compliance status
        if issues:
            compliance_status = "failed"
        elif warnings:
            compliance_status = "warning"
        else:
            compliance_status = "passed"
        
        # Update script
        script.compliance_status = compliance_status
        updated_scripts.append(script)
        
        # Record results
        compliance_results.append({
            "script_id": script.id,
            "status": compliance_status,
            "issues": issues,
            "warnings": warnings,
            "scan_time": "2024-01-15T16:15:00Z"
        })
    
    # Count results
    passed_count = sum(1 for r in compliance_results if r["status"] == "passed")
    failed_count = sum(1 for r in compliance_results if r["status"] == "failed")
    
    logger.info(f"✅ Compliance scan completed")
    logger.info(f"📊 Results: {passed_count} passed, {failed_count} failed")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Compliance scan completed: {passed_count} passed, {failed_count} failed")
    
    return {
        "scripts": updated_scripts,
        "current_drafts": compliance_results,
        "logs": logs
    }


def route_compliance_result(state: CampaignState) -> str:
    """
    Route based on compliance scan results.
    
    Args:
        state: Current campaign state
        
    Returns:
        Next node name
    """
    compliance_results = state.get("current_drafts", [])
    
    # Check if any scripts failed compliance
    failed_scripts = [r for r in compliance_results if r["status"] == "failed"]
    
    if failed_scripts:
        logger.info(f"🔄 {len(failed_scripts)} scripts failed compliance - returning to draft")
        return "draft_script"
    else:
        logger.info("✅ All scripts passed compliance - proceeding to legal review")
        return "HITL_legal"


def check_revision_limit(state: CampaignState) -> str:
    """
    Check if we've reached the revision limit for scripts.
    
    Args:
        state: Current campaign state
        
    Returns:
        Next node name
    """
    # Get iteration count
    iteration_count = state.get("iteration_count", {})
    cocreation_iterations = iteration_count.get("cocreation", 0)
    
    max_iterations = 3  # Maximum revision attempts
    
    if cocreation_iterations >= max_iterations:
        logger.info(f"⏱️ Reached maximum revision iterations ({max_iterations})")
        return "HITL_legal"
    else:
        logger.info(f"🔄 Revision iteration {cocreation_iterations + 1}/{max_iterations}")
        
        # Update iteration count
        iteration_count["cocreation"] = cocreation_iterations + 1
        
        return "compliance_scan"


def finish_phase4(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Complete Phase 4 and transition to Phase 5.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with phase transition
    """
    logger.info("🏁 Completing Phase 4: Co-creation")
    
    # Update phase
    phase = 5
    
    # Clear temporary draft data
    current_drafts = []
    
    # Add completion log
    logs = state.get("logs", [])
    logs.append("Phase 4 (Co-creation) completed")
    logs.append("Transitioning to Phase 5 (Publish & Boost)")
    
    logger.info("✅ Phase 4 completed successfully")
    logger.info("➡️ Moving to Phase 5: Publish & Boost")
    
    return {
        "phase": phase,
        "current_drafts": current_drafts,
        "logs": logs
    }


def create_cocreation_subgraph() -> StateGraph:
    """
    Create the Co-creation phase subgraph.
    
    Returns:
        Compiled co-creation subgraph
    """
    logger.info("🏗️ Creating Co-creation subgraph")
    
    # Create subgraph
    builder = StateGraph(CampaignState)
    
    # Add nodes
    builder.add_node("draft_script", draft_script)
    builder.add_node("compliance_scan", compliance_scan)
    builder.add_node("HITL_legal", create_hitl_node("legal"))
    builder.add_node("finish_p4", finish_phase4)
    
    # Add edges with conditional routing
    builder.add_edge(START, "draft_script")
    builder.add_edge("draft_script", "compliance_scan")
    builder.add_conditional_edges("compliance_scan", route_compliance_result, ["draft_script", "HITL_legal"])
    builder.add_edge("HITL_legal", "finish_p4")
    builder.add_edge("finish_p4", END)
    
    # Compile subgraph
    subgraph = builder.compile(name="cocreation-phase")
    
    logger.info("✅ Co-creation subgraph created")
    return subgraph


# Export as toolified agent
def create_cocreation_tool():
    """
    Create toolified version of co-creation subgraph.
    
    Returns:
        Co-creation tool for external use
    """
    from langchain_core.tools import tool
    
    @tool
    def cocreation_tool(
        contracts: List[Dict[str, Any]], 
        brand_guidelines: Dict[str, Any],
        objective: str
    ) -> Dict[str, Any]:
        """
        Execute content co-creation process.
        
        Args:
            contracts: List of signed contracts
            brand_guidelines: Brand guidelines and messaging
            objective: Campaign objective
            
        Returns:
            Co-creation results with approved scripts
        """
        logger.info("🔧 Co-creation tool activated")
        
        # Convert contracts to Contract objects
        from agent.state.models import Contract
        contract_objects = [
            Contract(
                id=c.get("id", ""),
                creator_id=c.get("creator_id", ""),
                terms=c.get("terms", {}),
                compensation=c.get("compensation", 0),
                deliverables=c.get("deliverables", []),
                timeline=c.get("timeline", {}),
                status=c.get("status", "draft")
            )
            for c in contracts
        ]
        
        # Create initial state
        state = CampaignState(
            contracts=contract_objects,
            objective=objective,
            brand_name=brand_guidelines.get("brand_name", "Brand"),
            phase=4,
            logs=[],
            scripts=[]
        )
        
        # Execute co-creation subgraph
        subgraph = create_cocreation_subgraph()
        result = subgraph.invoke(state)
        
        logger.info("✅ Co-creation tool completed")
        return result
    
    return cocreation_tool