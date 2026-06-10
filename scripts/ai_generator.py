"""
ai_generator.py — Generate release notes using Anthropic Claude API

Takes structured commit data and returns polished, stakeholder-friendly
release notes written by Claude AI.
"""

import os
import json
from typing import Optional
from scripts.git_parser import ParsedCommit, group_commits_by_type, summarise_commits


def _build_prompt(
    commits:     list[ParsedCommit],
    app_name:    str,
    version:     str,
    environment: str = "Production",
) -> str:
    """Build the prompt sent to Claude API."""

    groups  = group_commits_by_type(commits)
    summary = summarise_commits(commits)

    # Format commits for the prompt
    commit_sections = []
    for group_label, group_commits in groups.items():
        lines = [f"\n### {group_label}"]
        for c in group_commits:
            scope_str = f"[{c.scope}] " if c.scope else ""
            ticket_str = f" ({', '.join(c.ticket_refs)})" if c.ticket_refs else ""
            breaking_str = " ⚠️ BREAKING" if c.is_breaking else ""
            lines.append(f"- {scope_str}{c.subject}{ticket_str}{breaking_str}")
            if c.body:
                lines.append(f"  Context: {c.body[:200]}")
        commit_sections.append('\n'.join(lines))

    commits_text = '\n'.join(commit_sections)

    prompt = f"""You are an expert Release Manager writing release notes for a software deployment.

APPLICATION : {app_name}
VERSION     : {version}
ENVIRONMENT : {environment}
RELEASE DATE: {summary['date_range']['to'] or 'Today'}

COMMIT SUMMARY:
- Total commits : {summary['total']}
- New features  : {summary['features']}
- Bug fixes     : {summary['bugfixes']}
- Maintenance   : {summary['maintenance']}
- Breaking changes: {summary['breaking']}
- Contributors  : {', '.join(summary['authors'][:5])}

RAW COMMITS (grouped by type):
{commits_text}

INSTRUCTIONS:
Write professional release notes that:
1. Start with a 2-3 sentence executive summary of what this release delivers
2. Group changes under clear headings using emojis:
   🚀 New Features, 🐛 Bug Fixes, ⚡ Performance, 🔧 Maintenance, ⚠️ Breaking Changes
3. Rewrite each commit into plain English that non-technical stakeholders can understand
4. Highlight business impact where possible (e.g. "improves checkout reliability" not "fixes null pointer exception")
5. Flag any breaking changes prominently with clear migration steps if inferable
6. End with a "Deployment Notes" section covering: rollback version, key monitoring points
7. Keep a professional but readable tone — suitable for both engineers and business stakeholders

Format the output in clean Markdown."""

    return prompt


def generate_with_claude(
    commits:     list[ParsedCommit],
    app_name:    str     = "Application",
    version:     str     = "1.0.0",
    environment: str     = "Production",
    api_key:     Optional[str] = None,
    model:       str     = "claude-sonnet-4-20250514",
    max_tokens:  int     = 1500,
) -> str:
    """
    Generate release notes using the Anthropic Claude API.

    Args:
        commits:     List of ParsedCommit objects from git_parser
        app_name:    Name of the application being released
        version:     Release version string
        environment: Target deployment environment
        api_key:     Anthropic API key (falls back to ANTHROPIC_API_KEY env var)
        model:       Claude model to use
        max_tokens:  Maximum tokens in the response

    Returns:
        Generated release notes as a Markdown string.

    Raises:
        ValueError:  If no API key is provided
        RuntimeError: If the API call fails
    """
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "anthropic package not installed. Run: pip install anthropic"
        )

    # Resolve API key
    resolved_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not resolved_key:
        raise ValueError(
            "No Anthropic API key found.\n"
            "Options:\n"
            "  1. Set ANTHROPIC_API_KEY in your .env file\n"
            "  2. Pass --api-key on the command line\n"
            "  3. Use --mock for demo mode (no API key needed)\n"
            "Get a free key at: console.anthropic.com"
        )

    if not commits:
        return "No commits found for the specified range. No release notes generated."

    prompt = _build_prompt(commits, app_name, version, environment)

    try:
        client = anthropic.Anthropic(api_key=resolved_key)
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    except anthropic.AuthenticationError:
        raise RuntimeError(
            "Invalid Anthropic API key. Check your ANTHROPIC_API_KEY in .env"
        )
    except anthropic.RateLimitError:
        raise RuntimeError(
            "Anthropic API rate limit hit. Wait a moment and try again."
        )
    except anthropic.APIError as e:
        raise RuntimeError(f"Anthropic API error: {e}")
