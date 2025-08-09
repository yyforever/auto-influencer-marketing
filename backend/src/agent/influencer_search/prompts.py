"""
Prompt templates for influencer search workflow.

Contains all LLM prompt templates used throughout the influencer search
process, organized by functionality and optimized for Gemini models.
"""

from datetime import datetime

# Query Parsing Prompts
SEARCH_QUERY_EXTRACTION_PROMPT = """
你是一位专业的网红营销搜索专家。请从用户的自然语言请求中提取结构化的搜索参数。

用户请求：{user_messages}

请提取以下搜索参数：

🔍 **搜索范围**：
- platform: 社交媒体平台 (默认为 'instagram' 如果未指定)
- niche: 内容领域或行业垂直分类
- location: 地理位置偏好 (如果未提及则为 None)

👥 **粉丝数量**：
- min_followers: 最小粉丝数 (如果未指定默认为 10,000)
- max_followers: 最大粉丝数 (如果未指定默认为 1,000,000)

🏷️ **关键词**：
- keywords: 与内容或品牌相关的关键词列表

**重要指导原则**：
1. 如果信息缺失，使用合理的网红营销默认值
2. 从用户语境中推断隐含的搜索意图
3. 优先考虑用户明确提到的要求
4. 关键词应该涵盖内容主题和潜在品牌匹配点

请返回结构化的搜索参数。
"""

SEARCH_REFINEMENT_PROMPT = """
基于初始搜索结果，请评估是否需要调整搜索参数以获得更好的结果。

原始搜索查询：{original_query}
找到的结果数量：{results_count}
用户原始请求：{user_request}

请分析：
1. 结果数量是否合适 (理想范围：3-20个)
2. 搜索参数是否过于严格或宽松
3. 是否遗漏了重要的搜索条件

如果需要调整，请提供新的搜索参数。否则，确认当前参数合适。
"""

# Result Processing Prompts
INFLUENCER_PROFILE_ENHANCEMENT_PROMPT = """
请为以下网红档案补充和优化信息，使其更完整和有用：

基础信息：{basic_info}

请增强以下方面：
1. **受众分析**: 基于niche和follower数量推断目标受众特征
2. **内容特色**: 根据niche推断可能的内容类型和风格
3. **合作潜力**: 评估与不同类型品牌的合作适配度
4. **联系建议**: 提供初步的outreach策略建议

保持客观和专业，基于可获得的数据进行合理推断。
"""

RANKING_EXPLANATION_PROMPT = """
请解释为什么这些网红被选为搜索结果的顶部推荐：

搜索查询：{search_query}
推荐的网红：{recommended_influencers}

请从以下角度提供排名解释：
1. **匹配度分析**: 与搜索条件的匹配程度
2. **质量评估**: 账户质量和真实性指标
3. **商业价值**: 潜在的营销效果和ROI
4. **合作可行性**: 联系和合作的可能性

为每位网红提供简明的推荐理由。
"""

# Response Generation Prompts  
SEARCH_RESULTS_SUMMARY_PROMPT = """
请为网红搜索结果生成一个专业、清晰的总结报告。

搜索参数：{search_query}
找到的网红数量：{total_results}
返回的结果：{returned_results}

网红列表：{influencer_list}

请生成包含以下内容的总结：

## 🔍 搜索概要
- 搜索平台和领域
- 粉丝数量范围
- 地理位置要求
- 关键词匹配

## 📊 结果统计
- 总发现数量
- 返回结果数量
- 平均质量指标

## 👥 推荐网红
为每位网红提供：
- 基本信息 (用户名、粉丝数、互动率)
- 匹配度评分和说明
- 联系信息
- 推荐理由

## 💡 下一步建议
- 如何联系这些网红
- 进一步筛选建议
- 替代搜索方向

保持专业、详细且易读的格式。
"""

NO_RESULTS_GUIDANCE_PROMPT = """
很抱歉，根据您的搜索条件没有找到合适的网红。

搜索条件：{search_query}

## 🔄 优化建议

**可能的原因：**
1. 搜索条件过于严格
2. 该领域的网红数量较少  
3. 地理位置限制过于具体
4. 粉丝数量范围过窄

**建议调整：**
1. **放宽粉丝范围**: 考虑扩大 min_followers 和 max_followers
2. **扩展地理范围**: 如果指定了location，尝试更广泛的区域
3. **调整内容领域**: 考虑相关的niche分类
4. **修改关键词**: 使用更通用或相关的关键词

**替代方案：**
- 尝试相关的内容领域
- 考虑微型网红 (更少粉丝但更高互动)
- 探索新兴平台的创作者

请调整搜索条件后重新尝试，或告诉我您希望如何修改搜索参数。
"""

ERROR_RECOVERY_PROMPT = """
搜索过程中遇到了问题，但我们可以协助您解决。

错误信息：{error_message}
搜索请求：{user_request}

## 🔧 问题解决

**常见问题及解决方案：**
1. **参数格式错误**: 请检查粉丝数量、平台名称等格式
2. **网络连接问题**: 请稍后重试
3. **搜索条件冲突**: 检查最小/最大粉丝数设置

**建议操作：**
1. 简化搜索条件
2. 使用常见的平台名称 (instagram, tiktok, youtube)
3. 检查拼写和格式

请重新描述您的搜索需求，我将为您提供更好的搜索结果。
"""

# Template formatting helpers
def format_search_query_prompt(user_messages: str) -> str:
    """Format the search query extraction prompt with user messages"""
    return SEARCH_QUERY_EXTRACTION_PROMPT.format(user_messages=user_messages)

def format_results_summary_prompt(
    search_query: dict,
    total_results: int, 
    returned_results: int,
    influencer_list: str
) -> str:
    """Format the results summary prompt with search data"""
    return SEARCH_RESULTS_SUMMARY_PROMPT.format(
        search_query=search_query,
        total_results=total_results,
        returned_results=returned_results,
        influencer_list=influencer_list
    )

def format_no_results_prompt(search_query: dict) -> str:
    """Format the no results guidance prompt"""
    return NO_RESULTS_GUIDANCE_PROMPT.format(search_query=search_query)

def format_error_recovery_prompt(error_message: str, user_request: str) -> str:
    """Format the error recovery prompt"""
    return ERROR_RECOVERY_PROMPT.format(
        error_message=error_message,
        user_request=user_request
    )


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