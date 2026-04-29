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

from rules.issue import Issue


def check_no_retry_on_http(workflow):
    issues = []

    for node in workflow.get("nodes", []):
        # n8n HTTP Request nodes carry "httpRequest" in their type string
        # (e.g. "n8n-nodes-base.httpRequest"), so a substring check is enough
        if "httpRequest" not in node.get("type", ""):
            continue

        # retryOnFail is a top-level node property, not inside parameters;
        # missing key is treated the same as False (not configured)
        if not node.get("retryOnFail", False):
            issues.append(Issue(
                rule_name="no_retry_on_http",
                severity="medium",
                message=f"Node '{node.get('name', node.get('id', 'unknown'))}' is an HTTP Request node with no retry on failure.",
            ))

    return issues
