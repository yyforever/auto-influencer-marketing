"""
Prompt templates for influencer search workflow.

Contains all LLM prompt templates used throughout the influencer search
process, organized by functionality and optimized for Gemini models.
"""

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