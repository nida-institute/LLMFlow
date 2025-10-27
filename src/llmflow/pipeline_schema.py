from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class LLMConfig(BaseModel):
    """LLM provider configuration"""

    model_config = ConfigDict(extra="allow")

    provider: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = 4000
    temperature: Optional[float] = None


class StepConfig(BaseModel):
    """Configuration for a pipeline step"""

    model_config = ConfigDict(extra="allow")

    name: str
    type: str
    function: Optional[str] = None
    prompt: Optional[Union[str, Dict[str, Any]]] = None
    input: Optional[Any] = None
    inputs: Optional[Union[Dict[str, Any], List[Any]]] = None
    outputs: Optional[Union[str, List[str]]] = None
    append_to: Optional[str] = None
    steps: Optional[List["StepConfig"]] = None
    item_var: Optional[str] = None
    condition: Optional[str] = None


class PipelineConfig(BaseModel):
    """Root pipeline configuration"""

    model_config = ConfigDict(extra="allow")

    name: str
    description: Optional[str] = None
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict)
    llm_config: Optional[LLMConfig] = None
    linter_config: Optional[Dict[str, Any]] = None
    steps: List[StepConfig]
    vars: Optional[Dict[str, Any]] = None
    prompts_dir: Optional[str] = None


# Enable forward references
StepConfig.model_rebuild()
