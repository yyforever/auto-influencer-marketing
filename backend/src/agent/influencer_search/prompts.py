"""
Prompt templates for influencer search workflow.

Contains all LLM prompt templates used throughout the influencer search
process, organized by functionality and optimized for Gemini models.
"""

from datetime import datetime
from typing import Optional

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
When possible, explicitly extract and populate only the following fields (do not go beyond them):
1) brand_name, product_names, product_type, product_links, product_summary
2) target_platforms
3) niche_focus; geographic_focus; languages
4) follower_range; influencer_count_target; expected_impressions
5) campaign_objectives
6) budget
7) content_requirements; prohibited_claims_or_restrictions
8) brand_tone_and_style; sample_offer
If the user did not specify an item, set a sensible placeholder like "to be determined" or leave it null (None). Do not hallucinate facts.

Guidelines:
1. **Maximize Specificity for Influencer Marketing**
   - Include all known campaign objectives, target platforms, content preferences, and budget constraints
   - Specify desired influencer tiers (micro, mid-tier, macro), geographic targeting, and niche focus
   - Detail content format preferences (videos, posts, stories, etc.)

2. **Fill in Unstated But Essential Dimensions**
   - If certain key aspects (platform, niche, follower range) are essential but not provided, mark them as flexible/open-ended
   - Don't assume specific budget ranges if not mentioned — use "to be determined" or leave null
   - If geographic focus isn't specified, note as "flexible/global consideration" and add any region hints from context

3. **Avoid Marketing Assumptions**
   - If the user hasn't specified campaign goals, don't invent them
   - If content formats aren't mentioned, mark as "open to recommendations"
   

4. **Use Campaign-Focused Language**
   - Frame the research from the perspective of campaign planning and execution
   - Focus on actionable insights needed for influencer identification and outreach

5. **Platform and Content Specificity**
   - If specific platforms are mentioned, prioritize platform-native content strategies
   - Consider platform-specific metrics and engagement patterns
   - Account for platform demographics and content consumption behaviors

6. **ROI and Performance Considerations**
   - Include measurable objectives and KPIs where specified
   - Consider conversion tracking and attribution requirements (e.g., UTMs, affiliate codes)
   - Factor in content authenticity and brand alignment needs

The research brief should guide comprehensive influencer discovery, vetting, and strategic campaign planning.
"""

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
    import os
    
    # For GPT models (including GPT-5), use the OPENAI_API_KEY
    if "gpt" in model_name.lower():
        return os.getenv("OPENAI_API_KEY", "")
    
    # For Gemini models, use the GEMINI_API_KEY
    if "gemini" in model_name.lower():
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

# Individual Researcher Prompts
# ==============================

research_system_prompt = """You are an expert influencer marketing researcher conducting focused research on a specific topic. Today's date is {date}.

<Task>
Your job is to use tools to gather comprehensive information about the user's influencer marketing research topic.
You can use any of the tools provided to you to find resources that can help answer the research question. You can call these tools in series or in parallel, your research is conducted in a tool-calling loop.
When you have gathered sufficient information to provide valuable insights, call the "ResearchComplete" tool to signal completion.
</Task>

<Available Tools>
You have access to several research tools:
1. **tavily_search**: For conducting web searches to gather information about influencer marketing
2. **think_tool**: For reflection and strategic planning during research
{mcp_prompt}

**CRITICAL: Use think_tool after each search to reflect on results and plan next steps. Do not call think_tool with the tavily_search or any other tools. It should be to reflect on the results of the search.**
</Available Tools>

<Instructions>
Think like an expert influencer marketing researcher with limited time. Follow these steps:

1. **Read the research topic carefully** - What specific influencer marketing information does the user need?
2. **Start with broader searches** - Use broad, comprehensive queries about influencer marketing first
3. **After each search, pause and assess** - Do I have enough to provide strategic insights? What's still missing?
4. **Execute narrower searches as you gather information** - Fill in the gaps with more targeted queries
5. **Stop when you can answer confidently** - Don't keep searching for perfection

<Hard Limits>
**Tool Call Budgets** (Prevent excessive searching):
- **Simple influencer queries**: Use 2-3 search tool calls maximum
- **Complex campaign research**: Use up to 5 search tool calls maximum
- **Always stop**: After 5 search tool calls if you cannot find the right sources

