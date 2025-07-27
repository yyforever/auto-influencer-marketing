"""
Logging utilities for campaign management.
"""

import logging
import os
from typing import Dict, Any, List
from datetime import datetime


def _get_log_level() -> int:
    """Get log level from environment variable with fallback to INFO."""
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, log_level_str, logging.INFO)


def setup_campaign_logging(campaign_id: str) -> logging.Logger:
    """
    Set up logging for a campaign with robust handler management.
    
    This function ensures that:
    1. No duplicate handlers are added
    2. Clean configuration even if external code modified the logger
    3. Proper isolation from parent loggers
    4. Thread-safe operation
    
    Args:
        campaign_id: Campaign identifier
        
    Returns:
        Configured logger
    """
    logger_name = f"campaign.{campaign_id}"
    logger = logging.getLogger(logger_name)
    
    # Use a more robust configuration tracking mechanism
    expected_handler_signature = f"campaign_handler_{campaign_id}"
    
    # Check if logger is already properly configured
    if hasattr(logger, '_campaign_handler_signature') and \
       logger._campaign_handler_signature == expected_handler_signature:
        # Verify the handler is still there and properly configured
        if len(logger.handlers) == 1 and \
           hasattr(logger.handlers[0], '_campaign_signature') and \
           logger.handlers[0]._campaign_signature == expected_handler_signature:
            return logger
    
    # Clean slate: remove ALL existing handlers (including external ones)
    for handler in logger.handlers[:]:
        try:
            handler.close()  # Properly close file handlers, etc.
        except (AttributeError, OSError):
            pass  # Some handlers don't support close()
        logger.removeHandler(handler)
    
    # Configure logger properties
    log_level = _get_log_level()
    logger.setLevel(log_level)
    
    # Prevent propagation to avoid duplicate logs in parent loggers
    # This is crucial for campaign-specific logging
    logger.propagate = False
    
    # Create formatter with more detailed information
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Mark the handler with our signature for verification
    console_handler._campaign_signature = expected_handler_signature
    
    # Add the handler
    logger.addHandler(console_handler)
    
    # Mark logger as properly configured with our signature
    logger._campaign_handler_signature = expected_handler_signature
    
    logger.info(f"📊 Campaign logging initialized for: {campaign_id}")
    return logger


def reset_campaign_logging(campaign_id: str) -> None:
    """
    Reset campaign logging configuration.
    
    Useful for testing or when logger reconfiguration is needed.
    This function provides a clean slate for logger reconfiguration.
    
    Args:
        campaign_id: Campaign identifier
    """
    logger_name = f"campaign.{campaign_id}"
    logger = logging.getLogger(logger_name)
    
    # Remove all handlers with proper cleanup
    for handler in logger.handlers[:]:
        try:
            handler.close()  # Properly close file handlers, streams, etc.
        except (AttributeError, OSError):
            pass  # Some handlers don't support close()
        logger.removeHandler(handler)
    
    # Remove configuration markers
    if hasattr(logger, '_campaign_handler_signature'):
        delattr(logger, '_campaign_handler_signature')
    if hasattr(logger, '_campaign_configured'):  # Legacy marker
        delattr(logger, '_campaign_configured')
    
    # Reset logger properties to defaults
    logger.setLevel(logging.NOTSET)
    logger.propagate = True  # Reset to default propagation


def log_phase_transition(
    logger: logging.Logger,
    from_phase: int,
    to_phase: int,
    state: Dict[str, Any]
) -> List[str]:
    """
    Log phase transition with state summary.
    
    Args:
        logger: Campaign logger
        from_phase: Previous phase number
        to_phase: Next phase number
        state: Current campaign state
        
    Returns:
        Updated logs list
    """
    phase_names = {
        1: "Strategy",
        2: "Discovery", 
        3: "Outreach",
        4: "Co-creation",
        5: "Publish & Boost",
        6: "Monitor & Optimize",
        7: "Settle & Archive"
    }
    
    from_name = phase_names.get(from_phase, f"Phase {from_phase}")
    to_name = phase_names.get(to_phase, f"Phase {to_phase}")
    
    logger.info(f"🔄 Phase transition: {from_name} → {to_name}")
    
    # Log key state metrics
    metrics = {
        "candidates_count": len(state.get("candidates", [])),
        "contracts_count": len(state.get("contracts", [])),
        "scripts_count": len(state.get("scripts", [])),
        "posts_count": len(state.get("posts", [])),
        "current_budget": state.get("budget", 0)
    }
    
    logger.info(f"📈 State metrics: {metrics}")
    
    # Update logs in state
    logs = state.get("logs", [])
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] Phase transition: {from_name} → {to_name}"
    logs.append(log_entry)
    
    return logs


