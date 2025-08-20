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
TRANSFORM_MESSAGES_INTO_INFLUENCER_RESEARCH_BRIEF_PROMPT = """You will be given a set of messages that have been exchanged so far between yourself and the user. 
Your job is to translate these messages into a more detailed and concrete influencer research task brief that will be used to guide the influencer research.

The messages that have been exchanged so far between yourself and the user are:
<Messages>
{messages}
</Messages>

You will return a single influencer research task brief that will be used to guide the influencer research.

Guidelines:
0. Clarify Task Type
- You need to first clarify whether this task is to supplement research with new influencers (searching for influencers different from the existing influencer list) or to completely re-search for influencers (ignoring existing influencers).

1. Maximize Specificity and Detail
- Include all known user preferences and explicitly list key attributes or dimensions to consider.
- It is important that all details from the user are included in the instructions.

2. Fill in Unstated But Necessary Dimensions as Open-Ended
- If certain attributes are essential for a meaningful output but the user has not provided them, explicitly state that they are open-ended or default to no specific constraint.

3. Avoid Unwarranted Assumptions
- If the user has not provided a particular detail, do not invent one.
- Instead, state the lack of specification and guide the researcher to treat it as flexible or accept all possible options.

4. Use the First Person
- Phrase the request from the perspective of the user.

5. Sources
- You will use "Nox Influencer" platform as the sole source for influencer information.
- If the query is in a specific language, prioritize sources published in that language.
"""

INFLUENCER_RESEARCH_SUPERVISOR_PROMPT = """Influencer research is most important of all in influencer marketing. You are a influencer research supervisor. Your job is to conduct influencer research by calling the "ConductInfluencerResearch" tool.

<Task>
Your focus is to call the "ConductInfluencerResearch" tool to conduct influencer research against the overall influencer research brief passed in by the user. 
When you are completely satisfied with the research findings returned from the tool calls, then you should call the "ResearchComplete" tool to indicate that you are done with your research.
</Task>

<Available Tools>
You have access to three main tools:
1. **ConductInfluencerResearch**: Delegate influencer research tasks to specialized sub-agents
2. **ResearchComplete**: Indicate that influencer research is complete
3. **think_tool**: For reflection and strategic planning during research

**CRITICAL: Use think_tool before calling ConductInfluencerResearch to plan your approach, and after each ConductInfluencerResearch to assess progress. Do not call think_tool with any other tools in parallel.**
</Available Tools>

<Instructions>
Think like a influencer research manager with limited time and resources. Follow these steps:

1. **Read the brief carefully** - What specific influencers does the user need?
2. **Decide how to delegate the influencer research** - Carefully consider the brief and decide how to delegate the influencer research. Are there multiple independent directions that can be explored simultaneously?
3. **After each call to ConductInfluencerResearch, pause and assess** - Do I have enough influencers to finish the influencer task? What's still missing?
</Instructions>

<Hard Limits>
**Task Delegation Budgets** (Prevent excessive delegation):
- **Bias towards single agent** - Use single agent for simplicity unless the user request has clear opportunity for parallelization
- **Stop when you finish the task confidently** - Don't keep delegating influencer research for perfection
- **Limit tool calls** - Always stop after {max_researcher_iterations} tool calls to ConductInfluencerResearch and think_tool if you cannot find the right influencers

**Maximum {max_concurrent_research_units} parallel agents per iteration**
</Hard Limits>

<Show Your Thinking>
Before you call ConductInfluencerResearch tool call, use think_tool to plan your approach:
- Can the task be broken down into smaller sub-tasks?

After each ConductInfluencerResearch tool call, use think_tool to analyze the results:
- What influencers did I find?
- What's missing?
- Do I have enough influencers to finish the overall influencer research task?
- Should I delegate more influencer research or call ResearchComplete?
</Show Your Thinking>

<Scaling Rules>
**Simple influencer-finding, lists, and rankings** can use a single sub-agent:
- *Example*: List the top 100 game influencers with more than 200K followers on TikTok in Germany → Use 1 sub-agent

**Multi group influencers presented in the task request** can use a sub-agent for each group:
- *Example*: YouTube and TikTok and Instagram United States influencers with middle tier followers → Use 3 sub-agents
- Delegate clear, distinct, non-overlapping subtopics

**Important Reminders:**
- Each ConductInfluencerResearch call spawns a dedicated research agent for that specific influencer research task
- A separate agent will write the final report - you just need to gather information
- When calling ConductInfluencerResearch, provide complete standalone instructions - sub-agents can't see other agents' work
- Do NOT use acronyms or abbreviations in your research questions, be very clear and specific
</Scaling Rules>"""


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

