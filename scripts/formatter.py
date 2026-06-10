"""
formatter.py — Format and save generated release notes

Supports: Markdown, JSON (Jira/ServiceNow-ready), plain text
"""

import json
import os
from datetime import date
from scripts.git_parser import ParsedCommit, summarise_commits, group_commits_by_type


def save_markdown(content: str, output_path: str) -> str:
    """Save release notes as a Markdown file."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return output_path


def to_json(
    commits:   list[ParsedCommit],
    content:   str,
    app_name:  str,
    version:   str,
    environment: str = "Production",
) -> dict:
    """
    Build a structured JSON payload — compatible with Jira and ServiceNow.
    Useful for automated ticket creation post-release.
    """
    summary = summarise_commits(commits)
    groups  = group_commits_by_type(commits)

    changes = []
    for group_label, group_commits in groups.items():
        for c in group_commits:
            changes.append({
                "hash":           c.short_hash,
                "type":           c.commit_type,
                "category":       c.category,
                "scope":          c.scope,
                "subject":        c.subject,
                "author":         c.author,
                "date":           c.date,
                "is_breaking":    c.is_breaking,
                "ticket_refs":    c.ticket_refs,
            })

    return {
        "release": {
            "application":  app_name,
            "version":      version,
            "environment":  environment,
            "generated_at": date.today().isoformat(),
        },
        "summary": summary,
        "changes": changes,
        "release_notes_markdown": content,
        "meta": {
            "generator": "ai-release-notes",
            "source":    "https://github.com/tayyab-karem/ai-release-notes",
        }
    }


def save_json(payload: dict, output_path: str) -> str:
    """Save structured release data as JSON."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, default=str)
    return output_path


def to_plain_text(markdown_content: str) -> str:
    """Strip Markdown formatting for plain text output (email, Slack, etc.)."""
    import re
    text = markdown_content
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)   # headers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)                  # bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)                      # italic
    text = re.sub(r'`(.+?)`', r'\1', text)                        # inline code
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)          # links
    text = re.sub(r'^\|.+\|$', '', text, flags=re.MULTILINE)      # tables
    text = re.sub(r'^[-*]\s+', '• ', text, flags=re.MULTILINE)    # bullets
    text = re.sub(r'\n{3,}', '\n\n', text)                        # extra blank lines
    text = re.sub(r'^---+$', '─' * 40, text, flags=re.MULTILINE)  # horizontal rules
    return text.strip()


def print_dry_run(commits: list[ParsedCommit]) -> None:
    """Print commit summary table to console (no generation)."""
    if not commits:
        print("No commits found for the specified range.")
        return

    summary = summarise_commits(commits)
    print(f"\n{'─'*60}")
    print(f"  DRY RUN — Commits found: {summary['total']}")
    print(f"{'─'*60}")
    print(f"  Features    : {summary['features']}")
    print(f"  Bug fixes   : {summary['bugfixes']}")
    print(f"  Maintenance : {summary['maintenance']}")
    print(f"  Breaking    : {summary['breaking']}")
    print(f"  Date range  : {summary['date_range']['from']} → {summary['date_range']['to']}")
    print(f"  Authors     : {', '.join(summary['authors'])}")
    print(f"{'─'*60}\n")
    print(f"{'HASH':<8}  {'TYPE':<12}  {'SCOPE':<15}  SUBJECT")
    print(f"{'─'*8}  {'─'*12}  {'─'*15}  {'─'*35}")
    for c in commits[:30]:
        scope = c.scope[:14] if c.scope else '-'
        subj  = c.subject[:50] + ('…' if len(c.subject) > 50 else '')
        breaking = ' ⚠️' if c.is_breaking else ''
        print(f"{c.short_hash:<8}  {c.commit_type:<12}  {scope:<15}  {subj}{breaking}")
    if len(commits) > 30:
        print(f"\n  ... and {len(commits) - 30} more commits")
    print()
