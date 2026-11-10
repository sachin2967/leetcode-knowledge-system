"""Local-only orchestration. Run with uvicorn src.api.app:app on loopback.

Owner acknowledgement is a local trust boundary, not hosted authentication.
No live profile or personal snippet is cached in application state.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, HTTPException

from src.api.models import (
    ImportRequest, ImportResponse, PracticeRequest, PracticeResponse,
    ProfileRequest, TemplateRequest,
)
from src.data.catalog import read_sqlite
from src.data.models import Problem
from src.data.personal_code import (
    PersonalCodeError, TemplateSearch, import_accepted_code, retrieve_templates,
)
from src.data.solved import SolvedList, SolvedListError, fetch_public_solved, read_solved_fixture
from src.data.validation import load_taxonomy_ids
from src.knowledge_profile.diagnosis import diagnose_target
from src.knowledge_profile.profile import KnowledgeProfile, build_profile
from src.ranking.ranker import rank_problems


ROOT = Path(__file__).resolve().parents[2]


def create_app(root: Path = ROOT, *, public_fetcher: Callable[..., SolvedList] = fetch_public_solved) -> FastAPI:
    """Load validated local snapshots at startup; injectable public I/O for tests."""
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.taxonomy = load_taxonomy_ids(root / "docs/CONCEPT_TAXONOMY.md")
        application.state.catalog = read_sqlite(
            root / "data/sample/catalog_mvp-1.0.sqlite3", application.state.taxonomy)
        yield

    application = FastAPI(title="LeetCode Knowledge-Aware Practice", version="0.6.0", lifespan=lifespan)

    def profile(source: ProfileRequest) -> KnowledgeProfile:
        try:
            solved = (read_solved_fixture(root / "data/sample/demo_solved_mvp-1.json")
                      if source.mode == "demo" else public_fetcher(source.username, application.state.catalog))
        except SolvedListError as exc:
            raise HTTPException(503, "Solved history unavailable; try demo mode or retry later.") from exc
        return build_profile(solved, application.state.catalog, application.state.taxonomy)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/catalog", response_model=tuple[Problem, ...])
    def catalog() -> tuple[Problem, ...]:
        return application.state.catalog

    @application.get("/concepts", response_model=list[str])
    def concepts() -> list[str]:
        return sorted(application.state.taxonomy)

    @application.post("/profiles", response_model=KnowledgeProfile)
    def profiles(request: ProfileRequest) -> KnowledgeProfile:
        return profile(request)

    @application.post("/practice", response_model=PracticeResponse)
    def practice(request: PracticeRequest) -> PracticeResponse:
        unknown = set(request.concepts) - application.state.taxonomy
        if unknown:
            raise HTTPException(422, "Use only concept IDs from /concepts")
        target = None
        if request.target_problem_id is not None:
            target = next((p for p in application.state.catalog if p.problem_id == request.target_problem_id), None)
            if target is None:
                raise HTTPException(404, "Target problem is outside the local catalog")
        learner = profile(request.source)
        diagnosis = (diagnose_target(target, learner, application.state.catalog,
                                    application.state.taxonomy, path_limit=request.limit) if target else None)
        recommendations = rank_problems(
            application.state.catalog, request.query, concepts=tuple(request.concepts),
            difficulty=request.difficulty, profile=learner, limit=request.limit)
        return PracticeResponse(profile=learner, recommendations=recommendations, diagnosis=diagnosis)

    def authorize(acknowledged: bool) -> None:
        if not acknowledged:
            raise HTTPException(403, "Explicit owner authorization is required for personal code access")

    @application.post("/personal/import", response_model=ImportResponse)
    def import_code(request: ImportRequest) -> ImportResponse:
        authorize(request.owner_authorized)
        # Only relative paths within raw are accepted; domain code resolves and
        # checks containment again, including symlink and '..' escapes.
        source = Path(request.source)
        if source.is_absolute() or source.drive:
            raise HTTPException(422, "Source must be a relative path inside data/raw")
        try:
            count = import_accepted_code(request.owner, root / "data/raw" / source,
                                         root / "data", owner_authorized=True)
        except PersonalCodeError as exc:
            raise HTTPException(422, str(exc)) from exc
        return ImportResponse(imported=count)

    @application.post("/personal/templates", response_model=TemplateSearch)
    def templates(request: TemplateRequest) -> TemplateSearch:
        authorize(request.owner_authorized)
        try:
            return retrieve_templates(request.owner, request.query, application.state.catalog,
                                      root / "data", taxonomy_ids=application.state.taxonomy)
        except PersonalCodeError as exc:
            raise HTTPException(422, str(exc)) from exc

    return application


app = create_app()