@tool(description="Multi-platform influencer search engine supporting YouTube, Instagram, and TikTok.")
async def influencer_search_tool(
    keywords: list[str],
    platform: str = "youtube",
    min_followers: int = 50000,
    max_followers: int = 1000000,
    countries: str = "US,UK",
    language: str = "en",
    limit: int = 200
) -> str:
    """Search for influencers across social media platforms using keyword-based filtering.

    Args:
        keywords: List of search keywords to find relevant influencers
        platform: Target platform for search (youtube, instagram, or tiktok)
        min_followers: Minimum follower count threshold for filtering results
        max_followers: Maximum follower count threshold for filtering results
        countries: Comma-separated country codes for geographic filtering (e.g., "US,UK,CA")
        language: Language code for content language filtering (e.g., "en", "es")
        limit: Maximum number of results to return (capped at 200 for API limits)

    Returns:
        Formatted string containing influencer profiles with metrics including name, 
        follower count, location, engagement rate, average views, and Nox score.
    """
    import aiohttp
    import os
    
    # Validate platform
    if platform.lower() not in ['youtube', 'instagram', 'tiktok']:
        return f"Unsupported platform: {platform}"
    # API configuration
    base_url = os.getenv('INFLUENCER_API_BASE_URL', 'http://10.101.150.253:10155')
    uid = os.getenv('INFLUENCER_API_UID', '5773389b0e4207dfeebd6d34de70afea')
    
    # Format keywords with delimiter
    formatted_keywords = ',5,'.join(keywords) + ',5'
    
    # Build request
    url = f"{base_url}/ws/{platform.lower()}/star/search"
    params = {
        'followerGte': min_followers,
        'followerLte': max_followers,
        'country': countries,
        'language': language,
        'pageNum': 1,
        'pageSize': min(limit, 200),  # Cap at 200 for API limits
        'searchWords': formatted_keywords
    }
    headers = {'uid': uid}
    
    # Make request
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    return f"API error: {response.status}"
                
                data = await response.json()
                
                # Parse response
                if data.get('errorNum') != 0 or 'retDataList' not in data:
                    return "No results found"
                
                influencers = data['retDataList']
                if not influencers:
                    return f"No {platform} influencers found for '{', '.join(keywords)}'"
                
                # Format results
                results = [f"Found {len(influencers)} {platform} influencers for '{', '.join(keywords)}':\n"]
                
                for i, inf in enumerate(influencers, 1):
                    name = inf.get('nickName') or 'Unknown'
                    country = inf.get('country') or 'Unknown'
                    followers = inf.get('followers') or 0
                    average_views = inf.get('estimateVideoViews') or 0
                    score = inf.get('noxScore') or 0
                    
                    # Special handling for engagement to avoid None * 100 error
                    interactive_rate = inf.get('interactiveRate')
                    engagement = (0 if interactive_rate is None else interactive_rate) * 100
                    
                    results.append(f"{i}. {name}")
                    results.append(f"   Platform: {platform}")
                    results.append(f"   Followers: {followers:,}")
                    results.append(f"   Location: {country}")
                    results.append(f"   Engagement: {engagement:.2f}%")
                    results.append(f"   Average Views: {average_views:,}")
                    results.append(f"   Nox Score: {score:.2f}\n")
                
                search_summary = f"Found {len(influencers)} {platform} influencers for '{', '.join(keywords)}', with {min_followers} to {max_followers} followers, in {countries} countries, in {language} language:\n"
                return search_summary + "\n".join(results)
                
    except Exception as e:
        return f"Search failed: {str(e)}"

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