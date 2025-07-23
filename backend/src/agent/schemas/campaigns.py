from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, PositiveFloat, PositiveInt

# class KPI(BaseModel):
#     """Key-Performance-Indicators of the campaign."""
#     ROI: Optional[PositiveFloat] = Field(default=None, description="Desired return on investment percentage, e.g. 200 == 200 %")
#     exposure: Optional[PositiveInt] = Field(default=None, description="Target total impressions")
#     number_of_influencers: Optional[PositiveInt] = Field(default=None, description="Target number of influencers")

#     # ⬇️ 任何多余字段都会触发 ValidationError
#     model_config = ConfigDict(extra='forbid')   # Pydantic v2; v1 用 `class Config: extra = 'forbid'`

class CampaignBasicInfo(BaseModel):
    """
    Flattened schema for influencer‑marketing campaign extraction.
    
    分成三块：
    ── core:   基本信息（目标、预算）
    ── KPI:    关键成效指标（ROI、曝光、网红数量）
    ── target: 受众与产品卖点
    
    所有字段都设为 Optional，模型 *只* 在用户明确提到时才填写；缺失则保持 None。
    """
    # ---------- core ----------
    objective: Optional[List[str]] = Field(
        default=None,
        description=(
            "A list of campaign objectives as short phrases, e.g. "
            "'提升品牌知名度', '新品上市预热'. "
            "Return None if user gave no explicit objectives."
        ),
    )
    initial_budget: Optional[PositiveFloat] = Field(
        default=None,
        description=(
            "Initial campaign budget **in USD**. "
            "Extract numeric value only; do not include currency symbols. "
            "Return None if not provided."
        ),
    )

    # ---------- KPI ----------
    kpi_ROI: Optional[PositiveFloat] = Field(
        default=None,
        description=(
            "Desired return on investment expressed as a percentage. "
            "E.g. 200 -> 200 %. Must be a positive float."
        ),
    )
    kpi_exposure: Optional[PositiveInt] = Field(
        default=None,
        description=(
            "Target total impressions (number of times the content should be seen). "
            "Positive integer; do not add units like '次' or 'views'."
        ),
    )
    kpi_number_of_influencers: Optional[PositiveInt] = Field(
        default=None,
        description=(
            "Total number of influencers to recruit for the campaign. "
            "Positive integer."
        ),
    )

    # ---------- audience / product ----------
    target_audience: Optional[List[str]] = Field(
        default=None,
        description=(
            "A list of target audience segments, each as a short noun phrase, "
            "e.g. '白领', '学生', '健身爱好者'. "
            "Return None if not mentioned."
        ),
    )
    product_pillars: Optional[List[str]] = Field(
        default=None,
        description=(
            "Key product selling points or features, each as a short phrase, "
            "e.g. '24h 保温', '不锈钢内胆'. "
            "Include only what the user explicitly states."
        ),
    )

    # ---------- global config ----------
    model_config = ConfigDict(
        # strict=True,          # 类型必须完全符合；不做隐式转换
        extra='forbid',       # 拒收任何未知字段
    )

class CalarifyCampaignInfoWithHuman(BaseModel):
    """
    Calarify campaign info with human.
    """
    need_clarification: bool = Field(description="Whether the user needs to be asked some clarifying questions.")
    questions: Optional[str] = Field(description="The clarifying questions for the user.")