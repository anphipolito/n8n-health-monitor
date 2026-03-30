# -----------------------------------------------------------------------------
# Rule        : loop_too_many_nodes
# Severity    : Medium
# Purpose     : Flag Loop Over Items nodes that drive more than 5 downstream
#               nodes. Large loop bodies are harder to debug, more likely to
#               hit n8n memory limits, and a signal that the logic should be
#               split into a sub-workflow.
# What to check: Identify loop nodes (splitInBatches / loopOverItems), then
#               BFS-traverse their body branch (output index 0) through the
#               connections map, counting distinct nodes until the path cycles
#               back to the loop node or dead-ends. Flag if count > THRESHOLD.
# Prompt hint : To change the threshold, update the THRESHOLD constant.
#               To also count nested loops, recurse into any loop node found
#               during the BFS. To skip utility nodes (e.g. Set, StickyNote),
#               filter by node type before incrementing the count.
# -----------------------------------------------------------------------------

from collections import deque
from datetime import datetime, timezone

# n8n's "Loop Over Items" node has the internal type "splitInBatches".
# "loopoveritems" is included for any community/renamed variants.
_LOOP_TYPE_KEYWORDS = ("splitinbatches", "loopoveritems")

THRESHOLD = 5


def _is_loop_node(node):
    return any(kw in node.get("type", "").lower() for kw in _LOOP_TYPE_KEYWORDS)


def _count_loop_body_nodes(loop_node_name, connections):
    """
    BFS from the loop node's first output branch (index 0).
    n8n's Loop Over Items node outputs:
      - branch 0 ("loop"): the body nodes
      - branch 1 ("done"): the exit path
    We follow branch 0 and stop if we reach the loop node again (cycle back).
    Returns the count of distinct nodes visited inside the loop body.
    """
    outgoing = connections.get(loop_node_name, {}).get("main", [])
    if not outgoing:
        return 0

    # outgoing[0] is the loop-body branch; outgoing[1] (if present) is the done branch
    body_starts = [edge["node"] for edge in outgoing[0] if "node" in edge]

    visited = set()
    queue = deque(body_starts)

    while queue:
        name = queue.popleft()
        # Stop if already counted or if we've looped back to the loop node itself
        if name in visited or name == loop_node_name:
            continue
        visited.add(name)
        for branch in connections.get(name, {}).get("main", []):
            for edge in branch:
                target = edge.get("node")
                if target and target not in visited and target != loop_node_name:
                    queue.append(target)

    return len(visited)


def check_loop_too_many_nodes(workflow):
    issues = []
    workflow_id = workflow.get("workflow_id", "unknown")
    connections = workflow.get("connections", {})
    now = datetime.now(timezone.utc).isoformat()

    for node in workflow.get("nodes", []):
        if not _is_loop_node(node):
            continue

        node_name = node.get("name", node.get("id", "unknown"))
        count = _count_loop_body_nodes(node_name, connections)

        if count > THRESHOLD:
            issues.append({
                "rule_name": "loop_too_many_nodes",
                "severity": "medium",
                "workflow_id": workflow_id,
                "message": f"Loop node '{node_name}' has {count} connected nodes inside it (threshold: {THRESHOLD}).",
                "detected_at": now,
            })

    return issues
