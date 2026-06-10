"""
git_parser.py — Extract and parse commits from Git history

Reads git log between tags/branches/dates and structures
commit data for the AI generator to process.
"""

import subprocess
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ── Commit types (Conventional Commits standard) ──────────────────
COMMIT_TYPE_MAP = {
    "feat":     ("feature",     "New Features"),
    "fix":      ("bugfix",      "Bug Fixes"),
    "hotfix":   ("bugfix",      "Bug Fixes"),
    "perf":     ("performance", "Performance Improvements"),
    "refactor": ("refactor",    "Code Refactoring"),
    "docs":     ("docs",        "Documentation"),
    "chore":    ("maintenance", "Maintenance"),
    "build":    ("maintenance", "Maintenance"),
    "ci":       ("maintenance", "Maintenance"),
    "test":     ("testing",     "Testing"),
    "style":    ("style",       "Style / Formatting"),
    "revert":   ("revert",      "Reverts"),
    "security": ("security",    "Security"),
    "deps":     ("maintenance", "Maintenance"),
}

DEFAULT_TYPE = ("other", "Other Changes")


@dataclass
class ParsedCommit:
    """Structured representation of a single Git commit."""
    hash:            str
    short_hash:      str
    author:          str
    date:            str
    raw_message:     str
    commit_type:     str        # feat | fix | chore | etc.
    category:        str        # feature | bugfix | maintenance | etc.
    category_label:  str        # "New Features" | "Bug Fixes" | etc.
    scope:           str        # component/module name if present
    subject:         str        # clean commit subject line
    body:            str        # full commit body
    is_breaking:     bool       # BREAKING CHANGE detected
    ticket_refs:     list       # JIRA/ServiceNow ticket refs found


