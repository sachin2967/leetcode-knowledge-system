"""Print a demo or live public concept profile without persisting user history."""

import argparse
import json
from pathlib import Path

from src.data.catalog import read_sqlite
from src.data.solved import SolvedListError, fetch_public_solved, read_solved_fixture
from src.data.validation import load_taxonomy_ids
from src.knowledge_profile.profile import build_profile, profile_dict


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--demo", action="store_true", help="Use the synthetic, reproducible demo list")
    source.add_argument("--username", help="Fetch a public LeetCode accepted list")
    args = parser.parse_args()
    taxonomy = load_taxonomy_ids(ROOT / "docs/CONCEPT_TAXONOMY.md")
    catalog = read_sqlite(ROOT / "data/sample/catalog_mvp-1.0.sqlite3", taxonomy)
    try:
        solved = (read_solved_fixture(ROOT / "data/sample/demo_solved_mvp-1.json") if args.demo
                  else fetch_public_solved(args.username, catalog))
    except SolvedListError as exc:
        parser.exit(1, f"Solved list unavailable: {exc}\n")
    print(json.dumps(profile_dict(build_profile(solved, catalog, taxonomy)), indent=2))


if __name__ == "__main__":
    main()
