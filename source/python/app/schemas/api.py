from pydantic import BaseModel, Field


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""


class TargetIn(BaseModel):
    project_id: int
    domain: str
    url: str
    source_type: str = "website"
    country: str = ""
    language: str = ""


class JobIn(BaseModel):
    project_id: int
    target_id: int
    url: str
    strategy: str = "AUTO"
    region: str = ""
    profile: str = "standard"


class AlertRuleIn(BaseModel):
    rule: str
    message: str
    project_id: int = 0
    channel: str = "inapp"
