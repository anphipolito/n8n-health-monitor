# -----------------------------------------------------------------------------
# Rule        : missing_error_handler
# Severity    : High
# Purpose     : Ensure every workflow has a designated error-handling workflow
#               so that failures are caught and acted on rather than silently
#               dropped. Without this, a crashed workflow produces no alert.
# What to check: workflow["settings"]["errorWorkflow"] must be present and
#               non-empty. This is a built-in n8n setting, not a node type.
# Prompt hint : To extend this rule, also verify that the referenced error
#               workflow actually exists (requires a cross-workflow lookup).
#               To skip trigger-only workflows, check whether the workflow
#               has any active execution nodes before flagging.
# -----------------------------------------------------------------------------

from datetime import datetime, timezone


def check_missing_error_handler(workflow):
    # n8n stores the error workflow ID under settings.errorWorkflow;
    # an absent settings key or an empty string both count as unconfigured
    if workflow.get("settings", {}).get("errorWorkflow"):
        return []

    # One issue per workflow — this is a global configuration gap, not per-node
    return [{
        "rule_name": "missing_error_handler",
        "severity": "high",
        "workflow_id": workflow.get("workflow_id", "unknown"),
        "message": "Workflow has no error handler configured in settings.",
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }]
