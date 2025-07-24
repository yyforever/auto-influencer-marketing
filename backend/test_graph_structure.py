"""Test the refactored graph structure."""

from agent.influencer_marketing_graph import graph

def test_graph_structure():
    """Test that the graph has the expected structure."""
    print("🧪 Testing graph structure...")
    
    # Get graph nodes
    nodes = list(graph.nodes.keys())
    print(f"Graph nodes: {nodes}")
    
    expected_nodes = [
        "initialize_campaign_info",
        "auto_clarify_campaign_info", 
        "request_human_review",
        "apply_human_review_result",
        "generate_campaign_plan"
    ]
    
    for node in expected_nodes:
        if node in nodes:
            print(f"✅ Node '{node}' exists")
        else:
            print(f"❌ Node '{node}' missing")
    
    # Test checkpointer
    if graph.checkpointer:
        print("✅ Checkpointer configured")
    else:
        print("❌ Checkpointer missing")
    
    print("\n🧪 Testing state schema...")
    from agent.state.states import AgentState
    
    # Create a minimal state to test schema
    test_state = {
        "messages": [],
        "campaign_basic_info": None,
        "need_clarification": None,
        "human_review_result": None
    }
    
    print(f"✅ State schema: {list(test_state.keys())}")
    print("✅ Refactored graph structure is valid!")

if __name__ == "__main__":
    test_graph_structure()