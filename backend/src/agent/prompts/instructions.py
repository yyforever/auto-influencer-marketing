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