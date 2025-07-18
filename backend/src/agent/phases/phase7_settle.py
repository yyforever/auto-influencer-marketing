"""
Phase 7: Settle & Archive - Campaign finalization and asset management.
"""

import logging
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END

from agent.state import CampaignState, SettleState
from agent.tools import InfluencityAPI
from agent.state.models import Invoice

logger = logging.getLogger(__name__)


def generate_invoice_pool(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Generate invoice pool for influencer payments.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with invoice pool
    """
    logger.info("🧾 Generating invoice pool for payments")
    
    # Get contracts and performance data
    contracts = state.get("contracts", [])
    performance_metrics = state.get("performance", {})
    
    # Generate invoices for each contract
    invoices = []
    for contract in contracts:
        # Calculate final payment based on performance
        base_compensation = contract.compensation
        performance_bonus = 0
        
        # Find related posts and calculate bonus
        posts = state.get("posts", [])
        creator_posts = [p for p in posts if p.creator_id == contract.creator_id]
        
        if creator_posts:
            # Calculate performance bonus based on engagement
            total_engagement = 0
            for post in creator_posts:
                metric = performance_metrics.get(post.id)
                if metric:
                    total_engagement += metric.likes + metric.shares + metric.comments
            
            # Performance bonus: $1 per 1000 engagement points
            performance_bonus = min(total_engagement / 1000, base_compensation * 0.2)
        
        final_amount = base_compensation + performance_bonus
        
        # Create invoice
        invoice = Invoice(
            id=f"invoice_{contract.id}",
            creator_id=contract.creator_id,
            amount=final_amount,
            currency="USD",
            status="pending",
            payment_method="bank_transfer",
            created_at="2024-01-20T16:00:00Z"
        )
        
        invoices.append(invoice)
    
    # Calculate total payment amount
    total_amount = sum(invoice.amount for invoice in invoices)
    
    logger.info(f"✅ Generated {len(invoices)} invoices")
    logger.info(f"💰 Total payment amount: ${total_amount:.2f}")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Invoice pool generated: {len(invoices)} invoices, ${total_amount:.2f} total")
    
    return {
        "settlements": invoices,
        "logs": logs
    }


def bulk_payment(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Process bulk payments to influencers.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with payment processing results
    """
    logger.info("💸 Processing bulk payments")
    
    # Get invoices
    invoices = state.get("settlements", [])
    
    if not invoices:
        logger.warning("⚠️ No invoices found for payment processing")
        return {"logs": state.get("logs", []) + ["No invoices to process"]}
    
    # Prepare payment pool for Influencity API
    payment_pool = []
    for invoice in invoices:
        payment_data = {
            "invoice_id": invoice.id,
            "creator_id": invoice.creator_id,
            "amount": invoice.amount,
            "currency": invoice.currency,
            "payment_method": invoice.payment_method
        }
        payment_pool.append(payment_data)
    
    # Use Influencity API for bulk payment
    api = InfluencityAPI("demo_key")
    payment_result = api.bulk_payment_processing(payment_pool)
    
    # Update invoice statuses
    successful_payments = payment_result.get("successful_payments", 0)
    failed_payments = payment_result.get("failed_payments", 0)
    transaction_ids = payment_result.get("transaction_ids", [])
    
    # Update invoice statuses
    updated_invoices = []
    for i, invoice in enumerate(invoices):
        if i < successful_payments:
            invoice.status = "paid"
            invoice.paid_at = "2024-01-20T16:30:00Z"
        else:
            invoice.status = "failed"
        updated_invoices.append(invoice)
    
    logger.info(f"✅ Payment processing completed")
    logger.info(f"📊 Results: {successful_payments} successful, {failed_payments} failed")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Bulk payment processed: {successful_payments} successful, {failed_payments} failed")
    
    return {
        "settlements": updated_invoices,
        "logs": logs
    }


def archive_assets(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Archive campaign assets to cloud storage.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with archival results
    """
    logger.info("📦 Archiving campaign assets")
    
    # Get campaign assets
    scripts = state.get("scripts", [])
    posts = state.get("posts", [])
    performance_metrics = state.get("performance", {})
    
    # Create archive manifest
    archive_manifest = {
        "campaign_id": state.get("campaign_id", "unknown"),
        "archive_date": "2024-01-20T17:00:00Z",
        "assets": {
            "scripts": len(scripts),
            "posts": len(posts),
            "metrics": len(performance_metrics)
        },
        "storage_location": "s3://campaign-assets/archive/",
        "retention_period": "7_years"
    }
    
    # Simulate archival process
    archived_items = []
    
    # Archive scripts
    for script in scripts:
        archived_items.append({
            "type": "script",
            "id": script.id,
            "path": f"s3://campaign-assets/archive/scripts/{script.id}.json",
            "size": len(script.content)
        })
    
    # Archive post links
    for post in posts:
        archived_items.append({
            "type": "post_link",
            "id": post.id,
            "path": f"s3://campaign-assets/archive/posts/{post.id}.json",
            "platform": post.platform
        })
    
    # Archive performance metrics
    for post_id, metric in performance_metrics.items():
        archived_items.append({
            "type": "metrics",
            "id": post_id,
            "path": f"s3://campaign-assets/archive/metrics/{post_id}.json",
            "timestamp": metric.timestamp
        })
    
    logger.info(f"✅ Archived {len(archived_items)} assets")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Asset archival completed: {len(archived_items)} items")
    
    return {
        "archive_manifest": archive_manifest,
        "logs": logs
    }


def update_creator_db(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Update creator database with campaign performance data.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with database update results
    """
    logger.info("🗄️ Updating creator database")
    
    # Get campaign data
    candidates = state.get("candidates", [])
    contracts = state.get("contracts", [])
    performance_metrics = state.get("performance", {})
    
    # Update creator profiles with performance data
    updated_profiles = []
    
    for candidate in candidates:
        # Check if creator was contracted
        creator_contract = next((c for c in contracts if c.creator_id == candidate.id), None)
        
        if creator_contract:
            # Find creator's posts
            posts = state.get("posts", [])
            creator_posts = [p for p in posts if p.creator_id == candidate.id]
            
            # Calculate performance metrics
            total_views = 0
            total_engagement = 0
            
            for post in creator_posts:
                metric = performance_metrics.get(post.id)
                if metric:
                    total_views += metric.views
                    total_engagement += metric.likes + metric.shares + metric.comments
            
            # Update creator profile
            profile_update = {
                "creator_id": candidate.id,
                "campaign_performance": {
                    "total_views": total_views,
                    "total_engagement": total_engagement,
                    "engagement_rate": total_engagement / total_views if total_views > 0 else 0,
                    "collaboration_rating": 5.0,  # Default rating
                    "campaign_date": "2024-01-20"
                },
                "updated_at": "2024-01-20T17:15:00Z"
            }
            
            updated_profiles.append(profile_update)
    
    logger.info(f"✅ Updated {len(updated_profiles)} creator profiles")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append(f"Creator database updated: {len(updated_profiles)} profiles")
    
    return {
        "logs": logs
    }


def generate_final_report(state: CampaignState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Generate final campaign report.
    
    Args:
        state: Current campaign state
        config: Runnable configuration
        
    Returns:
        Updated state with final report
    """
    logger.info("📊 Generating final campaign report")
    
    # Get campaign data
    objective = state.get("objective", "")
    budget = state.get("budget", 0)
    kpi = state.get("kpi", {})
    candidates = state.get("candidates", [])
    contracts = state.get("contracts", [])
    posts = state.get("posts", [])
    performance_metrics = state.get("performance", {})
    settlements = state.get("settlements", [])
    
    # Calculate campaign metrics
    total_reach = sum(metric.views for metric in performance_metrics.values())
    total_engagement = sum(metric.likes + metric.shares + metric.comments for metric in performance_metrics.values())
    average_engagement_rate = sum(metric.engagement_rate for metric in performance_metrics.values()) / len(performance_metrics) if performance_metrics else 0
    total_spent = sum(settlement.amount for settlement in settlements)
    
    # Calculate ROI
    roi = (total_reach * 0.01) / total_spent if total_spent > 0 else 0  # Simplified ROI calculation
    
    # Generate final report
    final_report = {
        "campaign_summary": {
            "objective": objective,
            "budget": budget,
            "total_spent": total_spent,
            "roi": roi
        },
        "performance_metrics": {
            "total_reach": total_reach,
            "total_engagement": total_engagement,
            "average_engagement_rate": average_engagement_rate,
            "posts_published": len(posts),
            "platforms_used": len(set(post.platform for post in posts))
        },
        "influencer_metrics": {
            "candidates_evaluated": len(candidates),
            "contracts_signed": len(contracts),
            "payments_processed": len([s for s in settlements if s.status == "paid"])
        },
        "kpi_achievement": {
            "target_engagement_rate": kpi.get("target_engagement_rate", 0),
            "actual_engagement_rate": average_engagement_rate,
            "target_reach": kpi.get("target_reach", 0),
            "actual_reach": total_reach,
            "target_roas": kpi.get("target_roas", 0),
            "actual_roas": roi
        },
        "recommendations": [
            "Continue partnership with top-performing influencers",
            "Increase budget allocation for high-engagement platforms",
            "Expand to similar audience segments",
            "Optimize posting times based on peak engagement"
        ],
        "report_generated": "2024-01-20T17:30:00Z"
    }
    
    logger.info("✅ Final campaign report generated")
    logger.info(f"📈 Campaign ROI: {roi:.2f}")
    logger.info(f"🎯 Engagement rate: {average_engagement_rate:.3f}")
    
    # Add to logs
    logs = state.get("logs", [])
    logs.append("Final campaign report generated")
    
    return {
        "campaign_report": final_report,
        "logs": logs
    }


def create_settle_subgraph() -> StateGraph:
    """
    Create the Settle & Archive phase subgraph.
    
    Returns:
        Compiled settle subgraph
    """
    logger.info("🏗️ Creating Settle & Archive subgraph")
    
    # Create subgraph
    builder = StateGraph(CampaignState)
    
    # Add nodes
    builder.add_node("generate_invoice_pool", generate_invoice_pool)
    builder.add_node("bulk_payment", bulk_payment)
    builder.add_node("archive_assets", archive_assets)
    builder.add_node("update_creator_db", update_creator_db)
    builder.add_node("generate_final_report", generate_final_report)
    
    # Add edges - sequential flow
    builder.add_edge(START, "generate_invoice_pool")
    builder.add_edge("generate_invoice_pool", "bulk_payment")
    builder.add_edge("bulk_payment", "archive_assets")
    builder.add_edge("archive_assets", "update_creator_db")
    builder.add_edge("update_creator_db", "generate_final_report")
    builder.add_edge("generate_final_report", END)
    
    # Compile subgraph
    subgraph = builder.compile(name="settle-phase")
    
    logger.info("✅ Settle & Archive subgraph created")
    return subgraph


# Export as toolified agent
def create_settle_tool():
    """
    Create toolified version of settle subgraph.
    
    Returns:
        Settlement tool for external use
    """
    from langchain_core.tools import tool
    
    @tool
    def settlement_tool(
        contracts: List[Dict[str, Any]], 
        performance_metrics: Dict[str, Any],
        campaign_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute campaign settlement and archival process.
        
        Args:
            contracts: List of campaign contracts
            performance_metrics: Performance metrics data
            campaign_data: Campaign summary data
            
        Returns:
            Settlement results with final report
        """
        logger.info("🔧 Settlement tool activated")
        
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
                status=c.get("status", "completed")
            )
            for c in contracts
        ]
        
        # Create initial state
        state = CampaignState(
            contracts=contract_objects,
            performance=performance_metrics,
            objective=campaign_data.get("objective", ""),
            budget=campaign_data.get("budget", 0),
            kpi=campaign_data.get("kpi", {}),
            phase=7,
            logs=[],
            settlements=[]
        )
        
        # Execute settle subgraph
        subgraph = create_settle_subgraph()
        result = subgraph.invoke(state)
        
        logger.info("✅ Settlement tool completed")
        return result
    
    return settlement_tool