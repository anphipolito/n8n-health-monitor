# -----------------------------------------------------------------------------
# Rule        : no_env_var_separation
# Severity    : Medium
# Purpose     : Detect hardcoded internal/localhost URLs in node parameters.
#               These should be environment variables so the workflow can run
#               across dev, staging, and production without manual edits.
# What to check: Recursively scan all node parameters for strings that match
#               localhost, 127.x, or RFC-1918 private IP ranges
#               (10.x, 192.168.x, 172.16–31.x).
# Prompt hint : To expand coverage, also flag hardcoded port numbers on
#               known internal services (e.g. :5678 for n8n itself).
#               To reduce noise, whitelist specific nodes by name or type
#               (e.g. health-check nodes are expected to call localhost).
# -----------------------------------------------------------------------------

import re
from datetime import datetime, timezone

# Matches http/https URLs pointing at localhost or private IP ranges.
# RFC-1918 private ranges: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
_INTERNAL_URL_PATTERN = re.compile(
    r'https?://'
    r'(?:localhost|127\.\d+\.\d+\.\d+|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)'
)


def _find_internal_urls(value):
    """Recursively search a parameters structure for internal URLs. Returns list of matched URLs."""
    if isinstance(value, str):
        return _INTERNAL_URL_PATTERN.findall(value)
    if isinstance(value, dict):
        # Recurse into dict values; keys are parameter names, not user data
        found = []
        for v in value.values():
            found.extend(_find_internal_urls(v))
        return found
    if isinstance(value, list):
        # Parameters can contain lists (e.g. query params, headers arrays)
        found = []
        for item in value:
            found.extend(_find_internal_urls(item))
        return found
    # Numbers, booleans, None — nothing to scan
    return []


def check_no_env_var_separation(workflow):
    issues = []
    workflow_id = workflow.get("workflow_id", "unknown")

    for node in workflow.get("nodes", []):
        urls = _find_internal_urls(node.get("parameters", {}))

        # Deduplicate per node: the same URL repeated in different fields
        # should produce only one issue to avoid alert noise
        seen = set()
        for url in urls:
            if url in seen:
                continue
            seen.add(url)
            issues.append({
                "rule_name": "no_env_var_separation",
                "severity": "medium",
                "workflow_id": workflow_id,
                "message": f"Node '{node.get('name', node.get('id', 'unknown'))}' contains a hardcoded internal URL '{url}' in its parameters.",
                "detected_at": datetime.now(timezone.utc).isoformat(),
            })

    return issues
