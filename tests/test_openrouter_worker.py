from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import openrouter_worker as worker  # noqa: E402


class WorkerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = {
            "schema_version": "fusion.openrouter-provider-profile/v1",
            "model": "openai/gpt-oss-120b",
            "provider": "Cerebras",
            "temperature": 0,
            "top_p": 1,
            "base_seed": 42,
            "request_endpoint_maximum": True,
        }
        self.schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "schema_version": {"const": "test/v1"},
                "choice": {"type": "string", "enum": ["A", "B"]},
            },
            "required": ["schema_version", "choice"],
        }
        self.packet = {
            "schema_version": "fusion.managed-worker-packet/v1",
            "task_id": "TEST-01",
            "risk_tier": "LOW",
            "reasoning_effort": "high",
            "candidate_count": 1,
            "system_prompt": "proposal only",
            "user_prompt": "choose",
            "response_schema": self.schema,
        }
        self.endpoint = {
            "provider_name": "Cerebras",
            "max_completion_tokens": 40960,
        }

    def test_canonical_bytes_are_stable(self) -> None:
        self.assertEqual(worker.canonical_bytes({"b": 1, "a": 2}), b'{"a":2,"b":1}\n')

    def test_strict_json_rejects_duplicate_keys(self) -> None:
        with self.assertRaises(worker.DuplicateKeyError):
            worker.strict_loads('{"a":1,"a":2}')

    def test_strict_json_rejects_nonfinite_values(self) -> None:
        with self.assertRaises(ValueError):
            worker.strict_loads('{"a":NaN}')

    def test_cerebras_translation_preserves_fixed_value(self) -> None:
        translated = worker.translate_cerebras_schema(self.schema)
        self.assertNotIn("$schema", translated)
        self.assertEqual(translated["properties"]["schema_version"], {"enum": ["test/v1"]})

    def test_local_schema_validation_rejects_extra_and_wrong_fixed_value(self) -> None:
        errors = worker.validate_schema(
            {"schema_version": "wrong", "choice": "A", "extra": True}, self.schema
        )
        self.assertIn("$.schema_version:const", errors)
        self.assertIn("$.extra:additional", errors)

    def test_request_is_exactly_pinned_and_has_no_cost_budget(self) -> None:
        request = worker.build_request(self.profile, self.packet, self.endpoint, 1)
        self.assertEqual(request["model"], "openai/gpt-oss-120b")
        self.assertEqual(request["provider"]["order"], ["Cerebras"])
        self.assertFalse(request["provider"]["allow_fallbacks"])
        self.assertTrue(request["provider"]["require_parameters"])
        self.assertEqual(request["provider"]["data_collection"], "deny")
        self.assertEqual(request["max_tokens"], 40960)
        self.assertFalse(request["include_reasoning"])
        rendered = json.dumps(request)
        self.assertNotIn("cost_limit", rendered)
        self.assertNotIn("budget", rendered)

    def test_valid_response_is_admitted(self) -> None:
        response = {
            "model": "openai/gpt-oss-120b",
            "provider": "Cerebras",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": '{"schema_version":"test/v1","choice":"A"}',
                    },
                }
            ],
        }
        proposal, failures = worker.validate_response(
            response, profile=self.profile, packet=self.packet
        )
        self.assertEqual(failures, [])
        self.assertEqual(proposal, {"schema_version": "test/v1", "choice": "A"})

    def test_provider_drift_fails_closed(self) -> None:
        response = {
            "model": "openai/gpt-oss-120b",
            "provider": "Other",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": '{"schema_version":"test/v1","choice":"A"}',
                    },
                }
            ],
        }
        _, failures = worker.validate_response(response, profile=self.profile, packet=self.packet)
        self.assertIn("response_provider_identity", failures)

    def test_length_finish_fails_closed(self) -> None:
        response = {
            "model": "openai/gpt-oss-120b",
            "provider": "Cerebras",
            "choices": [
                {
                    "finish_reason": "length",
                    "message": {
                        "content": '{"schema_version":"test/v1","choice":"A"}',
                    },
                }
            ],
        }
        _, failures = worker.validate_response(response, profile=self.profile, packet=self.packet)
        self.assertIn("response_not_complete", failures)

    def test_profile_and_packet_contracts(self) -> None:
        worker.validate_profile(self.profile)
        worker.validate_packet(self.packet)
        broken = dict(self.packet)
        broken["candidate_count"] = 0
        with self.assertRaises(ValueError):
            worker.validate_packet(broken)


if __name__ == "__main__":
    unittest.main()
