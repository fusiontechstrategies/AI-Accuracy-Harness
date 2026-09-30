from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "PACKAGE_SHA256SUMS.txt"
ANCHOR = ROOT / "PACKAGE_SHA256SUMS.sha256"
EXCLUDED = {MANIFEST.name, ANCHOR.name}
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


def main() -> int:
    files = []
    for path in ROOT.rglob("*"):
        if path.is_symlink():
            raise SystemExit(f"symbolic link rejected: {path}")
        if (
            path.is_file()
            and path.name not in EXCLUDED
            and not EXCLUDED_PARTS.intersection(path.parts)
        ):
            files.append(path)
    lines = [
        f"{sha256_file(path)}  {path.relative_to(ROOT).as_posix()}"
        for path in sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())
    ]
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    ANCHOR.write_text(
        f"{sha256_file(MANIFEST)}  {MANIFEST.name}\n", encoding="utf-8", newline="\n"
    )
    print(f"WROTE {len(lines)} payload hashes")
    print(f"MANIFEST SHA256 {sha256_file(MANIFEST)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
