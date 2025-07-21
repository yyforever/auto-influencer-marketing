
from typing import Dict
from pydantic import BaseModel, Field


class CampaignBasicInfo(BaseModel):
    objective: str = Field(
        description="The objective of the campaign."
    )
    initial_budget: float = Field(
        description="The initial budget for the campaign."
    )
    kpi: Dict[str, float] = Field(
        description="The key performance indicators for the campaign."
    )