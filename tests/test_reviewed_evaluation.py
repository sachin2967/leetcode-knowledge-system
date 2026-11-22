import csv
import hashlib

import pytest

from scripts.evaluate_reviewed_ranking import load_review
from src.evaluation.provenance import text_sha256


def review_file(tmp_path):
    path = tmp_path / "review.csv"
    fields = [
        "query_id",
        "split",
        "query",
        "problem_id",
        "title",
        "difficulty",
        "grade_0_1_2",
        "reviewer_notes",
    ]
    row = dict(
        zip(
            fields,
            ["q", "test", "window", "76", "Minimum Window Substring", "Hard", "", ""],
        )
    )
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)
    return path, fields, row, hashlib.sha256(path.read_bytes()).hexdigest()


def test_source_fingerprints_survive_git_line_ending_conversion(tmp_path):
    windows, linux = tmp_path / "windows.json", tmp_path / "linux.json"
    windows.write_bytes(b'{\r\n  "version": 1\r\n}\r\n')
    linux.write_bytes(b'{\n  "version": 1\n}\n')
    assert text_sha256(windows) == text_sha256(linux)


def test_blanks_are_not_silently_scored_as_irrelevant(tmp_path):
    path, _, _, digest = review_file(tmp_path)
    with pytest.raises(ValueError, match="blanks are unjudged"):
        load_review(path, digest)


def test_grades_and_notes_are_allowed_but_candidate_changes_are_rejected(tmp_path):
    path, fields, row, digest = review_file(tmp_path)
    row.update(grade_0_1_2="2", reviewer_notes="Direct match")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)
    assert load_review(path, digest)[0]["grade_0_1_2"] == "2"
    row["problem_id"] = "3"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)
    with pytest.raises(ValueError, match="Frozen pairs changed"):
        load_review(path, digest)