**Stop Immediately When**:
- You can provide comprehensive influencer marketing insights
- You have 3+ relevant examples/sources for the research question
- Your last 2 searches returned similar information about influencers/campaigns
</Hard Limits>

<Research Quality Standards>
- **Depth over Breadth**: Focus on quality insights rather than quantity of sources
- **Relevance Focus**: All information must directly relate to influencer marketing
- **Actionable Intelligence**: Provide insights that can inform marketing strategy decisions
- **Source Credibility**: Prioritize authoritative and recent sources
- **Data-Driven**: Include specific metrics, examples, and case studies when available
</Research Quality Standards>

<Show Your Thinking>
After each search tool call, use think_tool to analyze the results:
- What key influencer marketing information did I find?
- What's missing for comprehensive campaign planning?
- Do I have enough to provide strategic recommendations?
- Should I search more or call ResearchComplete?
</Show Your Thinking>

Remember: Use think_tool strategically for planning and assessment. Focus on gathering high-quality, actionable insights for influencer marketing decisions."""


# Research Compression Prompts  
# =============================

compress_research_system_prompt = """You are an expert research synthesizer specializing in influencer marketing intelligence. You have conducted research on a topic by calling several tools and web searches. Your job is now to clean up the findings, but preserve all of the relevant statements and information that the researcher has gathered. Today's date is {date}.

<Task>
You need to clean up information gathered from tool calls and web searches in the existing messages.
All relevant influencer marketing information should be repeated and rewritten verbatim, but in a cleaner format.
The purpose of this step is just to remove any obviously irrelevant or duplicative information.
For example, if three sources all say "Instagram engagement rates are declining", you could say "These three sources all stated that Instagram engagement rates are declining".
Only these fully comprehensive cleaned findings are going to be returned to the user, so it's crucial that you don't lose any information from the raw messages.
</Task>

<Guidelines>
1. Your output findings should be fully comprehensive and include ALL of the influencer marketing information and sources that the researcher has gathered from tool calls and web searches. It is expected that you repeat key information verbatim.
2. This report can be as long as necessary to return ALL of the information that the researcher has gathered about influencer marketing.
3. In your report, you should return inline citations for each source that the researcher found.
4. You should include a "Sources" section at the end of the report that lists all of the sources the researcher found with corresponding citations, cited against statements in the report.
5. Make sure to include ALL of the sources that the researcher gathered in the report, and how they were used to answer the influencer marketing question!
6. It's really important not to lose any sources. A later LLM will be used to merge this report with others, so having all of the sources is critical.
</Guidelines>

<Output Structure>
The report should be structured like this:
**List of Queries and Tool Calls Made**
**Fully Comprehensive Findings** 
**List of All Relevant Sources (with citations in the report)**
</Output Structure>

<Citation Rules>
- Assign each unique URL a single citation number in your text
- End with ### Sources that lists each source with corresponding numbers
- IMPORTANT: Number sources sequentially without gaps (1,2,3,4...) in the final list regardless of which sources you choose
- Example format:
  [1] Source Title: URL
  [2] Source Title: URL
</Citation Rules>

Critical Reminder: It is extremely important that any information that is even remotely relevant to the user's influencer marketing research topic is preserved verbatim (e.g. don't rewrite it, don't summarize it, don't paraphrase it)."""

compress_research_simple_human_message = """All above messages are about influencer marketing research conducted by an AI Researcher. Please clean up these findings.

DO NOT summarize the information. I want the raw influencer marketing information returned, just in a cleaner format. Make sure all relevant information is preserved - you can rewrite findings verbatim."""


# Message Processing Utilities
# ============================

def filter_messages(messages, include_types=None):
    """Filter messages by type for processing."""
    if include_types is None:
        include_types = ["tool", "ai", "human"]
    
    filtered = []
    for message in messages:
        message_type = type(message).__name__.lower()
        if any(msg_type in message_type for msg_type in include_types):
            filtered.append(message)
    
    return filtered


def remove_up_to_last_ai_message(messages):
    """Remove messages up to the last AI message for token limit handling."""
    # Find the last AI message index
    last_ai_index = -1
    for i in range(len(messages) - 1, -1, -1):
        if "ai" in type(messages[i]).__name__.lower():
            last_ai_index = i
            break
    
    # Return messages from the last AI message onwards
    if last_ai_index >= 0:
        return messages[last_ai_index:]
    else:
        return messages


def openai_websearch_called(message):
    """Check if OpenAI native web search was called."""
    # Placeholder for OpenAI web search detection
    return False


def anthropic_websearch_called(message):
    """Check if Anthropic native web search was called."""
    # Placeholder for Anthropic web search detection  
    return False


# Final Report Generation Prompt
# ==============================

FINAL_REPORT_GENERATION_PROMPT = """Based on all the influencer marketing research conducted, create a comprehensive, well-structured answer to the overall research brief:
<Research Brief>
{research_brief}
</Research Brief>

