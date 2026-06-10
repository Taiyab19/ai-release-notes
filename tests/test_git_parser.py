"""
tests/test_git_parser.py — Unit tests for git_parser module
Run: pytest tests/ -v
"""

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.git_parser import (
    _parse_conventional_commit,
    _extract_ticket_refs,
    _parse_commit_block,
    group_commits_by_type,
    summarise_commits,
    ParsedCommit,
)


class TestParseConventionalCommit:

    def test_feat_with_scope(self):
        t, s, sub = _parse_conventional_commit("feat(auth): add OAuth2 support")
        assert t == "feat"
        assert s == "auth"
        assert sub == "add OAuth2 support"

    def test_fix_without_scope(self):
        t, s, sub = _parse_conventional_commit("fix: resolve timeout issue")
        assert t == "fix"
        assert s == ""
        assert sub == "resolve timeout issue"

    def test_breaking_change_marker(self):
        t, s, sub = _parse_conventional_commit("feat(api)!: rename all endpoints")
        assert t == "feat"
        assert s == "api"

    def test_non_conventional_commit(self):
        t, s, sub = _parse_conventional_commit("random commit message here")
        assert t == "other"
        assert sub == "random commit message here"

    def test_chore_with_scope(self):
        t, s, sub = _parse_conventional_commit("chore(deps): upgrade Flask to 3.0")
        assert t == "chore"
        assert s == "deps"

    def test_uppercase_type_normalised(self):
        t, s, sub = _parse_conventional_commit("FEAT: add new feature")
        assert t == "feat"


class TestExtractTicketRefs:

    def test_jira_ticket(self):
        refs = _extract_ticket_refs("Fixes PROJ-123 in payment flow")
        assert "PROJ-123" in refs

    def test_servicenow_change(self):
        refs = _extract_ticket_refs("Related to CHG001234 deployment")
        assert "CHG001234" in refs

    def test_servicenow_incident(self):
        refs = _extract_ticket_refs("Resolves INC005678")
        assert "INC005678" in refs

    def test_multiple_tickets(self):
        refs = _extract_ticket_refs("PROJ-1 and PROJ-2 both fixed")
        assert "PROJ-1" in refs
        assert "PROJ-2" in refs

    def test_no_tickets(self):
        refs = _extract_ticket_refs("simple commit message")
        assert refs == []


class TestParseCommitBlock:

    def _make_block(self, msg, author="Test User", hash_val="abc1234567"):
        return f"HASH:{hash_val}\nAUTHOR:{author}\nDATE:2025-01-15\nMSG:{msg}"

    def test_parses_feat_commit(self):
        block = self._make_block("feat(api): add new endpoint")
        commit = _parse_commit_block(block)
        assert commit is not None
        assert commit.commit_type == "feat"
        assert commit.scope == "api"
        assert commit.category == "feature"
        assert commit.category_label == "New Features"

    def test_parses_breaking_change(self):
        block = self._make_block("feat!: BREAKING CHANGE rename fields")
        commit = _parse_commit_block(block)
        assert commit is not None
        assert commit.is_breaking is True

    def test_short_hash(self):
        block = self._make_block("fix: something", hash_val="abcdef1234567890")
        commit = _parse_commit_block(block)
        assert commit.short_hash == "abcdef1"

    def test_empty_block_returns_none(self):
        assert _parse_commit_block("") is None

    def test_author_captured(self):
        block = self._make_block("fix: bug", author="Tayyab Karem")
        commit = _parse_commit_block(block)
        assert commit.author == "Tayyab Karem"


class TestGroupCommitsByType:

    def _make_commit(self, ctype, subject, breaking=False):
        from scripts.git_parser import COMMIT_TYPE_MAP, DEFAULT_TYPE
        info = COMMIT_TYPE_MAP.get(ctype, DEFAULT_TYPE)
        return ParsedCommit(
            hash="abc123", short_hash="abc123", author="Test",
            date="2025-01-01", raw_message=subject,
            commit_type=ctype, category=info[0], category_label=info[1],
            scope="", subject=subject, body="",
            is_breaking=breaking, ticket_refs=[]
        )

    def test_groups_by_type(self):
        commits = [
            self._make_commit("feat", "add feature"),
            self._make_commit("fix",  "fix bug"),
            self._make_commit("feat", "another feature"),
        ]
        groups = group_commits_by_type(commits)
        assert "New Features" in groups
        assert len(groups["New Features"]) == 2
        assert "Bug Fixes" in groups

    def test_breaking_changes_first(self):
        commits = [
            self._make_commit("feat", "breaking", breaking=True),
            self._make_commit("fix",  "normal fix"),
        ]
        groups = group_commits_by_type(commits)
        keys = list(groups.keys())
        assert keys[0] == "⚠️  Breaking Changes"


class TestSummariseCommits:

    def _make_commit(self, ctype, breaking=False):
        from scripts.git_parser import COMMIT_TYPE_MAP, DEFAULT_TYPE
        info = COMMIT_TYPE_MAP.get(ctype, DEFAULT_TYPE)
        return ParsedCommit(
            hash="abc", short_hash="abc", author="Dev",
            date="2025-01-01", raw_message="msg",
            commit_type=ctype, category=info[0], category_label=info[1],
            scope="", subject="msg", body="",
            is_breaking=breaking, ticket_refs=["PROJ-1"] if breaking else []
        )

    def test_counts_correctly(self):
        commits = [
            self._make_commit("feat"),
            self._make_commit("feat"),
            self._make_commit("fix"),
            self._make_commit("chore"),
            self._make_commit("feat", breaking=True),
        ]
        summary = summarise_commits(commits)
        assert summary['total']    == 5
        assert summary['features'] == 3
        assert summary['bugfixes'] == 1
        assert summary['maintenance'] == 1
        assert summary['breaking'] == 1

    def test_empty_commits(self):
        summary = summarise_commits([])
        assert summary['total'] == 0
