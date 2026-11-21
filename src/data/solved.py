"""Public solved-list input, kept separate from personal submission code."""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import Problem

ENDPOINT = "https://leetcode.com/graphql/"
QUERY = """query publicSolved($username: String!, $limit: Int!) {
  matchedUser(username: $username) { submitStats { acSubmissionNum { difficulty count } } }
  recentAcSubmissionList(username: $username, limit: $limit) { titleSlug }
}"""
USERNAME = re.compile(r"[A-Za-z0-9_-]{1,30}\Z")


class SolvedListError(ValueError):
    """Invalid or unavailable public solved-list input."""


@dataclass(frozen=True)
class SolvedList:
    username: str
    problem_ids: tuple[int, ...]
    source: str
    collected_at: str
    total_reported: int
    unmapped_ids: tuple[str, ...] = ()
    recency_ranks: tuple[int, ...] = ()


def validate_solved_list(value: SolvedList) -> SolvedList:
    if not isinstance(value.username, str) or not USERNAME.fullmatch(value.username):
        raise SolvedListError("Invalid public username")
    if not isinstance(value.source, str) or not value.source.strip():
        raise SolvedListError("Solved-list source is required")
    try:
        date.fromisoformat(value.collected_at)
    except (TypeError, ValueError) as exc:
        raise SolvedListError("Invalid collection date") from exc
    if (
        isinstance(value.total_reported, bool)
        or not isinstance(value.total_reported, int)
        or value.total_reported < 0
    ):
        raise SolvedListError("Invalid reported total")
    if any(
        isinstance(i, bool) or not isinstance(i, int) or i <= 0
        for i in value.problem_ids
    ):
        raise SolvedListError("Solved problem IDs must be positive integers")
    if len(set(value.problem_ids)) != len(value.problem_ids):
        raise SolvedListError("Duplicate solved problem ID")
    if value.recency_ranks and (
        len(value.recency_ranks) != len(value.problem_ids)
        or any(
            isinstance(rank, bool) or not isinstance(rank, int) or rank < 0
            for rank in value.recency_ranks
        )
        or len(set(value.recency_ranks)) != len(value.recency_ranks)
    ):
        raise SolvedListError(
            "Recency ranks must be distinct, nonnegative, and aligned with problem IDs"
        )
    if any(not isinstance(i, str) or not i.strip() for i in value.unmapped_ids):
        raise SolvedListError("Invalid unmapped problem identifier")
    if len(value.problem_ids) + len(value.unmapped_ids) > value.total_reported:
        raise SolvedListError("More solved IDs than reported total")
    return value


def read_solved_fixture(path: Path) -> SolvedList:
    """Read a safe, explicit fixture; raw third-party exports belong in data/raw."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        required = {
            "username",
            "problem_ids",
            "source",
            "collected_at",
            "total_reported",
        }
        if not isinstance(data, dict) or set(data) not in (
            required,
            required | {"recency_ranks"},
        ):
            raise SolvedListError("Solved fixture fields mismatch")
        if not isinstance(data["problem_ids"], list):
            raise SolvedListError("problem_ids must be a list")
        data["problem_ids"] = tuple(data["problem_ids"])
        if "recency_ranks" in data:
            data["recency_ranks"] = tuple(data["recency_ranks"])
        return validate_solved_list(SolvedList(**data))
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        raise SolvedListError("Cannot read solved fixture") from exc


def _http_post(payload: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "leetcode-knowledge-system/0.2",
        },
    )
    try:
        with urlopen(request, timeout=12) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise SolvedListError("Public solved list is unavailable") from exc


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def fetch_public_solved(
    username: str,
    catalog: tuple[Problem, ...],
    *,
    limit: int = 20,
    post: Callable[[dict[str, Any]], dict[str, Any]] = _http_post,
    collected_at: str | None = None,
) -> SolvedList:
    """Fetch public recent accepts and total count, mapping slugs to catalog IDs.

    LeetCode's public endpoint currently exposes recent submissions rather than a
    complete accepted-problem list. Repeated submissions are deduplicated. The
    profile reports incomplete history whenever fewer unique IDs than the public
    accepted count are available. No private code or credentials are requested.
    """
    if not isinstance(username, str) or not USERNAME.fullmatch(username):
        raise SolvedListError("Invalid public username")
    if not 1 <= limit <= 20:
        raise SolvedListError("limit must be between 1 and 20")
    slug_to_id = {_slug(problem.title): problem.problem_id for problem in catalog}
    if len(slug_to_id) != len(catalog):
        raise SolvedListError("Catalog titles have ambiguous slugs")
    payload = post(
        {"query": QUERY, "variables": {"username": username, "limit": limit}}
    )
    if not isinstance(payload, dict) or payload.get("errors"):
        raise SolvedListError("Public profile query failed")
    result = payload.get("data")
    user = result.get("matchedUser") if isinstance(result, dict) else None
    recent = result.get("recentAcSubmissionList") if isinstance(result, dict) else None
    if (
        not isinstance(user, dict)
        or not isinstance(recent, list)
        or len(recent) > limit
    ):
        raise SolvedListError("Public profile not found or unavailable")
    stats = user.get("submitStats")
    counts = stats.get("acSubmissionNum") if isinstance(stats, dict) else None
    if not isinstance(counts, list):
        raise SolvedListError("Public accepted count unavailable")
    all_counts = [
        item.get("count")
        for item in counts
        if isinstance(item, dict) and item.get("difficulty") == "All"
    ]
    if (
        len(all_counts) != 1
        or isinstance(all_counts[0], bool)
        or not isinstance(all_counts[0], int)
    ):
        raise SolvedListError("Invalid public accepted count")
    total = all_counts[0]
    slugs = []
    for rank, item in enumerate(recent):
        slug = item.get("titleSlug") if isinstance(item, dict) else None
        if not isinstance(slug, str) or not slug.strip():
            raise SolvedListError("Invalid recent accepted problem slug")
        if slug not in {prior_slug for prior_slug, _ in slugs}:
            slugs.append((slug, rank))
    mapped = [(slug_to_id[slug], rank) for slug, rank in slugs if slug in slug_to_id]
    ids = tuple(problem_id for problem_id, _ in mapped)
    ranks = tuple(rank for _, rank in mapped)
    unknown = tuple(slug for slug, _ in slugs if slug not in slug_to_id)
    return validate_solved_list(
        SolvedList(
            username,
            ids,
            "LeetCode public recent accepted submissions",
            collected_at or date.today().isoformat(),
            total,
            unknown,
            ranks,
        )
    )
