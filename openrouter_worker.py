from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_API = "https://openrouter.ai/api/v1/models"
CHAT_API = "https://openrouter.ai/api/v1/chat/completions"
ENDPOINTS_API = "https://openrouter.ai/api/v1/models/{model}/endpoints"
KEY_PATTERN = re.compile(r"sk-or-v1-[A-Za-z0-9_-]+")
TASK_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
REQUIRED_PROVIDER_PARAMETERS = {
    "reasoning",
    "reasoning_effort",
    "response_format",
    "seed",
    "structured_outputs",
}


class DuplicateKeyError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant rejected: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key rejected: {key}")
        result[key] = value
    return result


def strict_loads(text: str | bytes) -> Any:
    return json.loads(
        text,
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )


def write_json_new(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(canonical_bytes(value))


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write(canonical_bytes(value))


def translate_cerebras_schema(value: Any) -> Any:
    """Preserve semantics while using Cerebras' supported JSON-schema subset."""
    if isinstance(value, list):
        return [translate_cerebras_schema(item) for item in value]
    if not isinstance(value, dict):
        return value
    translated: dict[str, Any] = {}
    for key, item in value.items():
        if key == "$schema":
            continue
        if key == "const":
            translated["enum"] = [translate_cerebras_schema(item)]
        else:
            translated[key] = translate_cerebras_schema(item)
    return translated


def validate_schema(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}:const")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}:enum")
    expected_type = schema.get("type")
    type_ok = True
    if expected_type == "object":
        type_ok = isinstance(value, dict)
    elif expected_type == "array":
        type_ok = isinstance(value, list)
    elif expected_type == "string":
        type_ok = isinstance(value, str)
    elif expected_type == "integer":
        type_ok = type(value) is int
    elif expected_type == "number":
        type_ok = (type(value) in {int, float}) and math.isfinite(float(value))
    elif expected_type == "boolean":
        type_ok = type(value) is bool
    elif expected_type == "null":
        type_ok = value is None
    if not type_ok:
        return [f"{path}:type:{expected_type}"]
    if isinstance(value, dict):
        properties = schema.get("properties") or {}
        required = schema.get("required") or []
        for key in required:
            if key not in value:
                errors.append(f"{path}.{key}:required")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}.{key}:additional")
        for key, child in properties.items():
            if key in value and isinstance(child, dict):
                errors.extend(validate_schema(value[key], child, f"{path}.{key}"))
    elif isinstance(value, list):
        if "minItems" in schema and len(value) < int(schema["minItems"]):
            errors.append(f"{path}:minItems")
        if "maxItems" in schema and len(value) > int(schema["maxItems"]):
            errors.append(f"{path}:maxItems")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(validate_schema(item, item_schema, f"{path}[{index}]"))
    elif isinstance(value, str):
        if "minLength" in schema and len(value) < int(schema["minLength"]):
            errors.append(f"{path}:minLength")
        if "maxLength" in schema and len(value) > int(schema["maxLength"]):
            errors.append(f"{path}:maxLength")
        if "pattern" in schema and re.fullmatch(str(schema["pattern"]), value) is None:
            errors.append(f"{path}:pattern")
    elif type(value) in {int, float}:
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}:minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}:maximum")
    return errors


