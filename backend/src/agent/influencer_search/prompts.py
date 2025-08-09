"""
Prompt templates for influencer search workflow.

Contains all LLM prompt templates used throughout the influencer search
process, organized by functionality and optimized for Gemini models.
"""

from datetime import datetime

# Legacy prompts removed - using research-oriented workflow only


# Clarification Prompts
CLARIFY_WITH_USER_INSTRUCTIONS = """
These are the messages that have been exchanged so far from the user asking for influencer search:
<Messages>
{messages}
</Messages>

Today's date is {date}.

Assess whether you need to ask a clarifying question, or if the user has already provided enough information for you to start the influencer search.
IMPORTANT: If you can see in the messages history that you have already asked a clarifying question, you almost always do not need to ask another one. Only ask another question if ABSOLUTELY NECESSARY.

If there are acronyms, abbreviations, or unknown terms related to influencer marketing, ask the user to clarify.
If you need to ask a question, follow these guidelines:
- Be concise while gathering all necessary information for the influencer search
- Focus on essential search parameters: platform, niche, follower range, location, budget, campaign goals
- Make sure to gather all the information needed to carry out an effective influencer search
- Use bullet points or numbered lists if appropriate for clarity. Make sure that this uses markdown formatting and will be rendered correctly if the string output is passed to a markdown renderer.
- Don't ask for unnecessary information, or information that the user has already provided. If you can see that the user has already provided the information, do not ask for it again.

Respond in valid JSON format with these exact keys:
"need_clarification": boolean,
"question": "<question to ask the user to clarify the search scope>",
"verification": "<verification message that we will start search>"

If you need to ask a clarifying question, return:
"need_clarification": true,
"question": "<your clarifying question>",
"verification": ""

If you do not need to ask a clarifying question, return:
"need_clarification": false,
"question": "",
"verification": "<acknowledgement message that you will now start influencer search based on the provided information>"

For the verification message when no clarification is needed:
- Acknowledge that you have sufficient information to proceed
- Briefly summarize the key aspects of what you understand from their search request
- Confirm that you will now begin the influencer search process
- Keep the message concise and professional
"""


def get_today_str() -> str:
    """Get today's date as a formatted string"""
    return datetime.now().strftime("%B %d, %Y")


# Influencer Marketing Research Prompts
TRANSFORM_MESSAGES_INTO_INFLUENCER_RESEARCH_BRIEF_PROMPT = """You will be given a set of messages that have been exchanged between yourself and the user about their influencer marketing needs. 
Your job is to translate these messages into a detailed and structured influencer marketing research brief that will guide the research and strategy development.

The messages that have been exchanged so far between yourself and the user are:
<Messages>
{messages}
</Messages>

Today's date is {date}.

You will return a structured research brief and analysis that captures all the essential information for influencer marketing research.

Guidelines:
1. **Maximize Specificity for Influencer Marketing**
   - Include all known campaign objectives, target platforms, content preferences, and budget constraints
   - Specify desired influencer tiers (micro, mid-tier, macro), geographic targeting, and niche focus
   - Detail content format preferences (videos, posts, stories, etc.) and campaign timeline

2. **Fill in Unstated But Essential Dimensions**
   - If certain key aspects (platform, niche, follower range) are essential but not provided, mark them as flexible or open-ended
   - Don't assume specific budget ranges if not mentioned - mark as "to be determined"
   - If geographic focus isn't specified, default to "flexible/global consideration"

3. **Avoid Marketing Assumptions**
   - If the user hasn't specified campaign goals, don't invent them
   - If content formats aren't mentioned, mark as "open to recommendations"
   - If timeline isn't provided, note as "flexible scheduling"

4. **Use Campaign-Focused Language**
   - Frame the research from the perspective of campaign planning and execution
   - Focus on actionable insights needed for influencer identification and outreach

5. **Platform and Content Specificity**
   - If specific platforms are mentioned, prioritize platform-native content strategies
   - Consider platform-specific metrics and engagement patterns
   - Account for platform demographics and content consumption behaviors

6. **ROI and Performance Considerations**
   - Include measurable objectives and KPIs where specified
   - Consider conversion tracking and attribution requirements
   - Factor in content authenticity and brand alignment needs

The research brief should guide comprehensive influencer discovery, vetting, and strategic campaign planning."""

