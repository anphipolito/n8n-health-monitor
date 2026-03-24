# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A system that continuously monitors n8n workflows for production-readiness issues, tracks health scores over time, alerts on changes via Slack, and blocks deploys when critical issues are found.

## Input modes
- API: fetch live workflows from n8n REST API
- File: load exported workflow JSON files from a local folder

## Core features
1. Health checks — scan workflows against production-readiness rules
2. Continuous monitoring — Prefect scheduled flow, runs on a schedule
3. Change detection — only alert when something changes vs last run
4. Slack alerts — notify on new issues or resolved issues
5. Score tracking — store results per run for trend analysis
6. CI/CD gate — GitHub Actions blocks deploy on High severity issues
7. Trend dashboard — simple HTML dashboard showing scores over time

## Rules
- Missing error handler (High)
- Hardcoded credentials (High)
- AI node without input validation (High)
- No retry on HTTP nodes (Medium)
- Loop Over Items with more than 5 nodes (Medium)
- No environment separation (Medium)
- No sticky note documentation (Low)

## Stack
- Python
- SQLite via SQLAlchemy (DATABASE_URL in .env — swappable to Postgres later)
- Prefect (scheduling)
- Jinja2 (HTML report)
- requests (n8n API)
- python-dotenv
- argparse (CLI)
- Slack SDK (alerts)

## Project structure
n8n-health-monitor/
├── main.py
├── fetcher.py
├── analyzer.py
├── diff.py
├── notifier.py
├── reporter.py
├── storage.py
├── rules/
│   ├── __init__.py
│   ├── error_handling.py
│   ├── credentials.py
│   ├── retries.py
│   ├── loops.py
│   ├── environment.py
│   └── documentation.py
├── templates/
│   └── report.html
├── flows/
│   └── monitor_flow.py
├── .github/
│   └── workflows/
│       └── health_gate.yml
├── dashboard/
│   └── index.html
├── Dockerfile
├── .env.example
└── README.md

## Database
SQLite via SQLAlchemy. Two tables:
- workflow_runs: one row per workflow per run
  (id, run_at, workflow_id, workflow_name, health_score, 
   high_count, medium_count, low_count)
- workflow_issues: one row per issue found
  (id, run_id, workflow_id, rule_name, severity, message, 
   first_seen_at, resolved_at)

## Architecture principles

- Fetching, analyzing, reporting, and storing are fully separate modules
- `analyzer.py` is used by both the Prefect flow and the GitHub Actions gate — keep it dependency-free from Prefect
- Each rule is its own file in `rules/`; `rules/__init__.py` aggregates them
- `DATABASE_URL` in `.env` makes storage swappable from SQLite to Postgres with one line change
- `diff.py` compares current run results against the previous run to drive change-only Slack alerts

## Build order

1. `fetcher.py`
2. `rules/` (one file at a time)
3. `analyzer.py`
4. `storage.py`
5. `diff.py`
6. `notifier.py`
7. `flows/monitor_flow.py`
8. `.github/workflows/health_gate.yml`
9. `reporter.py` + `templates/report.html`
10. `dashboard/index.html`

## Running the monitor

```bash
# API mode (fetch live workflows)
python main.py --mode api

# File mode (load exported JSON from a folder)
python main.py --mode file --input-dir ./workflows

# Run Prefect flow directly
python flows/monitor_flow.py
```

## Environment

Copy `.env.example` to `.env` and fill in:
- `N8N_API_URL`, `N8N_API_KEY` — n8n instance connection
- `DATABASE_URL` — defaults to `sqlite:///health.db`
- `SLACK_BOT_TOKEN`, `SLACK_CHANNEL` — for alerts