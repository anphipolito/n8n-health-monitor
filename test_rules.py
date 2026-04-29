import unittest

from rules.no_retry_on_http import check_no_retry_on_http
from rules.no_sticky_note_doc import check_no_sticky_note_doc
from rules.missing_error_handler import check_missing_error_handler
from rules.no_env_var_separation import check_no_env_var_separation
from rules.hardcoded_credentials import check_hardcoded_credentials
from rules.loop_too_many_nodes import check_loop_too_many_nodes


class TestRules(unittest.TestCase):
    def _make_workflow(self, nodes=None, settings=None, connections=None):
        return {
            "workflow_id": "test_wf",
            "nodes": nodes or [],
            "settings": settings or {},
            "connections": connections or {},
        }

    def test_no_retry_on_http(self):
        # Non-HTTP node — no issue
        workflow = self._make_workflow(
            nodes=[{"id": "1", "name": "Set", "type": "n8n-nodes-base.set"}]
        )
        self.assertEqual(check_no_retry_on_http(workflow), [])

        # Empty workflow — no issue
        self.assertEqual(check_no_retry_on_http(self._make_workflow()), [])

        # HTTP node with retryOnFail missing — should flag
        workflow_no_retry = self._make_workflow(
            nodes=[{"id": "2", "name": "HTTP Call", "type": "n8n-nodes-base.httpRequest"}]
        )
        issues = check_no_retry_on_http(workflow_no_retry)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].severity, "medium")
        self.assertIn("HTTP Call", issues[0].message)

        # HTTP node with retryOnFail False — should flag
        workflow_retry_false = self._make_workflow(
            nodes=[{"id": "3", "name": "HTTP Call", "type": "n8n-nodes-base.httpRequest", "retryOnFail": False}]
        )
        issues = check_no_retry_on_http(workflow_retry_false)
        self.assertEqual(len(issues), 1)

        # HTTP node with retryOnFail True — no issue
        workflow_retry_true = self._make_workflow(
            nodes=[{"id": "4", "name": "HTTP Call", "type": "n8n-nodes-base.httpRequest", "retryOnFail": True}]
        )
        self.assertEqual(check_no_retry_on_http(workflow_retry_true), [])

    def test_no_sticky_note_doc(self):
        # Default placeholder content — should flag
        workflow_default = self._make_workflow(
            nodes=[{"id": "2", "name": "Note", "type": "n8n-nodes-base.stickyNote",
                    "parameters": {"content": "## I'm a note\n**Double click** to edit me. [Guide](https://docs.n8n.io/workflows/components/sticky-notes/)"}}]
        )
        issues = check_no_sticky_note_doc(workflow_default)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].message, "Workflow has a sticky note with default placeholder content, indicating it's likely not used for documentation.")

        # Empty content — should flag
        workflow_empty = self._make_workflow(
            nodes=[{"id": "2", "name": "Note", "type": "n8n-nodes-base.stickyNote",
                    "parameters": {"content": ""}}]
        )
        issues = check_no_sticky_note_doc(workflow_empty)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].message, "Workflow has a sticky note with empty content.")

        # No sticky note — should flag
        workflow_no_note = self._make_workflow(
            nodes=[{"id": "1", "name": "Set", "type": "n8n-nodes-base.set"}]
        )
        issues = check_no_sticky_note_doc(workflow_no_note)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].message, "Workflow has no sticky note documentation.")

        # Proper documentation — no issue
        workflow_proper = self._make_workflow(
            nodes=[
                {"id": "1", "name": "Set", "type": "n8n-nodes-base.set"},
                {"id": "2", "name": "Note", "type": "n8n-nodes-base.stickyNote",
                 "parameters": {"content": "This is a proper documentation note."}},
            ]
        )
        self.assertEqual(check_no_sticky_note_doc(workflow_proper), [])

    def test_missing_error_handler(self):
        self.assertEqual(len(check_missing_error_handler({"workflow_id": "wf1"})), 1)
        self.assertEqual(len(check_missing_error_handler({"workflow_id": "wf1", "settings": {}})), 1)
        self.assertEqual(check_missing_error_handler({"workflow_id": "wf1", "settings": {"errorWorkflow": "err_wf"}}), [])

    def test_no_env_var_separation(self):
        workflow = self._make_workflow(
            nodes=[
                {"id": "1", "name": "Internal Call", "type": "n8n-nodes-base.httpRequest",
                 "parameters": {"url": "http://localhost:5678/api"}},
                {"id": "2", "name": "External Call", "type": "n8n-nodes-base.httpRequest",
                 "parameters": {"url": "https://api.example.com"}},
            ]
        )
        issues = check_no_env_var_separation(workflow)
        self.assertEqual(len(issues), 1)
        self.assertIn("Internal Call", issues[0].message)
        self.assertEqual(issues[0].severity, "medium")

    def test_hardcoded_credentials(self):
        workflow = {
            "workflow_id": "wf1",
            "nodes": [
                {"id": "1", "name": "HTTP Node", "type": "n8n-nodes-base.httpRequest",
                 "parameters": {"password": "supersecret123"}},
                {"id": "2", "name": "Clean Node", "type": "n8n-nodes-base.set",
                 "parameters": {"value": "hello"}},
            ],
        }
        issues = check_hardcoded_credentials(workflow)
        self.assertEqual(len(issues), 1)
        self.assertIn("HTTP Node", issues[0].message)
        self.assertEqual(issues[0].severity, "high")

    def test_loop_too_many_nodes(self):
        nodes = [{"id": str(i), "name": f"Node{i}", "type": "n8n-nodes-base.set"} for i in range(1, 8)]
        nodes[0] = {"id": "0", "name": "Loop", "type": "n8n-nodes-base.splitInBatches"}

        connections_big = {
            "Loop":  {"main": [[{"node": "Node1", "type": "main", "index": 0}]]},
            "Node1": {"main": [[{"node": "Node2", "type": "main", "index": 0}]]},
            "Node2": {"main": [[{"node": "Node3", "type": "main", "index": 0}]]},
            "Node3": {"main": [[{"node": "Node4", "type": "main", "index": 0}]]},
            "Node4": {"main": [[{"node": "Node5", "type": "main", "index": 0}]]},
            "Node5": {"main": [[{"node": "Node6", "type": "main", "index": 0}]]},
            "Node6": {"main": [[{"node": "Loop",  "type": "main", "index": 0}]]},
        }
        issues = check_loop_too_many_nodes(self._make_workflow(nodes=nodes, connections=connections_big))
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].severity, "medium")
        self.assertIn("6", issues[0].message)

        connections_small = {
            "Loop":  {"main": [[{"node": "Node1", "type": "main", "index": 0}]]},
            "Node1": {"main": [[{"node": "Node2", "type": "main", "index": 0}]]},
            "Node2": {"main": [[{"node": "Node3", "type": "main", "index": 0}]]},
            "Node3": {"main": [[{"node": "Loop",  "type": "main", "index": 0}]]},
        }
        self.assertEqual(check_loop_too_many_nodes(self._make_workflow(nodes=nodes, connections=connections_small)), [])


if __name__ == "__main__":
    unittest.main()
