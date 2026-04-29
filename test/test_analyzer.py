import unittest

from analyzer import analyze_workflow
                                         
class TestAnalyzer(unittest.TestCase):
                                                                                                             
    def _make_workflow(self, nodes=None, settings=None, connections=None):
        return {                                                                                           
            "workflow_id": "test_wf",                                                                    
            "workflow_name": "Test Workflow",                                                              
            "nodes": nodes or [],       
            "settings": settings or {},                                                                    
            "connections": connections or {},                                                              
        }
                                                                                                            
    def test_happy_path(self):
        # Workflow with issues
        workflow = self._make_workflow(
            nodes=[
                {"type": "n8n-nodes-base.httpRequest", "parameters": {"url": "http://example.com"},"retryOnFail": False},
                {"type": "n8n-nodes-base.stickyNote", "parameters": {"content": "## I'm a note\n**Double click** to edit me. [Guide](https://docs.n8n.io/workflows/components/sticky-notes/)"}},
                {"id": "1", "name": "Internal Call", "type": "n8n-nodes-base.httpRequest", "retryOnFail": True,
                 "parameters": {"url": "http://localhost:5678/api"}},

            ],
            settings= {"errorWorkflow": None }
        )
        result = analyze_workflow(workflow)
        self.assertEqual(result.health_score, 55)  # 4 issues (1 high, 2 medium, 1 low) = 100 -20-10 -10 -5 =55
        self.assertEqual(len(result.issues), 4)
        self.assertEqual(len(result.rule_errors), 0)
                                                                           
    def test_clean_workflow(self):
        # Workflow with no issues
        workflow = self._make_workflow(
            nodes=[
                {"type": "n8n-nodes-base.httpRequest", "parameters": {"url": "http://example.com"},"retryOnFail": True},
                {"type": "n8n-nodes-base.stickyNote", "parameters": {"content": "This is a proper documentation note."}},
            ],
            settings= {"errorWorkflow": "err_wf" }
        )
        result = analyze_workflow(workflow)
        self.assertEqual(result.health_score, 100)
        self.assertEqual(len(result.issues), 0)
        self.assertEqual(len(result.rule_errors), 0)

    
    def test_score_floor(self):
        # Workflow with many high-severity issues to test score floor at 0
        workflow = self._make_workflow(
            nodes=[
                {"id": "0", "name": "Loop", "type": "n8n-nodes-base.splitInBatches"},
                {"type": "n8n-nodes-base.httpRequest", "parameters": {"url": "http://example.com"},"retryOnFail": False},
                {"type": "n8n-nodes-base.stickyNote", "parameters": {"content": "## I'm a note\n**Double click** to edit me. [Guide](https://docs.n8n.io/workflows/components/sticky-notes/)"}},
                {"id": "1", "name": "HTTP Node", "type": "n8n-nodes-base.httpRequest",
                 "parameters": {"password": "supersecret123"}},
                {"id": "1", "name": "Internal Call", "type": "n8n-nodes-base.httpRequest", "retryOnFail": False,
                 "parameters": {"url": "http://localhost:5678/api"}},
                {"id": 1, "name": f"Node1", "type": "n8n-nodes-base.set"},
                {"id": 2, "name": f"Node2", "type": "n8n-nodes-base.set"},
                {"type": "n8n-nodes-base.httpRequest", "parameters": {"url": "http://example.com"},"retryOnFail": False},
               {"id": "1", "name": "HTTP Node", "type": "n8n-nodes-base.httpRequest",
                 "parameters": {"x-api-key": "supersecret12dafd3"}},

            ],
            settings= {"errorWorkflow": None },
            connections= {
            "Loop":  {"main": [[{"node": "Node1", "type": "main", "index": 0}]]},
            "Node1": {"main": [[{"node": "Node2", "type": "main", "index": 0}]]},
            "Node2": {"main": [[{"node": "Node3", "type": "main", "index": 0}]]},
            "Node3": {"main": [[{"node": "Node4", "type": "main", "index": 0}]]},
            "Node4": {"main": [[{"node": "Node5", "type": "main", "index": 0}]]},
            "Node5": {"main": [[{"node": "Node6", "type": "main", "index": 0}]]},
            "Node6": {"main": [[{"node": "Loop",  "type": "main", "index": 0}]]},
        }
        )
        result = analyze_workflow(workflow)
        self.assertEqual(result.health_score, 0)  # Score should not go below 0
        self.assertEqual(len(result.issues), 10)
        self.assertEqual(len(result.rule_errors), 0)

    def test_rule_crash_isolation(self):
        # Workflow designed to cause a rule to crash (e.g. missing expected keys)
        workflow = self._make_workflow(
            nodes=[
                {"type": "n8n-nodes-base.httpRequest"},  # Missing parameters and retryOnFail
            ],
            settings= {"errorWorkflow": None }
        )
        result = analyze_workflow(workflow)
        # missing_error_handler (high -20) + no_retry_on_http (medium -10) + no_sticky_note_doc (low -5) = 65
        self.assertEqual(result.health_score, 65)
        self.assertEqual(len(result.issues), 3)
        self.assertEqual(len(result.rule_errors), 0)  # Rule should handle missing keys gracefully
    def test_detected_at_is_string(self): 
        workflow = self._make_workflow()
        result = analyze_workflow(workflow)
        self.assertIsInstance(result.detected_at, str)                                                           
                                                                                                           
if __name__ == "__main__":
    unittest.main()                                                                                        
  