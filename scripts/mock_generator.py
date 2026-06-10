"""
mock_generator.py — Generate demo release notes without an API key

Uses template-based generation to produce realistic-looking release notes.
Perfect for portfolio demos, CI testing, and showing recruiters the output
without needing an Anthropic account.
"""

from datetime import date
from scripts.git_parser import ParsedCommit, group_commits_by_type, summarise_commits

# Emoji map per category
EMOJI_MAP = {
    "New Features":              "🚀",
    "Bug Fixes":                 "🐛",
    "Performance Improvements":  "⚡",
    "Code Refactoring":          "♻️",
    "Maintenance":               "🔧",
    "Documentation":             "📚",
    "Testing":                   "🧪",
    "Security":                  "🔒",
    "Style / Formatting":        "🎨",
    "Other Changes":             "📝",
    "⚠️  Breaking Changes":      "⚠️",
}

# Human-friendly rewrites for common commit patterns
REWRITE_PATTERNS = [
    (["oauth", "sso", "auth"],      "Enhances authentication security and user access management"),
    (["timeout", "latency", "slow"],"Improves service reliability and response times under load"),
    (["rate limit", "throttle"],    "Protects service stability by managing traffic thresholds"),
    (["health check", "healthcheck"],"Improves deployment monitoring and incident detection accuracy"),
    (["rollback", "revert"],        "Strengthens release safety with improved rollback capability"),
    (["migration", "schema"],       "Updates data layer for improved performance and compatibility"),
    (["dependency", "upgrade", "deps"], "Keeps dependencies current for security and compatibility"),
    (["deploy", "pipeline", "ci"], "Streamlines the release and deployment process"),
    (["monitor", "alert", "log"],   "Improves operational visibility and incident response"),
    (["performance", "cache", "speed"], "Delivers faster response times for end users"),
    (["security", "vulnerability", "cve"], "Addresses security concerns to protect the platform"),
    (["api", "endpoint"],           "Extends API capabilities for consumers"),
    (["test", "coverage"],          "Improves code quality and reliability assurance"),
    (["config", "setting", "env"],  "Improves system configurability and deployment flexibility"),
]


def _humanise(subject: str, scope: str = "") -> str:
    """Convert a technical commit subject into plain English."""
    text = f"{scope} {subject}".lower()
    for keywords, human_text in REWRITE_PATTERNS:
        if any(kw in text for kw in keywords):
            # Capitalise and add scope context if available
            if scope:
                return f"{human_text} ({scope} module)"
            return human_text
    # Fallback: title-case the original subject
    return subject.strip().capitalize()


def generate_mock(
    commits:     list[ParsedCommit],
    app_name:    str = "Application",
    version:     str = "1.0.0",
    environment: str = "Production",
) -> str:
    """
    Generate realistic release notes without calling any API.
    Used for --mock mode and unit testing.
    """
    if not commits:
        return (
            f"# Release Notes — {app_name} v{version}\n\n"
            "No commits found for the specified range.\n"
        )

    summary = summarise_commits(commits)
    groups  = group_commits_by_type(commits)
    today   = date.today().isoformat()

    # ── Executive Summary ─────────────────────────────────────────
    feature_count = summary['features']
    fix_count     = summary['bugfixes']
    breaking_count= summary['breaking']

    summary_parts = []
    if feature_count:
        summary_parts.append(
            f"{feature_count} new feature{'s' if feature_count > 1 else ''}"
        )
    if fix_count:
        summary_parts.append(
            f"{fix_count} bug fix{'es' if fix_count > 1 else ''}"
        )
    if summary['maintenance']:
        summary_parts.append("maintenance improvements")

    exec_summary = (
        f"This release delivers {', '.join(summary_parts)} to {app_name}. "
        f"All changes have been validated in Staging and are ready for Production deployment."
    )
    if breaking_count:
        exec_summary += (
            f"\n\n> ⚠️  **This release contains {breaking_count} breaking "
            f"change{'s' if breaking_count > 1 else ''}. "
            f"Review the Breaking Changes section before deploying.**"
        )

    lines = [
        f"# Release Notes — {app_name} v{version}",
        f"",
        f"**Release date:** {today}  ",
        f"**Environment:** {environment}  ",
        f"**Total changes:** {summary['total']}  ",
        f"**Contributors:** {', '.join(summary['authors'][:5])}  ",
        f"",
        f"---",
        f"",
        f"## Executive Summary",
        f"",
        exec_summary,
        f"",
        f"---",
        f"",
    ]

    # ── Change Sections ───────────────────────────────────────────
    for group_label, group_commits in groups.items():
        emoji = EMOJI_MAP.get(group_label, "📝")
        lines.append(f"## {emoji} {group_label}")
        lines.append("")

        for commit in group_commits:
            human_text = _humanise(commit.subject, commit.scope)
            ticket_str = ""
            if commit.ticket_refs:
                ticket_str = f" — *{', '.join(commit.ticket_refs)}*"

            if commit.is_breaking:
                lines.append(f"- **[BREAKING]** {human_text}{ticket_str}")
                lines.append(f"  - *Action required: Review API/config changes before deploying*")
            else:
                lines.append(f"- {human_text}{ticket_str}")

            # Add commit ref for traceability
            lines.append(f"  *(commit: `{commit.short_hash}` — {commit.date})*")

        lines.append("")

    # ── Deployment Notes ──────────────────────────────────────────
    lines += [
        "---",
        "",
        "## 📋 Deployment Notes",
        "",
        f"| Field                  | Value                              |",
        f"|------------------------|------------------------------------|",
        f"| Version                | {version}                          |",
        f"| Previous version       | *(check Artifactory for rollback)* |",
        f"| Deployment window      | As per maintenance schedule        |",
        f"| Estimated deploy time  | 30–45 minutes                      |",
        f"| Rollback time          | < 15 minutes                       |",
        f"| Change request         | Raise CHG ticket before deploying  |",
        f"",
        "### Post-deployment checklist",
        "- [ ] Health endpoint returns HTTP 200",
        "- [ ] Smoke tests passing",
        "- [ ] Response time within SLA thresholds",
        "- [ ] No error rate spike in Splunk / Dynatrace",
        "- [ ] Stakeholders notified of successful deployment",
        "",
        "---",
        "",
        f"*Generated by AI Release Notes Generator — "
        f"github.com/tayyab-karem/ai-release-notes*",
    ]

    return '\n'.join(lines)
