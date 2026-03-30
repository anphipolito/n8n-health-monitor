# -----------------------------------------------------------------------------
# Rule        : no_retry_on_http
# Severity    : Medium
# Purpose     : Ensure HTTP Request nodes are configured to retry on failure,
#               reducing fragility caused by transient network errors.
# What to check: Every node whose type contains "httpRequest". Flag it if
#               retryOnFail is False or the key is absent entirely.
# Prompt hint : To tighten this rule, also check parameters.options.timeout
#               or require a specific retry count. To loosen it, whitelist
#               internal-only endpoints that don't need retries.
# -----------------------------------------------------------------------------

from datetime import datetime, timezone


def check_no_retry_on_http(workflow):
    issues = []
    workflow_id = workflow.get("workflow_id", "unknown")

    for node in workflow.get("nodes", []):
        # n8n HTTP Request nodes carry "httpRequest" in their type string
        # (e.g. "n8n-nodes-base.httpRequest"), so a substring check is enough
        if "httpRequest" not in node.get("type", ""):
            continue

        # retryOnFail is a top-level node property, not inside parameters;
        # missing key is treated the same as False (not configured)
        if not node.get("retryOnFail", False):
            issues.append({
                "rule_name": "no_retry_on_http",
                "severity": "medium",
                "workflow_id": workflow_id,
                "message": f"Node '{node.get('name', node.get('id', 'unknown'))}' is an HTTP Request node with no retry on failure.",
                "detected_at": datetime.now(timezone.utc).isoformat(),
            })

    return issues
