campaign_info_extraction_instructions = """
你的目标是识别用户指令中的网红营销的要求信息，将其提取出来按照指定的格式输出，来确定用户对本次网红营销Campaign的基本要求。
Instructions:
- 只提取用户输入信息中的营销相关信息，不要添加任何其他信息。
- 如果用户输入信息中没有提到所需的信息时，禁止推测，直接返回空值。

Format:
- Format your response as a JSON object with ALL two of these exact keys:
   - "objective": 本次营销的目标，可以有多个
   - "initial_budget": 用户期望的预算
   - "kpi_ROI": 用户期望本次营销的ROI
   - "kpi_exposure": 用户期望本次营销的曝光量
   - "kpi_number_of_influencers": 用户期望本次营销的参与网红数量
   - "target_audience": 用户期望本次营销的目标受众，即希望可以吸引的受众群体，可以有多个
   - "product_pillars": 用户期望本次营销的产品卖点，即希望可以突出展示的产品特点，可以有多个

```

Context: {user_query}"""

clarify_campaign_info_with_human_instructions = """
These are the messages that have been exchanged so far from the user asking for the campaign:
<Messages>
{messages}
</Messages>

This is the campaign basic info that has been extracted from the user's query for now:
<Campaign_Basic_Info>
{campaign_basic_info}
</Campaign_Basic_Info>

Assess whether you need to ask some clarifying question, or if the user has already provided enough information for you to start to generate a campaign plan.
IMPORTANT: If you can see in the messages history that you have already asked a clarifying question, you almost always do not need to ask another one. Only ask another question if ABSOLUTELY NECESSARY.

If there are acronyms, abbreviations, or unknown terms, ask the user to clarify.
If you need to ask a question in a marketing context, follow these guidelines:
- Be concise while gathering all necessary information
- Ensure you collect all details required to create or refine the marketing strategy, campaign, or asset in a clear, well-structured manner
- Use bullet points or numbered lists for clarity (formatted in Markdown so they render correctly)
- Avoid asking for information that's unnecessary or already provided—verify what the user has shared before requesting anything new

Respond in valid JSON format with these exact keys:
"need_clarification": boolean,
"questions": "<questions to ask the user to clarify the campaign scope>", # 可以有多个问题

If you need to ask a clarifying question, return:
"need_clarification": true,
"questions": "<your clarifying questions>"

If you do not need to ask a clarifying question, return:
"need_clarification": false,
"questions": ""
"""