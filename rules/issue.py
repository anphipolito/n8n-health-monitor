from dataclasses import dataclass, field


@dataclass
class Issue:
    rule_name: str
    severity: str
    message: str
    workflow_id: str = field(default="")
    detected_at: str = field(default="")
