from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class LLMOptions(BaseModel):
    timeout_seconds: Optional[int] = None

    class Config:
        extra = "forbid"

class PromptConfig(BaseModel):
    file: str
    inputs: Dict[str, Any]

    class Config:
        extra = "forbid"

class StepConfig(BaseModel):
    name: str
    type: str
    prompt: Optional[PromptConfig] = None
    function: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Any] = None
    log: Optional[str] = None
    llm_options: Optional[LLMOptions] = None
    output_type: Optional[str] = None
    saveas: Optional[str] = None
    append_to: Optional[str] = None
    steps: Optional[List[Any]] = None
    item_var: Optional[str] = None
    input: Optional[str] = None

    class Config:
        extra = "forbid"

class PipelineConfig(BaseModel):
    name: str
    variables: Dict[str, Any]
    llm_config: Dict[str, Any]
    linter_config: Optional[Dict[str, Any]] = None
    steps: List[StepConfig]

    class Config:
        extra = "forbid"

# Example usage:
# import yaml
# with open('pipelines/storyflow-psalms.yaml') as f:
#     data = yaml.safe_load(f)
# pipeline = PipelineConfig(**data)
# print(pipeline)
