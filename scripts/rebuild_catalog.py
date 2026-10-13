"""Rebuild local catalog snapshots from the curated seed."""

from pathlib import Path

from src.data.catalog import load_seed, write_json, write_sqlite
from src.data.validation import load_taxonomy_ids


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    taxonomy = load_taxonomy_ids(ROOT / "docs/CONCEPT_TAXONOMY.md")
    problems = load_seed(ROOT / "data/sample/problems_seed.psv", taxonomy)
    write_sqlite(ROOT / "data/sample/catalog_mvp-1.0.sqlite3", problems, taxonomy)
    write_json(ROOT / "data/sample/catalog_mvp-1.0.json", problems, taxonomy)
    print(f"Rebuilt catalog_mvp-1.0 with {len(problems)} problems")


if __name__ == "__main__":
    main()
