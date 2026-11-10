"""Strict transport inputs; domain dataclasses also define response schemas."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.knowledge_profile.diagnosis import Diagnosis
from src.knowledge_profile.profile import KnowledgeProfile
from src.ranking.ranker import Recommendation


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProfileRequest(RequestModel):
    mode: Literal["demo", "public"] = "demo"
    username: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,30}$")

    @model_validator(mode="after")
    def check_source(self) -> "ProfileRequest":
        if (self.mode == "public") != (self.username is not None):
            raise ValueError("Supply a username only in public mode")
        return self


class PracticeRequest(RequestModel):
    source: ProfileRequest = Field(default_factory=ProfileRequest)
    query: str = Field(default="", max_length=500)
    concepts: list[str] = Field(default_factory=list, max_length=28)
    difficulty: Literal["Easy", "Medium", "Hard"] | None = None
    limit: int = Field(default=10, ge=1, le=50, strict=True)
    target_problem_id: int | None = Field(default=None, gt=0, strict=True)


class PracticeResponse(BaseModel):
    profile: KnowledgeProfile
    recommendations: tuple[Recommendation, ...]
    diagnosis: Diagnosis | None


class OwnerRequest(RequestModel):
    owner: str = Field(pattern=r"^[A-Za-z0-9_-]{1,30}$")
    owner_authorized: bool = Field(default=False, strict=True)


class ImportRequest(OwnerRequest):
    source: str = Field(min_length=1, max_length=500)


class TemplateRequest(OwnerRequest):
    query: str = Field(min_length=1, max_length=500)


class ImportResponse(BaseModel):
    imported: int
