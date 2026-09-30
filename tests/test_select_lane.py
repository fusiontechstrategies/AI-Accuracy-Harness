from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import select_lane as routing  # noqa: E402


def request(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": "fusion.hybrid-routing-request/v1",
        "task_id": "TEST-ROUTE",
        "task_class": "BOUNDED_STRUCTURAL_SELECTION",
        "risk_tier": "LOW",
        "contains_restricted_data": False,
        "external_action_required": False,
        "deterministic_oracle_available": True,
        "local_adapter_qualified": False,
        "remote_adapter_qualified": True,
    }
    value.update(changes)
    return value


class RoutingTests(unittest.TestCase):
    def test_remote_bounded_lane_is_admitted(self) -> None:
        self.assertEqual(
            routing.select_lane(request())["lane"],
            "OPENROUTER_CEREBRAS_GPT_OSS_120B",
        )

    def test_exact_local_lane_is_preferred(self) -> None:
        decision = routing.select_lane(
            request(
                task_class="LOCAL_PYTHON_TEST_EXTRACTION",
                local_adapter_qualified=True,
                remote_adapter_qualified=True,
            )
        )
        self.assertEqual(decision["lane"], "LOCAL_DEVSTRAL_V4")

    def test_restricted_data_never_routes_remote(self) -> None:
        decision = routing.select_lane(request(contains_restricted_data=True))
        self.assertEqual(decision["lane"], "LEAD_ONLY")

    def test_restricted_data_can_use_exact_qualified_local_lane(self) -> None:
        decision = routing.select_lane(
            request(
                task_class="LOCAL_PYTHON_TEST_EXTRACTION",
                contains_restricted_data=True,
                local_adapter_qualified=True,
                remote_adapter_qualified=False,
            )
        )
        self.assertEqual(decision["lane"], "LOCAL_DEVSTRAL_V4")

    def test_high_risk_is_never_worker_admitted(self) -> None:
        decision = routing.select_lane(request(risk_tier="HIGH"))
        self.assertEqual(decision["lane"], "LEAD_ONLY")

    def test_security_review_is_never_worker_admitted(self) -> None:
        decision = routing.select_lane(request(task_class="OPEN_SECURITY_ANALYSIS"))
        self.assertEqual(decision["lane"], "LEAD_ONLY")

    def test_missing_oracle_fails_closed(self) -> None:
        decision = routing.select_lane(request(deterministic_oracle_available=False))
        self.assertEqual(decision["lane"], "LEAD_ONLY")

    def test_external_action_fails_closed(self) -> None:
        decision = routing.select_lane(request(external_action_required=True))
        self.assertEqual(decision["lane"], "LEAD_ONLY")


if __name__ == "__main__":
    unittest.main()