def load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    value = strict_loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def load_key(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    matches = KEY_PATTERN.findall(text)
    if len(matches) != 1 or matches[0] != text:
        raise ValueError("key file must contain exactly one bare OpenRouter key")
    return matches[0]


def validate_profile(profile: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "model",
        "provider",
        "temperature",
        "top_p",
        "base_seed",
        "request_endpoint_maximum",
    }
    if set(profile) != required:
        raise ValueError("provider profile keys do not match the frozen contract")
    if profile["schema_version"] != "fusion.openrouter-provider-profile/v1":
        raise ValueError("provider profile schema version is invalid")
    if not isinstance(profile["model"], str) or not profile["model"]:
        raise ValueError("provider profile model is invalid")
    if not isinstance(profile["provider"], str) or not profile["provider"]:
        raise ValueError("provider profile provider is invalid")
    if type(profile["base_seed"]) is not int:
        raise ValueError("provider profile base seed is invalid")
    if type(profile["request_endpoint_maximum"]) is not bool:
        raise ValueError("provider profile endpoint-maximum policy is invalid")


def validate_packet(packet: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "task_id",
        "risk_tier",
        "reasoning_effort",
        "candidate_count",
        "system_prompt",
        "user_prompt",
        "response_schema",
    }
    if set(packet) != required:
        raise ValueError("task packet keys do not match the frozen contract")
    if packet["schema_version"] != "fusion.managed-worker-packet/v1":
        raise ValueError("task packet schema version is invalid")
    if not isinstance(packet["task_id"], str) or TASK_ID_PATTERN.fullmatch(packet["task_id"]) is None:
        raise ValueError("task ID is invalid")
    if packet["risk_tier"] not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        raise ValueError("risk tier is invalid")
    if packet["reasoning_effort"] not in {"low", "medium", "high"}:
        raise ValueError("reasoning effort is invalid for gpt-oss-120b")
    if type(packet["candidate_count"]) is not int or packet["candidate_count"] < 1:
        raise ValueError("candidate count must be a positive integer")
    if not isinstance(packet["system_prompt"], str) or not packet["system_prompt"].strip():
        raise ValueError("system prompt is invalid")
    if not isinstance(packet["user_prompt"], str) or not packet["user_prompt"].strip():
        raise ValueError("user prompt is invalid")
    if not isinstance(packet["response_schema"], dict):
        raise ValueError("response schema is invalid")


def request_json(
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    key: str | None = None,
    retry_events: Path | None = None,
) -> dict[str, Any]:
    data = canonical_bytes(payload) if payload is not None else None
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Title": "Fusion Hybrid Accuracy Harness",
    }
    if key is not None:
        headers["Authorization"] = f"Bearer {key}"
    method = "POST" if payload is not None else "GET"
    for attempt in range(4):
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=900) as response:
                raw = response.read()
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:4000]
            if exc.code == 429 and payload is not None and attempt < 3:
                try:
                    delay = max(1.0, float(exc.headers.get("Retry-After", "60")) + 1.0)
                except (TypeError, ValueError):
                    delay = 60.0
                if retry_events is not None:
                    append_jsonl(
                        retry_events,
                        {
                            "schema_version": "fusion.provider-retry/v1",
                            "recorded_at": utc_now(),
                            "attempt": attempt + 1,
                            "status": 429,
                            "delay_seconds": delay,
                            "reason": "upstream shared-pool rate limit before an admitted response",
                        },
                    )
                remaining = delay
                while remaining > 0:
                    interval = min(remaining, 55.0)
                    time.sleep(interval)
                    remaining -= interval
                continue
            raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
    value = strict_loads(raw)
    if not isinstance(value, dict):
        raise RuntimeError("OpenRouter response was not a JSON object")
    return value


def resolve_endpoint(profile: dict[str, Any]) -> dict[str, Any]:
    endpoint_data = request_json(ENDPOINTS_API.format(model=profile["model"]))
    data = endpoint_data.get("data")
    endpoints = data.get("endpoints") if isinstance(data, dict) else None
    matches = [
        item
        for item in (endpoints or [])
        if isinstance(item, dict) and item.get("provider_name") == profile["provider"]
    ]
    if len(matches) != 1:
        raise RuntimeError("exact provider endpoint did not resolve once")
    endpoint = matches[0]
    supported = set(endpoint.get("supported_parameters") or [])
    missing = sorted(REQUIRED_PROVIDER_PARAMETERS - supported)
    if missing:
        raise RuntimeError(f"provider endpoint lacks required parameters: {missing}")
    if endpoint.get("status") != 0:
        raise RuntimeError("provider endpoint is not currently healthy")
    return endpoint


def build_request(
    profile: dict[str, Any],
    packet: dict[str, Any],
    endpoint: dict[str, Any],
    ordinal: int,
) -> dict[str, Any]:
    request: dict[str, Any] = {
        "model": profile["model"],
        "messages": [
            {"role": "system", "content": packet["system_prompt"]},
            {
                "role": "user",
                "content": (
                    packet["user_prompt"]
                    + f"\n\nCandidate ordinal: {ordinal}. Return only the contracted result."
                ),
            },
        ],
        "stream": False,
        "temperature": profile["temperature"],
        "top_p": profile["top_p"],
        "seed": profile["base_seed"] + ordinal,
        "reasoning_effort": packet["reasoning_effort"],
        "include_reasoning": False,
        "provider": {
            "order": [profile["provider"]],
            "allow_fallbacks": False,
            "require_parameters": True,
            "data_collection": "deny",
        },
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "managed_worker_result",
                "strict": True,
                "schema": translate_cerebras_schema(packet["response_schema"]),
            },
        },
        "usage": {"include": True},
    }
    if profile["request_endpoint_maximum"]:
        endpoint_maximum = endpoint.get("max_completion_tokens")
        if type(endpoint_maximum) is not int or endpoint_maximum < 1:
            raise RuntimeError("provider endpoint maximum completion size is unavailable")
        request["max_tokens"] = endpoint_maximum
    return request


