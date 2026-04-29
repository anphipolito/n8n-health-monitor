from rules import ALL_RULES, Issue
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class WorkflowResult:
    workflow_id: str
    workflow_name: str
    health_score: int
    high_count: int
    medium_count: int
    low_count: int
    issues: list[Issue]
    message: str
    detected_at: str
    rule_errors: list


def calculate_health_score(issues: list[Issue]) -> int:
    score = 100
    for issue in issues:
        if issue.severity == 'high':
            score -= 20
        elif issue.severity == 'medium':
            score -= 10
        elif issue.severity == 'low':
            score -= 5
    return max(score, 0)


def analyze_workflow(workflow) -> WorkflowResult:
    all_issues: list[Issue] = []
    rule_errors = []
    workflow_id = workflow.get("workflow_id", "unknown")
    detected_at = datetime.now(timezone.utc).isoformat()

    for rule in ALL_RULES:
        try:
            result = rule(workflow)
            if result:
                for issue in result:
                    issue.workflow_id = workflow_id
                    issue.detected_at = detected_at
                all_issues.extend(result)
                logging.info(f"Rule {rule.__name__} applied successfully for workflow {workflow_id}")
        except Exception as e:
            logging.error(f"Error applying rule {rule.__name__}: {e} for workflow {workflow_id}")
            rule_errors.append({"rule_name": rule.__name__, "error": str(e)})

    health_score = calculate_health_score(all_issues)
    counts = {"high": 0, "medium": 0, "low": 0}
    for issue in all_issues:
        counts[issue.severity] = counts.get(issue.severity, 0) + 1
    logging.info(f"Workflow {workflow_id} analyzed with health score {health_score} and issues count: {counts}")

    return WorkflowResult(
        workflow_id=workflow_id,
        workflow_name=workflow.get("workflow_name", "unknown"),
        health_score=health_score,
        issues=all_issues,
        rule_errors=rule_errors,
        high_count=counts["high"],
        medium_count=counts["medium"],
        low_count=counts["low"],
        message=f"Workflow analyzed with {len(all_issues)} issues found.",
        detected_at=detected_at,
    )


