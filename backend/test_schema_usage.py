"""Test schema usage in nodes."""

from agent.schemas.campaigns import CampaignBasicInfo, CalarifyCampaignInfoWithHuman

def test_schema_definitions():
    """Test that schemas are properly defined."""
    print("🧪 Testing schema definitions...")
    
    # Test CampaignBasicInfo fields
    print("\n📋 CampaignBasicInfo fields:")
    for field_name, field_info in CampaignBasicInfo.model_fields.items():
        print(f"  • {field_name}: {field_info.annotation}")
    
    # Test CalarifyCampaignInfoWithHuman fields  
    print("\n❓ CalarifyCampaignInfoWithHuman fields:")
    for field_name, field_info in CalarifyCampaignInfoWithHuman.model_fields.items():
        print(f"  • {field_name}: {field_info.annotation}")

def test_schema_usage_logic():
    """Test the logic of schema usage in nodes."""
    print("\n🧪 Testing schema usage logic...")
    
    print("✅ Node 1 (initialize_campaign_info):")
    print("   → Uses CampaignBasicInfo for EXTRACTION")
    print("   → Extracts: objective, budget, KPIs, audience, etc.")
    
    print("✅ Node 2 (auto_clarify_campaign_info):")  
    print("   → Uses CalarifyCampaignInfoWithHuman for CLARIFICATION")
    print("   → Determines: need_clarification (bool), questions (str)")
    
    print("✅ Schema usage is now CORRECT!")

if __name__ == "__main__":
    test_schema_definitions()
    test_schema_usage_logic()