def validate_response(
    response: dict[str, Any],
    *,
    profile: dict[str, Any],
    packet: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    if response.get("model") != profile["model"]:
        failures.append("response_model_identity")
    if response.get("provider") != profile["provider"]:
        failures.append("response_provider_identity")
    choices = response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        return None, [*failures, "response_choice_count"]
    choice = choices[0]
    if not isinstance(choice, dict) or choice.get("finish_reason") != "stop":
        failures.append("response_not_complete")
    message = choice.get("message") if isinstance(choice, dict) else None
    if not isinstance(message, dict):
        return None, [*failures, "response_message_missing"]
    if message.get("tool_calls"):
        failures.append("unexpected_tool_call")
    content = message.get("content")
    try:
        if not isinstance(content, str):
            raise TypeError("response content is not a string")
        proposal = strict_loads(content)
        if not isinstance(proposal, dict):
            raise TypeError("proposal is not an object")
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return None, [*failures, f"proposal_parse:{type(exc).__name__}"]
    failures.extend(validate_schema(proposal, packet["response_schema"]))
    return proposal, sorted(set(failures))


def verified_checkpoint(candidate_dir: Path, request: dict[str, Any]) -> dict[str, Any] | None:
    receipts = sorted(candidate_dir.glob("attempt-*/receipt.json"))
    admitted: list[dict[str, Any]] = []
    for receipt_path in receipts:
        receipt = load_json_object(receipt_path, label="checkpoint receipt")
        attempt_dir = receipt_path.parent
        request_path = attempt_dir / "request.json"
        response_path = attempt_dir / "response.json"
        proposal_path = attempt_dir / "proposal.json"
        if not all(path.is_file() for path in (request_path, response_path, proposal_path)):
            continue
        if request_path.read_bytes() != canonical_bytes(request):
            continue
        if receipt.get("request_sha256") != sha256_file(request_path):
            continue
        if receipt.get("response_sha256") != sha256_file(response_path):
            continue
        if receipt.get("proposal_sha256") != sha256_file(proposal_path):
            continue
        if receipt.get("workflow_valid") is True:
            admitted.append(receipt)
    if len(admitted) > 1:
        raise RuntimeError("multiple admitted checkpoints exist for one candidate")
    return admitted[0] if admitted else None


def next_attempt_dir(candidate_dir: Path) -> Path:
    existing = sorted(candidate_dir.glob("attempt-*"))
    number = len(existing) + 1
    path = candidate_dir / f"attempt-{number:02d}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def seal_evidence(root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise RuntimeError(f"symbolic link rejected in evidence: {path}")
        if path.is_file() and path.name != "seal.json":
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    rows.sort(key=lambda item: item["path"])
    return {
        "schema_version": "fusion.evidence-seal/v1",
        "created_at": utc_now(),
        "file_count": len(rows),
        "files": rows,
        "root_sha256": sha256_bytes(canonical_bytes(rows)),
    }


def run(
    *,
    profile_path: Path,
    packet_path: Path,
    output_root: Path,
    key_path: Path,
    resume: bool,
) -> dict[str, Any]:
    profile = load_json_object(profile_path, label="provider profile")
    packet = load_json_object(packet_path, label="task packet")
    validate_profile(profile)
    validate_packet(packet)
    if output_root.exists() and not resume:
        raise RuntimeError("refusing to overwrite an existing output directory")
    output_root.mkdir(parents=True, exist_ok=resume)
    if (output_root / "summary.json").exists() or (output_root / "seal.json").exists():
        raise RuntimeError("evidence run is already complete")
    profile_copy = output_root / "provider-profile.json"
    packet_copy = output_root / "task-packet.json"
    for destination, value in ((profile_copy, profile), (packet_copy, packet)):
        expected = canonical_bytes(value)
        if destination.exists():
            if destination.read_bytes() != expected:
                raise RuntimeError(f"resume identity mismatch: {destination.name}")
        else:
            write_json_new(destination, value)
    endpoint = resolve_endpoint(profile)
    endpoint_record = output_root / f"endpoint-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    write_json_new(endpoint_record, endpoint)
    key = load_key(key_path)
    receipts: list[dict[str, Any]] = []
    for ordinal in range(1, packet["candidate_count"] + 1):
        request = build_request(profile, packet, endpoint, ordinal)
        candidate_dir = output_root / f"candidate-{ordinal:02d}"
        candidate_dir.mkdir(exist_ok=True)
        checkpoint = verified_checkpoint(candidate_dir, request)
        if checkpoint is not None:
            receipts.append(checkpoint)
            print(f"candidate={ordinal} resumed workflow_valid=True", flush=True)
            continue
        attempt_dir = next_attempt_dir(candidate_dir)
        request_path = attempt_dir / "request.json"
        response_path = attempt_dir / "response.json"
        proposal_path = attempt_dir / "proposal.json"
        write_json_new(request_path, request)
        started = time.monotonic()
        response = request_json(
            CHAT_API,
            payload=request,
            key=key,
            retry_events=attempt_dir / "provider-retries.jsonl",
        )
        elapsed = time.monotonic() - started
        write_json_new(response_path, response)
        proposal, failures = validate_response(response, profile=profile, packet=packet)
        if proposal is not None:
            write_json_new(proposal_path, proposal)
        usage = response.get("usage") if isinstance(response.get("usage"), dict) else {}
        receipt = {
            "schema_version": "fusion.managed-worker-call/v1",
            "task_id": packet["task_id"],
            "candidate_ordinal": ordinal,
            "attempt": int(attempt_dir.name.removeprefix("attempt-")),
            "workflow_valid": not failures,
            "failures": failures,
            "model": response.get("model"),
            "provider": response.get("provider"),
            "finish_reason": ((response.get("choices") or [{}])[0]).get("finish_reason"),
            "elapsed_seconds": round(elapsed, 3),
            "usage": usage,
            "request_sha256": sha256_file(request_path),
            "response_sha256": sha256_file(response_path),
            "proposal_sha256": sha256_file(proposal_path) if proposal_path.is_file() else None,
            "authority": "proposal_only; semantic and promotion approval withheld",
        }
        write_json_new(attempt_dir / "receipt.json", receipt)
        receipts.append(receipt)
        print(
            f"candidate={ordinal} workflow_valid={not failures} "
            f"cost={float(usage.get('cost') or 0.0):.8f} elapsed={elapsed:.2f}s",
            flush=True,
        )
    key_bytes = key.encode("utf-8")
    if any(key_bytes in path.read_bytes() for path in output_root.rglob("*") if path.is_file()):
        raise RuntimeError("credential leak detected in evidence output")
    total_cost = sum(float((item.get("usage") or {}).get("cost") or 0.0) for item in receipts)
    complete = len(receipts) == packet["candidate_count"] and all(
        item.get("workflow_valid") is True for item in receipts
    )
    summary = {
        "schema_version": "fusion.managed-worker-summary/v1",
        "created_at": utc_now(),
        "task_id": packet["task_id"],
        "risk_tier": packet["risk_tier"],
        "model": profile["model"],
        "provider": profile["provider"],
        "candidate_count": packet["candidate_count"],
        "workflow_valid_candidates": sum(item.get("workflow_valid") is True for item in receipts),
        "total_reported_cost_usd": round(total_cost, 8),
        "eligible_for_independent_lead_review": complete,
        "semantic_approval": False,
        "promotion_authorized": False,
        "boundary": "proposal_only; deterministic project gates and independent lead approval required",
        "profile_sha256": sha256_file(profile_copy),
        "packet_sha256": sha256_file(packet_copy),
        "endpoint_record_sha256": sha256_file(endpoint_record),
        "receipts": receipts,
    }
    write_json_new(output_root / "summary.json", summary)
    write_json_new(output_root / "seal.json", seal_evidence(output_root))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a proposal-only OpenRouter worker packet")
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--key-file", type=Path)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    key_path = args.key_file
    if key_path is None:
        configured = os.environ.get("OPENROUTER_API_KEY_FILE")
        if not configured:
            raise SystemExit("provide --key-file or OPENROUTER_API_KEY_FILE")
        key_path = Path(configured)
    try:
        summary = run(
            profile_path=args.profile.resolve(),
            packet_path=args.packet.resolve(),
            output_root=args.output.resolve(),
            key_path=key_path.resolve(),
            resume=args.resume,
        )
    except Exception as exc:
        print(f"WORKER FAILED CLOSED: {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["eligible_for_independent_lead_review"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
