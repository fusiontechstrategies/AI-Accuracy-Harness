from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "PACKAGE_SHA256SUMS.txt"
ANCHOR = ROOT / "PACKAGE_SHA256SUMS.sha256"
LINE = re.compile(r"([0-9a-f]{64})  ([^\\]+)")
EXCLUDED_PARTS = {
    ".git",
    ".hypothesis",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "venv",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_line(text: str) -> tuple[str, str]:
    match = LINE.fullmatch(text)
    if not match:
        raise ValueError(f"malformed manifest line: {text!r}")
    digest, relative = match.groups()
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != relative:
        raise ValueError(f"non-canonical manifest path: {relative!r}")
    return digest, relative


def main() -> int:
    anchor_lines = ANCHOR.read_text(encoding="utf-8").splitlines()
    if len(anchor_lines) != 1:
        raise SystemExit("PACKAGE NOT VERIFIED: malformed manifest anchor")
    expected_manifest_hash, anchor_name = parse_line(anchor_lines[0])
    if anchor_name != MANIFEST.name or sha256_file(MANIFEST) != expected_manifest_hash:
        raise SystemExit("PACKAGE NOT VERIFIED: manifest anchor mismatch")
    expected: dict[str, str] = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, relative = parse_line(line)
        if relative in expected:
            raise SystemExit(f"PACKAGE NOT VERIFIED: duplicate entry {relative}")
        expected[relative] = digest
    actual: dict[str, Path] = {}
    for path in ROOT.rglob("*"):
        if path.is_symlink():
            raise SystemExit(f"PACKAGE NOT VERIFIED: symbolic link {path}")
        if (
            path.is_file()
            and path not in {MANIFEST, ANCHOR}
            and not EXCLUDED_PARTS.intersection(path.parts)
        ):
            actual[path.relative_to(ROOT).as_posix()] = path
    if set(expected) != set(actual):
        raise SystemExit("PACKAGE NOT VERIFIED: inventory mismatch")
    mismatches = [
        relative
        for relative, wanted in expected.items()
        if sha256_file(actual[relative]) != wanted
    ]
    if mismatches:
        raise SystemExit(f"PACKAGE NOT VERIFIED: hash mismatch {sorted(mismatches)}")
    print(f"PACKAGE VERIFIED: {len(expected)} payload files")
    print(f"MANIFEST SHA256: {expected_manifest_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
