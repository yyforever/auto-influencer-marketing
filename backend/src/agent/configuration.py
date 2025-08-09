import os
from pydantic import BaseModel, Field
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig


class Configuration(BaseModel):
    """The configuration for the agent."""

    query_generator_model: str = Field(
        default="gemini-2.0-flash",
        metadata={
            "description": "The name of the language model to use for the agent's query generation."
        },
    )

    reflection_model: str = Field(
        default="gemini-2.5-flash",
        metadata={
            "description": "The name of the language model to use for the agent's reflection."
        },
    )

    answer_model: str = Field(
        default="gemini-2.5-pro",
        metadata={
            "description": "The name of the language model to use for the agent's answer."
        },
    )

    number_of_initial_queries: int = Field(
        default=3,
        metadata={"description": "The number of initial search queries to generate."},
    )

    max_research_loops: int = Field(
        default=2,
        metadata={"description": "The maximum number of research loops to perform."},
    )
    
    # HITL Configuration
    allow_skip_human_review_campaign_info: bool = Field(
        default=False,
        metadata={"description": "Skip human review for campaign info."},
    )
    
    # Clarification Configuration
    allow_clarification: bool = Field(
        default=False,
        metadata={"description": "Allow clarification questions to be asked to users when search scope is unclear."},
    )
    
    # Research Configuration
    research_model: str = Field(
        default="gemini-2.0-flash",
        metadata={"description": "The model to use for research brief generation."},
    )
    research_model_max_tokens: int = Field(
        default=4000,
        metadata={"description": "Maximum tokens for research model output."},
    )
    max_structured_output_retries: int = Field(
        default=3,
        metadata={"description": "Maximum retries for structured output generation."},
    )
    max_concurrent_research_units: int = Field(
        default=3,
        metadata={"description": "Maximum number of concurrent research units in supervisor."},
    )
    max_researcher_iterations: int = Field(
        default=5,
        metadata={"description": "Maximum iterations for researcher supervisor."},
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = config.get("configurable", {}) if config else {}
        field_names = list(cls.model_fields.keys())
        values: dict[str, Any] = {
            field_name: os.environ.get(field_name.upper(), configurable.get(field_name))
            for field_name in field_names
        }
        return cls(**{k: v for k, v in values.items() if v is not None})

    class Config:
        arbitrary_types_allowed = True