"""
tests/test_mock_generator.py — Tests for mock generator
tests/test_formatter.py     — Tests for formatter
"""

import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.git_parser import ParsedCommit, COMMIT_TYPE_MAP, DEFAULT_TYPE
from scripts.mock_generator import generate_mock
from scripts.formatter import to_plain_text, to_json


def make_commit(ctype="feat", subject="test subject", scope="",
                breaking=False, tickets=None):
    info = COMMIT_TYPE_MAP.get(ctype, DEFAULT_TYPE)
    return ParsedCommit(
        hash="abc1234", short_hash="abc1234", author="Tayyab Karem",
        date="2025-01-15", raw_message=f"{ctype}: {subject}",
        commit_type=ctype, category=info[0], category_label=info[1],
        scope=scope, subject=subject, body="",
        is_breaking=breaking, ticket_refs=tickets or []
    )


class TestMockGenerator:

    def test_returns_string(self):
        commits = [make_commit("feat", "add new feature")]
        result = generate_mock(commits, "payment-service", "v2.0.0")
        assert isinstance(result, str)
        assert len(result) > 50

    def test_contains_version(self):
        commits = [make_commit()]
        result = generate_mock(commits, "payment-service", "v2.4.0")
        assert "v2.4.0" in result

    def test_contains_app_name(self):
        commits = [make_commit()]
        result = generate_mock(commits, "payment-service", "v1.0.0")
        assert "payment-service" in result

    def test_empty_commits_handled(self):
        result = generate_mock([], "app", "v1.0.0")
        assert "No commits" in result

    def test_breaking_change_flagged(self):
        commits = [make_commit("feat", "rename API fields", breaking=True)]
        result = generate_mock(commits, "app", "v2.0.0")
        assert "BREAKING" in result or "Breaking" in result

    def test_ticket_refs_included(self):
        commits = [make_commit("fix", "fix bug", tickets=["PROJ-123"])]
        result = generate_mock(commits, "app", "v1.0.0")
        assert "PROJ-123" in result

    def test_contains_deployment_notes(self):
        commits = [make_commit()]
        result = generate_mock(commits, "app", "v1.0.0")
        assert "Deployment" in result

    def test_multiple_commit_types(self):
        commits = [
            make_commit("feat", "new feature"),
            make_commit("fix",  "bug fix"),
            make_commit("chore","maintenance"),
        ]
        result = generate_mock(commits, "app", "v1.0.0")
        assert "New Features" in result or "Features" in result
        assert "Bug Fix" in result or "fix" in result.lower()


class TestFormatter:

    def test_plain_text_strips_headers(self):
        md = "# My Release Notes\n\n## Section\n\nSome content."
        text = to_plain_text(md)
        assert "#" not in text
        assert "My Release Notes" in text

    def test_plain_text_strips_bold(self):
        md = "This is **bold text** here."
        text = to_plain_text(md)
        assert "**" not in text
        assert "bold text" in text

    def test_plain_text_strips_links(self):
        md = "See [GitHub](https://github.com) for details."
        text = to_plain_text(md)
        assert "GitHub" in text
        assert "https://" not in text

    def test_to_json_structure(self):
        commits = [make_commit("feat", "new feature", tickets=["PROJ-1"])]
        content = "# Release Notes"
        payload = to_json(commits, content, "app", "v1.0.0", "Production")
        assert "release" in payload
        assert "summary" in payload
        assert "changes" in payload
        assert payload["release"]["version"] == "v1.0.0"
        assert payload["release"]["application"] == "app"
        assert payload["release"]["environment"] == "Production"

    def test_to_json_changes_list(self):
        commits = [make_commit("feat", "feature one")]
        payload = to_json(commits, "", "app", "v1.0.0")
        assert len(payload["changes"]) == 1
        assert payload["changes"][0]["type"] == "feat"
        assert payload["changes"][0]["subject"] == "feature one"

    def test_to_json_summary_counts(self):
        commits = [
            make_commit("feat", "f1"),
            make_commit("fix",  "f2"),
        ]
        payload = to_json(commits, "", "app", "v1.0.0")
        assert payload["summary"]["total"] == 2
        assert payload["summary"]["features"] == 1
        assert payload["summary"]["bugfixes"] == 1