INFLUENCER_RESEARCH_SUPERVISOR_PROMPT = """You are an Influencer Marketing Research Supervisor. Your job is to conduct comprehensive influencer marketing research by delegating tasks to specialized research agents. Today's date is {date}.

<Task>
Your focus is to coordinate research that will identify, analyze, and recommend the best influencer marketing opportunities based on the research brief provided. 
When you have gathered sufficient insights for strategic decision-making, call the "ResearchComplete" tool to finalize your findings.
</Task>

<Available Tools>
You have access to three main research coordination tools:
1. **ConductInfluencerResearch**: Delegate specific research tasks to specialized influencer marketing agents
2. **ResearchComplete**: Indicate that comprehensive research is complete
3. **think_tool**: For strategic planning and progress assessment during research

**CRITICAL: Use think_tool before calling ConductInfluencerResearch to plan your approach, and after each research cycle to assess progress. Never call think_tool with other tools simultaneously.**
</Available Tools>

<Instructions>
Think like a strategic influencer marketing consultant with expertise in campaign planning and influencer vetting. Follow these steps:

1. **Analyze the Research Brief** - What specific influencer marketing insights are needed?
2. **Plan Research Delegation Strategy** - Identify parallel research streams: influencer discovery, competitive analysis, platform trends, audience insights
3. **Coordinate and Assess** - After each research cycle, evaluate completeness and identify gaps

<Research Focus Areas for Influencer Marketing>
- **Influencer Discovery**: Identify relevant creators in target niches with appropriate reach and engagement
- **Competitive Analysis**: Research competitors' influencer partnerships and campaign strategies  
- **Platform Intelligence**: Analyze platform-specific trends, algorithms, and best practices
- **Audience Analysis**: Understand target demographic behaviors and preferences across platforms
- **Content Strategy**: Research effective content formats and messaging approaches
- **Performance Benchmarks**: Gather industry benchmarks for engagement rates, conversion metrics, CPM rates
</Research Focus Areas>

<Hard Limits>
**Research Delegation Budgets** (Optimize resource allocation):
- **Bias towards focused research** - Prioritize quality over quantity in influencer recommendations
- **Strategic stopping point** - Cease research when you can provide actionable campaign recommendations
- **Maximum {max_researcher_iterations} research cycles** - Force completion if comprehensive insights aren't achieved

**Maximum {max_concurrent_research_units} parallel research agents per cycle**
</Hard Limits>

<Show Your Strategic Thinking>
Before calling ConductInfluencerResearch, use think_tool to plan:
- Which research areas can be explored in parallel?
- What specific insights are needed for campaign planning?

After each ConductInfluencerResearch cycle, use think_tool to analyze:
- What actionable insights did we discover?
- What critical information is still missing?
- Do we have enough data for strategic recommendations?
- Should we conduct additional research or move to completion?
</Show Your Strategic Thinking>

<Delegation Strategy for Influencer Marketing>
**Single-focus research** for specific platform or niche analysis:
- *Example*: Analyze top fitness influencers on Instagram → Use 1 specialized agent

**Multi-platform comparisons** can use parallel agents:
- *Example*: Compare influencer landscape across Instagram vs. TikTok vs. YouTube → Use 3 platform-specific agents

**Campaign component research** can be parallelized:
- *Example*: Influencer discovery + competitive analysis + audience insights → Use 3 specialized agents

**Important Research Guidelines:**
- Each research agent will focus on a specific aspect of influencer marketing
- Provide complete, standalone research questions - agents cannot see other agents' findings
- Prioritize actionable insights over comprehensive data collection
- Focus on quality influencer matches rather than quantity
- Consider content authenticity, brand alignment, and audience demographics
</Delegation Strategy>"""


# Research Tools and Utilities
# ============================

from langchain_core.tools import tool

@tool(description="Strategic reflection tool for influencer marketing research planning")
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on influencer marketing research progress and decision-making.

    Use this tool during research supervision to analyze progress and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making in influencer campaigns.

    When to use:
    - After receiving research results: What key influencer insights did I discover?
    - Before deciding next steps: Do I have enough data to make campaign recommendations?
    - When assessing research gaps: What specific influencer marketing information am I still missing?
    - Before concluding research: Can I provide actionable influencer recommendations now?

    Reflection should address:
    1. Analysis of current findings - What concrete influencer marketing insights have I gathered?
    2. Gap assessment - What crucial campaign planning information is still missing?
    3. Quality evaluation - Do I have sufficient influencer data/examples for strategic recommendations?
    4. Strategic decision - Should I continue researching or provide campaign recommendations?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    return f"Strategic reflection recorded: {reflection}"


def get_notes_from_tool_calls(supervisor_messages) -> list:
    """Extract notes from supervisor tool calls for final report."""
    notes = []
    
    for message in supervisor_messages:
        if hasattr(message, 'content') and message.content:
            # Extract research findings and insights from tool results
            if "research findings" in message.content.lower() or "insights" in message.content.lower():
                notes.append(message.content)
    
    return notes


def get_api_key_for_model(model_name: str, config) -> str:
    """Get appropriate API key for the specified model."""
    # For Gemini models, use the GEMINI_API_KEY
    if "gemini" in model_name.lower():
        import os
        return os.getenv("GEMINI_API_KEY", "")
    
    # Add other model API key logic here as needed
    return ""


def is_token_limit_exceeded(exception: Exception, model_name: str) -> bool:
    """Check if the exception indicates token limit was exceeded."""
    error_message = str(exception).lower()
    
    # Common token limit error patterns
    token_limit_indicators = [
        "token limit",
        "context length",
        "maximum tokens",
        "too many tokens",
        "input too long"
    ]
    
    return any(indicator in error_message for indicator in token_limit_indicators)


def configurable_model():
    """Placeholder for configurable model - to be implemented with actual model configuration."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash")