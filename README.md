# AI Release Notes Generator 🤖

> A Python tool that reads your Git commit history and automatically generates
> professional, structured release notes using an LLM (Claude AI / Anthropic API).
> Built to demonstrate the intersection of Release Management expertise and
> modern AI/GenAI skills.

---

## Why This Exists

Writing release notes manually is one of the most time-consuming, error-prone
parts of a release cycle. Release Managers spend hours reading commits, grouping
changes, and translating technical jargon into stakeholder-friendly language.

This tool automates that entire process in seconds.

---

## What It Does

```
Git Repository
     │
     ▼
┌─────────────────────────────────────┐
│  1. EXTRACT                         │
│     Read commits between two tags   │
│     or date ranges from Git log     │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  2. ENRICH                          │
│     Parse conventional commits,     │
│     detect breaking changes,        │
│     group by type (feat/fix/chore)  │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  3. GENERATE (Claude AI)            │
│     Send structured commit data     │
│     to Anthropic API → get polished │
│     release notes in return         │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  4. OUTPUT                          │
│     Markdown file  ✓                │
│     JSON (for ServiceNow/Jira) ✓    │
│     Plain text     ✓                │
└─────────────────────────────────────┘
```

---

## Sample Output

Given commits like:
```
feat(auth): add OAuth2 support for enterprise SSO
fix(payments): resolve timeout on high-volume transactions
feat(api): add rate limiting to public endpoints
chore(deps): upgrade Flask from 2.3 to 3.0
fix(deploy): correct health check endpoint path
```

The tool generates:

---

**Release Notes — v2.4.0**
*Released: 2025-01-15 | Environment: Production*

### 🚀 New Features
- **Enterprise SSO Support** — OAuth2 integration enables single sign-on for enterprise customers, reducing login friction and improving security posture.
- **API Rate Limiting** — Public endpoints now enforce rate limits to protect service stability under high traffic conditions.

### 🐛 Bug Fixes
- **Payment Reliability** — Resolved a timeout issue affecting high-volume transaction processing. Customers should see improved reliability during peak periods.
- **Deployment Health Checks** — Corrected health check endpoint path, ensuring accurate monitoring and faster incident detection post-deployment.

### 🔧 Maintenance
- Upgraded Flask framework to v3.0 for improved performance and security patches.

---

## Features

| Feature | Description |
|---------|-------------|
| Git log parsing | Reads commits between any two tags, branches, or dates |
| Conventional commits | Detects feat/fix/chore/docs/refactor automatically |
| AI summarisation | Claude AI rewrites technical commits into plain English |
| Breaking change detection | Flags `BREAKING CHANGE` commits prominently |
| Multiple output formats | Markdown, JSON (Jira/ServiceNow-ready), plain text |
| Dry run mode | Preview commits without calling the API |
| Custom templates | Bring your own release notes template |
| Mock mode | Works without an API key for demo/testing |

---

## Repository Structure

```
ai-release-notes/
├── generate_release_notes.py   # Main CLI script
├── scripts/
│   ├── git_parser.py           # Git log extraction & parsing
│   ├── ai_generator.py         # Anthropic API integration
│   ├── formatter.py            # Output formatting (MD/JSON/text)
│   └── mock_generator.py       # Mock AI for demo/testing
├── templates/
│   └── release_notes.md        # Default release notes template
├── tests/
│   ├── test_git_parser.py      # Unit tests — git parsing
│   ├── test_formatter.py       # Unit tests — formatting
│   └── test_mock_generator.py  # Unit tests — mock generator
├── output/                     # Generated release notes land here
├── .env.example                # API key setup guide
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Install
```bash
git clone https://github.com/tayyab-karem/ai-release-notes.git
cd ai-release-notes
pip install -r requirements.txt
```

### 2. Add your API key (optional — mock mode works without it)
```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
# Get one free at: console.anthropic.com
```

### 3. Run

```bash
# Generate release notes for last 20 commits (mock mode — no API key needed)
python generate_release_notes.py --mock

# Generate from real git log (last 20 commits)
python generate_release_notes.py

# Generate between two tags
python generate_release_notes.py --from v1.3.0 --to v1.4.0

# Generate from a date range
python generate_release_notes.py --since "2025-01-01" --until "2025-01-31"

# Specify output format
python generate_release_notes.py --format json
python generate_release_notes.py --format markdown
python generate_release_notes.py --format text

# Preview commits without generating (dry run)
python generate_release_notes.py --dry-run

# Specify app name and version
python generate_release_notes.py --app "payment-service" --version "2.4.0"
```

---

## Integration Ideas

This tool slots naturally into a Jenkins or GitHub Actions pipeline:

```groovy
// Jenkinsfile — auto-generate release notes as part of the pipeline
stage('Generate Release Notes') {
    steps {
        sh '''
            python generate_release_notes.py \
                --from ${PREV_TAG} \
                --to ${VERSION} \
                --app ${APP_NAME} \
                --format markdown \
                --output artifacts/RELEASE_NOTES.md
        '''
        archiveArtifacts artifacts: 'artifacts/RELEASE_NOTES.md'
    }
}
```

---

## Tools & Technologies

`Python 3.11` · `Anthropic Claude API` · `GitPython` · `subprocess` · `argparse` ·
`python-dotenv` · `pytest` · `Release Management` · `CI/CD` · `ITSM`

---

## Author

**Tayyab Karem** — Release Management Specialist | DevOps & Production Support | ITSM
📍 Pune, India | 🔗 [LinkedIn](https://www.linkedin.com/in/tayyab-karem/) | Available immediately

> *This project demonstrates the combination of 10+ years of Release Management
> expertise with modern AI/GenAI skills — automating one of the most manual
> parts of the release cycle.*
