"""Test the refactored HITL implementation."""

import os
from langchain_core.messages import HumanMessage
from agent.influencer_marketing_graph import graph

# Test configuration
config = {"configurable": {"thread_id": "test_123"}}

def test_basic_flow():
    """Test basic flow without interrupts."""
    input_data = {
        "messages": [
            HumanMessage(content="我想推广一个环保产品，预算1万美元，目标用户是年轻人")
        ]
    }
    
    print("🧪 Testing basic flow...")
    
    # Test with skip enabled
    config_skip = {
        "configurable": {
            "thread_id": "test_skip",
            "allow_skip_human_review_campaign_info": True
        }
    }
    
    try:
        result = graph.invoke(input_data, config_skip)
        print("✅ Skip flow works")
        print(f"Final state: {result}")
    except Exception as e:
        print(f"❌ Skip flow failed: {e}")

def test_interrupt_flow():
    """Test interrupt flow (will actually interrupt)."""
    input_data = {
        "messages": [
            HumanMessage(content="我想推广一个环保产品，预算1万美元，目标用户是年轻人")
        ]
    }
    
    print("\n🧪 Testing interrupt flow...")
    
    try:
        result = graph.invoke(input_data, config)
        
        # Check if interrupted
        if "__interrupt__" in result:
            print("✅ Interrupt triggered successfully")
            print(f"Interrupt data: {result['__interrupt__']}")
            
            # Test resume
            from langgraph.types import Command
            resume_result = graph.invoke(
                Command(resume="yes"), 
                config
            )
            print("✅ Resume works")
            print(f"Resume result: {resume_result}")
        else:
            print("⚠️  No interrupt detected")
            
    except Exception as e:
        print(f"❌ Interrupt flow failed: {e}")

if __name__ == "__main__":
    # Set environment
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  GEMINI_API_KEY not set, some tests may fail")
        
    test_basic_flow()
    test_interrupt_flow()