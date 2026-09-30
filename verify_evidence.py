from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import openrouter_worker as worker  # noqa: E402


def verify(root: Path) -> dict[str, Any]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("evidence root is missing or linked")
    seal_path = root / "seal.json"
    summary_path = root / "summary.json"
    if not seal_path.is_file() or not summary_path.is_file():
        raise ValueError("evidence seal or summary is missing")
    seal = worker.load_json_object(seal_path, label="evidence seal")
    rows = seal.get("files")
    if not isinstance(rows, list):
        raise ValueError("evidence seal file inventory is invalid")
    expected: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256"}:
            raise ValueError("evidence seal row is invalid")
        relative = row["path"]
        path = Path(relative)
        if (
            not isinstance(relative, str)
            or path.is_absolute()
            or ".." in path.parts
            or path.as_posix() != relative
            or relative == "seal.json"
            or relative in expected
        ):
            raise ValueError("evidence seal path is invalid")
        expected[relative] = row
    actual: dict[str, Path] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symbolic link rejected: {path}")
        if path.is_file() and path != seal_path:
            actual[path.relative_to(root).as_posix()] = path
    if set(expected) != set(actual):
        raise ValueError("evidence inventory is incomplete or contains unsealed files")
    for relative, row in expected.items():
        path = actual[relative]
        if path.stat().st_size != row["bytes"] or worker.sha256_file(path) != row["sha256"]:
            raise ValueError(f"evidence hash mismatch: {relative}")
    if seal.get("file_count") != len(rows):
        raise ValueError("evidence seal file count is invalid")
    if seal.get("root_sha256") != worker.sha256_bytes(worker.canonical_bytes(rows)):
        raise ValueError("evidence seal root hash is invalid")
    summary = worker.load_json_object(summary_path, label="worker summary")
    profile = worker.load_json_object(root / "provider-profile.json", label="provider profile")
    packet = worker.load_json_object(root / "task-packet.json", label="task packet")
    worker.validate_profile(profile)
    worker.validate_packet(packet)
    if summary.get("profile_sha256") != worker.sha256_file(root / "provider-profile.json"):
        raise ValueError("summary profile hash mismatch")
    if summary.get("packet_sha256") != worker.sha256_file(root / "task-packet.json"):
        raise ValueError("summary packet hash mismatch")
    disk_receipts: list[dict[str, Any]] = []
    for receipt_path in sorted(root.glob("candidate-*/attempt-*/receipt.json")):
        receipt = worker.load_json_object(receipt_path, label="call receipt")
        attempt = receipt_path.parent
        request_path = attempt / "request.json"
        response_path = attempt / "response.json"
        proposal_path = attempt / "proposal.json"
        if receipt.get("request_sha256") != worker.sha256_file(request_path):
            raise ValueError("receipt request hash mismatch")
        if receipt.get("response_sha256") != worker.sha256_file(response_path):
            raise ValueError("receipt response hash mismatch")
        if receipt.get("proposal_sha256") != worker.sha256_file(proposal_path):
            raise ValueError("receipt proposal hash mismatch")
        response = worker.load_json_object(response_path, label="response")
        proposal, failures = worker.validate_response(response, profile=profile, packet=packet)
        if failures or proposal is None:
            raise ValueError("independent response replay failed")
        if proposal_path.read_bytes() != worker.canonical_bytes(proposal):
            raise ValueError("proposal replay mismatch")
        disk_receipts.append(receipt)
    summary_receipts = summary.get("receipts")
    if not isinstance(summary_receipts, list) or summary_receipts != disk_receipts:
        raise ValueError("summary receipt census mismatch")
    if len(disk_receipts) != packet["candidate_count"]:
        raise ValueError("candidate count mismatch")
    if not all(item.get("workflow_valid") is True for item in disk_receipts):
        raise ValueError("one or more candidates were not workflow-valid")
    return {
        "schema_version": "fusion.evidence-verification/v1",
        "status": "VERIFIED",
        "task_id": packet["task_id"],
        "files": len(rows),
        "candidates": len(disk_receipts),
        "seal_root_sha256": seal["root_sha256"],
        "semantic_approval": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Independently verify a managed-worker evidence run")
    parser.add_argument("evidence_root", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.evidence_root.resolve())
    except Exception as exc:
        print(f"EVIDENCE NOT VERIFIED: {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
