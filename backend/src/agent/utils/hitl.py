"""
Human-in-the-Loop (HITL) utilities for campaign management.
"""

import logging
from typing import Dict, Any, Literal, Optional, Callable
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

logger = logging.getLogger(__name__)

# Valid review types
VALID_REVIEW_TYPES = ["strategy", "contract", "legal", "budget"]
VALID_DECISIONS = ["approve", "revise", "reject"]


class HITLInterrupt:
    """Human-in-the-Loop interrupt for critical decision points"""
    
    @staticmethod
    def interrupt_for_review(
        state: Dict[str, Any], 
        review_type: Literal["strategy", "contract", "legal", "budget"],
        data_to_review: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create HITL interrupt for human review.
        
        Args:
            state: Current campaign state
            review_type: Type of review needed
            data_to_review: Data that needs human review
            
        Returns:
            Updated state with interrupt information
        """
        logger.info(f"🛑 HITL Interrupt requested for: {review_type}")
        logger.info(f"📋 Review data: {data_to_review}")
        
        # Prepare interrupt data
        interrupt_data = {
            "interrupt_type": review_type,
            "review_data": data_to_review,
            "timestamp": "2024-01-15T14:30:00Z",
            "status": "pending_review"
        }
        
        # Add to state logs
        logs = state.get("logs", [])
        logs.append(f"HITL interrupt created: {review_type}")
        
        # Create actual LangGraph interrupt
        interrupt(f"Review required for {review_type}")
        
        logger.info(f"✅ HITL interrupt created: {interrupt_data}")
        return {
            "logs": logs,
            "hitl_interrupt": interrupt_data
        }


class HITLApproval:
    """Handle HITL approval responses"""
    
    @staticmethod
    def process_approval(
        state: Dict[str, Any],
        approval_type: Literal["strategy", "contract", "legal", "budget"],
        decision: Literal["approve", "revise", "reject"],
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process human approval decision.
        
        Args:
            state: Current campaign state
            approval_type: Type of approval
            decision: Human decision
            feedback: Optional feedback from human reviewer
            
        Returns:
            Updated state with approval information
        """
        logger.info(f"✅ Processing HITL approval: {approval_type}")
        logger.info(f"🎯 Decision: {decision}")
        if feedback:
            logger.info(f"💬 Feedback: {feedback}")
        
        # Record approval in state
        approvals = state.get("approvals", {})
        approvals[approval_type] = {
            "decision": decision,
            "feedback": feedback,
            "timestamp": "2024-01-15T14:45:00Z",
            "reviewer": "human_reviewer"
        }
        
        # Add to logs
        logs = state.get("logs", [])
        logs.append(f"HITL approval processed: {approval_type} -> {decision}")
        
        # Determine next action based on decision
        next_action = HITLApproval._determine_next_action(approval_type, decision)
        
        logger.info(f"➡️ Next action: {next_action}")
        
        return {
            "approvals": approvals,
            "logs": logs,
            "next_action": next_action
        }
    
    @staticmethod
    def _determine_next_action(
        approval_type: str, 
        decision: str
    ) -> str:
        """
        Determine next action based on approval decision.
        
        Args:
            approval_type: Type of approval
            decision: Human decision
            
        Returns:
            Next action to take
        """
        action_map = {
            "strategy": {
                "approve": "proceed_to_discovery",
                "revise": "revise_strategy",
                "reject": "halt_campaign"
            },
            "contract": {
                "approve": "proceed_to_cocreation",
                "revise": "revise_contract",
                "reject": "find_alternative_influencer"
            },
            "legal": {
                "approve": "proceed_to_publish",
                "revise": "revise_content",
                "reject": "halt_content_creation"
            },
            "budget": {
                "approve": "proceed_with_budget_increase",
                "revise": "adjust_budget_allocation",
                "reject": "maintain_current_budget"
            }
        }
        
        return action_map.get(approval_type, {}).get(decision, "unknown_action")
    
    @staticmethod
    def _extract_review_data(state: Dict[str, Any], review_type: str) -> Dict[str, Any]:
        """
        Extract relevant data for human review.
        
        Args:
            state: Current campaign state
            review_type: Type of review
            
        Returns:
            Data to be reviewed by human
        """
        extraction_map = {
            "strategy": {
                "objective": state.get("objective"),
                "budget": state.get("budget"),
                "kpi": state.get("kpi"),
                "target_audience": state.get("target_audience")
            },
            "contract": {
                "contracts": state.get("contracts", []),
                "current_negotiations": state.get("current_negotiations", [])
            },
            "legal": {
                "scripts": state.get("scripts", []),
                "compliance_results": state.get("current_drafts", [])
            },
            "budget": {
                "current_budget": state.get("budget"),
                "performance": state.get("performance", {}),
                "optimization_decisions": state.get("optimization_decisions", [])
            }
        }
        
        return extraction_map.get(review_type, {})


def create_hitl_node(review_type: str, auto_approve: bool = True) -> Callable[[Dict[str, Any], RunnableConfig], Dict[str, Any]]:
    """
    Factory function to create HITL nodes for different review types.
    
    Args:
        review_type: Type of review (strategy, contract, legal, budget)
        auto_approve: Whether to auto-approve for demo mode (default: True)
        
    Returns:
        HITL node function
        
    Raises:
        ValueError: If review_type is not valid
    """
    if review_type not in VALID_REVIEW_TYPES:
        raise ValueError(f"Invalid review_type: {review_type}. Must be one of {VALID_REVIEW_TYPES}")
    
    logger.info(f"🏗️ Creating HITL node for {review_type} review (auto_approve: {auto_approve})")
    def hitl_node(state: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """
        HITL node implementation.
        
        Args:
            state: Current campaign state
            config: Runnable configuration
            
        Returns:
            Updated state after HITL review
        """
        logger.info(f"🔍 HITL {review_type} review node activated")
        
        # Extract relevant data for review
        review_data = HITLApproval._extract_review_data(state, review_type)
        
        # Create interrupt - this will actually pause execution if in production mode
        interrupt_result = HITLInterrupt.interrupt_for_review(
            state, review_type, review_data
        )
        
        # Handle approval based on mode
        if auto_approve:
            # Demo mode: auto-approve most reviews
            decision = "approve" if review_type != "budget" else "revise"
            feedback = f"Auto-{decision}d in demo mode"
            
            approval_result = HITLApproval.process_approval(
                state, review_type, decision, feedback
            )
            
            # Merge results
            updated_state = {**interrupt_result, **approval_result}
            
            logger.info(f"✅ HITL {review_type} review completed: {decision}")
            return updated_state
        else:
            # Production mode: return state and wait for human input
            # The interrupt will pause execution here
            logger.info(f"⏳ HITL {review_type} review waiting for human input")
            return interrupt_result
    
    return hitl_node


def handle_human_input(
    state: Dict[str, Any],
    review_type: Literal["strategy", "contract", "legal", "budget"],
    decision: Literal["approve", "revise", "reject"],
    feedback: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handle human input for HITL approval.
    
    This function should be called to resume execution after a HITL interrupt.
    
    Args:
        state: Current campaign state
        review_type: Type of review that was interrupted
        decision: Human decision
        feedback: Optional feedback from human reviewer
        
    Returns:
        Updated state with human approval
        
    Raises:
        ValueError: If review_type or decision is invalid
    """
    # Validate inputs
    if review_type not in VALID_REVIEW_TYPES:
        raise ValueError(f"Invalid review_type: {review_type}. Must be one of {VALID_REVIEW_TYPES}")
    
    if decision not in VALID_DECISIONS:
        raise ValueError(f"Invalid decision: {decision}. Must be one of {VALID_DECISIONS}")
    
    logger.info(f"👤 Processing human input for {review_type} review")
    logger.info(f"🎯 Decision: {decision}")
    if feedback:
        logger.info(f"💬 Feedback: {feedback}")
    
    # Process the human approval
    approval_result = HITLApproval.process_approval(
        state, review_type, decision, feedback
    )
    
    # Clear any pending interrupts
    approval_result["hitl_interrupt"] = None
    
    logger.info(f"✅ Human input processed: {decision}")
    return approval_result


def get_pending_reviews(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Get any pending HITL reviews from the state.
    
    Args:
        state: Current campaign state
        
    Returns:
        Pending interrupt data if any, None otherwise
    """
    interrupt_data = state.get("hitl_interrupt")
    if interrupt_data and interrupt_data.get("status") == "pending_review":
        return interrupt_data
    return None