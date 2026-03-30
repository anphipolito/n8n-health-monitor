# -----------------------------------------------------------------------------
# Rule        : no_sticky_note_doc
# Severity    : Low
# Purpose     : Encourage workflow documentation by flagging workflows that
#               have no sticky note nodes. Sticky notes are the standard n8n
#               mechanism for leaving human-readable explanations inline.
# What to check: Scan all nodes for at least one with type
#               "n8n-nodes-base.stickyNote". If none exist, raise one
#               workflow-level issue.
# Prompt hint : To refine this rule, check that the sticky note content is
#               non-empty (parameters.content) or meets a minimum length.
#               To disable for simple one-node workflows, add a min node
#               count guard (e.g. skip if len(nodes) < 3).
# -----------------------------------------------------------------------------

from datetime import datetime, timezone


def check_no_sticky_note_doc(workflow):
    # A single sticky note anywhere in the workflow satisfies the rule;
    # we don't care about placement or content at this severity level
    has_sticky = any(
        node.get("type") == "n8n-nodes-base.stickyNote"
        for node in workflow.get("nodes", [])
    )
    if has_sticky:
        return []

    # One issue per workflow — this is not a per-node check
    return [{
        "rule_name": "no_sticky_note_doc",
        "severity": "low",
        "workflow_id": workflow.get("workflow_id", "unknown"),
        "message": "Workflow has no sticky note documentation.",
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }]
