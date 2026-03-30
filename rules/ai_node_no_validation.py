# -----------------------------------------------------------------------------
# Rule        : ai_node_no_validation
# Severity    : High
# Purpose     : Ensure that AI nodes (LLMs, chat models) are always preceded
#               by at least one input validation step. Passing raw, unvalidated
#               user input to an AI node risks prompt injection, runaway token
#               usage, and unpredictable outputs in production.
# What to check: For each AI node, inspect its directly-upstream nodes via the
#               connections map. Flag the AI node if none of the upstream nodes
#               are a recognised validation type (if, switch, set, code, filter).
# Prompt hint : To deepen the check, walk more than one hop upstream (some
#               validation may be two nodes back). To add AI providers, extend
#               _AI_TYPE_KEYWORDS with their n8n type substrings. To relax the
#               rule for internal-only workflows, add a workflow tag check.
# -----------------------------------------------------------------------------

from datetime import datetime, timezone

# Substrings matched against node type (lowercased) to identify AI nodes.
# Covers n8n's native OpenAI node, LangChain sub-nodes, and community nodes.
_AI_TYPE_KEYWORDS = ("openai", "anthropic", "langchain", "@n8n/n8n-nodes-langchain", "lmchat", "lmopenai")

# Node types that count as input validation / guarding logic.
# "set" is included because it's often used to sanitise or transform inputs
# before they reach an AI node.
_VALIDATION_TYPE_KEYWORDS = ("if", "switch", "set", "code", "filter")


def _is_ai_node(node):
    return any(kw in node.get("type", "").lower() for kw in _AI_TYPE_KEYWORDS)


def _is_validation_node(node):
    return any(kw in node.get("type", "").lower() for kw in _VALIDATION_TYPE_KEYWORDS)


def check_ai_node_no_validation(workflow):
    issues = []
    workflow_id = workflow.get("workflow_id", "unknown")

    # Index nodes by name for fast lookup when resolving upstream node objects
    nodes_by_name = {n["name"]: n for n in workflow.get("nodes", []) if "name" in n}
    connections = workflow.get("connections", {})

    # n8n's connections map is source-keyed: { "NodeA": { "main": [[{node: "NodeB"}]] } }
    # We need the reverse (target → sources) to find what feeds into each AI node.
    upstream = {name: [] for name in nodes_by_name}
    for source_name, conn_data in connections.items():
        for branch in conn_data.get("main", []):
            for edge in branch:
                target = edge.get("node")
                # Guard against connections referencing nodes not in the node list
                if target and target in upstream:
                    upstream[target].append(source_name)

    now = datetime.now(timezone.utc).isoformat()

    for node in workflow.get("nodes", []):
        if not _is_ai_node(node):
            continue

        node_name = node.get("name", node.get("id", "unknown"))
        parent_names = upstream.get(node_name, [])

        # Resolve parent names to node dicts so we can check their types
        parents = [nodes_by_name[n] for n in parent_names if n in nodes_by_name]

        # Only one direct parent needs to be a validation node to satisfy the rule
        if not any(_is_validation_node(p) for p in parents):
            issues.append({
                "rule_name": "ai_node_no_validation",
                "severity": "high",
                "workflow_id": workflow_id,
                "message": f"AI node '{node_name}' has no input validation node connected before it.",
                "detected_at": now,
            })

    return issues