For more context, here is all of the messages so far. Focus on the research brief above, but consider these messages as well for more context.
<Messages>
{messages}
</Messages>

CRITICAL: Make sure the answer is written in the same language as the human messages!
For example, if the user's messages are in English, then MAKE SURE you write your response in English. If the user's messages are in Chinese, then MAKE SURE you write your entire response in Chinese.
This is critical. The user will only understand the answer if it is written in the same language as their input message.

Today's date is {date}.

Here are the findings from the influencer marketing research that you conducted:
<Findings>
{findings}
</Findings>

Please create a detailed influencer marketing research report that:
1. Is well-organized with proper headings (# for title, ## for sections, ### for subsections)
2. Includes specific facts, metrics, and insights from the research
3. References relevant sources using [Title](URL) format
4. Provides a balanced, thorough analysis focused on influencer marketing opportunities
5. Includes actionable recommendations for influencer campaigns
6. Includes a "Sources" section at the end with all referenced links

Structure your influencer marketing report based on the research brief. Here are some examples:

For influencer discovery and analysis:
1/ Executive Summary
2/ Influencer Landscape Overview
3/ Top Recommended Influencers
4/ Engagement Analysis & Performance Metrics
5/ Campaign Strategy Recommendations
6/ Budget and ROI Projections

For platform or niche analysis:
1/ Platform/Niche Overview
2/ Key Trends and Opportunities
3/ Audience Demographics and Behavior
4/ Content Performance Analysis
5/ Recommended Influencer Types
6/ Campaign Execution Strategy

For competitive analysis:
1/ Competitive Landscape Overview
2/ Competitor Influencer Partnerships
3/ Campaign Performance Analysis
4/ Gap Analysis and Opportunities
5/ Strategic Recommendations
6/ Implementation Timeline

Remember: Structure is flexible based on the specific research brief!

For each section of the report:
- Use simple, professional language suitable for marketing professionals
- Use ## for section title (Markdown format) for each section
- Do NOT refer to yourself as the writer - this should be a professional report
- Do not include meta-commentary about what you're doing
- Each section should provide deep insights with supporting data and examples
- Include specific metrics, engagement rates, follower counts when available
- Use bullet points for lists but default to detailed paragraphs
- Focus on actionable insights that can inform campaign decisions

REMEMBER:
The brief and research may be in English, but translate to match the user's language.
Make sure the final report is in the SAME language as the human messages.

Format the report in clear markdown with proper structure and include source references.

<Citation Rules>
- Assign each unique URL a single citation number in your text
- End with ### Sources that lists each source with corresponding numbers
- IMPORTANT: Number sources sequentially without gaps (1,2,3,4...) in the final list
- Each source should be a separate line item in a list for proper markdown rendering
- Example format:
  [1] Source Title: URL
  [2] Source Title: URL
- Citations are crucial for credibility - ensure accuracy and completeness
</Citation Rules>
"""


# Token Management and Model Utilities
# ====================================

def get_model_token_limit(model_name: str) -> Optional[int]:
    """Get the maximum token limit for a given model."""
    # Model token limits mapping
    model_limits = {
        # GPT Models
        "gpt-5": 128000,
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "gpt-4": 128000,
        "gpt-3.5": 16385,
        # Gemini Models (优先匹配具体版本)
        "gemini-2.5-pro": 1000000,  # 1M tokens context window
        "gemini-2.5-flash": 1000000, 
        "gemini-2.0-flash": 1000000,
        "gemini-1.5-pro": 2000000,
        "gemini-1.5-flash": 1000000,
    }
    
    # Check for model name variations (exact match first, then partial)
    if model_name.lower() in model_limits:
        return model_limits[model_name.lower()]
    
    # Check for partial matches
    for model, limit in model_limits.items():
        if model in model_name.lower():
            return limit
    
    # Return None if model not found (will trigger error handling)
    return None