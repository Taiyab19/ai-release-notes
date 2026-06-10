#!/usr/bin/env python3
"""
generate_release_notes.py — AI-powered Release Notes Generator
Author : Tayyab Karem — Release Management Specialist
GitHub : github.com/tayyab-karem/ai-release-notes

Usage:
    python generate_release_notes.py --mock
    python generate_release_notes.py --from v1.3.0 --to v1.4.0
    python generate_release_notes.py --since 2025-01-01 --format json
    python generate_release_notes.py --dry-run
"""

import argparse
import os
import sys
from datetime import date
from pathlib import Path

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate AI-powered release notes from Git commit history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_release_notes.py --mock
  python generate_release_notes.py --from v1.3.0 --to v1.4.0
  python generate_release_notes.py --since 2025-01-01
  python generate_release_notes.py --dry-run
  python generate_release_notes.py --app payment-service --version 2.4.0 --format json
        """
    )

    # Source options
    src = parser.add_argument_group('Source (what commits to include)')
    src.add_argument('--from',    dest='from_ref', metavar='REF',
                     help='Start tag/branch/commit (e.g. v1.3.0)')
    src.add_argument('--to',      dest='to_ref',   metavar='REF',
                     help='End tag/branch/commit (e.g. v1.4.0, default: HEAD)')
    src.add_argument('--since',   metavar='DATE',
                     help='Start date (e.g. 2025-01-01)')
    src.add_argument('--until',   metavar='DATE',
                     help='End date (e.g. 2025-01-31)')
    src.add_argument('--max',     type=int, default=50, metavar='N',
                     help='Maximum number of commits (default: 50)')
    src.add_argument('--repo',    default='.', metavar='PATH',
                     help='Path to git repository (default: current directory)')

    # Release metadata
    meta = parser.add_argument_group('Release metadata')
    meta.add_argument('--app',     default='Application', metavar='NAME',
                      help='Application name (default: Application)')
    meta.add_argument('--version', default=None, metavar='VER',
                      help='Release version (default: auto-detect from git tags)')
    meta.add_argument('--env',     default='Production', metavar='ENV',
                      help='Target environment (default: Production)')

    # Output options
    out = parser.add_argument_group('Output')
    out.add_argument('--format',  choices=['markdown', 'json', 'text'], default='markdown',
                     help='Output format (default: markdown)')
    out.add_argument('--output',  metavar='PATH',
                     help='Output file path (default: output/RELEASE_NOTES_<version>.md)')
    out.add_argument('--stdout',  action='store_true',
                     help='Print to stdout instead of saving to file')

    # Modes
    modes = parser.add_argument_group('Modes')
    modes.add_argument('--mock',     action='store_true',
                       help='Use mock generator (no API key needed — great for demos)')
    modes.add_argument('--dry-run',  action='store_true',
                       help='Show commits that would be included, without generating')
    modes.add_argument('--api-key',  metavar='KEY',
                       help='Anthropic API key (overrides ANTHROPIC_API_KEY env var)')

    return parser.parse_args()


def main():
    args = parse_args()

    print("═" * 60)
    print("  AI Release Notes Generator")
    print("  github.com/tayyab-karem/ai-release-notes")
    print("═" * 60)

    # ── Step 1: Extract commits ───────────────────────────────────
    print(f"\n📂 Reading commits from: {os.path.abspath(args.repo)}")

    from scripts.git_parser import get_commits, get_repo_info, get_tags

    try:
        commits = get_commits(
            repo_path  = args.repo,
            from_ref   = args.from_ref,
            to_ref     = args.to_ref,
            since      = args.since,
            until      = args.until,
            max_count  = args.max,
        )
    except RuntimeError as e:
        # If not a git repo, use sample commits for demo
        print(f"⚠️  Git note: {e}")
        print("   Using sample commits for demonstration...\n")
        commits = _get_sample_commits()

    if not commits:
        print("❌ No commits found for the specified range.")
        print("   Try: --mock  or adjust your --from / --since parameters")
        sys.exit(0)

    print(f"✅ Found {len(commits)} commits")

    # ── Step 2: Dry run — just show commits ───────────────────────
    if args.dry_run:
        from scripts.formatter import print_dry_run
        print_dry_run(commits)
        print("ℹ️  Dry run complete. Remove --dry-run to generate release notes.")
        return

    # ── Step 3: Resolve version ───────────────────────────────────
    version = args.version
    if not version:
        try:
            tags = get_tags(args.repo)
            version = tags[0] if tags else f"v1.0.{date.today().strftime('%Y%m%d')}"
        except Exception:
            version = f"v1.0.{date.today().strftime('%Y%m%d')}"

    print(f"🏷️  Version: {version}")
    print(f"🌍 Environment: {args.env}")
    print(f"📦 Application: {args.app}")

    # ── Step 4: Generate release notes ───────────────────────────
    if args.mock:
        print("\n🤖 Generating release notes (mock mode — no API call)...")
        from scripts.mock_generator import generate_mock
        content = generate_mock(commits, args.app, version, args.env)
        print("✅ Release notes generated (mock)")
    else:
        print("\n🤖 Generating release notes via Claude AI...")
        try:
            from scripts.ai_generator import generate_with_claude
            content = generate_with_claude(
                commits     = commits,
                app_name    = args.app,
                version     = version,
                environment = args.env,
                api_key     = args.api_key,
            )
            print("✅ Release notes generated by Claude AI")
        except (ImportError, ValueError, RuntimeError) as e:
            print(f"⚠️  AI generation failed: {e}")
            print("   Falling back to mock generator...")
            from scripts.mock_generator import generate_mock
            content = generate_mock(commits, args.app, version, args.env)

    # ── Step 5: Format and output ─────────────────────────────────
    from scripts.formatter import (
        save_markdown, save_json, to_json, to_plain_text, print_dry_run
    )

    safe_version = version.replace('/', '-').replace(' ', '-')

    if args.stdout:
        if args.format == 'json':
            import json
            payload = to_json(commits, content, args.app, version, args.env)
            print(json.dumps(payload, indent=2, default=str))
        elif args.format == 'text':
            print(to_plain_text(content))
        else:
            print(content)
        return

    # Save to file
    if args.format == 'json':
        output_path = args.output or f"output/release-{safe_version}.json"
        payload = to_json(commits, content, args.app, version, args.env)
        saved = save_json(payload, output_path)
        print(f"\n💾 JSON saved: {saved}")

    elif args.format == 'text':
        output_path = args.output or f"output/RELEASE_NOTES_{safe_version}.txt"
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(to_plain_text(content))
        saved = output_path
        print(f"\n💾 Text file saved: {saved}")

    else:  # markdown (default)
        output_path = args.output or f"output/RELEASE_NOTES_{safe_version}.md"
        saved = save_markdown(content, output_path)
        print(f"\n💾 Markdown saved: {saved}")

    # Preview first few lines
    print("\n" + "─" * 60)
    print("  PREVIEW (first 20 lines):")
    print("─" * 60)
    for line in content.split('\n')[:20]:
        print(f"  {line}")
    print("  ...")
    print("─" * 60)
    print(f"\n✅ Done! Open {saved} to see the full release notes.\n")


def _get_sample_commits():
    """Return sample commits for demo when not run inside a git repo."""
    from dataclasses import dataclass
    from scripts.git_parser import ParsedCommit

    samples = [
        ("feat",  "auth",     "add OAuth2 support for enterprise SSO",        False),
        ("fix",   "payments", "resolve timeout on high-volume transactions",   False),
        ("feat",  "api",      "add rate limiting to public endpoints",         False),
        ("chore", "deps",     "upgrade Flask from 2.3 to 3.0",                False),
        ("fix",   "deploy",   "correct health check endpoint path",            False),
        ("feat",  "reports",  "add real-time deployment dashboard",            False),
        ("perf",  "db",       "optimise slow queries on transactions table",   False),
        ("fix",   "auth",     "fix session expiry not triggering on logout",   False),
        ("docs",  "",         "update API documentation for v2 endpoints",     False),
        ("feat",  "webhook",  "BREAKING CHANGE: rename webhook payload fields",True),
    ]

    commits = []
    for i, (ctype, scope, subject, breaking) in enumerate(samples):
        from scripts.git_parser import COMMIT_TYPE_MAP, DEFAULT_TYPE
        type_info = COMMIT_TYPE_MAP.get(ctype, DEFAULT_TYPE)
        commits.append(ParsedCommit(
            hash         = f"abc{i:04d}ef",
            short_hash   = f"abc{i:04d}",
            author       = "Tayyab Karem",
            date         = "2025-01-15",
            raw_message  = f"{ctype}({scope}): {subject}" if scope else f"{ctype}: {subject}",
            commit_type  = ctype,
            category     = type_info[0],
            category_label = type_info[1],
            scope        = scope,
            subject      = subject,
            body         = "",
            is_breaking  = breaking,
            ticket_refs  = [f"PROJ-{100+i}"] if i % 3 == 0 else [],
        ))
    return commits


if __name__ == "__main__":
    main()
