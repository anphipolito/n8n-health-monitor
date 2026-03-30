from rules.no_retry_on_http import check_no_retry_on_http
from rules.no_sticky_note_doc import check_no_sticky_note_doc
from rules.missing_error_handler import check_missing_error_handler
from rules.no_env_var_separation import check_no_env_var_separation
from rules.hardcoded_credentials import check_hardcoded_credentials
from rules.ai_node_no_validation import check_ai_node_no_validation
from rules.loop_too_many_nodes import check_loop_too_many_nodes

ALL_RULES = [
    check_no_retry_on_http,
    check_no_sticky_note_doc,
    check_missing_error_handler,
    check_no_env_var_separation,
    check_hardcoded_credentials,
    check_ai_node_no_validation,
    check_loop_too_many_nodes,
]