def log_node_execution(
    logger: logging.Logger,
    node_name: str,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    execution_time: float
) -> None:
    """
    Log node execution details.
    
    Args:
        logger: Campaign logger
        node_name: Name of the executed node
        input_data: Node input data
        output_data: Node output data
        execution_time: Execution time in seconds
    """
    logger.info(f"⚙️ Node executed: {node_name}")
    logger.info(f"⏱️ Execution time: {execution_time:.2f}s")
    
    # Log input summary
    if input_data:
        input_summary = {k: len(v) if isinstance(v, list) else str(v)[:100] 
                        for k, v in input_data.items()}
        logger.info(f"📥 Input summary: {input_summary}")
    
    # Log output summary
    if output_data:
        output_summary = {k: len(v) if isinstance(v, list) else str(v)[:100] 
                         for k, v in output_data.items()}
        logger.info(f"📤 Output summary: {output_summary}")


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Dict[str, Any],
    node_name: str = None
) -> None:
    """
    Log error with context information.
    
    Args:
        logger: Campaign logger
        error: Exception that occurred
        context: Additional context information
        node_name: Name of the node where error occurred
    """
    error_msg = f"❌ Error in {node_name or 'unknown node'}: {str(error)}"
    logger.error(error_msg)
    
    if context:
        context_summary = {k: str(v)[:200] for k, v in context.items()}
        logger.error(f"🔍 Error context: {context_summary}")
    
    logger.error(f"📋 Error type: {type(error).__name__}")


def log_performance_metrics(
    logger: logging.Logger,
    metrics: Dict[str, Any],
    phase: int
) -> None:
    """
    Log performance metrics for a phase.
    
    Args:
        logger: Campaign logger
        metrics: Performance metrics
        phase: Current phase number
    """
    logger.info(f"📊 Phase {phase} Performance Metrics:")
    
    for metric_name, value in metrics.items():
        if isinstance(value, (int, float)):
            logger.info(f"  {metric_name}: {value}")
        else:
            logger.info(f"  {metric_name}: {str(value)[:100]}")


def log_budget_changes(
    logger: logging.Logger,
    old_budget: float,
    new_budget: float,
    reason: str
) -> None:
    """
    Log budget changes with reason.
    
    Args:
        logger: Campaign logger
        old_budget: Previous budget amount
        new_budget: New budget amount
        reason: Reason for budget change
    """
    change = new_budget - old_budget
    change_type = "increase" if change > 0 else "decrease"
    
    logger.info(f"💰 Budget {change_type}: ${old_budget:.2f} → ${new_budget:.2f}")
    logger.info(f"📝 Reason: {reason}")
    logger.info(f"💵 Change amount: ${abs(change):.2f}")


def create_campaign_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a summary of the campaign state.
    
    Args:
        state: Current campaign state
        
    Returns:
        Campaign summary
    """
    summary = {
        "campaign_id": state.get("campaign_id", "unknown"),
        "current_phase": state.get("phase", 1),
        "objective": state.get("objective", "not_set"),
        "budget": state.get("budget", 0),
        "metrics": {
            "candidates": len(state.get("candidates", [])),
            "contracts": len(state.get("contracts", [])),
            "scripts": len(state.get("scripts", [])),
            "posts": len(state.get("posts", [])),
            "settlements": len(state.get("settlements", []))
        },
        "total_logs": len(state.get("logs", [])),
        "approvals": len(state.get("approvals", {})),
        "last_updated": datetime.now().isoformat()
    }
    
    return summary