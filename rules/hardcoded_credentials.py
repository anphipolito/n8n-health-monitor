# -----------------------------------------------------------------------------
# Rule        : hardcoded_credentials
# Severity    : High
# Purpose     : Detect secrets, passwords, or API keys stored directly in
#               workflow parameters. Hardcoded credentials are a critical
#               security risk — they end up in exports, version history, and
#               backups in plain text.
# What to check: Two complementary signals in node parameters:
#               1. Sensitive key names (password, secret, token, etc.)
#               2. Values that match known credential formats (Bearer tokens,
#                  OpenAI keys, Slack tokens, AWS key IDs, long base64 blobs)
#               n8n dynamic expressions (={{ ... }}) are skipped — those
#               resolve at runtime and are not hardcoded.
# Prompt hint : To reduce false positives, raise the base64 length threshold
#               above 40 or tighten the key name list. To add providers,
#               extend _CREDENTIAL_VALUE_PATTERN with their key prefixes
#               (e.g. "ghp_" for GitHub PATs, "glpat-" for GitLab tokens).
# -----------------------------------------------------------------------------

import re
from datetime import datetime, timezone

# Parameter key names that commonly hold credentials.
# Case-insensitive so "Password", "API_KEY", "Authorization" all match.
_SENSITIVE_KEY_PATTERN = re.compile(
    r'password|secret|token|api_key|apikey|passwd|authorization',
    re.IGNORECASE,
)

# Value patterns for well-known credential formats.
# Each alternative targets a specific provider or encoding:
_CREDENTIAL_VALUE_PATTERN = re.compile(
    r'(?:'
    r'Bearer\s+\S{10,}'               # HTTP Authorization: Bearer <token>
    r'|sk-[A-Za-z0-9]{20,}'          # OpenAI secret keys
    r'|xox[bpoa]-[A-Za-z0-9-]{10,}'  # Slack bot/user/app tokens
    r'|AKIA[A-Z0-9]{16}'             # AWS IAM access key IDs
    r'|[A-Za-z0-9+/]{40,}'           # Generic long base64 strings (40+ chars)
    r')'
)

# n8n expressions look like ={{ $json.someField }} — they are dynamic
# references resolved at runtime, not hardcoded values; skip them
_N8N_EXPRESSION = re.compile(r'^\s*=\s*\{')


def _scan_parameters(params, node_name, workflow_id, issues):
    """Recursively walk parameters, flagging suspicious key/value pairs."""
    if isinstance(params, dict):
        for key, value in params.items():
            if isinstance(value, str) and not _N8N_EXPRESSION.match(value):
                # Key-name check: flag regardless of value content
                if _SENSITIVE_KEY_PATTERN.search(key):
                    issues.append({
                        "rule_name": "hardcoded_credentials",
                        "severity": "high",
                        "workflow_id": workflow_id,
                        "message": f"Node '{node_name}' may contain a hardcoded credential in parameter '{key}'.",
                        "detected_at": None,  # filled by caller with a single timestamp
                    })
                # Value-pattern check: key name is neutral but value looks like a secret
                elif _CREDENTIAL_VALUE_PATTERN.search(value):
                    issues.append({
                        "rule_name": "hardcoded_credentials",
                        "severity": "high",
                        "workflow_id": workflow_id,
                        "message": f"Node '{node_name}' may contain a hardcoded credential in parameter '{key}'.",
                        "detected_at": None,
                    })
            else:
                # Value is not a plain string — recurse into nested dicts/lists
                _scan_parameters(value, node_name, workflow_id, issues)
    elif isinstance(params, list):
        for item in params:
            _scan_parameters(item, node_name, workflow_id, issues)


def check_hardcoded_credentials(workflow):
    issues = []
    workflow_id = workflow.get("workflow_id", "unknown")

    # One timestamp for the entire run so all issues in this workflow share it
    now = datetime.now(timezone.utc).isoformat()

    for node in workflow.get("nodes", []):
        node_name = node.get("name", node.get("id", "unknown"))
        node_issues = []
        _scan_parameters(node.get("parameters", {}), node_name, workflow_id, node_issues)

        # Stamp detected_at here rather than inside the recursive helper
        # to avoid repeated datetime.now() calls per issue
        for issue in node_issues:
            issue["detected_at"] = now
        issues.extend(node_issues)

    return issues
