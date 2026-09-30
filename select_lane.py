from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "fusion.hybrid-routing-request/v1"
EXPECTED_KEYS = {
    "schema_version",
    "task_id",
    "task_class",
    "risk_tier",
    "contains_restricted_data",
    "external_action_required",
    "deterministic_oracle_available",
    "local_adapter_qualified",
    "remote_adapter_qualified",
}
TASK_CLASSES = {
    "LOCAL_PYTHON_TEST_EXTRACTION",
    "BOUNDED_STRUCTURAL_SELECTION",
    "OPEN_SECURITY_ANALYSIS",
    "CODE_EDIT",
    "EXTERNAL_ACTION",
    "UNCLASSIFIED",
}
RISK_TIERS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def duplicate_reject(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key rejected: {key}")
        value[key] = item
    return value


def load_request(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=duplicate_reject,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON number rejected: {token}")
        ),
    )
    if not isinstance(value, dict) or set(value) != EXPECTED_KEYS:
        raise ValueError("routing request keys do not match the frozen contract")
    if value["schema_version"] != SCHEMA_VERSION:
        raise ValueError("routing request schema version is unsupported")
    if not isinstance(value["task_id"], str) or not 1 <= len(value["task_id"]) <= 128:
        raise ValueError("task_id is invalid")
    if value["task_class"] not in TASK_CLASSES:
        raise ValueError("task_class is invalid")
    if value["risk_tier"] not in RISK_TIERS:
        raise ValueError("risk_tier is invalid")
    for key in EXPECTED_KEYS - {"schema_version", "task_id", "task_class", "risk_tier"}:
        if type(value[key]) is not bool:
            raise ValueError(f"{key} must be a boolean")
    return value


def select_lane(request: dict[str, Any]) -> dict[str, Any]:
    task_class = request["task_class"]
    risk = request["risk_tier"]
    if risk in {"HIGH", "CRITICAL"}:
        lane = "LEAD_ONLY"
        reason = "high_risk_requires_independent_lead_judgment"
    elif task_class in {"OPEN_SECURITY_ANALYSIS", "CODE_EDIT", "EXTERNAL_ACTION", "UNCLASSIFIED"}:
        lane = "LEAD_ONLY"
        reason = "task_class_is_not_worker_qualified"
    elif request["external_action_required"]:
        lane = "LEAD_ONLY"
        reason = "worker_lanes_have_no_external_action_authority"
    elif not request["deterministic_oracle_available"]:
        lane = "LEAD_ONLY"
        reason = "deterministic_oracle_is_required"
    elif request["contains_restricted_data"]:
        if task_class == "LOCAL_PYTHON_TEST_EXTRACTION" and request["local_adapter_qualified"]:
            lane = "LOCAL_DEVSTRAL_V4"
            reason = "restricted_data_admitted_only_to_exact_local_qualified_lane"
        else:
            lane = "LEAD_ONLY"
            reason = "restricted_data_has_no_qualified_local_lane"
    elif task_class == "LOCAL_PYTHON_TEST_EXTRACTION" and request["local_adapter_qualified"]:
        lane = "LOCAL_DEVSTRAL_V4"
        reason = "exact_local_structural_lane_is_qualified"
    elif task_class == "BOUNDED_STRUCTURAL_SELECTION" and request["remote_adapter_qualified"]:
        lane = "OPENROUTER_CEREBRAS_GPT_OSS_120B"
        reason = "exact_remote_bounded_lane_is_qualified"
    else:
        lane = "LEAD_ONLY"
        reason = "required_project_adapter_is_not_qualified"
    return {
        "schema_version": "fusion.hybrid-routing-decision/v1",
        "task_id": request["task_id"],
        "lane": lane,
        "admission": "ADMITTED_PROPOSAL_ONLY" if lane != "LEAD_ONLY" else "NOT_ADMITTED_TO_WORKER",
        "reason": reason,
        "tools_allowed": False,
        "repository_mutation_allowed": False,
        "semantic_approval": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed hybrid worker lane selector")
    parser.add_argument("request", type=Path)
    args = parser.parse_args()
    try:
        request = load_request(args.request.resolve())
        decision = select_lane(request)
    except Exception as exc:
        print(f"ROUTING REJECTED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(decision, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
