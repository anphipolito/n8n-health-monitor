# -----------------------------------------------------------------------------
# Rule        : no_sticky_note_doc
# Severity    : Low
# Purpose     : Encourage workflow documentation by flagging workflows that
#               have no sticky note nodes. Sticky notes are the standard n8n
#               mechanism for leaving human-readable explanations inline.
# What to check: Scan all nodes for at least one with type
#               "n8n-nodes-base.stickyNote".If exist, check if the sticky note content is the default placeholder text, which indicates it's likely not being used for documentation. If so, raise a low-severity issue. If no sticky note nodes are found at all, raise a different low-severity issue.

# Prompt hint : To refine this rule, check that the sticky note content is
#               non-empty (parameters.content) or meets a minimum length.
#               To disable for simple one-node workflows, add a min node
#               count guard (e.g. skip if len(nodes) < 3).
# -----------------------------------------------------------------------------

from rules.issue import Issue

_DEFAULT_STICKY_CONTENT = "## I'm a note\n**Double click** to edit me. [Guide](https://docs.n8n.io/workflows/components/sticky-notes/)"


def check_no_sticky_note_doc(workflow):
    # A single sticky note anywhere in the workflow satisfies the rule;
    has_sticky = any(
        node.get("type") == "n8n-nodes-base.stickyNote"
        for node in workflow.get("nodes", [])
    )
    if has_sticky:
        stick_notes = [node for node in workflow.get("nodes", []) if node.get("type") == "n8n-nodes-base.stickyNote"]
        for sticky in stick_notes:
            content = sticky.get("parameters", {}).get("content", "").strip()
            if content == _DEFAULT_STICKY_CONTENT:
                return [Issue(
                    rule_name="no_sticky_note_doc",
                    severity="low",
                    message="Workflow has a sticky note with default placeholder content, indicating it's likely not used for documentation.",
                )]
            elif content == "":
                return [Issue(
                    rule_name="no_sticky_note_doc",
                    severity="low",
                    message="Workflow has a sticky note with empty content.",
                )]
            else:
                return []  # At least one sticky note with non-placeholder content, so no issue
    else:
        # One issue per workflow — this is not a per-node check
        return [Issue(
            rule_name="no_sticky_note_doc",
            severity="low",
            message="Workflow has no sticky note documentation.",
        )]