def _run_git(args: list[str], cwd: str = ".") -> str:
    """Run a git command and return stdout. Raises on failure."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git error: {result.stderr.strip()}")
        return result.stdout.strip()
    except FileNotFoundError:
        raise RuntimeError("Git is not installed or not in PATH.")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Git command timed out.")


def _parse_conventional_commit(message: str) -> tuple[str, str, str]:
    """
    Parse a conventional commit message.
    Returns: (type, scope, subject)

    Examples:
      "feat(auth): add OAuth2 support"  → ("feat", "auth", "add OAuth2 support")
      "fix: resolve timeout issue"      → ("fix", "",     "resolve timeout issue")
      "random commit message"           → ("other", "",   "random commit message")
    """
    # Match: type(scope): subject  OR  type: subject
    pattern = r'^(\w+)(?:\(([^)]+)\))?!?:\s*(.+)$'
    match = re.match(pattern, message.strip().split('\n')[0])
    if match:
        return match.group(1).lower(), match.group(2) or "", match.group(3).strip()
    return "other", "", message.strip().split('\n')[0]


def _extract_ticket_refs(text: str) -> list[str]:
    """Extract JIRA/ServiceNow/GitHub ticket references from commit text."""
    patterns = [
        r'\b([A-Z]{2,}-\d+)\b',          # JIRA: PROJ-123
        r'\bCHG\d+\b',                    # ServiceNow: CHG001234
        r'\bINC\d+\b',                    # ServiceNow: INC001234
        r'(?:closes?|fixes?|refs?)\s+#(\d+)',  # GitHub: closes #123
    ]
    refs = []
    for pattern in patterns:
        refs.extend(re.findall(pattern, text, re.IGNORECASE))
    return list(set(refs))


def _parse_commit_block(block: str) -> Optional[ParsedCommit]:
    """Parse a single commit block from git log output."""
    if not block.strip():
        return None

    lines = block.strip().split('\n')
    if len(lines) < 4:
        return None

    try:
        commit_hash  = lines[0].replace('HASH:', '').strip()
        author       = lines[1].replace('AUTHOR:', '').strip()
        date_str     = lines[2].replace('DATE:', '').strip()
        raw_message  = '\n'.join(lines[3:]).replace('MSG:', '', 1).strip()
    except IndexError:
        return None

    # Parse conventional commit format
    commit_type, scope, subject = _parse_conventional_commit(raw_message)

    # Map to category
    type_info    = COMMIT_TYPE_MAP.get(commit_type, DEFAULT_TYPE)
    category     = type_info[0]
    category_label = type_info[1]

    # Detect breaking changes
    is_breaking = (
        'BREAKING CHANGE' in raw_message or
        'BREAKING-CHANGE' in raw_message or
        bool(re.match(r'^\w+(?:\([^)]+\))?!:', raw_message))
    )

    # Extract body (everything after first line)
    body_lines = raw_message.split('\n')[1:]
    body = '\n'.join(body_lines).strip()

    return ParsedCommit(
        hash=commit_hash,
        short_hash=commit_hash[:7],
        author=author,
        date=date_str,
        raw_message=raw_message,
        commit_type=commit_type,
        category=category,
        category_label=category_label,
        scope=scope,
        subject=subject if subject else raw_message.split('\n')[0],
        body=body,
        is_breaking=is_breaking,
        ticket_refs=_extract_ticket_refs(raw_message),
    )


def get_commits(
    repo_path: str = ".",
    from_ref:  Optional[str] = None,
    to_ref:    Optional[str] = None,
    since:     Optional[str] = None,
    until:     Optional[str] = None,
    max_count: int = 50,
    exclude_merges: bool = True,
) -> list[ParsedCommit]:
    """
    Extract and parse commits from a Git repository.

    Args:
        repo_path:      Path to the Git repo (default: current directory)
        from_ref:       Start tag/branch/commit (e.g. "v1.3.0")
        to_ref:         End tag/branch/commit (e.g. "v1.4.0")
        since:          Start date (e.g. "2025-01-01")
        until:          End date (e.g. "2025-01-31")
        max_count:      Maximum number of commits to retrieve
        exclude_merges: Skip merge commits (default: True)

    Returns:
        List of ParsedCommit objects, newest first.
    """
    # Build git log arguments
    fmt = 'HASH:%H%nAUTHOR:%an%nDATE:%ad%nMSG:%s%n%b%n---COMMIT-END---'
    args = [
        'log',
        f'--pretty=format:{fmt}',
        '--date=short',
        f'--max-count={max_count}',
    ]

    if exclude_merges:
        args.append('--no-merges')

    # Range: between two refs
    if from_ref and to_ref:
        args.append(f'{from_ref}..{to_ref}')
    elif from_ref:
        args.append(f'{from_ref}..HEAD')
    elif to_ref:
        args.append(to_ref)

    # Date range
    if since:
        args.append(f'--since={since}')
    if until:
        args.append(f'--until={until}')

    raw_output = _run_git(args, cwd=repo_path)

    if not raw_output:
        return []

    # Split into individual commit blocks
    blocks = raw_output.split('---COMMIT-END---')
    commits = []
    for block in blocks:
        commit = _parse_commit_block(block)
        if commit:
            commits.append(commit)

    return commits


def get_tags(repo_path: str = ".") -> list[str]:
    """Return all tags in the repo, newest first."""
    try:
        raw = _run_git(['tag', '--sort=-version:refname'], cwd=repo_path)
        return [t.strip() for t in raw.split('\n') if t.strip()]
    except RuntimeError:
        return []


def get_repo_info(repo_path: str = ".") -> dict:
    """Return basic repo metadata."""
    info = {}
    try:
        info['remote_url']    = _run_git(['remote', 'get-url', 'origin'], cwd=repo_path)
        info['current_branch']= _run_git(['rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo_path)
        info['latest_tag']    = _run_git(['describe', '--tags', '--abbrev=0'], cwd=repo_path)
        info['latest_commit'] = _run_git(['rev-parse', '--short', 'HEAD'], cwd=repo_path)
    except RuntimeError:
        pass
    return info


def group_commits_by_type(commits: list[ParsedCommit]) -> dict[str, list[ParsedCommit]]:
    """Group commits by their category label for structured output."""
    groups: dict[str, list[ParsedCommit]] = {}
    # Ensure breaking changes always come first
    breaking = [c for c in commits if c.is_breaking]
    if breaking:
        groups['⚠️  Breaking Changes'] = breaking

    for commit in commits:
        if commit.is_breaking:
            continue
        label = commit.category_label
        groups.setdefault(label, []).append(commit)

    return groups


def summarise_commits(commits: list[ParsedCommit]) -> dict:
    """Return a summary dict of commit stats."""
    return {
        'total':          len(commits),
        'features':       sum(1 for c in commits if c.category == 'feature'),
        'bugfixes':       sum(1 for c in commits if c.category == 'bugfix'),
        'maintenance':    sum(1 for c in commits if c.category == 'maintenance'),
        'breaking':       sum(1 for c in commits if c.is_breaking),
        'with_tickets':   sum(1 for c in commits if c.ticket_refs),
        'authors':        list(set(c.author for c in commits)),
        'date_range':     {
            'from': commits[-1].date if commits else None,
            'to':   commits[0].date  if commits else None,
        },
    }
