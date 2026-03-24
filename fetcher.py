import json
import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _normalize(raw: dict, environment: str) -> dict:
    """Map a raw n8n workflow dict to the normalized project format."""
    return {
        "workflow_id":   str(raw.get("id", "")),
        "workflow_name": raw.get("name", "Unnamed"),
        "environment":   environment,
        "active":        bool(raw.get("active", False)),
        "nodes":         raw.get("nodes", []),
        "connections":   raw.get("connections", {}),
    }


# ---------------------------------------------------------------------------
# Source functions
# ---------------------------------------------------------------------------

def get_from_local(path: str, environment: str) -> list[dict]:
    """Load workflows from *.json files in a local directory."""
    workflows = []
    files = list(Path(path).glob("*.json"))

    if not files:
        logger.warning(f"No JSON files found in: {path}")
        return []

    for file in files:
        try:
            raw = json.loads(file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Skipping {file.name}: {e}")
            continue

        # n8n exports can be a single workflow {} or a list [{}]
        if isinstance(raw, dict):
            raw = [raw]

        for workflow in raw:
            workflows.append(_normalize(workflow, environment))

    return workflows


def get_from_api(api_url: str, api_key: str, environment: str, active_only: bool = False) -> list[dict]:
    """Fetch all workflows from the n8n REST API (handles pagination)."""
    workflows = []
    headers = {"X-N8N-API-KEY": api_key, "Accept": "application/json"}
    cursor = None

    while True:
        params = {"limit": 100}
        if cursor:
            params["cursor"] = cursor
        if active_only:
            params["active"] = "true"

        response = requests.get(f"{api_url}/workflows", headers=headers, params=params)

        if not response.ok:
            raise RuntimeError(
                f"n8n API error {response.status_code}: {response.text}"
            )

        body = response.json()
        for workflow in body.get("data", []):
            workflows.append(_normalize(workflow, environment))

        cursor = body.get("nextCursor")
        if not cursor:
            break

    return workflows


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def fetch_workflows(source: str, **kwargs) -> list[dict]:
    """
    Load and normalize workflows from the given source.

    Args:
        source: "api" or "file"
        **kwargs: Override env var defaults.
                  - path (str): directory for file mode
                  - api_url (str): n8n API base URL for api mode
                  - api_key (str): n8n API key for api mode
                  - active_only (bool): api mode only — fetch only active workflows (default False)

    Returns:
        List of normalized workflow dicts.
    """
    environment = os.getenv("ENVIRONMENT", "production")

    if source == "file":
        path = kwargs.get("path") or os.getenv("WORKFLOW_DIR", "./workflows")
        return get_from_local(path, environment)

    elif source == "api":
        api_url = kwargs.get("api_url") or os.getenv("N8N_API_URL", "")
        api_key = kwargs.get("api_key") or os.getenv("N8N_API_KEY", "")
        active_only = kwargs.get("active_only", False)

        if not api_url or not api_key:
            raise ValueError("N8N_API_URL and N8N_API_KEY must be set in .env for API mode.")

        return get_from_api(api_url, api_key, environment, active_only=active_only)

    else:
        raise ValueError(f"Unknown source '{source}'. Use 'api' or 'file'.")
