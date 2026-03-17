"""File discovery by glob pattern."""
import os
from typing import List


def scan_files(
    path: str,
    extensions: List[str],
    excludes: List[str] | None = None,
) -> List[str]:
    excludes = set(excludes or [])
    matched = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in excludes]
        for filename in files:
            _, ext = os.path.splitext(filename)
            if ext in extensions:
                matched.append(os.path.join(root, filename))
    return sorted(matched)
